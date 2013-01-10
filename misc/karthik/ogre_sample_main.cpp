#include "ExampleApplication.h"

/*
ManualObject* createCubeMesh(Ogre::String name, Ogre::String matName)
{

    ManualObject* cube = new ManualObject(name);
    cube->begin(matName);

    cube->position(0.5,-0.5,1.0);
    cube->normal(0.408248,-0.816497,0.408248);
    cube->textureCoord(1,0);
    cube->position(-0.5,-0.5,0.0);
    cube->normal(-0.408248,-0.816497,-0.408248);
    cube->textureCoord(0,1);
    cube->position(0.5,-0.5,0.0);
    cube->normal(0.666667,-0.333333,-0.666667);
    cube->textureCoord(1,1);
    cube->position(-0.5,-0.5,1.0);
    cube->normal(-0.666667,-0.333333,0.666667);
    cube->textureCoord(0,0);
    cube->position(0.5,0.5,1.0);
    cube->normal(0.666667,0.333333,0.666667);
    cube->textureCoord(1,0);
    cube->position(-0.5,-0.5,1.0);
    cube->normal(-0.666667,-0.333333,0.666667);
    cube->textureCoord(0,1);
    cube->position(0.5,-0.5,1.0);
    cube->normal(0.408248,-0.816497,0.408248);
    cube->textureCoord(1,1);
    cube->position(-0.5,0.5,1.0);
    cube->normal(-0.408248,0.816497,0.408248);
    cube->textureCoord(0,0);
    cube->position(-0.5,0.5,0.0);
    cube->normal(-0.666667,0.333333,-0.666667);
    cube->textureCoord(0,1);
    cube->position(-0.5,-0.5,0.0);
    cube->normal(-0.408248,-0.816497,-0.408248);
    cube->textureCoord(1,1);
    cube->position(-0.5,-0.5,1.0);
    cube->normal(-0.666667,-0.333333,0.666667);
    cube->textureCoord(1,0);
    cube->position(0.5,-0.5,0.0);
    cube->normal(0.666667,-0.333333,-0.666667);
    cube->textureCoord(0,1);
    cube->position(0.5,0.5,0.0);
    cube->normal(0.408248,0.816497,-0.408248);
    cube->textureCoord(1,1);
    cube->position(0.5,-0.5,1.0);
    cube->normal(0.408248,-0.816497,0.408248);
    cube->textureCoord(0,0);
    cube->position(0.5,-0.5,0.0);
    cube->normal(0.666667,-0.333333,-0.666667);
    cube->textureCoord(1,0);
    cube->position(-0.5,-0.5,0.0);
    cube->normal(-0.408248,-0.816497,-0.408248);
    cube->textureCoord(0,0);
    cube->position(-0.5,0.5,1.0);
    cube->normal(-0.408248,0.816497,0.408248);
    cube->textureCoord(1,0);
    cube->position(0.5,0.5,0.0);
    cube->normal(0.408248,0.816497,-0.408248);
    cube->textureCoord(0,1);
    cube->position(-0.5,0.5,0.0);
    cube->normal(-0.666667,0.333333,-0.666667);
    cube->textureCoord(1,1);
    cube->position(0.5,0.5,1.0);
    cube->normal(0.666667,0.333333,0.666667);
    cube->textureCoord(0,0);

    cube->triangle(0,1,2);
    cube->triangle(3,1,0);
    cube->triangle(4,5,6);
    cube->triangle(4,7,5);
    cube->triangle(8,9,10);
    cube->triangle(10,7,8);
    cube->triangle(4,11,12);
    cube->triangle(4,13,11);
    cube->triangle(14,8,12);
    cube->triangle(14,15,8);
    cube->triangle(16,17,18);
    cube->triangle(16,19,17);
    cube->end();

    return cube;

}

ManualObject* createTriangle(Ogre::String name, Ogre::String matName)
{

    ManualObject* triangle = new ManualObject(name);
    //triangle->begin(matName, RenderOperation::OT_LINE_STRIP);
    triangle->begin(matName);

    triangle->position(0, 0, 0);    //cube->normal(0.408248,-0.816497,0.408248);cube->textureCoord(1,0);
    triangle->position(100, 0, 0);   //cube->normal(-0.408248,-0.816497,-0.408248);cube->textureCoord(0,1);
    triangle->position(0, 100, 0);    //cube->normal(0.666667,-0.333333,-0.666667);cube->textureCoord(1,1);

    triangle->colour(1.0, 0.0, 0.0, 1.0);
    triangle->colour(1.0, 0.0, 0.0, 1.0);
    triangle->colour(1.0, 0.0, 0.0, 1.0);

    triangle->triangle(0, 1, 2);
    triangle->end();

    return triangle;
}

ManualObject* createTriangle1(SceneManager* s, Ogre::String name)
{
    ManualObject* manual = s->createManualObject(name);
    manual->begin("", RenderOperation::OT_TRIANGLE_FAN);

    manual->position(-100.0, -100.0, 0.0);
    manual->colour(1.0, 0.0, 0.0, 1);


    manual->position( 100.0, -100.0, 0.0);
    manual->colour(1.0, 0.0, 0.0, 1);


    manual->position( 100.0,  100.0, 0.0);
    manual->colour(1.0, 0.0, 0.0, 1);


    manual->position(-100.0,  100.0, 0.0);
    manual->colour(1.0, 0.0, 0.0, 1);


    manual->index(0);
    manual->index(1);
    manual->index(2);
    manual->index(3);
    manual->index(0);

    //manual->triangle(0, 1, 2);

    manual->end();

    return manual;
}
*/

