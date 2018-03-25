# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create an outer corner using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class

class Corner(pypeType):
	def __init__(self, obj, PSize="", G=20, H=30, M=30, POD=20, PID=10):
		"""Create an outer corner with the center at (0,0,0) and elbows along x, y and z axis.		"""
		# Run parent __init__ and define common attributes
		super(Corner, self).__init__(obj)
		obj.PType="OSE_Corner"
		obj.PRating=""
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","G","Corner","Distnace from the center to begin of innerpart of the socket").G=G
		obj.addProperty("App::PropertyLength","H","Corner","Distance between the center and a corner end").H=H
		obj.addProperty("App::PropertyLength","M","Corner","Outside diameter of the corner.").M=M
		obj.addProperty("App::PropertyLength","POD","Corner","Pipe outer diameter.").POD=POD
		obj.addProperty("App::PropertyLength","PID","Corner","Pipe inner diameter.").PID=PID
		obj.addProperty("App::PropertyVectorList","Ports","Corner","Ports relative positions.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		if prop in ["G"]:
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)
	@staticmethod
	def createPrimitiveCorner(L, D):
		"""Create corner consisting of two cylinder along x-,y- and y axis and a ball in the center."""
		x_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
		y_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))
		z_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1))
		sphere = Part.makeSphere(D/2)
		return sphere.fuse([x_cylinder, y_cylinder, z_cylinder])
		
	@staticmethod
	def addSockets(D, H, G, shape):
		"""Add socket cylinders with diamater D to the ends of the corner shape."""
		x_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(G,0,0), FreeCAD.Vector(1,0,0))
		y_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(0,G,0), FreeCAD.Vector(0,1,0))
		z_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(0,0,G), FreeCAD.Vector(0,0,1))
		return shape.fuse([x_socket, y_socket, z_socket])
		
	@staticmethod	
	def createShape(obj):
		G = obj.G
		H = obj.H
		M = obj.M
		POD = obj.POD
		PID = obj.PID

		outer = Corner.createPrimitiveCorner(H, M)
		inner = Corner.createPrimitiveCorner(H, PID)
		inner = Corner.addSockets(POD, H, G, inner)
		return outer.cut(inner)

	def execute(self, obj):
		# Create the shape of the tee.
		shape = Corner.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		port_x = FreeCAD.Vector(obj.G,0, 0)
		port_y = FreeCAD.Vector(0,obj.G,0)
		port_z = FreeCAD.Vector(0,0,obj.G)
		return [port_x, port_y, port_z]

class CornerBuilder:
	""" Create a corner using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.G = 20
		self.H = 30
		self.M = 30
		self.POD = 20
		self.PID = 10
		
	def create(self, obj):
		"""Create a corner.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Corner")
		"""			
		corner = Corner(obj, PSize="", G=self.G, H=self.H, M=self.M, POD=self.POD, PID=self.PID)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		return corner

# Create a test corner.
def Test():
	document = FreeCAD.activeDocument()
	builder = CornerBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-Corner")
	builder.create(feature)
	document.recompute()
	
#Test()
