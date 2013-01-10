import os
import math
import time
import logging
import threading
import ctypes
from itertools import chain

import Image #PIL
import wx
import ogre.renderer.OGRE as ogre

from procodile.utils import log_method_call as logmt
from procodile.procedural import rungen, re_rungens
from procodile.draw import SurfaceGroup
import procodile.buildspace as buildspace
from procodile.recipe import RecipeBasedGenerator

from utils import PIDEException, load_image, app_abs_path
import viewer

log = logging.getLogger()

def get_scene_manager():
    return viewer.SCENE_MANAGER

def get_mesh_manager():
    return ogre.MeshManager.getSingleton()

class BuildTreeOverlay:
    MAX_COMPUTATION_TIME_PER_FRAME = 1 / 30.
    MAX_ACTIONS_PILEUP = 100

    STATE_READY = 0
    STATE_RUNNING = 1
    STATE_PAUSED = 2
    STATE_COMPLETED = 3

    @logmt
    def __init__(self, gen_class, doc):

        self.state = self.STATE_READY
        self.gen_class = gen_class
        self.doc = doc
        self.root_gen = None
        self.highlighted = None

        #: generator/geom info to corresponding object map
        self.info_to_obj = {}

        #: generator/geom to corresponding info object map
        self.obj_to_info = {}

        #: entity to generator info map
        self.entity_to_info = {}

        self.materials = set()
        self.textures = set()

        self._actions = None
        self._bspace = None
        self._thread = None

        self.build_time_elapsed = 0
        self._build_start_time = 0
        self._next_callback_time = 1

        self._flow_control_pause = False
        self._build_completed = False
        self._build_completed_sent = False
        self.on_first_gen_created = None

    def _queue_action(self, action):
        if self._actions is None:
            return

        self._actions.append(action)

    def on_frame_started(self, event):

        if self._actions is None:
            return

        # flow control
        # ensure that the background generation thread
        # does not steal all the cpu. if the actions
        # queue crossed threshold, pause generation until
        # it clears
        bs = self._bspace
        bs_paused = bs.state == bs.STATE_PAUSED

        if len(self._actions) > self.MAX_ACTIONS_PILEUP:
            if not bs_paused:
                bs.pause()
                self._flow_control_pause = True

        else:
            if bs_paused and self._flow_control_pause:
                bs.resume()
                self._flow_control_pause = False

        # when paused, do not perform any action
        if self.state == self.STATE_PAUSED:
            return

        # consume actions
        time_left = self.MAX_COMPUTATION_TIME_PER_FRAME

        for index, action in enumerate(self._actions):

            if action is None:
                continue

            try:
                start_time = time.time()
                action()
                time_taken = time.time() - start_time
                time_left = time_left - time_taken
                if time_left <= 0:
                    break
            except:
                log.exception('delayed action failed')
            finally:
                self._actions[index] = None

        while self._actions and self._actions[0] is None:
            self._actions.pop(0)

        if self._build_completed and not self._actions \
            and not self._build_completed_sent:
            self.doc.on_build_completed()
            self._build_completed_sent = True

    def on_frame_ended(self, event):
        pass

    def event_handler(self, event, args):
        self.build_time_elapsed = time.time() - self._build_start_time

        if math.floor(self.build_time_elapsed) == self._next_callback_time:
            self.doc.on_time_elapsed(self.build_time_elapsed)
            self._next_callback_time += 1

        handler = None

        if event == 'add_gen':
            handler = self.handle_add_gen

        elif event == 'del_gen':
            handler = self.handle_del_gen

        elif event == 'add_geom':
            handler = self.handle_add_geom

        elif event == 'del_geom':
            handler = self.handle_del_geom

        elif event == 'add_material':
            handler = self.handle_add_material

        elif event == 'add_texture':
            handler = self.handle_add_texture

        if handler and self._actions is not None:
            self._actions.append(lambda: handler(*args))

    def handle_add_gen(self, gen_obj, parent_obj):

        gen_info = GeneratorInfo(gen_obj, self)
        self.info_to_obj[gen_info] = gen_obj
        self.obj_to_info[gen_obj] = gen_info

        if parent_obj == None:
            bases = gen_obj.__class__.__bases__ #TODO
            if len(bases) == 2:
                _parent, other_parent = bases
                gen_class = _parent if _parent != RecipeBasedGenerator else \
                                                                other_parent
            else:
                gen_class = gen_obj.__class__

        else:
            gen_class = gen_obj.__class__

        gen_obj.name = self.doc.get_generators_map()[gen_class]

        if parent_obj is None:
            parent_node = self.doc.scene_node
            self.root_gen = gen_info
            self.doc.on_root_gen_created()

        else:
            pgen_info = self.obj_to_info[parent_obj]
            pgen_info.sub_gen_infos.append(gen_info)
            parent_node = pgen_info.node

        parent_node.addChild(gen_info.node)

        if self.on_first_gen_created:
            self.on_first_gen_created(gen_info)
            self.on_first_gen_created = None

    def handle_del_gen(self, gen_obj, parent_obj):

        gen_info = self.obj_to_info.pop(gen_obj)
        del self.info_to_obj[gen_info]

        if parent_obj:
            pgen_info = self.obj_to_info[parent_obj]
            pgen_info.sub_gen_infos.remove(gen_info)

            parent_node = pgen_info.node
            parent_node.removeChild(gen_info.node)

        else:
            self.doc.on_root_gen_destroyed()
            self.root_gen = None

        gen_info.cleanup()

    def handle_add_geom(self, gen_obj, geom):
        gen_info = self.obj_to_info[gen_obj]

        if geom in self.obj_to_info:
            return

        geom_info = GeomInfo(geom, self)
        self.info_to_obj[geom_info] = geom
        self.obj_to_info[geom] = geom_info

        gen_info.geom_infos.append(geom_info)

        for e in geom_info.render():
            gen_info.node.attachObject(e)
            self.entity_to_info[e.name] = gen_info

    def handle_del_geom(self, gen_obj, geom):
        gen_info = self.obj_to_info[gen_obj]
        geom_info = self.obj_to_info[geom]

        del self.obj_to_info[geom]
        del self.info_to_obj[geom_info]

        gen_info.geom_infos.remove(geom_info)

        for e in geom_info.entities:
            gen_info.node.detachObject(e)
            del self.entity_to_info[e.name]

        geom_info.cleanup()

    def handle_add_material(self, material):
        self._create_material(material)

    def handle_add_texture(self, texture):
        self._create_texture(texture)

    def _get_image_data(self, image_fpath):
        image = Image.open(image_fpath)

        image_data = image.getdata()

        if len(image_data[0]) == 3:
            image_data = [(b, g, r, 255) for r, g, b in image_data]

        elif len(image_data[0]) == 4:
            image_data = [(b, g, r, a) for r, g, b, a in image_data]

        else:
            raise Exception('bad texture: %s' % image_fpath)

        image_data = list(chain(*image_data))
        return image_data, image.size

    def _create_texture(self, texture):
        texture_name = 'texture_%x' % id(texture)

        # load texture image data
        image_data, (width, height) = self._get_image_data(texture.fpath)

        # create ogre texture object
        tm = ogre.TextureManager.getSingleton()
        res_group = ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME
        t = tm.createManual(texture_name,
                              res_group,
                              ogre.TEX_TYPE_2D,
                              width, height,
                              0,
                              ogre.PF_BYTE_BGRA,
                              ogre.TU_DEFAULT)

        # set image data into ogre texture
        buflen = width * height * 4
        pbuffer = t.getBuffer()
        pointer = pbuffer.lock(0, buflen, ogre.HardwareBuffer.HBL_NORMAL)
        storageclass = ctypes.c_uint8 * buflen
        cbuffer = storageclass.from_address(ogre.CastInt(pointer))

        for i in xrange(buflen):
            cbuffer[i] = image_data[i]

        pbuffer.unlock()

        self.textures.add(texture_name)

    def _create_material(self, material):
        material_name = 'material_%x' % id(material)

        mm = ogre.MaterialManager.getSingleton()
        mat = mm.create(material_name,
                   ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME)

        pass0 = mat.getTechnique(0).getPass(0)

        if material.texture and material.texture.fpath:
            texture_name = 'texture_%x' % id(material.texture)
            tus = pass0.createTextureUnitState(texture_name)
            tmethod = material.address_mode.upper()
            tmethod = getattr(ogre.TextureUnitState, 'TAM_%s' % tmethod)
            tus.setTextureAddressingMode(tmethod)
            tus.setTextureScroll(*material.scroll)
            tus.setTextureScale(*material.scale)
            tus.setTextureRotate(material.rotate)

        else:
            pass0.setAmbient(material.ambient)
            pass0.setDiffuse(material.diffuse)
            pass0.setSpecular(material.specular)
            pass0.setSelfIllumination(material.emissive)
            pass0.setShininess(material.shininess)
        
        self.materials.add(material_name)

    @logmt
    def _do_build(self, gen_infos=None):

        bspace = self._bspace

        try:

            if gen_infos:
                re_rungens([g.generator for g in gen_infos])

            else:
                g = self.gen_class
                config = g.make_config()
                seed = 0
                rungen(g, config, seed, g.__name__, bspace=bspace)

        except (SystemExit, KeyboardInterrupt):
            raise

        except:
            log.exception('during build')

        self.state = self.STATE_COMPLETED
        self._thread = None
        self._build_completed = True

        if not self._actions:
            self.doc.on_build_completed()
            self._build_completed_sent = True

    @logmt
    def build(self):
        if self.state != self.STATE_READY:
            raise PIDEException('not ready')

        self.state = self.STATE_RUNNING

        self._actions = []
        self._bspace = buildspace.BuildSpace()
        self._bspace.event_handlers.append(self.event_handler)

        self._thread = threading.Thread(target=self._do_build,
                                        name='build_%x' % id(self))
        self._thread.start()
        self._build_start_time = time.time()

    @logmt
    def rebuild(self, gen_infos, on_first_gen_created=None):
        assert(gen_infos != None)

        if self.state != self.STATE_COMPLETED:
            raise Exception('cannot rebuild in current state')

        self.state = self.STATE_RUNNING
        self.on_first_gen_created = on_first_gen_created

        fn = lambda: self._do_build(gen_infos)
        self._thread = threading.Thread(target=fn,
                                        name='rebuild_%x' % id(self))
        self._thread.start()
        self._build_start_time = time.time()
        
    @logmt
    def pause(self):
        self._flow_control_pause = False

        if self.state != self.STATE_RUNNING:
            return

        self.state = self.STATE_PAUSED
        self._bspace.pause()

    @logmt
    def resume(self):
        if self.state != self.STATE_PAUSED:
            return

        self.state = self.STATE_RUNNING
        self._bspace.resume()

    @logmt
    def stop(self):
        if self.state not in (self.STATE_RUNNING,
                              self.STATE_PAUSED):
            return

        self._bspace.stop()

        self._actions = None
        self._thread = None
        self.state = self.STATE_COMPLETED

        # wait for thread to die
        timeout = 10
        wait_time = .1
        while self._thread and timeout >= 0:
            time.sleep(wait_time)
            timeout -= wait_time

        if timeout < 0:
            log.error('timedout waiting for thread to stop')

    @logmt
    def cleanup(self):
        if self.state == self.STATE_READY:
            return

        elif self.state == self.STATE_COMPLETED:
            pass

        else:
            self.stop()

        # detach root scene node of build tree from document scene node
        root_node = self.root_gen.node
        parent_node = root_node.getParent()
        if parent_node:
            parent_node.removeChild(root_node)

        self.root_gen.cleanup()

        self.gen_class = None
        self.highlighted = None
        self.doc = None
        self.root_gen = None
        self.info_to_obj = self.obj_to_info = None

        mm = ogre.MaterialManager.getSingleton()
        for mname in self.materials:
            mm.remove(mname)
        self.materials = None

        tm = ogre.TextureManager.getSingleton()
        for tname in self.textures:
            if tm.resourceExists(tname):
                tm.remove(tname)
        self.textures = None

        self._bspace = None
        self.state = None

    @logmt
    def pick_entity(self, entity):
        entity = entity.name
        gen_info = self.entity_to_info.get(entity)
        return gen_info

    @logmt
    def highlight(self, node):
        if self.highlighted:
            self.highlighted.unhighlight()
            self.highlighted = None

        node.highlight()
        self.highlighted = node

    @logmt
    def get_bounding_box(self):
        return self.root_gen.get_bounding_box()

    @logmt
    def suggest_xpaths(self, gen_infos, names):
        generators = [g.generator for g in gen_infos]
        return self._bspace.suggest_xpaths(generators, names)

    @logmt
    def query(self, match_fn):
        gens = self._bspace.query(match_fn)

        _map = self.obj_to_info
        gen_infos = [_map[g] for g in gens if g in _map]
        return gen_infos

