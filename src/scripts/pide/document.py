import os
import math
import time
import logging
from cStringIO import StringIO as stringio

import wx
import ogre.renderer.OGRE as ogre

from procodile.utils import log_method_call as logmt
from procodile.loader import set_loader, Loader, get_class
from procodile.collada import make_collada
from procodile.xmlwriter import XMLNode

from utils import PIDEException
from configuration import ConfigurationWidget as ConfWidget
from configuration import GeneratorsWidget, XpathWidget, ModificationsWidget
from buildtree import BuildTreeOverlay, BuildTree
from dialogs import SaveAsDialog
import viewer

log = logging.getLogger()

def get_scene_manager():
    return viewer.SCENE_MANAGER

class Document:
    FLY_MODE = 0
    EXAMINE_MODE = 1
    NAVIGATION_MODES = [FLY_MODE, EXAMINE_MODE]
    DEFAULT_NAVIGATION_MODE = EXAMINE_MODE

    STATE_READY = 0
    STATE_RUNNING = 1
    STATE_PAUSED = 2
    STATE_COMPLETED = 3

    @logmt
    def __init__(self, recipe, loader, app):

        self.state = self.STATE_READY

        self.app = app
        self.recipe = recipe
        self.loader = loader

        _id = self._get_id

        sm = get_scene_manager()
        self.scene_node = sm.createSceneNode()
        self.obtree = None
        self._actions = []

        self._user_navigated = False #: whether user moved around
            # in the viewport
        self._next_view_adjust = 1 #: adjust view (to fit screen)
            # after so many seconds

        # GUI widgets
        p = self.app.frame

        if not getattr(self, 'obtree_widget', None):
            self.obtree_widget = BuildTree(p, -1, (0, 0),
                                    wx.DefaultSize,
                                    wx.TR_DEFAULT_STYLE | wx.NO_BORDER,
                                    on_item_select=self.on_obtree_item_select)
            self.obtree_widget.Hide()

        if not getattr(self, 'xpath_widget', None):
            self.xpath_widget = XpathWidget(p)
            self.xpath_widget.Hide()

        if not getattr(self, 'conf_widget', None):
            self.gen_widget = GeneratorsWidget(p, self)
            self.mod_widget = ModificationsWidget(p, self)

            self.conf_widget = ConfWidget(p, self)
            self.conf_widget.Hide()

        # camera oriented members
        self.center_node = sm.createSceneNode()
        self.camera_node = self.center_node.createChildSceneNode()
        self.camera_node.lookAt((0, 0, 0), ogre.Node.TS_LOCAL)

        camera = sm.createCamera(_id('camera'))
        camera.nearClipDistance = .1
        camera.setAutoAspectRatio(True)
        self.camera_node.attachObject(camera)
        self.camera = camera

        # camera light
        light = sm.createLight('light_%x' % id(self))
        light.setType(ogre.Light.LT_POINT)
        light.setPosition((0, 0, 0))
        light.setSpecularColour((0.9, 0.9, 0.9))
        light.setDiffuseColour((0.7, 0.7, 0.7))
        self.light = light
        self.camera_node.attachObject(light)
        self.light.setVisible(False)

        # 3D navigation oriented members
        self.navigation_mode = self.DEFAULT_NAVIGATION_MODE
        self.move_scale = 0.0
        self.move_speed = 3.0
        self.num_moves = 0
        self.acceleration = 3
        self.last_time = time.time()

        self.x_start = 0
        self.y_start = 0
        self._click = False
        self._ray_scene_query = sm.createRayQuery(ogre.Ray())
        self._selection = set()
        self._sel_xpath = None
        self._sel_geom = None
        self._sel_xpaths = []

    @logmt
    def get_display_name(self):
        name, location, _id, version = self.recipe.generator
        _id = _id.split('.')
        _id = '.'.join(_id[-2:])
        return _id

    @logmt
    def get_properties(self):
        name, location, _id, version = self.recipe.generator

        properties = [
                        ('name', self.get_display_name()),
                        ('generator_id', _id),
                        ('location', location),
                        ('version', version)
                     ]

        return properties

    @logmt
    def on_root_gen_created(self):
        self.obtree_widget.set_build_tree(self.obtree)
        rg = self.obtree.root_gen
        self.conf_widget.update_panes(rg, 'gen', '//%s' % rg.generator.IDENT.id)
    
    @logmt
    def on_root_gen_destroyed(self):
        self.obtree_widget.clear_build_tree()

    def on_time_elapsed(self, time_elapsed):
        self._next_view_adjust -= 1

        if self._next_view_adjust <= 0 and not self._user_navigated:
            self._actions.append(lambda: self._set_view('perspective'))
            self._actions.append(lambda: self._fit_to_view())
            self._next_view_adjust = 10

    @logmt
    def _update_recipe(self, loader=None):
        loader = loader or self.loader

        old_loader = set_loader(self.loader)

        try:
            self.recipe.update()
        finally:
            set_loader(old_loader)

        self.loader = loader

    @logmt
    def run(self):
        if self.state != self.STATE_READY:
            raise PIDEException('not in ready state. please reset')

        self._update_recipe()

        gen_class = self.recipe.make_generator(self.recipe._root_generator)
        self.obtree = BuildTreeOverlay(gen_class, self)
        self.obtree.build()

        self.state = self.STATE_RUNNING

    @logmt
    def pause(self):
        if self.state != self.STATE_RUNNING:
            raise PIDEException('not running')

        self.obtree.pause()
        self.state = self.STATE_PAUSED

    @logmt
    def resume(self):
        if self.state != self.STATE_PAUSED:
            raise PIDEException('not paused')

        self.obtree.resume()
        self.state = self.STATE_RUNNING

    @logmt
    def stop(self):
        if self.state not in (self.STATE_PAUSED,
                              self.STATE_RUNNING):
            return

        self.obtree.stop()
        self.state = self.STATE_COMPLETED

    @logmt
    def rebuild(self, gen_infos, on_first_gen_created=None):

        if self.state == self.STATE_READY:
            raise PIDEException('not in required state. cannot reload')

        if self.state in (self.STATE_PAUSED,
                          self.STATE_RUNNING):
            self.stop()

        self._update_recipe()
        self.state = self.STATE_RUNNING

        self.obtree.rebuild(gen_infos, on_first_gen_created)

    @logmt
    def export_collada(self):
        if self.state == self.STATE_RUNNING:
            self.pause()

        # FIXME: complete this implementation

    @logmt
    def on_build_completed(self):
        self.state = self.STATE_COMPLETED
        self.app.on_document_done(self)

        obt = self.obtree_widget
        if obt:
            obt.Expand(obt.GetRootItem())

        if not self._user_navigated and self._actions is not None:
            self._actions.append(lambda: self._set_view('perspective'))
            self._actions.append(lambda: self._fit_to_view())

    @logmt
    def cleanup(self, preserve_gui_widgets=False):

        if self.state in (self.STATE_RUNNING,
                          self.STATE_PAUSED):
            self.stop()

        sm = get_scene_manager()

        if self.obtree:
            self.obtree.cleanup()
            self.obtree = None
            self.obtree_widget.clear_build_tree()

        parent_node = self.scene_node.getParent()
        if parent_node:
            parent_node.removeChild(self.scene_node)

        sm.destroySceneNode(self.scene_node)

        self.camera_node.detachObject(self.camera)
        sm.destroyCamera(self.camera)
        self.camera_node.detachObject(self.light)
        sm.destroyLight(self.light)

        self.center_node.removeChild(self.camera_node)
        sm.destroySceneNode(self.camera_node)
        sm.destroySceneNode(self.center_node)

        # cleanup GUI widgets!
        if preserve_gui_widgets:
            self.obtree_widget.DeleteAllItems()

        else:
            for widget_name in ('obtree_widget',
                                'xpath_widget', 'conf_widget'):
                widget = getattr(self, widget_name)
                widget.Destroy()
                setattr(self, widget_name, None)

        self._actions = []
        self.state = None

    @logmt
    def reset(self):
        self.cleanup(preserve_gui_widgets=True)
        self.__init__(self.recipe, self.loader, self.app)

    @logmt
    def save(self):
        if not self.recipe.package_dir or not self.recipe.fpath:
            return self.save_as()

        else:
            return self.recipe.save()

    @logmt
    def save_as(self):
        pdir = self.recipe.package_dir
        fpath = self.recipe.fpath

        dlg = SaveAsDialog(self.app.frame, -1)
        dlg.CenterOnParent()
        response = dlg.ShowModal()

        if response == wx.ID_CANCEL:
            return

        pdir = dlg.package_dir.GetValue()
        fpath = dlg.fpath.GetValue()

        self.recipe.save(package_dir=pdir, fpath=fpath)

        _pdir = pdir.rsplit(os.path.sep, 1)[-1]
        _fpath = fpath.rsplit('.')[0]
        self.app.frame.change_tabname(_pdir + '.' + _fpath)

        return pdir, fpath

    @logmt
    def reload(self):
        '''
        Reload code.
        '''
        self._update_recipe(Loader())

    def _get_id(self, name):
        return '%s_%x' % (name, id(self))

    def _camera_lookat(self, point=None):
        if not point:
            bbox = self.obtree.get_bounding_box()
            point = bbox.getCenter()

        if self.navigation_mode == self.EXAMINE_MODE:
            self.camera_node.lookAt(point, ogre.Node.TS_LOCAL)
        else:
            self.camera.lookAt(point)

    def _place_light(self):
        if self.navigation_mode != self.FLY_MODE:
            return

        self.light.setPosition(self.camera.getPosition())

    def _move_camera(self, vector):
        if self.navigation_mode == self.EXAMINE_MODE:
            self.camera_node.translate(vector)

        else:
            self.camera.moveRelative(vector)

        self._place_light()

    @logmt
    def set_navigation_mode(self, mode):
        mode = self.EXAMINE_MODE if mode == 'examine' else self.FLY_MODE
        self._actions.append(lambda: self._set_navigation_mode(mode))

    @logmt
    def toggle_navigation_mode(self):
        mode = self.FLY_MODE if self.navigation_mode == self.EXAMINE_MODE\
                                  else self.EXAMINE_MODE
        self._actions.append(lambda: self._set_navigation_mode(mode))

        return mode

    @logmt
    def _set_navigation_mode(self, mode):
        self._user_navigated = True

        self.center_node.resetOrientation()
        self.camera.setOrientation(ogre.Quaternion())
        self.camera.setPosition((0, 0, 0))
        self.camera_node.detachAllObjects()
        self.camera_node.setPosition((0, 0, 0))
        self.light.setPosition((0, 0, 0))

        if mode == self.EXAMINE_MODE:
            self.camera_node.attachObject(self.camera)
            self.camera_node.attachObject(self.light)

        self.navigation_mode = mode

    @logmt
    def set_view(self, view='perspective', delayed=True):
        self._user_navigated = True

        actions = []

        if view == 'fit':
            actions.append(lambda: self._fit_to_view())
        elif view == 'lookat':
            actions.append(lambda: self._camera_lookat())
        else:
            actions.append(lambda: self._set_view(view))
            actions.append(lambda: self._fit_to_view())

        if delayed:
            self._actions.extend(actions)
        else:
            for a in actions:
                a()

    @logmt
    def get_view(self):
        return self.navigation_mode

    @logmt
    def _set_view(self, view):

        if self.navigation_mode == self.EXAMINE_MODE:
            c = self.center_node
        else:
            c = self.camera

        if view == 'perspective':
            c.setOrientation(ogre.Quaternion(math.pi/4, (-1, 1, 0)))

        elif view == 'top':
            c.setOrientation(ogre.Quaternion(-math.pi/2, (1, 0, 0)))

        elif view == 'bottom':
            c.setOrientation(ogre.Quaternion(math.pi/2, (1, 0, 0)))

        elif view == 'right':
            c.setOrientation(ogre.Quaternion(math.pi/2, (0, 1, 0)))

        elif view == 'left':
            c.setOrientation(ogre.Quaternion(-math.pi/2, (0, 1, 0)))

        elif view == 'back':
            c.setOrientation(ogre.Quaternion(math.pi, (0, 1, 0)))

        else:
            # front is default
            c.setOrientation(ogre.Quaternion())

    @logmt
    def _fit_to_view(self, bbox=None):

        if bbox is None:
            if not self.obtree:
                return
            bbox = self.obtree.get_bounding_box()

        # http://www.ogre3d.org/forums/viewtopic.php?f=5&t=49611
        near_plane = self.camera.getNearClipDistance()
        theta = self.camera.getFOVy() / 2.

        aspect_ratio = self.camera.getAspectRatio()
        if aspect_ratio < 1.0:
            theta *= aspect_ratio

        sv = bbox.getSize()
        size = max(sv.x, sv.y, sv.z)
        theta = theta.valueRadians()
        distance = (size / math.sin(theta)) + near_plane
        distance /= 2.
        distance = distance + distance / 10.

        if self.navigation_mode == self.EXAMINE_MODE:
            self.camera_node.setPosition((0, 0, 0))
            self.center_node.setPosition(bbox.getCenter())
        else:
            self.camera.setPosition(bbox.getCenter())

        self._move_camera((0, 0, distance))
        self._place_light()

    def on_key_down(self, event):
        is_examine_mode = self.navigation_mode == self.EXAMINE_MODE

        k = event.m_keyCode
        t = ogre.Vector3().ZERO

        amount = self.move_scale
        amount = amount + amount * (self.num_moves / self.acceleration)

        if k in (wx.WXK_LEFT, ord('A')):
            if not is_examine_mode:
                t.x = -amount

        elif k in (wx.WXK_RIGHT, ord('D')):
            if not is_examine_mode:
                t.x = amount

        elif k in (wx.WXK_UP, ord('W')):
            t.z =  -amount

        elif k in (wx.WXK_DOWN, ord('S')):
            t.z =  amount

        else:
            return

        self._user_navigated = True

        if event.ShiftDown():
            self.num_moves += 1
        else:
            self.num_moves = 0

        self._move_camera(t)

    @logmt
    def _cast_ray(self, ray):
        '''
        http://www.ogre3d.org/addonforums/viewtopic.php?f=3&t=11621
        '''

        sm = get_scene_manager()

        # variable to hold resulting entity
        closest_entity = None

        # variable to hold point of hit
        closest_result = None

        # create a query object
        ray_query = sm.createRayQuery(ray)
        ray_query.setSortByDistance(True)

        # execute the query, returns a vector of hits
        ray_query.execute(ray_query)
        result = ray_query.getLastResults()

        if len(result) == 0:
            # raycast did not hit an objects bounding box
            return None;

        # at this point we have raycast to a series of different objects
        # bounding boxes. we need to test these different objects to see
        # which is the first polygon hit. there are some minor
        # optimizations (distance based) that mean we wont have to
        # check all of the objects most of the time, but the worst case
        # scenario is that we need to test every triangle of every object.
        closest_dist = -1.0

        for item in result:

            # stop checking if we have found a raycast hit that is closer
            # than all remaining entities
            if closest_dist >= 0.0 and closest_dist < item.distance:
                break

            # only check this result if its a hit against an entity
            if not item.movable:
                continue

            if item.movable.getMovableType() != "Entity":
                continue

            # get the entity to check
            entity = sm.getEntity(item.movable.getName())

            # get the buffers from the mesh
            buffers = self._get_mesh_info(entity.getMesh())
            vertex_buffer = buffers[0]
            index_buffer = buffers[1]

            # get the world position, orientation (as a Matrix) and scale
            position = entity.getParentNode()._getDerivedPosition()
            orientation = entity.getParentNode()._getDerivedOrientation()
            mat_orient = ogre.Matrix3()
            orientation.ToRotationMatrix(mat_orient)
            scale = entity.getParentNode()._getDerivedScale()

            # Now test for hitting individual triangles on the mesh
            new_closest = False

            # get the positions of the vertices from the vertex buffer
            # three vertices each form a triangle
            triangle = []
            i = 1

            for vertex_num in index_buffer:
                start = vertex_num * 8

                pt = ogre.Vector3(vertex_buffer[start],
                                  vertex_buffer[start + 1],
                                  vertex_buffer[start + 2])

                # factor in the world position, orientation and scale
                pt = (mat_orient * (pt * scale)) + position
                triangle.append(pt)

                if i % 3 == 0:
                    # check for a hit against this triangle
                    hit = ogre.Math.intersects(ray,
                            triangle[0], triangle[1], triangle[2],
                            True, False)

                    # if it was a hit check if its the closest
                    if hit.first:
                        if closest_dist < 0.0 or hit.second < closest_dist:
                            # this is the closest so far, save it off
                            closest_dist = hit.second
                            new_closest = True

                    # reset the triangle
                    triangle = []

                i = i + 1

            # if we found a new closest raycast for this object, update the
            # closest_result and closest_entity before moving on to the next
            # object.
            if new_closest:
                closest_entity = entity
                closest_result = ray.getPoint(closest_dist)

        #destroy the query
        sm.destroyQuery(ray_query)

        # return the result
        return [closest_entity, closest_result]

    def _get_mesh_info(self, mesh):
        '''
        http://www.ogre3d.org/addonforums/viewtopic.php?f=3&t=11621
        '''

        added_shared = False

        current_offset = 0
        shared_offset = 0
        next_offset = 0
        index_offset = 0

        vertex_count = 0
        index_count = 0

        # Calculate how many vertices and indices we're going to need
        num_sub_meshes = mesh.getNumSubMeshes()
        for i in range(0, num_sub_meshes):
            submesh = mesh.getSubMesh(i)

            # We only need to add the shared vertices once
            if submesh.useSharedVertices:
                if not added_shared:
                    vertex_count += mesh.sharedVertexData.vertexCount
                    added_shared = True
            else:
                vertex_count += submesh.vertexData.vertexCount

            # Add the indices
            index_count += submesh.indexData.indexCount

        added_shared = False;

        # Run through the submeshes again, adding the data into the arrays
        for i in range(0, num_sub_meshes):
            submesh = mesh.getSubMesh(i)

            vertexData = None
            if submesh.useSharedVertices:
                vertexData =  mesh.sharedVertexData
            else:
                vertexData = submesh.vertexData

            if not submesh.useSharedVertices or\
                (submesh.useSharedVertices and not added_shared):

                if submesh.useSharedVertices:
                    added_shared = True
                    shared_offset = current_offset

                # retrieve index buffer for this submesh
                indexData = submesh.indexData
                ibuf = indexData.indexBuffer
                pointer = ibuf.lock(ogre.HardwareBuffer.HBL_READ_ONLY)
                index_buffer = None

                if bool(ibuf.getType() == ogre.HardwareIndexBuffer.IT_32BIT):
                    index_buffer = ogre.getUint32(pointer, index_count)
                else:
                    index_buffer = ogre.getUint16(pointer, index_count)
                ibuf.unlock()


                # retrieve vertex buffer for this submesh
                posElem = vertexData.vertexDeclaration\
                                .findElementBySemantic(ogre.VES_POSITION)
                vbuf = vertexData.vertexBufferBinding\
                                .getBuffer(posElem.getSource())
                pointer = vbuf.lock(ogre.HardwareBuffer.HBL_READ_ONLY)

                # There are 8 float entries for each vertex in the buffer
                # 3 for position, 3 for normal, 2 for texture coordinate.
                # We only need the position.
                vertex_buffer = ogre.getFloat(pointer, vertex_count * 8)
                vbuf.unlock()

        return [vertex_buffer, index_buffer]

    def _add_to_selection(self, gen_info):
        self._selection.add(gen_info)
        gen_info.highlight()

    def _clear_selection(self):
        for gen_info in self._selection:
            gen_info.unhighlight()

        if self._sel_geom:
            self._sel_geom.unhighlight()
            self._sel_geom = None

        self._selection.clear()

    @logmt
    def _on_manual_selection(self):
        self._sel_xpath = None
        self._sel_xpaths = []

        self._sel_xpaths = self.get_xpath_suggestions()
        if self._sel_xpaths:
            self._sel_xpath = self._sel_xpaths[0]

        self._on_selection_changed('gen')

    @logmt
    def _on_selection_changed(self, sel_type):
        self.update_conf_widget(sel_type)
        self.xpath_widget.update(self._sel_xpaths, self)

    @logmt
    def update_conf_widget(self, sel_type):
        if sel_type == 'geom':
            self.conf_widget.update_panes(self._sel_geom, sel_type,
                                          self._sel_xpath[0])

        elif sel_type == 'class':
            xpath, desc, _class = self._sel_xpath
            self.conf_widget.update_panes(_class, 'class',
                                          self._sel_xpath[0])

        else:
            gen = list(self._selection)[0]
            self.conf_widget.update_panes(gen, sel_type,
                                          self._sel_xpath[0])

    @logmt
    def pick_generator(self, x, y, width, height):
        mouse_ray = self.camera.getCameraToViewportRay(x / float(width),
                                                       y / float(height))

        data = self._cast_ray(mouse_ray)
        if not data:
            return

        entity, point = data
        if not entity:
            return

        gen_info = self.obtree.pick_entity(entity)
        return gen_info

    @logmt
    def select_xpath(self, xpath, description=''):
        self._clear_selection()
        self._sel_xpath = None

        gen_infos = self.query(xpath)
        if not gen_infos:
            return

        for g in gen_infos:
            self._add_to_selection(g)

        g = gen_infos[0]
        self._sel_xpath = (xpath, description, g.generator.__class__)

        sel_type = 'gen' if len(self._selection) == 1 else 'class'

        self.update_conf_widget(sel_type)

    @logmt
    def on_mouse_click(self, event):
        wnd = event.GetEventObject()
        width, height = wnd.GetClientSizeTuple()
        x, y = event.GetPosition()
        gen_info = self.pick_generator(x, y, width, height)

        if not event.ControlDown() or self._sel_geom:
            self._clear_selection()

        if not gen_info:
            return

        self._add_to_selection(gen_info)
