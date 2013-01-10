import os
import sys
import logging
import traceback

import wx
import wx.lib.filebrowsebutton as filebrowse
import wx.combo

from procodile.loader import get_loader
from procodile.utils import log_method_call as logmt

from utils import PIDEException

log = logging.getLogger()

def display_tab_properties(parent, name, doc):
    new_name = ''

    dlg = PropertiesDialog(parent, name, doc, -1)
    dlg.CenterOnScreen()
    response = dlg.ShowModal()

    if response == wx.ID_CANCEL:
        return

    new_name = dlg.tc_name.GetValue()

    return new_name

def get_html(name, doc):

        data = doc.get_properties()

        data_html = []
        for key, value in data:
            dhtml = '''
            <tr><td><b>%s</b></td><td>%s</td></tr>
            ''' % (key, value)
            data_html.append(dhtml)
        data_html = '\n'.join(data_html)

        html = '''\
        <html>
        <body bgcolor="#ffffcc" text="#000000">
        <h4>%(name)s</h4><br/>
        <h5>Info</h5>
        <table bgcolor="#eeeebb" border="0" width="100%%" cellspacing="1px">
        %(data_html)s
        </table>
        </body>
        </html>
        ''' % locals()

        return html

class PropertiesDialog(wx.Dialog):
    '''
    Displays a dialog to display tab properties.
    '''

    @logmt
    def __init__(self, parent, name, doc, _id,
                 title= 'Properties',
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE):

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)

        self.name = None

        # name
        self.tc_name = wx.TextCtrl(self, -1, name,
                                   size=(125, -1))

        self.details = wx.html.HtmlWindow(self, -1,
                                 style=wx.NO_FULL_REPAINT_ON_RESIZE,
                                 size=size)

        self.details.SetPage(get_html(name, doc))

        # ok button
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        self.okay_button = btn

        self._layout()

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        # name box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Name :")
        label.SetHelpText("Name of the generator")
        box.Add(label, 0, flags, 5)
        box.Add(self.tc_name, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # details box
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.details, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.SetItemMinSize(self.details, (400, 200))

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btnsizer.AddButton(self.okay_button)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel selection and close dialog")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)


def get_upload_details(parent, app):
    repo_uri = None
    username = None
    password = None
    package_dir = None
    package_home = None

    dlg = UploadDialog(parent, app, -1)
    dlg.CenterOnScreen()
    response = dlg.ShowModal()

    if response == wx.ID_CANCEL:
        return

    repo_uri = dlg.repo_uri.GetValue()
    username = dlg.username.GetValue()
    password = dlg.password.GetValue()
    package_dir = dlg.package_dir
    package_home = dlg.package_home.GetValue()
    version = dlg.version.GetValue()

    app.state.update_autocomplete('repo_uri', repo_uri)
    app.state.update_autocomplete('username', username)
    app.state.update_autocomplete('package_dir', package_dir)
    app.state.update_autocomplete('package_home', package_home)
    app.state.update_autocomplete('version', version)

    return dlg, repo_uri, username, password, package_dir, package_home, version

class UploadDialog(wx.Dialog):
    '''
    Displays a dialog to upload a package.
    '''

    @logmt
    def __init__(self, parent, app, _id,
                 title='Upload Package',
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE):

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)

        self.repo_uri = None
        self.username = None
        self.password = None
        self.package_dir = None
        self.package_home = None
        self.generators_list = None

        # repo_uri
        r_repo_uris = app.state.get_autocomplete('repo_uri', num=5)
        d_uri = r_repo_uris[0] if r_repo_uris else ''

        cb_repo = wx.ComboBox(self, 500, d_uri, (90, 50),
                             (160, -1), r_repo_uris, wx.CB_DROPDOWN)
        self.repo_uri = cb_repo

        # username, password
        r_usernames = app.state.get_autocomplete('username', num=5)
        d_username = r_usernames[0] if r_usernames else ''

        cb_usrname = wx.ComboBox(self, 500, d_username, (90, 50),
                                (160, -1), r_usernames, wx.CB_DROPDOWN)
        self.username = cb_usrname

        tc_pwd = wx.TextCtrl(self, -1, size=(125, -1), style=wx.TE_PASSWORD)
        self.password = tc_pwd

        # package_dir
        r_package_dirs = app.state.get_autocomplete('package_dir', num=1)
        d_pack_dir = r_package_dirs[0] if r_package_dirs else '.'
        d_pack_value = r_package_dirs[0] if r_package_dirs else ''

        dbb = filebrowse.DirBrowseButton(self, -1, size=(450, -1),
                                         changeCallback = self.OnPath,
                                         startDirectory = d_pack_dir,
                                         labelText='',
                                         buttonText='...')

        self.dir_browse_button = dbb

        # package_home
        r_pack_homes = app.state.get_autocomplete('package_home', num=5)
        d_pack_home = r_pack_homes[0] if r_pack_homes else ''

        cb_pack_home = wx.ComboBox(self, 500, d_pack_home, (90, 50),
                                  (160, -1), r_pack_homes, wx.CB_DROPDOWN)
        self.package_home = cb_pack_home

        # version
        r_versions = app.state.get_autocomplete('version', num=5)
        d_version = r_versions[0] if r_versions else ''

        cb_version = wx.ComboBox(self, 500, d_version, (90, 50),
                                  (160, -1), r_versions, wx.CB_DROPDOWN)
        self.version = cb_version

        # generators_list
        d_gens = app.state.get_recent_generators(num=1)
        self.d_gen = d_gens[0][1] if d_gens else ''

        bcb = wx.ComboBox(self, 500, self.d_gen, (90, 50),
                          (160, -1), [], wx.CB_DROPDOWN)
        self.generators_list = bcb

        # ok button
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("Upload chosen package")
        btn.SetDefault()
        self.okay_button = btn

        # this has to be done after generators_list is initialized
        dbb.SetValue(d_pack_value)

        self._layout()

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        # repo box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Repository :")
        label.SetHelpText("Repository to which package to be uploaded")
        box.Add(label, 0, flags, 5)
        box.Add(self.repo_uri, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # username box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Username :")
        label.SetHelpText("Login required to upload")
        box.Add(label, 0, flags, 5)
        box.Add(self.username, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # password box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Password :")
        box.Add(label, 0, flags, 5)
        box.Add(self.password, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # directory choosing box and button
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Package :")
        label.SetHelpText("Pick a package by cliking on the button")
        box.Add(label, 0, flags, 5)
        box.Add(self.dir_browse_button, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # package home box
        box = wx.BoxSizer(wx.HORIZONTAL)
        p_label = wx.StaticText(self, -1, "Package Home :")
        p_label.SetHelpText("Package directory in repository")
        box.Add(p_label, 0, flags, 5)
        box.Add(self.package_home, 1, flags, 5)
        v_label = wx.StaticText(self, -1, "Version :")
        v_label.SetHelpText("Version of the package")
        box.Add(v_label, 0, flags, 5)
        box.Add(self.version, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # generator listing in chosen package
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Generators :")
        label.SetHelpText("Generators in the package")
        box.Add(label, 0, flags, 5)
        box.Add(self.generators_list, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btnsizer.AddButton(self.okay_button)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel selection and close dialog")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    @logmt
    def OnPath(self, evt):
        glist = self.generators_list
        glist.Clear()

        self.package_dir = evt.GetString()
        if not self.package_dir:
            return

        if not os.path.exists(self.package_dir):
            self.dir_browse_button.SetValue('')
            return

        self.package_dir = os.path.abspath(self.package_dir)

        try:
            package = get_loader().get_package(self.package_dir)
            meta = package.meta
        except:
            print ''.join(traceback.format_exception(*sys.exc_info()[:3]))
            self.dir_browse_button.SetValue('')

            dlg = wx.MessageDialog(self,
                    'Error occured when trying to load package.\n' + \
                    'Refer to log for more details.',
                    'Package load failed',
                    wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        self.version.SetValue(meta.version)

        for g in meta.generators:
            glist.Append(g.class_id, g.class_id)
            if self.d_gen == g.class_id:
                glist.SetValue(g.class_id)

def get_generator_info(parent, app, gen_info=None, display_name=False):
    name = None
    package_dir = None
    repo_uri = None
    generator_id = None
    version = None
    is_remote = False

    dlg = GeneratorChooserDialog(parent, app, -1, gen_info, display_name)
    dlg.CenterOnScreen()
    response = dlg.ShowModal()

    if response == wx.ID_CANCEL:
        return

    if dlg.tabs_pane.GetCurrentPage().name == 'local':
        package_dir = dlg.package_dir
        generator_id = dlg.generator_id
    else:
        is_remote = True
        remote_gen_id = dlg.tabs_pane.remote_panel.remote_generator.GetValue()
        if remote_gen_id:
            try:
                repo_uri, gen_id = remote_gen_id.rsplit('/', 1)
                repo_uri = repo_uri.rsplit('/', 1)[0] + '/api' #TODO
                generator_id, version = gen_id.split('-',1)
            except:
                raise PIDEException('Improper uri')
    if display_name:
        name = dlg.tabs_pane.GetCurrentPage().gen_name.GetValue()

    app.state.update_autocomplete('repo_uri', repo_uri)
    app.state.update_autocomplete('package_dir', package_dir)
    if is_remote:
        app.state.update_generator(repo_uri, generator_id, version)
    else:
        app.state.update_generator(package_dir, generator_id, version)

    return is_remote, name, package_dir, repo_uri, generator_id, version

class GeneratorChooserDialog(wx.Dialog):
    '''
    Displays a dialog to pick a package and then a
    generator from it.
    '''

    @logmt
    def __init__(self, parent, app, _id, gen_info, display_name,
                 title='Choose Generator',
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE):

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)


        self.app = app
        self.is_remote = False
        self.package_dir = None
        self.repo_uri = None
        self.generator_id = None
        self.version = None
        self.name = None
        self.display_name = display_name

        if gen_info:
            name, repo_uri, generator_id, ver = gen_info
            self.name = name
            self.generator_id = generator_id
            self.version = ver
            if 'http' in repo_uri:
                self.is_remote = True
                uri = '%s%s%s-%s' %( repo_uri, '/generator/', generator_id, ver)
                self.repo_uri = uri
            else:
                self.name = name
                self.package_dir = repo_uri

        self.tabs_pane = TabsPane(self, -1)

        sizer = wx.BoxSizer()
        sizer.Add(self.tabs_pane, 1, wx.EXPAND)
        self.SetSizer(sizer)

class TabsPane(wx.Notebook):
    def __init__(self, parent, log):
        wx.Notebook.__init__(self, parent, log, size=(21,21),
                             style=wx.BK_DEFAULT )
        self.log = log

        self.gcd = parent
        self.local_panel = LocalPanel(self, -1, self.gcd)
        self.remote_panel = RemotePanel(self, -1, self.gcd)
        self.AddPage(self.local_panel, "Local")
        self.AddPage(self.remote_panel, "Remote")

        if self.gcd.is_remote:
            self.ChangeSelection(1)

class RemotePanel(wx.Panel):
    def __init__(self, parent, log, gcd):
        self.log = log
        wx.Panel.__init__(self, parent, -1)

        self.gcd = gcd
        self.name = 'remote'
        self.gen_name = None

        if self.gcd.display_name:
            self.gen_name = wx.TextCtrl(self, -1, self.gcd.name or '',
                                            size=(125, -1))

        # repo_uri
        r_repo_uris = self.gcd.app.state.get_autocomplete('repo_uri', num=5)
        d_uri = self.gcd.repo_uri or r_repo_uris[0] if r_repo_uris else ''

        self.remote_generator = wx.ComboBox(self, 500, d_uri, (90, 50),
                                        (160, -1), r_repo_uris, wx.CB_DROPDOWN)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("Accept chosen generator")
        btn.SetDefault()
        self.okay_button = btn

        self._layout()

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        if self.gcd.display_name:
            # name box
            box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, "Name :")
            label.SetHelpText("Alias name that refers to the generator")
            box.Add(label, 0, flags, 5)
            box.Add(self.gen_name, 1, flags, 5)
            sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # repo box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Generator URL :")
        label.SetHelpText("URL that refers to the generator")
        box.Add(label, 0, flags, 5)
        box.Add(self.remote_generator, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btnsizer.AddButton(self.okay_button)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel selection and close dialog")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

class LocalPanel(wx.Panel):
    def __init__(self, parent, log, gcd):
        self.log = log
        wx.Panel.__init__(self, parent, -1)

        self.gcd = gcd
        self.name = 'local'
        self.package_dir = self.gcd.package_dir
        self.generator_id = self.gcd.generator_id
        self.gen_name = None

        # name of generator
        if self.gcd.display_name:
            self.gen_name = wx.TextCtrl(self, -1, self.gcd.name or '',
                                            size=(125, -1))

        # package_dir
        r_package_dirs = self.gcd.app.state.get_autocomplete('package_dir',
                                                             num=1)
        d_pack_dir = r_package_dirs[0] if r_package_dirs else '.'
        d_pack_value = r_package_dirs[0] if r_package_dirs else ''
        start_dir = self.package_dir or d_pack_dir

        dbb = filebrowse.DirBrowseButton(self, -1, size=(450, -1),
                                         changeCallback = self.OnPath,
                                         startDirectory = start_dir,
                                         labelText='',
                                         buttonText='...')
        self.dir_browse_button = dbb

        # generators
        d_gens = self.gcd.app.state.get_recent_generators(num=1)
        self.d_gen = d_gens[0][1] if d_gens else ''

        bcb = wx.combo.BitmapComboBox(self, pos=(25,25), size=(200,-1),
                                      style=wx.CB_READONLY)
        bcb.SetValue(self.generator_id or self.d_gen)
        self.generators_list = bcb

        # ok button
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("Accept chosen generator")        
        btn.SetDefault()
        self.okay_button = btn

        if not (self.gcd.generator_id and self.generator_id):
            self.okay_button.Disable()

        # this has to be done after generators_list is initialized
        dbb.SetValue(self.package_dir or d_pack_value)

        self._layout()

        self.Bind(wx.EVT_COMBOBOX, self.OnComboSelect)

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        if self.gcd.display_name:
            # name choosing box and button
            box = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, "Name :")
            label.SetHelpText("Alias name that refers to the generator")
            box.Add(label, 0, flags, 5)
            box.Add(self.gen_name, 1, flags, 5)
            sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # directory choosing box and button
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Package :")
        label.SetHelpText("Pick a package by cliking on the button")
        box.Add(label, 0, flags, 5)
        box.Add(self.dir_browse_button, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # generator listing in chosen package
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Generators :")
        label.SetHelpText("Choose a generator")
        box.Add(label, 0, flags, 5)
        box.Add(self.generators_list, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btnsizer.AddButton(self.okay_button)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel selection and close dialog")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    @logmt
    def OnPath(self, evt):
        if self.generator_id:
            return

        glist = self.generators_list
        glist.Clear()
        self.okay_button.Disable()

        self.package_dir = evt.GetString()
        if not self.package_dir:
            return

        if not os.path.exists(self.package_dir):
            self.dir_browse_button.SetValue('')
            return

        self.gcd.package_dir = os.path.abspath(self.package_dir)

        try:
            package = get_loader().get_package(self.package_dir)
            meta = package.meta
        except:
            print ''.join(traceback.format_exception(*sys.exc_info()[:3]))
            self.dir_browse_button.SetValue('')

            dlg = wx.MessageDialog(self,
                    'Error occured when trying to load package.\n' + \
                    'Refer to log for more details.',
                    'Package load failed',
                    wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        for g in meta.generators:
            glist.Append(g.class_id, wx.NullBitmap, g.class_id)
            if self.d_gen == g.class_id:
                glist.SetValue(self.d_gen)
                self.gcd.generator_id = self.d_gen
                self.okay_button.Enable()

    @logmt
    def OnComboSelect(self, evt):
        self.gcd.generator_id = self.generators_list.GetValue()
        self.okay_button.Enable()

class SaveAsDialog(wx.Dialog):
    '''
    Dialog to save a generator.
    '''

    @logmt
    def __init__(self, parent, _id,
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE,
                 title='Save As'):

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)

        s = self
        s.app_state = parent.app_state

        r_package_dirs = self.app_state.get_autocomplete('package_dir',
                                                             num=1)
        s.d_pack_dir = r_package_dirs[0] if r_package_dirs else ''

        s.package_dir = wx.TextCtrl(self, -1, s.d_pack_dir, size=(200, -1))
        s.package_dir_btn = wx.Button(self, -1, "...", size=(50, -1))
        self.Bind(wx.EVT_BUTTON, self.OnDirButton, s.package_dir_btn)

        s.fpath = wx.TextCtrl(self, -1, size=(200, -1))
        s.fpath_btn = wx.Button(self, -1, "...", size=(50, -1))
        self.Bind(wx.EVT_BUTTON, self.OnSaveButton, s.fpath_btn)

        self.okay_button = wx.Button(self, wx.ID_OK)
        self.okay_button.SetDefault()
        self.okay_button.Disable()

        self.cancel_button = wx.Button(self, wx.ID_CANCEL)
        self.cancel_button.SetHelpText("Cancel selection and close dialog")

        self.Freeze()

        self._layout()

        self.Thaw()

    @logmt
    def OnDirButton(self, evt):
        package_dir_dlg = wx.DirDialog(self, "Choose a directory:",
                                        defaultPath = self.d_pack_dir,
                                        style=wx.DD_DEFAULT_STYLE)

        if package_dir_dlg.ShowModal() == wx.ID_OK:
            _package_dir = package_dir_dlg.GetPath()

            self.package_dir.SetValue(_package_dir)
            self.d_pack_dir = _package_dir

    @logmt
    def OnSaveButton(self, evt):
        wildcard = "Python source (*.py)|*.py|"

        fpath_dlg = wx.FileDialog(self, message="Save file as ...",
                                  defaultDir = self.d_pack_dir,
                                  wildcard = wildcard,
                                  style=wx.SAVE)

        if fpath_dlg.ShowModal() == wx.ID_OK:
            _fpath = fpath_dlg.GetPath()

            _package_dir = self.package_dir.GetValue()

            if not _fpath or _package_dir not in _fpath:
                dlg = wx.MessageDialog(self,
                        'Choose a file within the package directory',
                        'File path error',
                        wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()

            else:
                self.okay_button.Enable()
                self.fpath.SetValue(_fpath.split(_package_dir)[-1].\
                                    strip(os.path.sep))

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        # package_dir
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Package Directory :")
        label.SetHelpText("Package directory to be saved in")
        box.Add(label, 0, flags, 5)
        box.Add(self.package_dir, 1, flags, 5)
        box.Add(self.package_dir_btn, 0, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # fpath
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "File path in directory :")
        label.SetHelpText("File path within the directory")
        box.Add(label, 0, flags, 5)
        box.Add(self.fpath, 1, flags, 5)
        box.Add(self.fpath_btn, 0, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(self.okay_button)
        btnsizer.AddButton(self.cancel_button)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

class BugReportDialog(wx.Dialog):
    '''
    Dialog to report a bug.
    '''

    @logmt
    def __init__(self, parent, _id,
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE,
                 title='Report Bug'):

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)

        s = self
        s.app_state = parent.app_state

        bug_list = ['Something\'s missing',
                    'Pide crash... go boom',
                    'Other problem',
                    ]
        s.bug_type = wx.ComboBox(s, 500, bug_list[0], (90, 50),
                                        (160, -1), bug_list, wx.CB_DROPDOWN)

        r_package_dirs = self.app_state.get_autocomplete('package_dir',
                                                             num=1)
        s.d_pack_dir = r_package_dirs[0] if r_package_dirs else ''

        s.attachment = wx.TextCtrl(s, -1, size=(200, -1))
        s.attachment_btn = wx.Button(s, -1, "...", size=(50, -1))
        self.Bind(wx.EVT_BUTTON, s.OnAttachButton, s.attachment_btn)

        s.description = wx.TextCtrl(s, -1, size=(300, 100),
                                    style= wx.TE_MULTILINE)

        r_usernames = s.app_state.get_autocomplete('username', num=5)
        d_username = r_usernames[0] if r_usernames else ''

        s.username = wx.TextCtrl(s, -1, d_username, size=(200, -1))
        s.password = wx.TextCtrl(s, -1, size=(200, -1),
                                    style= wx.TE_PASSWORD)

        s.okay_button = wx.Button(s, wx.ID_OK)
        s.okay_button.SetDefault()

        s.cancel_button = wx.Button(s, wx.ID_CANCEL)
        s.cancel_button.SetHelpText("Cancel selection and close dialog")

        s.Freeze()
        s._layout()
        s.Thaw()

    @logmt
    def OnAttachButton(self, evt):
        self.attachment_dlg = wx.FileDialog(self, message="Choose a file",
                                     defaultDir=self.d_pack_dir,
                                     defaultFile="",
                                     style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                    )


        if self.attachment_dlg.ShowModal() == wx.ID_OK:
            _attachment = self.attachment_dlg.GetPath()

            self.attachment.SetValue(_attachment)

    @logmt
    def _layout(self):

        flags = wx.ALIGN_CENTRE | wx.ALL
        sizer = wx.BoxSizer(wx.VERTICAL)

        # bug_type
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Bug type:")
        label.SetHelpText("Category of the bug")
        box.Add(label, 0, flags, 5)
        box.Add(self.bug_type, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # description box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Description:")
        label.SetHelpText("Description of the bug")
        box.Add(label, 0, flags, 5)
        box.Add(self.description, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # attachment
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Attachment:")
        label.SetHelpText("Supporting files related to the bug")
        box.Add(label, 0, flags, 5)
        box.Add(self.attachment, 1, flags, 5)
        box.Add(self.attachment_btn, 0, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # username box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Username :")
        label.SetHelpText("If provided, you will be notified\
                           when the bug is fixed")
        box.Add(label, 0, flags, 5)
        box.Add(self.username, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # password box
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Password :")
        box.Add(label, 0, flags, 5)
        box.Add(self.password, 1, flags, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(self.okay_button)
        btnsizer.AddButton(self.cancel_button)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)