class GeneratorInfo(object):

    def __init__(self, generator, obtree):
        self.generator = generator
        self.obtree = obtree

        self.sub_gen_infos = []
        self.geom_infos = []

        sm = get_scene_manager()
        self.node = sm.createSceneNode()

    @property
    def config(self):
        return self.generator.config

    @property
    def default_config(self):
        return self.generator.get_config()

    @property
    def sub_gens(self):
        return self.generator.children

    @property
    def geoms(self):
        return self.generator.geoms

    @property
    def id(self):
        return self.generator.id

    @property
    def seed(self):
        return self.generator.seed

    @property
    def s_seed(self):
        return self.generator.s_seed

    @property
    def name(self):
        return self.generator.name

    @property
    def location(self):
        return self.generator.location

    @property
    def bbox(self):
        return self.generator.bbox

    def cleanup(self):

        for g in self.sub_gen_infos:
            self.node.removeChild(g.node)
            g.cleanup()

        self.sub_gen_infos[:] = []

        for g in self.geom_infos:
            g.cleanup()

        self.geom_infos[:] = []

        sm = get_scene_manager()
        sm.destroySceneNode(self.node)
        self.node = None

    def highlight(self):
        for g in self.geom_infos:
            g.highlight()

        for g in self.sub_gen_infos:
            g.highlight()

    def unhighlight(self):
        for g in self.geom_infos:
            g.unhighlight()

        for g in self.sub_gen_infos:
            g.unhighlight()

    def get_bounding_box(self):
        bbox = ogre.AxisAlignedBox()

        for g in self.geom_infos:
            gbbox = g.get_bounding_box()
            if gbbox:
                bbox.merge(gbbox)

        for g in self.sub_gen_infos:
            bbox.merge(g.get_bounding_box())

        return bbox

    def __eq__(self, other):
        if other is None or not isinstance(other, GeneratorInfo):
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

