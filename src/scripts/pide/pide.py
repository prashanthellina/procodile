#!/usr/bin/env python
'''
Procedural IDE - PIDE
'''

import os
import sys
import traceback
import time
import optparse
import logging
import sqlite3
import glob

import wx
import wx.aui
import wx.py
import wx.lib.flatnotebook as fnb
import wx.lib.agw.genericmessagedialog as GMD
import ogre.renderer.OGRE as ogre

from procodile.utils import create_logger, get_user_app_dir, escape_html
from procodile.graphics import MaterialManager, MaterialColor, Color
from procodile.loader import set_loader, Loader, get_class, get_loader
from procodile.recipe import RecipeBasedGenerator, RecipeConfig
from procodile.repository.client import Client
from procodile.utils import log_function_call as logfn
from procodile.utils import log_method_call as logmt

from dialogs import get_generator_info, get_upload_details
from dialogs import display_tab_properties, BugReportDialog
from utils import load_image, PIDEException, ContainerPanel, app_abs_path
from document import Document, DocumentManager
import viewer

log = logging.getLogger()
IS_FIRST_RUN = False

class StreamLogger:
    def __init__(self, stream, log):
        self.stream = stream
        self.log = log

    def write(self, text):
        self.log.info(text)

class SplashScreen(wx.SplashScreen):
    def __init__(self):
        bmp = wx.Image(app_abs_path('images/splash.png')).ConvertToBitmap()
        wx.SplashScreen.__init__(self, bmp,
                                 wx.SPLASH_CENTRE_ON_SCREEN | \
                                 wx.SPLASH_NO_TIMEOUT,
                                 5000, None, -1)
        self.has_app_initialized = False
        self.min_time_shown = False
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        wx.FutureCall(2000, self.check_and_close)

    def OnClose(self, evt):
        evt.Skip()
        self.Hide()

    def app_initialized(self):
        self.has_app_initialized = True
        if self.min_time_shown:
            self.Close()

    def check_and_close(self):
        self.min_time_shown = True
        if self.has_app_initialized:
            self.Close()

class AppState:
    '''
    Represents persistent application state (across sessions).
    '''
    NUM = 10

    @logmt
    def __init__(self, fpath):
        #: path of database file
        self.fpath = fpath

        #: connection to database
        self._conn = sqlite3.connect(fpath)

        self._conn.row_factory = sqlite3.Row # key-value type row access

        #: cursor opened on database
        self._cursor = self._conn.cursor()

        self._ensure_schema()

    def _ensure_schema(self):
        state_schema_fpath = app_abs_path('state.schema')
        self._cursor.executescript(open(state_schema_fpath).read())
        self._conn.commit()

    @logmt
    def get_frequent_generators(self, num=NUM):
        query = 'SELECT * FROM generators ORDER BY count DESC LIMIT ?'
        return list(self._cursor.execute(query, (num,)))

    @logmt
    def get_recent_generators(self, num=NUM, all=False):
        query = 'SELECT * FROM generators ORDER BY time DESC LIMIT ?'
        results = list(self._cursor.execute(query, (num,)))
        if not all:
            results = [(r['location'],r['id'],r['version'])  for r in results]
            print 'results are ', results

        return results

    @logmt
    def update_generator(self, location, _id, version=None):
        query = 'SELECT count FROM generators WHERE location=? and \
                    id = ? and version = ?'
        count = self._cursor.execute(query, (location, _id, version)).fetchone()
        count = 0 if count is None else count[0]
        count += 1

        query = 'INSERT OR REPLACE INTO generators (time, count, \
                    location, id, version) VALUES (?, ?, ?, ?, ?)'
        self._cursor.execute(query, (int(time.time()), count,
                location, _id, version))
        self._conn.commit()
        return count

    @logmt
    def get_settings(self):
        query = 'SELECT key, value FROM settings'
        c = self._cursor
        return dict([(r['key'], r['value']) for r in c.execute(query)])

    @logmt
    def get_setting(self, key):
        query = 'SELECT value FROM settings WHERE key = ?'
        value = self._cursor.execute(query, key).fetchone()
        return None if value is None else value[0]

    @logmt
    def set_setting(self, key, value):
        query = 'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)'
        self._cursor.execute(query, (key, value))
        self._conn.commit()

    @logmt
    def update_autocomplete(self, key, value):
        if not value:
            return

        query = 'SELECT count FROM autocomplete WHERE key=? AND value=?'
        count = self._cursor.execute(query, (key, value)).fetchone()
        count = 0 if count is None else count[0]
        count += 1

        query = 'INSERT OR REPLACE INTO autocomplete (time, count, \
                    key, value) VALUES (?, ?, ?, ?)'
        self._cursor.execute(query, (int(time.time()), count,
                key, value))
        self._conn.commit()
        return count

    @logmt
    def get_autocomplete(self, key, num=NUM, ordering='recent', all=False):
        if ordering == 'recent':
            query = 'SELECT * FROM autocomplete WHERE key = ? \
                     ORDER BY time DESC LIMIT ?'
        elif ordering == 'frequency':
            query = 'SELECT * FROM autocomplete WHERE key = ? \
                     ORDER BY count DESC LIMIT ?'

        results = list(self._cursor.execute(query, (key, num)))
        if not all:
            results = [r['value'] for r in results]

        return results

class LogFormatter(logging.Formatter):
    LEVEL_COLORS = {
            logging.DEBUG : 'grey',
            logging.INFO : 'black',
            logging.WARNING : 'orange',
            logging.ERROR : 'maroon',
            logging.CRITICAL : 'red',
        }
    
    def __init__(self):
        logging.Formatter.__init__(self)

    def _prepare_message(self, message):
        m = message

        if not m:
            return ''

        m = escape_html(m)
        m = m.replace('\n', '<br>')
        m = m.replace('\t', '&nbsp;' * 4)
        m = m.replace(' ', '&nbsp;')

        return m

    def format(self, record):
        r = record
        P = self._prepare_message

        asctime = r.asctime
        level = r.levelname
        fname = r.filename
        message = P(r.getMessage())
        exc_text = P(r.exc_text)
        lcolor = self.LEVEL_COLORS.get(r.levelno, 'grey')

        html = '<font color="%(lcolor)s">%(asctime)s: '\
              '%(level)s: '\
              '%(fname)s: '\
              '%(message)s'\
               '%(exc_text)s</font>'\
              % locals()

        return html

