# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create an outer corner using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class
import Corner as CornerMod

class Corner(pypeType):
	def __init__(self, obj, PSize="", dims=CornerMod.Dimensions()):
		"""Create an outer corner with the center at (0,0,0) and elbows along x, y and z axis.		"""
		# Run parent __init__ and define common attributes
		super(Corner, self).__init__(obj)
		obj.PType="OSE_Corner"
		obj.PRating=""
		obj.PSize=PSize
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","G","Corner","Distnace from the center to begin of innerpart of the socket").G=dims.G
		obj.addProperty("App::PropertyLength","H","Corner","Distance between the center and a corner end").H=dims.H
		obj.addProperty("App::PropertyLength","M","Corner","Outside diameter of the corner.").M=dims.M
		obj.addProperty("App::PropertyLength","POD","Corner","Pipe outer diameter.").POD=dims.POD
		obj.addProperty("App::PropertyLength","PThk","Corner","Thickness of the pipe.").PThk=dims.PThk
		obj.addProperty("App::PropertyVectorList","Ports","Corner","Ports relative positions.").Ports = self.getPorts(obj)
		obj.addProperty("App::PropertyString","PartNumber","Corner","Part number").PartNumber=""
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		dim_properties = [ "G"] # Dimensions which influence port coordinates.
		if prop in dim_properties:
			# This function is called within __init__ too. Thus we need to wait untill
			# we have all the required attributes.
			if set(CornerMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
				obj.Ports = self.getPorts(obj)
	@classmethod
	def extractDimensions(cls, obj):
		dims = CornerMod.Dimensions()
		dims.G = obj.G
		dims.H = obj.H
		dims.M = obj.M
		dims.POD = obj.POD
		dims.PThk = obj.PThk
		return dims

	@classmethod
	def createPrimitiveCorner(cls, L, D):
		"""Create corner consisting of two cylinder along x-,y- and y axis and a ball in the center."""
		x_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
		y_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))
		z_cylinder = Part.makeCylinder(D/2, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1))
		sphere = Part.makeSphere(D/2)
		return sphere.fuse([x_cylinder, y_cylinder, z_cylinder])

	@classmethod
	def createOuterPart(cls, obj):
		dims = cls.extractDimensions(obj)
		return  cls.createPrimitiveCorner(dims.H, dims.M)

	@classmethod
	def createInnerPart(cls, obj):
		dims = cls.extractDimensions(obj)
		inner = cls.createPrimitiveCorner(dims.H, dims.PID())
		inner = Corner.addSockets(dims.POD, dims.H, dims.G, inner)
		return inner

	@classmethod
	def addSockets(cls, D, H, G, shape):
		"""Add socket cylinders with diamater D to the ends of the corner shape."""
		x_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(G,0,0), FreeCAD.Vector(1,0,0))
		y_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(0,G,0), FreeCAD.Vector(0,1,0))
		z_socket = Part.makeCylinder(D/2, H-G, FreeCAD.Vector(0,0,G), FreeCAD.Vector(0,0,1))
		return shape.fuse([x_socket, y_socket, z_socket])

	@classmethod
	def createShape(cls, obj):
		outer = cls.createOuterPart(obj)
		inner = cls.createInnerPart(obj)
		return outer.cut(inner)

	def execute(self, obj):
		# Create the shape of the tee.
		shape = Corner.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)

	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		dims = self.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		return [aux["p1"], aux["p2"], aux["p3"]] # x, y, z.

class CornerBuilder:
	""" Create a corner using flamingo. """
	def __init__(self, document):
		self.dims = CornerMod.Dimensions()
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.document = document

	def create(self, obj):
		"""Create a corner.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Corner")
		"""
		corner = Corner(obj, PSize="", dims=self.dims)
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