class GeomInfo:
    def __init__(self, geom, obtree):
        self.obtree = obtree
        self.geom = geom

        self._meshes = []
        self._materials = []
        self.entities = []

        self.num_vertices = 0
        self.num_triangles = 0

    def get_id(self):
        return '%x' % id(self)

    @property
    def bbox(self):
        return ''

    @property
    def visible(self):
        return self.geom.visible

    def is_rendered(self):
        return bool(self._meshes)

    def _make_mesh(self, geom, name, material_name):
        sm = get_scene_manager()

        mesh = geom.mesh
        if not mesh:
            return None
        
        vertices, indices, normals, tcoords = mesh

        obj = sm.createManualObject(name)
        obj.setDynamic(True)
        obj.begin(material_name, ogre.RenderOperation.OT_TRIANGLE_LIST)

        num_vertices = len(vertices)
        num_triangles = len(indices)

        for vindex, vertindices in enumerate(indices):
            for index in vertindices:
                vertex = vertices[index]
                normal = normals[index]

                x, y, z = vertex
                vertex = x, z, -y

                x, y, z = normal
                normal = x, z, -y

                obj.position(*vertex)
                obj.normal(*normal)

                if tcoords:
                    tcoord = tcoords[index] or (0.0, 0.0)
                    obj.textureCoord(*tcoord)

            i = vindex * 3
            obj.triangle(i, i+1, i+2)

        obj.end()
        mesh = obj.convertToMesh(name)
        sm.destroyManualObject(name)

        return mesh, num_triangles, num_vertices

    def make_mesh(self):
        name = self.get_id()
        g = self.geom

        self.num_triangles = 0
        self.num_vertices = 0

        if isinstance(g, SurfaceGroup):
            geoms = g.surfaces.values()
        else:
            geoms = [g]

        for index, geom in enumerate(geoms):

            mname = '%s_%s' % (name, index)

            material_name = 'default'
            if geom.material:
                material_name = 'material_%x' % id(geom.material)
            self._materials.append(material_name)

            data = self._make_mesh(geom, mname, material_name)
            mesh, num_t, num_v = data
            self._meshes.append((mname, mesh))
            self.num_triangles += num_t
            self.num_vertices += num_v

        return self._meshes

    def render(self):
        if self.is_rendered():
            return self.entities

        sm = get_scene_manager()

        self._materials = []
        meshes = self.make_mesh()

        self.entities = []

        for mname, mesh in meshes:
            entity = sm.createEntity(mname, mname)
            entity.setCastShadows(True)
            self.entities.append(entity)

        return self.entities

    def cleanup(self):
        if not self.is_rendered:
            return

        mm = get_mesh_manager()
        sm = get_scene_manager()

        for mname, mesh in self._meshes:
            mm.remove(mname)
        self._meshes = []

        for e in self.entities:
            sm.destroyEntity(e)

        self._materials = []
        self.entities = []

    def highlight(self):
        if not self.is_rendered():
            return

        if not self.visible:
            return

        for e in self.entities:
            e.setMaterialName('highlight')

    def unhighlight(self):
        if not self.is_rendered():
            return

        if not self.visible:
            return

        for index, e in enumerate(self.entities):
            e.setMaterialName(self._materials[index])

    def get_bounding_box(self):
        if not self.is_rendered():
            return

        if not self.visible:
            return

        bbox = ogre.AxisAlignedBox()

        for mname, m in self._meshes:
            bbox.merge(m.getBounds())

        return bbox