class LogViewer(wx.html.HtmlWindow, logging.Handler):

    def __init__(self, parent, id):
        wx.html.HtmlWindow.__init__(self, parent, id)
        logging.Handler.__init__(self)

        self.SetPage("")
        self.setFormatter(LogFormatter())
        self.parent = parent

    def emit(self, record):

        if record.levelno >= logging.WARNING:
            self.parent.on_important_log_event()

        self.Freeze()
        self.AppendToPage("<br>"+self.format(record))
        y = self.GetScrollRange(0)
        self.Scroll(0, y)
        self.Refresh()
        self.Thaw()

class AppFrame(wx.Frame):
    ID_FILE_BUTTONBAR = wx.NewId()
    ID_DOC_BUTTONBAR = wx.NewId()
    ID_VIEW_SETTINGS_BUTTONBAR = wx.NewId()
    ID_VIEW_WINDOWS_BUTTONBAR = wx.NewId()

    ID_NEW_DOCUMENT = wx.NewId()
    ID_SAVE_DOCUMENT = wx.NewId()
    ID_SAVE_DOCUMENT_AS = wx.NewId()
    ID_SAVE_SCREENSHOT = wx.NewId()
    ID_SAVE_SCREENSHOTS = wx.NewId()
    ID_UPLOAD = wx.NewId()
    ID_EXPORT_COLLADA = wx.NewId()
    ID_DOC_RELOAD = wx.NewId()
    ID_DOC_CLOSE = wx.NewId()
    ID_DOC_RUN = wx.NewId()
    ID_DOC_PAUSE = wx.NewId()
    ID_DOC_STOP = wx.NewId()

    ID_ABOUT = wx.NewId()
    ID_SETTINGS = wx.NewId()

    ID_VIEW_SHADING = wx.NewId()
    ID_VIEW_SHADING_SMOOTH = wx.NewId()
    ID_VIEW_SHADING_FLAT = wx.NewId()

    ID_VIEW_NAVIGATION = wx.NewId()
    ID_VIEW_NAVIGATION_FLY = wx.NewId()
    ID_VIEW_NAVIGATION_EXAMINE = wx.NewId()

    ID_VIEW_FIT = wx.NewId()
    ID_VIEW_LEFT = wx.NewId()
    ID_VIEW_BOTTOM = wx.NewId()
    ID_VIEW_BACK = wx.NewId()
    ID_VIEW_PERSPECTIVE = wx.NewId()
    ID_VIEW_FRONT = wx.NewId()
    ID_VIEW_TOP = wx.NewId()
    ID_VIEW_RIGHT = wx.NewId()

    ID_WND_BUILDTREE = wx.NewId()
    ID_WND_XPATH = wx.NewId()
    ID_WND_CONFIGURATION = wx.NewId()
    ID_WND_DEBUG = wx.NewId()
    ID_WND_SHOWALL = wx.NewId()
    ID_WND_HIDEALL = wx.NewId()

    ID_TAB_PANEL = wx.NewId()
    ID_TAB_DELETE = wx.NewId()
    ID_TAB_PROPERTIES = wx.NewId()

    ID_BUG_REPORT = wx.NewId()

    MIN_SIZE = (400, 300)

    @logmt
    def __init__(self, parent, app_state,
                       id=-1,
                       title="",
                       pos=wx.DefaultPosition,
                       size=wx.DefaultSize,
                       style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER |
                             wx.CLIP_CHILDREN | wx.MAXIMIZE,
                       app=None):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self.app = app
        self.app_state = app_state

        self.documents = {}
        self.vcontainers = {} #: viewer containers

        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow(self)

        self.viewer = None #: 3D viewer panel
        self.pyshell = None #: python shell window
        self.log_viewer = None #: Log viewer window
        self.debug_panel = None #: debug panel contains
                                # log_viewer and pyshell windows

        self.xpath_container = None #: Xpath container
        self.build_tree_container = None #: Build Tree container
        self.config_container = None #: Recipe Configuration container

        self.menu_bar = None #: application menu
        self.status_bar = None #: application status bar
        self.tool_bars = [] #: application tool bars

        self.tabs_panel = None #: tabs panel
        self._tab_images = None #: image list for tabs
        self._tab_image_indices = None #: tab image indices map

        self._close_sent = False
        self._cleaning_up = False

        # start building frame
        self.SetMinSize(self.MIN_SIZE)

        favicon = wx.Icon(app_abs_path('images/procodile.ico'),
                          wx.BITMAP_TYPE_ICO, 16, 16)
        self.SetIcon(favicon)

        self._create_menus()
        self._create_statusbar()
        self._create_toolbar()
        self._create_panes()

        self.mgr.Update()
        self._register_for_events()

    def _add_menu_item(self, menu, item, name, help='', image=None):
        menu_item = wx.MenuItem(menu, item, name, help)
        if image:
            image = app_abs_path('icons', image + '.png')
            image = load_image(image, (16, 16))
            menu_item.SetBitmap(image)

        menu.AppendItem(menu_item)

    @logmt
    def _create_menus(self):
        s = self
        A = self._add_menu_item

        mb = wx.MenuBar()

        file_menu = wx.Menu()
        A(file_menu, s.ID_NEW_DOCUMENT, '&Open\tCtrl+O', '', 'new_document')
        A(file_menu, s.ID_SAVE_DOCUMENT, '&Save\tCtrl+S', '', 'save')
        A(file_menu, s.ID_SAVE_DOCUMENT_AS, 'Save &As\tCtrl+A', '', 'saveas')
        A(file_menu, s.ID_SAVE_SCREENSHOT, 'Save Screensho&t\tCtrl+I', '',
                                           'save_screenshot')
        A(file_menu, s.ID_UPLOAD, '&Upload\tCtrl+U', '', 'upload')
        A(file_menu, s.ID_EXPORT_COLLADA, '&Export Collada\tCtrl+E',
          '', '')
        A(file_menu, wx.ID_EXIT, '&Exit\tAlt+F4')

        doc_menu = wx.Menu()
        A(doc_menu, s.ID_DOC_RUN, '&Run\tF2', '', 'play')
        A(doc_menu, s.ID_DOC_PAUSE, '&Pause\tF3', '', 'pause')
        A(doc_menu, s.ID_DOC_STOP, '&Stop\tF4', '', 'stop')
        doc_menu.AppendSeparator()
        A(doc_menu, s.ID_DOC_RELOAD, 'R&eload\tF5', '', 'reload')
        A(doc_menu, s.ID_DOC_CLOSE, '&Close\tCtrl+F4', '', 'close')
        doc_menu.AppendSeparator()
        A(doc_menu, s.ID_SAVE_SCREENSHOTS, 'Save Screensho&ts\tCtrl+Shift+I',
            '', 'save_screenshot')

        windows_menu = wx.Menu()
        A(windows_menu, s.ID_WND_XPATH, '&Xpath', '', 'generator_icon')
        A(windows_menu, s.ID_WND_BUILDTREE, '&Build Tree', '', 'build_tree')
        A(windows_menu, s.ID_WND_CONFIGURATION, '&Configuration', '',
            'configuration')
        A(windows_menu, s.ID_WND_DEBUG, 'Deb&ug', '', 'debug')
        windows_menu.AppendSeparator()
        A(windows_menu, s.ID_WND_SHOWALL, 'Show &All\tCtrl+Shift+A', '',
            'showall')
        A(windows_menu, s.ID_WND_HIDEALL, '&Hide All\tCtrl+Shift+H', '',
            'hideall')

        view_menu = wx.Menu()

        shading_menu = wx.Menu()
        A(shading_menu, s.ID_VIEW_SHADING_SMOOTH, '&Smooth', '', 'smooth')
        A(shading_menu, s.ID_VIEW_SHADING_FLAT, '&Flat', '', 'flat')

        nav_menu = wx.Menu()
        A(nav_menu, s.ID_VIEW_NAVIGATION_FLY, '&Fly', '', 'vfly')
        A(nav_menu, s.ID_VIEW_NAVIGATION_EXAMINE, '&EXAMINE', '', 'vexamine')

        view_menu.AppendMenu(s.ID_VIEW_SHADING, '&Shading', shading_menu)
        view_menu.AppendMenu(s.ID_VIEW_NAVIGATION, '&Navigation', nav_menu)
        view_menu.AppendSeparator()
        A(view_menu, s.ID_VIEW_FIT, '&Fit to View\tCtrl+F', '', 'fit')
        view_menu.AppendSeparator()
        A(view_menu, s.ID_VIEW_LEFT, '&Left\tCtrl+1', '', 'vleft')
        A(view_menu, s.ID_VIEW_BOTTOM, '&Bottom\tCtrl+2', '', 'vbottom')
        A(view_menu, s.ID_VIEW_BACK, '&Back\tCtrl+3', '', 'vbehind')
        A(view_menu, s.ID_VIEW_PERSPECTIVE, '&Perspective\tCtrl+7', '', 'vperspective')
        A(view_menu, s.ID_VIEW_FRONT, '&Front\tCtrl+4', '', 'vfront')
        A(view_menu, s.ID_VIEW_TOP, '&Top\tCtrl+5', '', 'vtop')
        A(view_menu, s.ID_VIEW_RIGHT, '&Right\tCtrl+6', '', 'vright')

        help_menu = wx.Menu()
        A(help_menu, s.ID_ABOUT, '&About\tF1', '', 'about')
        A(help_menu, s.ID_SETTINGS, '&Settings', '', 'settings')
        A(help_menu, s.ID_BUG_REPORT, '&Report Bug', '', 'bug')

        mb.Append(file_menu, '&File')
        mb.Append(doc_menu, '&Document')
        mb.Append(windows_menu, '&Windows')
        mb.Append(view_menu, '&View')
        mb.Append(help_menu, '&Help')

        self.SetMenuBar(mb)
        self.menu_bar = mb

    @logmt
    def _create_statusbar(self):

        num_sections = 2
        self.status_bar = self.CreateStatusBar(num_sections, wx.ST_SIZEGRIP)
        self.status_bar.SetStatusWidths([-2, -3])
        self.status_bar.SetStatusText("Ready", 0)
        self.status_bar.SetStatusText("Procedural IDE", 1)

    @logmt
    def _create_toolbar(self):

        s = self
        size = (24, 24)

        def A(tb, _id, text, img, shelp='', lhelp=''):
            img = app_abs_path('icons', img + '.png')
            img = load_image(img, size)
            tb.AddLabelTool(_id, text, img, shortHelp=shelp, longHelp=lhelp)

        # main toolbar
        tb = wx.ToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                        wx.TB_FLAT | wx.TB_NODIVIDER)

        tb.SetToolBitmapSize(size)

        A(tb, s.ID_NEW_DOCUMENT, 'Open', 'new_document', 'Open Generator')
        A(tb, s.ID_SAVE_DOCUMENT, 'Save', 'save', 'Save Generator')
        A(tb, s.ID_SAVE_DOCUMENT_AS, 'Save As', 'saveas', 'Save Generator As')
        A(tb, s.ID_UPLOAD, 'Upload', 'upload', 'Upload Package')
        A(tb, s.ID_SAVE_SCREENSHOT, 'Save Screenshot', 'save_screenshot',
            'Save Screenshot')
        tb.AddSeparator()
        A(tb, s.ID_DOC_RUN, 'Run', 'play', 'Run Generator')
        A(tb, s.ID_DOC_PAUSE, 'Pause', 'pause', 'Pause Generator')
        A(tb, s.ID_DOC_STOP, 'Stop', 'stop', 'Stop Generator')
        A(tb, s.ID_DOC_RELOAD, 'Reload', 'reload', 'Reload Generator')

        tb.Realize()
        self.tool_bars.append(tb)

        # view toolbar
        tb = wx.ToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                        wx.TB_FLAT | wx.TB_NODIVIDER)

        tb.SetToolBitmapSize(size)

        A(tb, s.ID_VIEW_NAVIGATION, 'Navigation', 'vfly',
            'Change navigation to fly mode')
        A(tb, s.ID_VIEW_FIT, 'Fit', 'fit', 'Fit to View')
        tb.AddSeparator()
        A(tb, s.ID_VIEW_LEFT, 'Left', 'vleft', 'View from Left')
        A(tb, s.ID_VIEW_BOTTOM, 'Bottom', 'vbottom', 'View from Bottom')
        A(tb, s.ID_VIEW_BACK, 'Back', 'vbehind', 'View from Back')
        A(tb, s.ID_VIEW_PERSPECTIVE, 'Perspective', 'vperspective',
            'Perspective View')
        A(tb, s.ID_VIEW_FRONT, 'Front', 'vfront', 'View from Front')
        A(tb, s.ID_VIEW_TOP, 'Top', 'vtop', 'View from Top')
        A(tb, s.ID_VIEW_RIGHT, 'Right', 'vright', 'View from Right')

        tb.AddSeparator()
        A(tb, s.ID_BUG_REPORT, 'Report Bug', 'bug', 'Report Bug')

        tb.Realize()
        self.tool_bars.append(tb)

    @logmt
    def _create_panes(self):

        self.pyshell = wx.py.shell.Shell(self, -1,
                                locals=self.app.shell_vars)

        self.log_viewer = LogViewer(self, -1)
        log.addHandler(self.log_viewer)

        style = wx.aui.AUI_NB_DEFAULT_STYLE
        style &= ~wx.aui.AUI_NB_CLOSE_BUTTON
        style &= ~wx.aui.AUI_NB_CLOSE_ON_ALL_TABS
        style &= ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        self.debug_panel = wx.aui.AuiNotebook(self, style=style)
        self.debug_panel.AddPage(self.pyshell, 'Shell')
        self.debug_panel.AddPage(self.log_viewer, 'Log')

        self.viewer = viewer.Viewer(self, -1, self, size=(1, 1))
        self.viewer.Hide()

        self.xpath_container = ContainerPanel(self, -1)
        self.build_tree_container = ContainerPanel(self, -1)
        self.config_container = ContainerPanel(self, -1)

        style = fnb.FNB_NODRAG | fnb.FNB_ALLOW_FOREIGN_DND

        size = (16, 16)
        L = lambda x: load_image(app_abs_path('icons', x + '.png'), size)
        tg = self._tab_images = wx.ImageList(*size)
        ti = self._tab_image_indices = {}
        ti['running'] = tg.Add(L('doc_running'))
        ti['paused'] = tg.Add(L('doc_paused'))
        ti['idle'] = tg.Add(L('doc_idle'))

        self.tabs_panel = fnb.FlatNotebook(self, self.ID_TAB_PANEL, style=style)
        self.tabs_panel.SetImageList(tg)

        self._rmenu = wx.Menu()
        item = wx.MenuItem(self._rmenu, self.ID_TAB_PROPERTIES,
                           "Properties", "Tab Properties")
        self._rmenu.AppendItem(item)
        item = wx.MenuItem(self._rmenu, self.ID_TAB_DELETE,
                           "Close Tab\tCtrl+F4", "Close Tab")
        self._rmenu.AppendItem(item)

        self.tabs_panel.SetRightClickMenu(self._rmenu)

        self.mgr.AddPane(self.tabs_panel, wx.aui.AuiPaneInfo().
                            Name('tabs').Caption('Documents').
                            Top().CenterPane().MaximizeButton().
                            MinSize((320, 240)))

        self.mgr.AddPane(self.xpath_container, wx.aui.AuiPaneInfo().
                            Name('xpath_container').
                            Caption('Selection Suggestions').Right().
                            MaximizeButton().MinSize((250, 100)))

        self.mgr.AddPane(self.build_tree_container, wx.aui.AuiPaneInfo().
                            Name('build_tree_container').Caption('Build Tree').
                            Right().MaximizeButton().MinSize((250, 100)))

        self.mgr.AddPane(self.config_container, wx.aui.AuiPaneInfo().
                            Name('config_container').Caption('Configuration').
                            Left().MaximizeButton().MinSize((250, 200)))

        self.mgr.AddPane(self.debug_panel, wx.aui.AuiPaneInfo().
                            Name('debug').Caption('Debug').
                            Bottom().MaximizeButton().MinSize((150, 200)).
                            Hide())

        for index, tb in enumerate(self.tool_bars):
            self.mgr.AddPane(tb, wx.aui.AuiPaneInfo().
                                Name('tb_%s' % index).Caption("ToolBar").
                                ToolbarPane().Top().
                                PaneBorder(False))

    @logmt
    def _register_for_events(self):

        s = self

        s.Bind(wx.EVT_ERASE_BACKGROUND, s.OnEraseBackground)
        s.Bind(wx.EVT_SIZE, s.OnSize)
        s.Bind(wx.EVT_CLOSE, s.OnClose)

        s.Bind(wx.aui.EVT_AUI_PANE_CLOSE, s.OnPaneClose)

        s.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, s.OnPageChanged)
        s.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, s.OnPageClosing)
        s.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSED, s.OnPageClosed)

        # Menu and Toolbar events

        W = lambda f: logfn(getattr(self, f))

        map = (
                (W('on_open'), s.ID_NEW_DOCUMENT),
                (W('on_save'), s.ID_SAVE_DOCUMENT),
                (W('on_save_as'), s.ID_SAVE_DOCUMENT_AS),
                (W('on_save_screenshot'), s.ID_SAVE_SCREENSHOT),
                (W('on_save_screenshots'), s.ID_SAVE_SCREENSHOTS),
                (W('on_upload'), s.ID_UPLOAD),
                (W('on_export_collada'), s.ID_EXPORT_COLLADA),
                (W('on_doc_reload'), s.ID_DOC_RELOAD),
                (W('on_doc_close'), s.ID_DOC_CLOSE),
                (W('on_doc_run'), s.ID_DOC_RUN),
                (W('on_doc_pause'), s.ID_DOC_PAUSE),
                (W('on_doc_stop'), s.ID_DOC_STOP),
                (W('on_about'), s.ID_ABOUT),
                (W('on_settings'), s.ID_SETTINGS),
                (W('on_view_shading'), s.ID_VIEW_SHADING),
                (W('on_view_shading_smooth'), s.ID_VIEW_SHADING_SMOOTH),
                (W('on_view_shading_flat'), s.ID_VIEW_SHADING_FLAT),
                (W('on_view_navigation'), s.ID_VIEW_NAVIGATION),
                (W('on_view_navigation_fly'), s.ID_VIEW_NAVIGATION_FLY),
                (W('on_view_navigation_examine'), s.ID_VIEW_NAVIGATION_EXAMINE),
                (W('on_view_fit'), s.ID_VIEW_FIT),
                (W('on_view_left'), s.ID_VIEW_LEFT),
                (W('on_view_bottom'), s.ID_VIEW_BOTTOM),
                (W('on_view_back'), s.ID_VIEW_BACK),
                (W('on_view_perspective'), s.ID_VIEW_PERSPECTIVE),
                (W('on_view_front'), s.ID_VIEW_FRONT),
                (W('on_view_top'), s.ID_VIEW_TOP),
                (W('on_view_right'), s.ID_VIEW_RIGHT),
                (W('on_wnd_xpath'), s.ID_WND_XPATH),
                (W('on_wnd_buildtree'), s.ID_WND_BUILDTREE),
                (W('on_wnd_configuration'), s.ID_WND_CONFIGURATION),
                (W('on_wnd_debug'), s.ID_WND_DEBUG),
                (W('on_wnd_showall'), s.ID_WND_SHOWALL),
                (W('on_wnd_hideall'), s.ID_WND_HIDEALL),
                (W('on_bug_report'), s.ID_BUG_REPORT),
              )

        for callback, _id in map:
            s.Bind(wx.EVT_MENU, callback, id=_id)
            s.Bind(wx.EVT_TOOL, callback, id=_id)
            s.Bind(wx.EVT_TOOL_RCLICKED, callback, id=_id)

        s.Bind(wx.EVT_MENU, s.OnExit, id=wx.ID_EXIT)
        s.Bind(wx.EVT_MENU, s.OnTabDelete, id=self.ID_TAB_DELETE)
        s.Bind(wx.EVT_MENU, s.OnTabProperties, id=self.ID_TAB_PROPERTIES)

    @logmt
    def on_bug_report(self, event):
        dlg = BugReportDialog(self.app.frame, -1)
        dlg.CenterOnParent()
        response = dlg.ShowModal()

        if response == wx.ID_CANCEL:
            return

        username = dlg.username.GetValue()
        password = dlg.password.GetValue()
        description = dlg.description.GetValue()
        attachment_path = dlg.attachment.GetValue()
        bug_type = dlg.bug_type.GetValue()

        try:
            client = Client('http://procodile.vaspra.com/api')
            if username:
                client.login(username, password)
            client.bug_report(bug_type, description, attachment_path)
        except Client.Exception, e:
            print ''.join(traceback.format_exception(*sys.exc_info()[:3]))

            dlg = wx.MessageDialog(self.frame,
                    'Error occured when trying to report bug.\n' + \
                    e.message,
                    'Bug reporting failed',
                    wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            self.on_bug_report()

    @logmt
    def add_document(self, doc, select=True):
        viewer_container = ContainerPanel(self, -1)

        self.vcontainers[doc] = viewer_container
        self.documents[viewer_container] = doc
        self.tabs_panel.AddPage(viewer_container, doc.get_display_name(),
                                select=select,
                                imageId=self._tab_image_indices['idle'])

    @logmt
    def del_document(self, doc):
        viewer_container = self.vcontainers[doc]
        if viewer_container not in self.documents:
            raise PIDEException('unknown document')

        index = self.tabs_panel.GetPageIndex(viewer_container)
        self.tabs_panel.DeletePage(index)

    @logmt
    def get_current_document(self):
        page = self.tabs_panel.GetCurrentPage()
        return self.documents[page] if page else None

    @logmt
    def update_document_state(self, doc):
        if doc not in self.vcontainers:
            return

        vcontainer = self.vcontainers[doc]
        page_index = self.tabs_panel.GetPageIndex(vcontainer)

        I = self._tab_image_indices
        image = I['idle']

        if doc.state == doc.STATE_RUNNING:
            image = I['running']

        elif doc.state == doc.STATE_PAUSED:
            image = I['paused']

        self.tabs_panel.SetPageImage(page_index, image)

    @logmt
    def _attach_to_container(self, widget, container):
        success = widget.Reparent(container)
        if not success:
            log.warning('reparenting failed')

        sizer = container.GetSizer()
        sizer.Add(widget, 1, wx.EXPAND)
        widget.Show()

        sizer.Layout()

    @logmt
    def _detach_from_container(self, widget, container):
        widget.Hide()

        sizer = container.GetSizer()
        success = sizer.Detach(widget)
        sizer.Layout()

        success = widget.Reparent(self)
        if not success:
            log.warning('reparenting failed')

    @logmt
    def _set_document(self, doc):
        a = self._attach_to_container

        viewer_container = self.vcontainers[doc]

        a(doc.xpath_widget, self.xpath_container)
        a(doc.obtree_widget, self.build_tree_container)
        a(doc.conf_widget, self.config_container)
        a(self.viewer, viewer_container)

        self.viewer.set_document(doc)
        self.viewer.Show()
        viewer_container.Show()

    @logmt
    def _unset_document(self, doc):
        viewer_container = self.vcontainers[doc]
        viewer_container.Hide()
        self.viewer.Hide()
        self.viewer.unset_document()

        d = self._detach_from_container

        d(self.viewer, viewer_container)
        d(doc.xpath_widget, self.xpath_container)
        d(doc.obtree_widget, self.build_tree_container)
        d(doc.conf_widget, self.config_container)

    @logmt
    def save_screenshot(self, fpath=None):

        state = self.app_state

        # get last used screenshot save location
        dirpath = os.getcwd()
        screenshot_dirs = state.get_autocomplete('screenshot_dir', num=1)
        if screenshot_dirs:
            dirpath = screenshot_dirs[0]

        # choose unused default filename
        fname = ''
        for i in xrange(10000):
            cur_fname = 'screeshot%d.jpg' % i
            if not os.path.exists(os.path.join(dirpath, cur_fname)):
                fname = cur_fname
                break

        # if fpath was not provided, show save dialog
        if not fpath:
            image_types = '*.jpeg;*.jpg;*.bmp;*.png;*.gif'
            wildcard = 'Images (%s)|%s|' % (image_types, image_types) + \
                       'All files (*.*)|*.*'

            dlg = wx.FileDialog(self,
                            message='Save screenshot as ...',
                            defaultDir=dirpath,
                            defaultFile=fname,
                            wildcard=wildcard,
                            style=wx.SAVE | wx.FD_OVERWRITE_PROMPT,
                            )
            dlg.SetFilterIndex(0)

            if dlg.ShowModal() == wx.ID_OK:
                fpath = dlg.GetPath()

            dlg.Destroy()

        if not fpath:
            return

        # ensure image extension
        extension = fpath.split('.')[-1].lower()
        if extension not in ('jpg', 'jpeg', 'png', 'bmp', 'gif'):
            return

        self.viewer.save_screenshot(fpath)

        # remember screenshot save location
        dirpath = os.path.dirname(fpath)
        state.update_autocomplete('screenshot_dir', dirpath)

    @logmt
    def OnPageChanged(self, event):
        if self._cleaning_up:
            return

        self.Freeze()

        try:
            t = self.tabs_panel

            to_index = event.GetSelection()
            from_index = event.GetOldSelection()

            to_page = t.GetPage(to_index)
            from_page = t.GetPage(from_index) if from_index != -1 else None

            if from_page:
                doc = self.documents[from_page]
                self._unset_document(doc)

            doc = self.documents[to_page]
            self._set_document(doc)
        finally:
            self.Thaw()

    @logmt
    def OnPageClosing(self, event):
        index = event.GetSelection()
        viewer_container = self.tabs_panel.GetPage(index)
        self._cleanup_document(viewer_container)

    @logmt
    def OnPageClosed(self, event):
        pass

    @logmt
    def _cleanup_document(self, viewer_container):
        self.Freeze()

        try:

            doc = self.documents.pop(viewer_container)
            self._unset_document(doc)

            viewer_container = self.vcontainers.pop(doc)

            self.app.on_document_tab_closed(doc)
        finally:
            self.Thaw()

    @logmt
    def OnTabDelete(self, event):
        self.tabs_panel.DeletePage(self.tabs_panel.GetSelection())

    @logmt
    def OnTabProperties(self, event):
        index = self.tabs_panel.GetSelection()
        page = self.tabs_panel.GetPage(index)
        doc = self.documents[page]

        name = self.tabs_panel.GetPageText(index)
        new_name = display_tab_properties(self, name, doc) or name

        if name != new_name:
            self.tabs_panel.SetPageText(index, new_name)

    def change_tabname(self, name):
        index = self.tabs_panel.GetSelection()
        self.tabs_panel.SetPageText(index, name)

    def OnPaneClose(self, event):
        pass

    @logmt
    def OnClose(self, event):
        if not self._close_sent:
            self._close_sent = True
            self.app.on_close()
        event.Veto()

    @logmt
    def OnExit(self, event):
        self.Close()

    @logmt
    def cleanup(self):

        self._cleaning_up = True

        log.removeHandler(self.log_viewer)
        self.log_viewer.close()

        for doc in self.documents.values():
            self.del_document(doc)

        if hasattr(self, 'mgr'):
            self.mgr.UnInit()
            del self.mgr

        self.Destroy()

    def OnEraseBackground(self, event):
        event.Skip()

    def OnSize(self, event):
        pass

    def on_open(self, event):
        self.app.load_generator()

    def on_save(self, event):
        self.app.save_document()

    def on_save_as(self, event):
        self.app.save_document_as()

    def on_save_screenshot(self, event):
        self.app.save_screenshot()

    def on_save_screenshots(self, event):
        self.app.save_screenshots()

    def on_upload(self, event):
        self.app.upload_package()

    def on_export_collada(self, event):
        self.app.export_collada()

    def on_doc_reload(self, event):
        self.app.on_reload()

    def on_doc_close(self, event):
        self.app.del_document()

    def on_doc_run(self, event):
        self.app.on_run()

    def on_doc_pause(self, event):
        self.app.pause_document()

    def on_doc_stop(self, event):
        self.app.on_stop()

    def on_about(self, event):
        msg = 'PIDE - Procodile IDE\n' + \
              'Advanced Procedural Geometry made easy!\n' + \
              '(c) Copyright 2009, Vaspra'

        dlg = wx.MessageDialog(self, msg, "About PIDE",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def on_settings(self, event):
        pass

    def on_view_shading(self, event):
        pass

    def on_view_shading_flat(self, event):
        pass

    def on_view_shading_smooth(self, event):
        pass

    def on_view_navigation(self, event):
        mode = self.app.toggle_document_navigation(None)
        self.app.set_document_view(None, 'perspective')

        FLY_MODE = 0
        EXAMINE_MODE = 1

        if mode  == FLY_MODE:
            shelp = 'Change navigation to examine mode'
            image = 'vexamine'
        else:
            shelp = 'Change navigation to fly mode'
            image = 'vfly'

        image = app_abs_path('icons', image + '.png')
        image = load_image(image, (24, 24))

        toolbar = event.GetEventObject()
        toolbar.SetToolNormalBitmap(self.ID_VIEW_NAVIGATION, image)
        toolbar.SetToolShortHelp(self.ID_VIEW_NAVIGATION, shelp)

    def on_view_navigation_fly(self, event):
        self.app.set_document_navigation(None, 'fly')

    def on_view_navigation_examine(self, event):
        self.app.set_document_navigation(None, 'examine')

    def on_view_fit(self, event):
        self.app.set_document_view(None, 'fit')

    def on_view_left(self, event):
        self.app.set_document_view(None, 'left')

    def on_view_bottom(self, event):
        self.app.set_document_view(None, 'bottom')

    def on_view_back(self, event):
        self.app.set_document_view(None, 'back')

    def on_view_perspective(self, event):
        self.app.set_document_view(None, 'perspective')

    def on_view_front(self, event):
        self.app.set_document_view(None, 'front')

    def on_view_top(self, event):
        self.app.set_document_view(None, 'top')

    def on_view_right(self, event):
        self.app.set_document_view(None, 'right')

    def _toggle(self, pane):
        pane = self.mgr.GetPane(pane)
        pane.Show(not pane.IsShown())
        self.mgr.Update()

    def on_wnd_xpath(self, event):
        self._toggle('xpath_container')

    def on_wnd_buildtree(self, event):
        self._toggle('build_tree_container')

    def on_wnd_configuration(self, event):
        self._toggle('config_container')

    def on_wnd_debug(self, event):
        self._toggle('debug')

    def _wnd_set_all(self, show=True):
        for pane in ('xpath_container',
                     'build_tree_container',
                     'config_container',
                     'debug'):
            pane = self.mgr.GetPane(pane)
            pane.Show() if show else pane.Hide()

        self.mgr.Update()

    def on_wnd_showall(self, event):
        self._wnd_set_all(True)

    def on_wnd_hideall(self, event):
        self._wnd_set_all(False)

    def on_important_log_event(self):

        def fn():
            debug_pane = self.mgr.GetPane('debug')
            if not debug_pane.IsShown():
                debug_pane.Show()
                self.mgr.Update()

            page = self.debug_panel.GetPageIndex(self.log_viewer)
            self.debug_panel.SetSelection(page)

        wx.CallAfter(fn)

class App(wx.App):
    @logmt
    def __init__(self, options):
        wx.App.__init__(self, redirect=False)

        self._splash = SplashScreen()
        self._splash.Show()

        # application's persistent state
        self.state = None
        self._load_state()

        self.doc_manager = DocumentManager(self)
        self.pkg_manager = None

        #: variables to be inserted into the python shell namespace
        self.shell_vars = {}
        self._init_shell_vars()

        #: command line options
        self.options = options

        self.frame = AppFrame(None, self.state, -1, size=(640, 480),
                              app=self, title='PIDE')
        self.frame.Maximize(True)

        self._make_materials()

        self.frame.Show(True)
        self.SetTopWindow(self.frame)

        self._splash.app_initialized()

        #TODO: find correct place to do this
        self.frame.viewer.StartRendering()

        if IS_FIRST_RUN:
            self.on_first_run()

        # open the load generator dialog on startup
        wx.CallAfter(self.load_generator)

    @logmt
    def on_first_run(self):
        o = os.path

        # to show sample package to user
        sample_package = o.normpath(o.join(os.getcwd(), '..', 'Samples'))
        repo = 'http://procodile.vaspra.com/api'
        self.state.update_autocomplete('package_dir', sample_package)
        self.state.update_autocomplete('repo_uri', repo)

    @logmt
    def _load_state(self):
        state_fpath = os.path.join(get_user_app_dir(), 'state.db')
        self.state = AppState(state_fpath)

    @logmt
    def _init_shell_vars(self):
        s = self.shell_vars
        s['app'] = self
        s['ogre'] = ogre

    @logmt
    def _make_materials(self):
        materials = MaterialManager()

        # default grey color
        default = MaterialColor((0.7, 0.7, 0.7))
        default.specular = Color((0.4, 0.4, 0.4))
        default.ambient = Color((0.5, 0.5, 0.5))
        default.shininess = 0.0
        materials.get_material(default, 'default')

        # default highlight red color
        highlight = MaterialColor((0.8, 0.4, 0.4))
        highlight.specular = Color((0.5, 0.1, 0.1))
        highlight.ambient = Color((0.6, 0.2, 0.2))
        highlight.shininess = 0.0
        materials.get_material(highlight, 'highlight')

        self.materials = materials

    @logmt
    def on_document_tab_closed(self, doc):
        self.doc_manager.del_document(doc)

    @logmt
    def on_close(self):
        self.doc_manager.stop()
        self.frame.cleanup()

    @property
    def cur_doc(self):
        return self.frame.get_current_document()

    def _ensure_doc(method):

        def wmethod(self, *args, **kwargs):
            args = list(args)
            get_doc = lambda doc: doc or self.frame.get_current_document()

            if 'doc' in kwargs:
                kwargs['doc'] = get_doc(kwargs['doc'])
                if not kwargs['doc']:
                    return

            elif args and (isinstance(args[0], (Document)) or args[0] == None):
                args[0] = get_doc(args[0])
                if not args[0]:
                    return

            else:
                kwargs['doc'] = get_doc(None)

            return method(self, *args, **kwargs)
        return wmethod

    @_ensure_doc
    @logmt
    def on_run(self, doc):
        if doc.state in (doc.STATE_READY,
                         doc.STATE_PAUSED):
            self.run_document(doc)

        elif doc.state == doc.STATE_COMPLETED:
            self.reset_document(doc)
            self.run_document(doc)

        else:
            self.frame.update_document_state(doc)

    @_ensure_doc
    @logmt
    def on_reload(self, doc):
        self.reload_document(doc)
        self.reset_document(doc)
        self.run_document(doc)

    @_ensure_doc
    @logmt
    def on_stop(self, doc):
        self.reset_document(doc)

    @logmt
    def add_document(self, recipe, loader):
        doc = self.doc_manager.add_document(recipe, loader)
        self.frame.add_document(doc)
        return doc

    @_ensure_doc
    @logmt
    def del_document(self, doc):
        self.frame.del_document(doc)
        self.doc_manager.del_document(doc)

    @_ensure_doc
    @logmt
    def reset_document(self, doc):
        is_active_doc = (doc == self.frame.get_current_document())
        viewer = self.frame.viewer

        if is_active_doc:
            viewer.unset_document()

        self.doc_manager.reset_document(doc)

        if is_active_doc:
            viewer.set_document(doc)

        self.frame.update_document_state(doc)

    @_ensure_doc
    @logmt
    def reload_document(self, doc):
        self.doc_manager.reload_document(doc)

    @_ensure_doc
    @logmt
    def save_document(self, doc):
        return self.doc_manager.save_document(doc)

    @_ensure_doc
    @logmt
    def save_document_as(self, doc):
        return self.doc_manager.save_document_as(doc)

    @logmt
    def save_screenshot(self, fpath=None):
        return self.frame.save_screenshot(fpath)

    @logmt
    def save_screenshots(self):
        doc = self.frame.get_current_document()
        props = dict(doc.get_properties())

        gen_id = props['generator_id']
        path = props['location']

        if not path:
            return

        dirpath = os.path.join(path, 'screenshots', gen_id)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        views = ('front', 'back', 'perspective', 'left', 'right',
                 'top', 'bottom')

        for index, view in enumerate(views):
            doc.set_view(view, delayed=False)
            self.frame.viewer.render_window.update()
            spath = os.path.join(dirpath, '%02d_%s.jpg' % (index, view))
            self.save_screenshot(spath)

    @_ensure_doc
    @logmt
    def run_document(self, doc):
        ret = None

        if doc.state == doc.STATE_READY:
            ret = doc.run()
        elif doc.state == doc.STATE_PAUSED:
            ret = doc.resume()

        self.frame.update_document_state(doc)
        return ret

    @_ensure_doc
    @logmt
    def pause_document(self, doc):
        if doc.state == doc.STATE_RUNNING:
            ret = doc.pause()
            self.frame.update_document_state(doc)
            return ret

    @_ensure_doc
    @logmt
    def stop_document(self, doc):
        if doc.state in (doc.STATE_RUNNING,
                         doc.STATE_PAUSED):
            ret = doc.stop()
            self.frame.update_document_state(doc)
            return ret

    @_ensure_doc
    @logmt
    def set_document_view(self, doc, view):
        return doc.set_view(view)

    @_ensure_doc
    @logmt
    def set_document_navigation(self, doc, navigation):
        return doc.set_navigation_mode(navigation)

    @_ensure_doc
    @logmt
    def toggle_document_navigation(self, doc):
        return doc.toggle_navigation_mode()

    @logmt
    def on_document_done(self, doc):
        self.frame.update_document_state(doc)

    @logmt
    def load_generator(self, start_dir=None):
        loader = Loader()
        old_loader = set_loader(loader)

        try:
            g_info = get_generator_info(self.frame, self)
            if not g_info:
                return
            is_remote, name, package_dir, repo_uri, generator_id, ver = g_info

            if is_remote:
                rc = RecipeConfig()
                rc.generator = (generator_id, repo_uri, generator_id, ver)

            else:
                _class = get_class(package_dir, generator_id)

                if RecipeBasedGenerator in _class.__bases__:
                    rc = _class.get_recipe_config()

                else:
                    rc = RecipeConfig()
                    rc.generator = (generator_id, package_dir, generator_id)

            doc = self.add_document(rc, loader)

        finally:
            set_loader(old_loader)

        self.run_document(doc)

    @logmt
    def upload_package(self, start_dir=None):
        info = get_upload_details(self.frame, self)
        if not info:
            return
        udg, repo_uri, username, password, package_dir, package_home, ver = info

        pdir = os.path.abspath(package_dir)
        no_snaps_gens = []

        package = get_loader().get_package(pdir)
        meta = package.meta

        if meta.version != ver:
            meta.version = ver
            xml_doc = meta.xmlize()
            xml_fpath = os.path.join(pdir, 'package.xml')
            stream = open(xml_fpath, 'w')
            stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            xml_doc.serialize(stream)

        for g in meta.generators:
            cdir = os.path.sep.join([pdir, 'screenshots', g.class_id])
            snaps = glob.glob(os.path.join(cdir, '*'))
            if not snaps:
                no_snaps_gens.append(g.class_id)

        if no_snaps_gens:

            dlg = GMD.GenericMessageDialog(udg,
                    'These generators do not have screenshots: \n' +\
                    '\n'.join(no_snaps_gens) +\
                    '\nDo you want to continue uploading',
                    'Missing Screenshots',
                    wx.YES_NO | wx.ICON_INFORMATION)

            response = dlg.ShowModal()
            if response == wx.ID_NO:
                self.upload_package()
            dlg.Destroy()

        try:
            client = Client(repo_uri)
            client.login(username, password)
            client.upload(package_dir, package_home)
        except Client.Exception, e:
            print ''.join(traceback.format_exception(*sys.exc_info()[:3]))

            dlg = wx.MessageDialog(udg,
                    'Error occured when trying to upload package.\n' + \
                    e.message,
                    'Package upload failed',
                    wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            self.upload_package()

        p_dir = package_dir.rsplit(os.path.sep, 1)[-1]
        dlg = wx.MessageDialog(udg,
                             'Package is accessible at:\n' +\
                             '%s/package/%s.%s.%s-%s' % (repo_uri, username,
                             package_home, p_dir, ver),
                             'Package upload successful',
                             wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    @_ensure_doc
    @logmt
    def export_collada(self, doc):

        dlg = wx.FileDialog(self.frame, message="Save file as ...",
                            defaultDir=os.getcwd(),
                            defaultFile="", style=wx.SAVE
                            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

        open(path, 'w').write(doc.export_collada())

    @logmt
    def test(self):
        pdir = r'Y:\code\procodile\checkout\blockworld\misc\karthik\models'
        gid = r'forest.Forest'
        _class = get_class(pdir, gid)
        rc = RecipeConfig()
        rc.generator = ('root', pdir, gid)
        self.add_document(rc)

    @logmt
    def OnExit(self):
        self.doc_manager.cleanup()

def except_hook(_type, value, tb):
    message = 'Uncaught exception:\n'
    message += ''.join(traceback.format_exception(_type, value, tb))
    log.error(message)

sys.excepthook = except_hook

def main(options):
    global log, IS_FIRST_RUN

    IS_FIRST_RUN = not os.path.exists(get_user_app_dir(False))

    if not options.log_file:
        options.log_file = os.path.join(get_user_app_dir(), 'pide.log')

    # create logger
    log_level = logging.DEBUG if options.debug else logging.INFO
    open(options.log_file, 'w').write('') # truncate log file
    log = create_logger(options.log_file, log_level)

    sys.stdout = StreamLogger(sys.stdout, log)
    sys.stderr = StreamLogger(sys.stderr, log)

    # initialize app
    app = App(options)
    app.MainLoop()

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='%prog [options]')
    parser.add_option('-l', '--log-file', default=None)
    parser.add_option('-d', '--debug', action='store_true')
    (options, args) = parser.parse_args()
    main(options)
