#!/usr/bin/env python 
 
import ogre.renderer.OGRE as ogre 
import SampleFramework as sf 

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

        ocube = scene_manager.createEntity('cube1', scene_manager.PT_CUBE)
        ocube.setMaterialName('RedColour')

        node = scene_manager.getRootSceneNode().createChildSceneNode('cube1_node')
        node.attachObject(ocube)
 
if __name__ == '__main__': 
   ta = TutorialApplication () 
   ta.go()