ManualObject* createBox(SceneManager* sceneMgr, const Ogre::String name, Ogre::ColourValue val)
{
      ManualObject* manual =  sceneMgr->createManualObject(name);

      manual->setDynamic(true);

      manual->begin("", RenderOperation::OT_TRIANGLE_LIST);

      //front
      manual->position(0, 0, 0); manual->normal(0,0,-1); manual->colour(val);
      manual->position(100, 0, 0); manual->normal(0,0,-1); manual->colour(val);
      manual->position(100, 100, 0); manual->normal(0,0,-1); manual->colour(val);
      manual->position(0, 100, 0); manual->normal(0,0,-1); manual->colour(val);
      manual->quad(0, 1, 2, 3);

      //back
      manual->position(0, 0, -100); manual->normal(0,0,1); manual->colour(val);
      manual->position(100, 0, -100); manual->normal(0,0,1); manual->colour(val);
      manual->position(100, 100, -100); manual->normal(0,0,1); manual->colour(val);
      manual->position(0, 100, -100); manual->normal(0,0,1); manual->colour(val);
      manual->quad(7, 6, 5, 4);

      //left side
      manual->position(0, 0, 0); manual->normal(-1, 0, 0); manual->colour(val);
      manual->position(0, 100, 0); manual->normal(-1, 0, 0); manual->colour(val);
      manual->position(0, 100, -100); manual->normal(-1, 0, 0); manual->colour(val);
      manual->position(0, 0, -100); manual->normal(-1, 0, 0); manual->colour(val);
      manual->quad(8, 9, 10, 11);

      //right side
      manual->position(100, 0, 0); manual->normal(1, 0, 0); manual->colour(val);
      manual->position(100, 0, -100); manual->normal(1, 0, 0); manual->colour(val);
      manual->position(100, 100, -100); manual->normal(1, 0, 0); manual->colour(val);
      manual->position(100, 100, 0); manual->normal(1, 0, 0); manual->colour(val);
      manual->quad(12, 13, 14, 15);

      //top
      manual->position(0, 100, 0); manual->normal(0, 1, 0); manual->colour(val);
      manual->position(100, 100, 0); manual->normal(0, 1, 0); manual->colour(val);
      manual->position(100, 100, -100); manual->normal(0, 1, 0); manual->colour(val);
      manual->position(0, 100, -100); manual->normal(0, 1, 0); manual->colour(val);
      manual->quad(16, 17, 18, 19);

      //bottom
      manual->position(0, 0, 0); manual->normal(0, -1, 0); manual->colour(val);
      manual->position(0, 0, -100); manual->normal(0, -1, 0); manual->colour(val);
      manual->position(100, 0, -100); manual->normal(0, -1, 0); manual->colour(val);
      manual->position(100, 0,  0); manual->normal(0, -1, 0); manual->colour(val);
      manual->quad(20, 21, 22, 23);


      manual->end();

      return manual;
}

