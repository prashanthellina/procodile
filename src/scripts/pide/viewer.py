import os
import math
import logging

import wx
import ogre.renderer.OGRE as ogre

from procodile.utils import log_function_call as logfn
from procodile.utils import log_method_call as logmt
from procodile.utils import get_user_app_dir

from utils import app_abs_path

SCENE_MANAGER = None
log = logging.getLogger()

class Viewer(wx.PyWindow):
    '''
    3D rendering window based on OGRE.
    '''

    @logmt
    def __init__(self, parent, _id, app,
                 size=wx.DefaultSize,
                 render_system="OpenGL"):

        self.parent = parent
        wx.PyWindow.__init__(self, parent, _id, size=size,
                             pos=wx.DefaultPosition)

        self.render_window = None
        self.app = app
        self.doc = None
        self.viewport = None

        #: dummy camera (actual camera provided by active document)
        self._camera = None

        # Event bindings
        self.Bind(wx.EVT_CLOSE, self._on_close_window)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self._on_erase_background)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_TIMER, self.update_render)

        # Timer creation
        self.timer = wx.Timer()
        self.timer.SetOwner(self)

        # Ogre Initialisation
        self._ogre_init(size, render_system)
        self.scene_init()
        self.update_render()

    @logmt
    def set_document(self, doc):
        if self.doc:
            raise Exception('unset doc (%s) first' % self.doc)

        doc_node = doc.scene_node
        root_node = self.scene_manager.getRootSceneNode()
        root_node.addChild(doc_node)

        doc.light.setVisible(True)

        self.viewport.setCamera(doc.camera)

        self.doc = doc

    @logmt
    def unset_document(self):
        if not self.doc:
            return

        doc_node = self.doc.scene_node
        root_node = self.scene_manager.getRootSceneNode()
        root_node.removeChild(doc_node)

        self.doc.light.setVisible(False)

        self.viewport.setCamera(self._camera)

        self.doc = None

    @logmt
    def _ogre_init(self, size, render_system):

        cfg_path = os.path.join(get_user_app_dir(), 'ogre.cfg')
        log_path = os.path.join(get_user_app_dir(), 'ogre.log')
        plugins_path = './plugins.cfg'

        root = ogre.Root(plugins_path, cfg_path, log_path)
        self.root = root

        rm = ogre.ResourceGroupManager.getSingleton()
        add = rm.addResourceLocation
        add(app_abs_path('materials'), 'FileSystem', 'General')

        if not os.path.exists(cfg_path):
            _continue = root.showConfigDialog()
        else:
            _continue = root.restoreConfig()
        if not _continue:
            sys.exit('Quit from Config Dialog')

        root.initialise(False)

        params = ogre.NameValuePairList()
        params['externalWindowHandle'] = str(self.GetHandle())

        x, y = size
        r = root.createRenderWindow('pide render', x, y, False, params)
        r.active = True
        self.render_window = r

        rm.initialiseAllResourceGroups()

    def _on_size(self, event):

        if getattr(self, 'root', None):
            self.update_render()
            self.render_window.windowMovedOrResized()

        event.Skip()

    def _on_erase_background(self, event):
        pass

    @logmt
    def _on_close_window(self, event):
        self.Destroy()

    def AcceptsFocus(self):
        return True

    def StartRendering(self, interval=33):
        self.timer.Start(interval)

    def update_render(self, event=None):

        self.OnFrameStarted(event)
        self.root.renderOneFrame()
        self.OnFrameEnded(event)

    @logmt
    def scene_init(self):
        self._choose_scene_manager()
        self._create_viewport()
        self._populate_scene()
        self._mouse_key_bindings()

    def _choose_scene_manager(self):
        global SCENE_MANAGER
        self.scene_manager = \
                self.root.createSceneManager(ogre.ST_GENERIC, "scene")
        SCENE_MANAGER = self.scene_manager

    def _create_viewport(self):
        r = self.render_window
        sm = self.scene_manager
        self._camera = sm.createCamera('camera')
        self.viewport = r.addViewport(self._camera, 0, 0.0, 0.0, 1.0, 1.0)
        self.viewport.backgroundColour = ogre.ColourValue(0.42, 0.46, 0.52)

    def _mouse_key_bindings(self):
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(wx.EVT_MOUSE_EVENTS, self._on_mouse_event)

    def _on_key_down(self, event):
        if self.doc:
            self.doc.on_key_down(event)
        event.Skip()

    def _on_mouse_event(self, event):
        self.SetFocus()
        if self.doc:
            self.doc.on_mouse_event(event)
        event.Skip()

    def _populate_scene(self):
        s = self.scene_manager
        s.AmbientLight = (0.3, 0.3, 0.3)

        # s.setSkyBox(True, 'Skyboxes/MountainRing')
#        self._create_floor()
   
    def _create_floor(self):

        s = self.scene_manager
        mm = ogre.MeshManager.getSingleton()
        mm.createPlane('plane.mesh', 'custom',
                       ogre.Plane((0, 0, 1), (0, 0, -0.01)),
                       2048, 2048, 2, 2);

        ground = s.createEntity('Ground', 'plane.mesh')
        ground.setMaterialName('Grid')
        ground_node = s.getRootSceneNode().createChildSceneNode()
        ground_node.attachObject(ground)
        ground_node.setOrientation(\
            ogre.Quaternion(ogre.Radian(-math.pi/2), (1, 0, 0)))

    def enable_shadows(self):
        s = self.scene_manager
        s.setShadowTechnique(ogre.SHADOWTYPE_STENCIL_ADDITIVE)

    def OnFrameStarted(self, event):
        if self.doc:
            self.doc.on_frame_started(event)

    def OnFrameEnded(self, event):
        if self.doc:
            self.doc.on_frame_ended(event)

    def save_screenshot(self, fpath):
        self.render_window.writeContentsToFile(fpath)