class BuildTreeWidget(wx.Panel):
    def __init__(self, parent, build_tree):
        wx.Panel.__init__(self, parent)

        self.Freeze()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(build_tree, 1, wx.EXPAND)
        self.sizer.Layout()
        
        self.Thaw()
        
class BuildTree(wx.TreeCtrl):
    @logmt
    def __init__(self, *args, **kwargs):
        self.on_item_select = kwargs.pop('on_item_select')
        super(BuildTree, self).__init__(*args, **kwargs)

        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpandItem)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnExpandedItem)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapseItem)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnCollapsedItem)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged)
        self.__collapsing = False

        self.build_tree = None

        self._image_list = None
        self._image_indices = {}
        self._init_tree_images()

        self._select = None
        self.expand_item = None
        self.selected_node = None

    @logmt
    def select_generator(self, gen_info):
        ids = []

        gen = gen_info.generator

        while 1:
            ids.append(gen.id)
            gen = gen.parent
            if not gen:
                break

        ids.reverse()
        self._select = ids[1:]

        root = self.GetRootItem()
        if self.IsExpanded(root):
            self.CollapseAndReset(root)
        else:
            self.Expand(root)

    def _init_tree_images(self):
        size = (16,16)
        images = wx.ImageList(*size)

        L = lambda x: load_image(app_abs_path('icons', x + '.png'), size)

        self._image_indices['root'] = images.Add(L('build_tree'))
        self._image_indices['generator'] = images.Add(L('generator_icon'))
        self._image_indices['geom'] = images.Add(L('geom_icon'))

        self._images_list = images
        self.SetImageList(images)

    def _set_node_image(self, node, image):
        index = self._image_indices[image]
        self.SetItemImage(node, index, wx.TreeItemIcon_Normal)
        self.SetItemImage(node, index, wx.TreeItemIcon_Expanded)

    @logmt
    def set_build_tree(self, build_tree):
        self.build_tree = build_tree

        root_gen = build_tree.root_gen
        root = self.AddRoot('%s' % root_gen.name)
        self.SetPyData(root, build_tree.root_gen)
        self._set_node_image(root, 'root')
        self.SetItemHasChildren(root)
        self.Expand(root)

    @logmt
    def clear_build_tree(self):
        self.DeleteAllItems()
        self.build_tree = None
        
    @logmt
    def OnSelectionChanged(self, event):
        item = event.GetItem()
        node = self.GetPyData(item)

        if self.selected_node == node:
            event.Veto()
            return
            
        self.selected_node = node