#        self._on_manual_selection()

        self.obtree_widget.select_generator(gen_info)

    def on_mouse_event(self, event):
        if self.navigation_mode == self.EXAMINE_MODE:
            c = self.center_node
        else:
            c = self.camera

        rotation = event.GetWheelRotation()
        rotation = rotation * 10 if event.ControlDown() else rotation
        rotation = rotation / 10.0 if event.ShiftDown() else rotation / 100.0
        self._move_camera((0, 0, rotation))

        if event.LeftDown():
            self.x_start, self.y_start = event.GetPosition()
            self._user_navigated = True
            self._click = True

        if event.LeftUp():
            if self._click:
                self._click = False
                self.on_mouse_click(event)

        if event.Dragging() and event.LeftIsDown():
            self._click = False
            x,y = event.GetPosition()
            dx = x - self.x_start
            dy = y - self.y_start
            self.x_start, self.y_start = x, y

            c.yaw(ogre.Degree( -dx / 3.0))
            c.pitch(ogre.Degree( -dy / 3.0))
            self._user_navigated = True

    def on_frame_started(self, event):
        cur_time = time.time()
        t = cur_time - self.last_time
        self.last_time = cur_time

        self.move_scale = self.move_speed * t

        # build tree construction activity
        if self.obtree:
            self.obtree.on_frame_started(event)

        # perform delayed actions
        for index, action in enumerate(self._actions):

            if action is None:
                continue

            try:
                action()
            finally:
                self._actions[index] = None

        while self._actions and self._actions[0] is None:
            self._actions.pop(0)

    def on_frame_ended(self, event):
        if self.obtree:
            self.obtree.on_frame_ended(event)

    def on_obtree_item_select(self, node, node_type):
        if node_type == 'gen':
            self._clear_selection()
            self._add_to_selection(node)
            self._on_manual_selection()

        elif node_type == 'geom':
            self._clear_selection()
            self._sel_geom = node
            node.highlight()
            self._on_selection_changed('geom')

    def _get_class(self, location, _id, version=None):
        old_loader = set_loader(self.loader)

        try:
            _class = get_class(location, _id, version)
        finally:
            set_loader(old_loader)

        return _class

    def get_generators_map(self):
        generators = {}

        for name, location, _id, version in self.recipe.generators:
            _class = self._get_class(location, _id, version)
            generators[_class] = name

        return generators

    @logmt
    def get_xpath_suggestions(self, gen_infos=None):
        gen_infos = gen_infos or self._selection
        names = self.get_generators_map()
        xpaths = self.obtree.suggest_xpaths(gen_infos, names)
        return xpaths

    @logmt
    def query(self, xpaths):
        match_fn = self.recipe.make_matcher(xpaths)
        return self.obtree.query(match_fn)

