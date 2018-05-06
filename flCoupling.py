# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 24 March 2018
# Create a coupling using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class
import coupling as couplingMod

class Coupling(pypeType):
	def __init__(self, obj, PSize="",  dims=couplingMod.Dimensions()):
		"""Create a coupling"""
		# Run parent __init__ and define common attributes
		super(Coupling, self).__init__(obj)
		obj.PType="OSE_Coupling"
		obj.PRating="CouplingFittingFromAnyCatalog"
		obj.PSize=PSize # Pipe size
		# Define specific attributes and set their values.
		# TODO: Check socket enumerations.
		obj.addProperty("App::PropertyLength","L","Coupling","Length of the coupling").L=dims.L
		obj.addProperty("App::PropertyLength","M","Coupling","Coupling outside diameter.").M=dims.M
		obj.addProperty("App::PropertyLength","M1","Coupling","Coupling outside diameter of the thin end.").M1=dims.M1
		obj.addProperty("App::PropertyLength","N","Coupling","Length of the middle part of the coupling.").N=dims.N
		obj.addProperty("App::PropertyLength","POD","Coupling","Pipe outer diameter at the socket 1.").POD=dims.POD
		obj.addProperty("App::PropertyLength","POD1","Coupling","Pipe outer diameter at the socket 2.").POD1=dims.POD1
		obj.addProperty("App::PropertyLength","PThk","Coupling","Thickness of the pipe at the socket 1.").PThk=dims.PThk
		obj.addProperty("App::PropertyLength","PThk1","Coupling","Thickenss of the pipe at the socket 2.").PThk1=dims.PThk1
		obj.addProperty("App::PropertyVectorList","Ports","Coupling","Ports relative positions.").Ports = self.getPorts(obj)
		obj.addProperty("App::PropertyString","PartNumber","Coupling","Part number").PartNumber=""		
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		dim_properties = [ "L", "M", "M1", "N"]
		
		if prop in dim_properties:
			# This function is called within __init__ too.
			# We wait for all dimension.
			if set(couplingMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
				obj.Ports = self.getPorts(obj)

	@classmethod
	def extractDimensions(cls, obj):
		dims = couplingMod.Dimensions()
		dims.L = obj.L
		dims.M = obj.M
		dims.M1 = obj.M1
		dims.N = obj.N
		dims.POD = obj.POD
		dims.POD1 = obj.POD1
		dims.PThk = obj.PThk
		dims.PThk1 = obj.PThk1
		return dims
						
	@classmethod
	def createOuterPart(cls, obj):
		dims = cls.extractDimensions(obj)
		
		if dims.M == dims.M1:
			return cls.createOuterPartEqual(obj)
		else:
			return cls.createOuterPartReduced(obj)

	@classmethod
	def createOuterPartEqual(cls, obj):
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		""" Create the outer part is a simple cylinder. This is when M and M1 are the equal."""
		# Create complete outer cylinder.
		radius = dims.M/2.0
		height = dims.L
		outer = Part.makeCylinder(radius, height,aux["p1"])
		return outer
		
	@classmethod
	def createOuterPartReduced(cls, obj):
		""" Create a outer part which is cylinder+cone+cylinder."""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		# Create socket 1.
		r1 = dims.M/2.0
		h1 = dims.bottomSocketOuterLength()
		cylinder1 = Part.makeCylinder(r1, h1, aux["p1"])
		# Create a cone and put it on the cylinder 1.
		r2 = dims.M1/2.0
		hc = dims.N
		cone = Part.makeCone(r1, r2, hc, aux["p4"])
		# Create a socket 2 and put it on the cone.
		h2 = dims.topSocketOuterLength()
		cylinder2 = Part.makeCylinder(r2, h2, aux["p5"])
		outer = cylinder1.fuse([cone, cylinder2])
		return outer
		
	@classmethod
	def createInnerPart(cls, obj):
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		# Create parts which must be removed from the coupling.
		if dims.PID() == dims.PID1():
			return cls.createInnerPartEqual(obj)
		else:
			return cls.createInnerPartReduced(obj)
	
	@classmethod
	def createInnerPartEqual(cls, obj):
		""" Create the inner part from cylinders. This is when POD and P=D1 are the equal."""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		# Create lower inner cylinder.
		height1 = dims.socketDepthA5()
		cylinder1i = Part.makeCylinder(dims.POD/2.0, height1)
		# Create intermediatiate inner cylinder (from beginning to the end of the complete socket).
		height2 = dims.L
		cylinder2i = Part.makeCylinder(dims.PID()/2.0, height2, aux["p1"])
		# Create an upper inner cylinder.
		cylinder3i = Part.makeCylinder(dims.POD/2.0, height1, aux["p3"])
		inner = cylinder1i.fuse([cylinder2i, cylinder3i])
		return inner
		
	@classmethod
	def createInnerPartReduced(cls, obj):
		""" Create a outer part which is cylinder+cone+cylinder."""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		# Create a lower cylinder.
		r = dims.POD/2.0
		h = dims.socketDepthA5()
		cylinder1i = Part.makeCylinder(r, h, aux["p1"])
		# Create a cone and put it on the cylinder 1.
		r1 = dims.PID()/2.0
		r2 = dims.PID1()/2.0
		hc = dims.N
		cone = Part.makeCone(r1, r2, hc, aux["p2"])
		# Create an upper cylinder.
		r = dims.POD1/2	
		h = dims.socketDepthA5()
		cylinder2i = Part.makeCylinder(r, h, aux["p3"])
		inner = cylinder1i.fuse([cone, cylinder2i])
		return inner
		
	def execute(self, obj):
		# Create the shape of the coupling.
		inner = Coupling.createInnerPart(obj)
		outer = Coupling.createOuterPart(obj)
		shape = outer.cut(inner)
		obj.Shape = shape
		# define Ports, i.e. where the tube have to be placed
		obj.Ports = self.getPorts(obj)
		
	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		dims = self.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		return [aux["p2"], aux["p3"]]


class CouplingBuilder:
	""" Create a coupling using flamingo. """
	def __init__(self, document):
		self.dims = couplingMod.Dimensions()
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.document = document
				
	def create(self, obj):
		"""Create a couzpling.
		 
		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Coupling")
		"""	
		coupling = Coupling(obj, PSize="", dims=self.dims)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos

		return coupling

# Create a test coupling.
def Test():
	document = FreeCAD.activeDocument()
	builder = CouplingBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-Coupling")
	builder.create(feature)
	document.recompute()
	
#Test()