#        node.obtree.highlight(node)

        node_type = 'gen' if isinstance(node, GeneratorInfo) else 'geom'

        if self.on_item_select:
            self.on_item_select(node, node_type)

    @logmt
    def OnExpandItem(self, event):
        item = event.GetItem()
        node = self.GetPyData(item)
    
        expand_id = None

        if self._select:
            expand_id = self._select.pop(0)

        if isinstance(node, GeomInfo):
            return

        for index, geom in enumerate(node.geom_infos):
            child = self.AppendItem(item, '%s' % geom.__class__.__name__)
            self.SetPyData(child, geom)
            self._set_node_image(child, 'geom')
            self.SetItemHasChildren(child, False)

        for g in node.sub_gen_infos:
            child = self.AppendItem(item, '%s' % g.name)
            if g.id == expand_id:
                self.expand_item = child
            self.SetPyData(child, g)
            self._set_node_image(child, 'generator')
            self.SetItemHasChildren(child, True)

    @logmt
    def OnExpandedItem(self, event):

        item = self.expand_item
        self.expand_item = None

        if item:
            _select = self._select

            def delayed():
                self.Expand(item)

                if not _select:
                    self.EnsureVisible(item)
                    self.SelectItem(item, True)
                
            wx.CallAfter(delayed)

    @logmt
    def OnCollapseItem(self, event):
        if self.__collapsing:
            event.Veto()
            return

        self.__collapsing = True
        item = event.GetItem()
        self.CollapseAndReset(item)
        self.DeleteChildren(item)
        self.SetItemHasChildren(item)
        self.__collapsing = False

    @logmt
    def OnCollapsedItem(self, event):
        item = event.GetItem()

        if item == self.GetRootItem() and self._select:
            wx.CallAfter(lambda: self.Expand(item))
