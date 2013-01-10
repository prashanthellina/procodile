#!/usr/bin/env python 
 
import ogre.renderer.OGRE as ogre 
import SampleFramework as sf 
import graphics
import system
from system import FACE_FRONT, FACE_BACK, FACE_UP, FACE_DOWN, FACE_LEFT, FACE_RIGHT

def create_material(name,
                    diffuse_colour,
                    specular_colour = None,
                    ambient_colour = None,
                    shininess = 0.0,
                    scene_blending = ogre.SBT_TRANSPARENT_ALPHA,
                    vertex_colour_tracking = ogre.TVC_NONE
                    ):

    specular_colour = specular_colour or diffuse_colour
    ambient_colour = ambient_colour or diffuse_colour

    m = ogre.MaterialManager.getSingleton().create(name, "General")

    m.setReceiveShadows(True)
    m.getTechnique(0).setLightingEnabled(True)
    m.getTechnique(0).getPass(0).setColourWriteEnabled(True)

    m.getTechnique(0).getPass(0).setDiffuse(diffuse_colour)
    m.getTechnique(0).getPass(0).setAmbient(ambient_colour)
    m.getTechnique(0).getPass(0).setShininess(shininess)
    m.getTechnique(0).getPass(0).setSpecular(specular_colour)
    m.getTechnique(0).getPass(0).setSceneBlending(scene_blending)
    m.getTechnique(0).getPass(0).setVertexColourTracking(vertex_colour_tracking)

    return m

def create_mesh(scene_manager, name, material, mesh):
    obj = scene_manager.createManualObject(name)
    obj.setDynamic(True)
    obj.begin(material, ogre.RenderOperation.OT_TRIANGLE_LIST)

    i = 0
    for index, quad in enumerate(mesh.quads):
        a, b, c, d = quad.points
        obj.position(*a); obj.normal(*quad.normal)
        obj.position(*b)
        obj.position(*c)
        obj.position(*d)
        
        obj.quad(i, i+1, i+2, i+3)
        i += 4

    obj.end()

    return obj
 
class TutorialApplication (sf.Application): 
    """Application class.""" 
 
    def _createScene (self):        
        # Setup the ambient light. 
        scene_manager = self.sceneManager 
        scene_manager.ambientLight = (0.1, 0.1, 0.1) 

        light = scene_manager.createLight('Light1')
        light.setType(ogre.Light.LT_POINT)
        light.setPosition((101, 150, 300))
        light.setSpecularColour((1.0, 1.0, 1.0, 1))
        light.setDiffuseColour((1.0, 1.0, 1.0, 1))

        create_material('RedColour',
                        diffuse_colour = (0.6, 0.0, 0.0),
                        specular_colour = (0.8, 0.0, 0.0),
                        ambient_colour = (0.5, 0.0, 0.0),
                        shininess = 0.6)

        m = graphics.MeshMaker()

        compound = system.Compound('a1-b2-c3.T-b4.L-a1-b3.T-h3.B-a1-b1-c1.D-a1-b1.B-100(a1)-100(b1.R)-100(b1.F)-100(b1.L)')

        '''
        compound.add_block('A1', None, None)
        compound.add_block('A2', 'A1', FACE_RIGHT)
        compound.add_block('A3', 'A2', FACE_RIGHT)
        compound.add_block('A4', 'A1', FACE_FRONT)
        compound.add_block('A5', 'A2', FACE_FRONT)
        compound.add_block('A6', 'A3', FACE_FRONT)
        compound.add_block('A7', 'A4', FACE_FRONT)
        compound.add_block('A8', 'A5', FACE_FRONT)
        #compound.add_block('A9', 'A6', FACE_FRONT)

        compound.add_block('B1', 'A1', FACE_DOWN)
        compound.add_block('B2', 'A2', FACE_DOWN)
        compound.add_block('B3', 'A3', FACE_DOWN)
        compound.add_block('B4', 'A4', FACE_DOWN)
        compound.add_block('B5', 'A5', FACE_DOWN)
        compound.add_block('B6', 'A6', FACE_DOWN)
        compound.add_block('B7', 'A7', FACE_DOWN)
        compound.add_block('B8', 'A8', FACE_DOWN)
        #compound.add_block('B9', 'A9', FACE_DOWN)

        compound.add_block('C1', 'B1', FACE_DOWN)
        compound.add_block('C2', 'B2', FACE_DOWN)
        compound.add_block('C3', 'B3', FACE_DOWN)
        compound.add_block('C4', 'B4', FACE_DOWN)
        compound.add_block('C5', 'B5', FACE_DOWN)
        compound.add_block('C6', 'B6', FACE_DOWN)
        #compound.add_block('C7', 'B7', FACE_DOWN)
        #compound.add_block('C8', 'B8', FACE_DOWN)
        #compound.add_block('C9', 'B9', FACE_DOWN)
        '''

        mesh = m.get_mesh(compound)

        mesh = create_mesh(scene_manager, 'mesh1', 'RedColour', mesh)
        mesh.convertToMesh('compound.mesh')
        ocube = scene_manager.createEntity('c1', 'compound.mesh')

        node = scene_manager.getRootSceneNode().createChildSceneNode('cube1_node')
        node.attachObject(ocube)
 
if __name__ == '__main__': 
   ta = TutorialApplication () 
   ta.go()