void initializeColor()
{
    Ogre::ColourValue val2 = Ogre::ColourValue(0.4,0.0,0.0,1);
    Ogre::MaterialPtr matptr = Ogre::MaterialManager::getSingleton().create("SolidColour", "General");
    matptr->setReceiveShadows(true);
    matptr->getTechnique(0)->setLightingEnabled(true);
    matptr->getTechnique(0)->getPass(0)->setColourWriteEnabled(true);
    //matptr->getTechnique(0)->getPass(0)->setDiffuse(val2);
    matptr->getTechnique(0)->getPass(0)->setAmbient(val2);
    matptr->getTechnique(0)->getPass(0)->setSpecular(val2);
    matptr->getTechnique(0)->getPass(0)->setSceneBlending(Ogre::SBT_TRANSPARENT_ALPHA);
    matptr->getTechnique(0)->getPass(0)->setVertexColourTracking(Ogre::TVC_SPECULAR);
}

class TutorialApplication : public ExampleApplication
{
protected:
public:
    TutorialApplication()
    {
    }

    ~TutorialApplication()
    {
    }
protected:
    void createScene(void)
    {
        mSceneMgr->setAmbientLight( ColourValue(0.1,0.1,0.1) );


        initializeColor();


        /*
        Entity *ent1 = mSceneMgr->createEntity( "Robot", "robot.mesh" );
        SceneNode *node1 = mSceneMgr->getRootSceneNode()->createChildSceneNode( "RobotNode" );
        node1->attachObject ( ent1 );



        SceneNode* mNode = mSceneMgr->getRootSceneNode()->createChildSceneNode();
        mNode->setPosition(0,0,0);
        //mNode->attachObject(createTriangle("Cube", "myMaterial"));
        mNode->attachObject(createTriangle1(mSceneMgr, "Cube"));



            SceneNode* mNode1 = mSceneMgr->getRootSceneNode()->createChildSceneNode();
            mNode1->setPosition(50,50,100);
            mNode1->attachObject(createTriangle("Cube1", "myMaterial"));
            */



        Light *light;
        light = mSceneMgr->createLight("Light1");
        light->setType(Light::LT_POINT);
        light->setPosition(Vector3(50, 200, -200));
        light->setSpecularColour(ColourValue(1.0, 1.0, 1.0, 1));
        light->setDiffuseColour(ColourValue(1.0, 1.0, 1.0, 1));

        ManualObject* box = createBox(mSceneMgr,"RedBox",Ogre::ColourValue(1,0,0));
        box->convertToMesh("RedBox.mesh");
        Entity *ent1 = mSceneMgr->createEntity( "MyBox", "RedBox.mesh" );
        SceneNode *node1 = mSceneMgr->getRootSceneNode()->createChildSceneNode( "RobotNode" );
        node1->attachObject( ent1 );


        /*
        Entity *ent2 = mSceneMgr->createEntity( "Robot2", "robot.mesh" );
        SceneNode *node2 = mSceneMgr->getRootSceneNode()->createChildSceneNode( "RobotNode2", Vector3( 50, 0, 0 ) );
        node2->attachObject( ent2 );
        */

    }
};

int main(int argc, char **argv)
{
    // Create application object
    TutorialApplication app;

    try
    {
        app.go();
    }
    catch ( Exception& e )
    {
        fprintf(stderr, "An exception has occurred: %s\n",
                e.what());
    }

    return 0;
}