class DocumentManager:
    @logmt
    def __init__(self, app):
        self.app = app
        self.documents = []

    @logmt
    def add_document(self, recipe, loader):
        doc = Document(recipe, loader, self.app)
        self.documents.append(doc)
        return doc

    def _ensure_doc(self, doc):
        return self.documents[doc] if isinstance(doc, int) else doc

    @logmt
    def del_document(self, doc):
        if doc not in self.documents:
            return
        doc = self._ensure_doc(doc)
        self.documents.remove(doc)
        doc.cleanup()

    @logmt
    def reset_document(self, doc):
        doc = self._ensure_doc(doc)
        doc.reset()

    def reload_document(self, doc):
        doc = self._ensure_doc(doc)
        doc.reload()

    @logmt
    def save_document(self, doc):
        doc = self._ensure_doc(doc)
        return doc.save()

    @logmt
    def save_document_as(self, doc):
        doc = self._ensure_doc(doc)
        return doc.save_as()

    @logmt
    def get_some_document(self):
        return self.documents[0] if self.documents else None

    @logmt
    def reset(self):
        for doc in self.documents:
            doc.reset()

    @logmt
    def cleanup(self):
        for doc in self.documents:
            doc.cleanup()

        self.documents[:] = []

    @logmt
    def stop(self):
        for doc in self.documents:
            doc.stop()
