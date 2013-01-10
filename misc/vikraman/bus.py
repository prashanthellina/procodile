#! /usr/bin/python

__author__="vikram"
__date__ ="$Nov 17, 2009 11:20:32 PM$"

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
import math


class WindowGrill(BaseGenerator):
    CONFIG = (
                'radius', (2,2),
		'height', (2,2), 		
             )

    SUB_GENERATORS = {
     #                   'book':None,
                     }

    def generate(self, config):
	
	# A window grill is being developed to be fitted into the bus.
        C = config
	grill = draw.makeCylinder(C.radius,C.height,(0,0,0),(1,0,0))
	grill_texture = self.get_material('wheel_text', M(texture='texture\\wheel.jpg'))
	grill.set_material(grill_texture)
	self.add_geom(grill)

class Wheelset(BaseGenerator):

    CONFIG = (
                'wheel_radius', (2,2),
		'height', (2,2), 
             )

    SUB_GENERATORS = {
     #                   'book':None,
                     }

    def generate(self, config):
        C = config

        wheel = draw.makeCylinder(C.wheel_radius-.25,C.height,(0,0,0),(0,1,0),2*math.pi)
        wheel_shape =  draw.makeCylinder(C.wheel_radius-.25,C.height-2,(0,1,0),(0,1,0),2*math.pi)
	wheel = wheel.cut(wheel_shape)
	alloy1 = draw.makeCylinder(C.wheel_radius-1,.01,(0,-.01,0),(0,1,0),2*math.pi)
	alloy2 = draw.makeCylinder(C.wheel_radius-1,.01,(0,C.height,0),(0,1,0),2*math.pi)
	axle = draw.makeCylinder(C.wheel_radius-.9*C.wheel_radius,C.height,(0,0,0),(0,1,0),2*math.pi)
	wheel_texture = self.get_material('wheel_text', M(texture='texture\\wheel.jpg'))
	wheel.set_material(wheel_texture)
	axle.set_material(wheel_texture)
	self.add_geom(alloy1)
	self.add_geom(alloy2)
	self.add_geom(wheel)
	self.add_geom(axle)

class Bus(BaseGenerator):

    CONFIG = (
                'length', (20,20),
                'width', (4.25,4.25),
                'height', (5, 5),
		'wheel_base',(12.5,12.5),
		'front_overhang',(3.5,3.5),
		'rear_overhang',(4.0,4.0),		
                'wheel_radius', (2,2),
             )

    SUB_GENERATORS = {
                        'Wheelset':Wheelset,		
			'WindowGrill':WindowGrill
                     }
   
    def generate(self, config):
        C = config
        
        main_frame = draw.makeBox(C.length, C.width, C.height)
	wheel_cavity = draw.makeCylinder(C.wheel_radius,C.width,(C.front_overhang,0,0),(0,1,0),2*math.pi)
	bus = main_frame.cut(wheel_cavity)
	wheel_cavity = draw.makeCylinder(C.wheel_radius,C.width,(C.length-C.rear_overhang,0,0),(0,1,0),2*math.pi)
# Here creating a hollow inside the bus
	bus_hollow = draw.makeBox(0.9*C.length, 0.9*C.width, 0.9*(C.height-C.wheel_radius),(0.05*C.length,0.05*C.width,C.wheel_radius))
	bus = bus.cut(wheel_cavity)
	bus=bus.cut(bus_hollow)
# To create a cut in the front side.
	cut_cuboid = draw.makeBox(C.width, C.width, C.height-C.wheel_radius,(0,0,C.wheel_radius))
	cuboid_transform= draw.Matrix()
	cuboid_transform.rotateY(-math.pi/4)	
	cut_cuboid = cut_cuboid.transform(cuboid_transform)	
	#C_transform.rotateY(math.pi/4)	
	#cut_cuboid = cut_cuboid.transform(cuboid_transform)
	#self.add_geom(cut_cuboid)
	bus = bus.cut(cut_cuboid)
	# Calling the Window grill
        # self.subgen('WindowGrill',(C.length/4,0,C.wheel_radius),C.length/5,(C.height-C.wheel_radius)-1,.1*(C.width))

	window1 = draw.makeBox(C.length/8,C.width,(C.height-C.wheel_radius)-2,(C.length/5,0,C.height-2))
	window2 = draw.makeBox(C.length/8,C.width,(C.height-C.wheel_radius)-2,(2*C.length/5,0,C.height-2))
	window3 = draw.makeBox(C.length/8,C.width,(C.height-C.wheel_radius)-2,(3*C.length/5,0,C.height-2))
	window4 = draw.makeBox(C.length/8,C.width,(C.height-C.wheel_radius)-2,(4*C.length/5,0,C.height-2))
	win_transform = draw.Matrix()
	#win_transform.rotateX(math.pi/2)
	#window = window.transform(win_transform)
	#grill1=  draw.makeCylinder(C.height/2,C.length,(0,C.height/4,0),(0,1,0))        
	#grill2 = draw.makeCylinder(C.height/2,C.length,(0,C.height/2,0),(0,1,0))       
	bus = bus.cut(window1)
	bus = bus.cut(window2)
	bus = bus.cut(window3)
	bus = bus.cut(window4)
	#self.add_geom(window)
	#self.add_geom(grill1)
	#self.add_geom(grill2)
	
	bus_texture = self.get_material('bus_text', M(texture='texture\\bus.jpg'))
	bus.set_material(bus_texture)
	self.subgen('Wheelset',(C.front_overhang,0,0),C.wheel_radius,C.width)		
	self.subgen('Wheelset',(C.length-C.rear_overhang,0,0),C.wheel_radius,C.width)
	# Adding the window grill
	self.subgen('WindowGrill', (C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)	
	self.subgen('WindowGrill', (C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)
	self.subgen('WindowGrill', (C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)
	self.subgen('WindowGrill', (C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)
	
	self.subgen('WindowGrill', (2*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)	
	self.subgen('WindowGrill', (2*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)
	self.subgen('WindowGrill', (2*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)
	self.subgen('WindowGrill', (2*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)

	self.subgen('WindowGrill', (3*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)	
	self.subgen('WindowGrill', (3*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)
	self.subgen('WindowGrill', (3*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)
	self.subgen('WindowGrill', (3*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)

	self.subgen('WindowGrill', (4*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)	
	self.subgen('WindowGrill', (4*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.25),.05,C.length/8)
	self.subgen('WindowGrill', (4*C.length/5,0,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)
	self.subgen('WindowGrill', (4*C.length/5,C.width,(C.height-2)+(C.height-C.wheel_radius-2)/2+.5),.05,C.length/8)

        self.add_geom(bus)
        

