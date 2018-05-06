# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create a tee using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class
import tee as teeMod

class Tee(pypeType):
	def __init__(self, obj, PSize="", dims=teeMod.Dimensions()):
		"""Create a Tee:
		
		Create a tee fitting __|__ with a signle vertical socket and two horizonal sockets.
		"""
		# Run parent __init__ and define common attributes
		super(Tee, self).__init__(obj)
		obj.PType="OSE_Tee"
		obj.PRating=""
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","G","Tee","Distnace from the center to begin of horizontal socket").G=dims.G
		obj.addProperty("App::PropertyLength","G1","Tee","Distnace from the center to begin of vertical socket").G1=dims.G1
		obj.addProperty("App::PropertyLength","G2","Tee","Distnace from the center to begin of horizontal socket").G2=dims.G2
		obj.addProperty("App::PropertyLength","H","Tee","Distance between the center its horizonal end.").H=dims.H
		obj.addProperty("App::PropertyLength","H1","Tee","Distance between the center its vertical end.").H1=dims.H1
		obj.addProperty("App::PropertyLength","H2","Tee","Distance between the center its horizontal end.").H2=dims.H2		
		obj.addProperty("App::PropertyLength","M","Tee","Tee outside diameter of the horizontal socket.").M=dims.M
		obj.addProperty("App::PropertyLength","M1","Tee","Tee outside diameter of the vertical socket.").M1=dims.M1
		obj.addProperty("App::PropertyLength","M2","Tee","Tee outside diameter of the vertical socket.").M2=dims.M2		
		obj.addProperty("App::PropertyLength","POD","Tee","Tee pipe outer diameter at the horizonal socket.").POD=dims.POD
		obj.addProperty("App::PropertyLength","POD1","Tee","Tee pipe outer diameter at the vertical socket.").POD1=dims.POD1
		obj.addProperty("App::PropertyLength","POD2","Tee","Tee pipe outer diameter at the other horizonal socket.").POD2=dims.POD2	
		obj.addProperty("App::PropertyLength","PThk","Tee","Thickness of the pipe at the horizontal socket.").PThk=dims.PThk
		obj.addProperty("App::PropertyLength","PThk1","Tee","Thickness of the pipe at the vertical socket.").PThk1=dims.PThk1
		obj.addProperty("App::PropertyLength","PThk2","Tee","Thickness of the pipe at the other horizontal socket.").PThk2=dims.PThk2
		obj.addProperty("App::PropertyVectorList","Ports","Tee","Ports relative positions.").Ports = self.getPorts(obj)
		obj.addProperty("App::PropertyString","PartNumber","Tee","Part number").PartNumber=""		
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		sock_dim_properties = [ "G", "G1", "G2"] # Only this properties infules port coordinates.
		
		if prop in sock_dim_properties:
			# This function is called within __init__ too.
			# We wait for all dimension.
			if set(teeMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
				obj.Ports = self.getPorts(obj)

	@classmethod
	def extractDimensions(cls, obj):
		dims = teeMod.Dimensions()
		dims.G = obj.G
		dims.G1 = obj.G1
		dims.G2 = obj.G2
		dims.H = obj.H
		dims.H1 = obj.H1
		dims.H2 = obj.H2
		dims.M = obj.M
		dims.M1 = obj.M1
		dims.M2 = obj.M2
		dims.POD = obj.POD
		dims.POD1 = obj.POD1
		dims.POD2 = obj.POD2
		dims.PThk = obj.PThk
		dims.PThk1 = obj.PThk1
		dims.PThk2 = obj.PThk2
		return dims
		
	@classmethod
	def createOuterPart(cls, obj):
		dims = cls.extractDimensions(obj)
			
		if dims.M == dims.M2:
			return cls.createOuterPartEqualHorizontal(obj)
		else:
			return cls.createOuterPartReducedHorizontal(obj)
			
	@classmethod
	def createOuterPartEqual(cls, obj):
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		""" Create the outer part is a simple cylinder. This is when M and M2 are the equal."""

		return outer
		
	@classmethod
	def horizontalWallEnhancement(cls, obj):
		""" If the diameter of the vertical part is larger than the diamter of the horizontal part,
		add an additional cylinder to the outer part in the middle.
		
		"""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		if dims.M1 > dims.M or dims.M1 > dims.M2:
			r = dims.M1/2.0
			h = dims.M1
			p = FreeCAD.Vector(-dims.M1/2.0,0,0)
			dr = FreeCAD.Vector(1,0,0) # Direction where to rotate the cylinder
			return Part.makeCylinder(r, h, p, dr)
		else:
			return None
						
	@classmethod
	def createOuterPartEqualHorizontal(cls, obj):
		""" Create an outer part, where the left and the right outer dimensions M and M2 are equal.
		"""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		L = dims.H+dims.H2
		r = dims.M1/2.0
		h = dims.H1
		vertical_outer_cylinder = Part.makeCylinder(r, h)
		r = dims.M/2.0
		h = L
		dr = FreeCAD.Vector(1,0,0) # Put cylinder along the x-axis.
		horizontal_outer_cylinder =  Part.makeCylinder(r, h, aux["p1"], dr)
		outer_fusion = None
		enh = cls.horizontalWallEnhancement(obj)		
		if enh is None:
				outer_fusion = horizontal_outer_cylinder.fuse([vertical_outer_cylinder])
		else:
				outer_fusion = horizontal_outer_cylinder.fuse([vertical_outer_cylinder, enh])
				
		return outer_fusion
					
	@classmethod
	def createOuterPartReducedHorizontal(cls, obj):
		""" Create a outer part which is cylinder+cone+cylinder+vertical cylinder.
		Also add an additional enhancement if the vertical part has too large diameter.
		"""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		# Create socket 1.
		r = dims.M/2.0
		h = dims.leftSocketOuterLength()
		dr = FreeCAD.Vector(1,0,0) # Put the cylinder along the x-ayis.
		cylinder1 = Part.makeCylinder(r, h, aux["p1"], dr)
		# Create a cone and put it at the right side of the cylinder 1.
		r1 = dims.M/2.0
		r2 = dims.M2/2.0
		h = dims.G+dims.G2
		dr = FreeCAD.Vector(1,0,0)
		cone = Part.makeCone(r1, r2, h, aux["p5"], dr)
		# Create a socket 2 and put it at the right side of the cone.
		r = dims.M2/2.0
		h = dims.rightSocketOuterLength()
		dr = FreeCAD.Vector(1,0,0) # Put the cylinder along the x-ayis.
		cylinder2 = Part.makeCylinder(r, h, aux["p6"], dr)
		# Create vertical part.
		r = dims.M1/2.0
		h = dims.H1
		vertical_outer_cylinder = Part.makeCylinder(r, h)
		# Combine all four parts and, if necessary, add enhacement.
		enh = cls.horizontalWallEnhancement(obj)		
		outer_fusion = None
		if enh is None:
				outer_fusion = cylinder1.fuse([cone, cylinder2, vertical_outer_cylinder])
		else:
				outer_fusion = cylinder1.fuse([cone, cylinder2, vertical_outer_cylinder, enh])
				
		return outer_fusion
							
	@classmethod
	def createInnerPart(cls, obj):
		dims = cls.extractDimensions(obj)
		if dims.PID() == dims.PID2():
			return cls.createInnerPartEqualHorizontal(obj)
		else:
			return cls.createInnerPartReducedHorizontal(obj)

	@classmethod
	def createInnerSockets(cls, obj):
		dims = cls.extractDimensions(obj)	
		aux = dims.calculateAuxiliararyPoints()	
		
		r = dims.POD/2.0
		h = dims.H-dims.G
		dr = FreeCAD.Vector(1,0,0) # Put cylinder along the x-axis.
		socket_left = Part.makeCylinder(r, h, aux["p1"], dr)
		
		r = dims.POD2/2.0
		h = dims.H2-dims.G2
		socket_right = Part.makeCylinder(r, h, aux["p3"], dr)

		r = dims.POD1/2.0
		h = dims.H1-dims.G1
		socket_top = Part.makeCylinder(r, h, aux["p4"])

		return [socket_left, socket_top, socket_right]

	@classmethod
	def createInnerPartEqualHorizontal(cls, obj):
		""" Create an outer part, where the left and the right outer dimensions M and M2 are equal.
		"""
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		L = dims.H+dims.H2
		r = dims.PID1()/2.0
		h = dims.H1
		vertical_inner_cylinder = Part.makeCylinder(r, h)
		r = dims.PID()/2.0
		h = L
		dr = FreeCAD.Vector(1,0,0) # Put cylinder along the x-axis.
		horizontal_inner_cylinder =  Part.makeCylinder(r, h, aux["p1"], dr)
		return horizontal_inner_cylinder.fuse([vertical_inner_cylinder]+cls.createInnerSockets(obj))
							
	@classmethod													
	def createInnerPartReducedHorizontal(cls, obj):
		""" Create a inner part with a connic middle simmilar to createOuterPartReducedHorizontal().
		"""	
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		
		# Create cylinder 1.
		r = dims.PID()/2.0
		h = dims.H - dims.G 
		dr = FreeCAD.Vector(1,0,0) # Put cylinder or cone along the x-axis.
		cylinder1 = Part.makeCylinder(r, h, aux["p1"], dr)
		# Create a cone and put it to the right of the cylinder 1.
		r1 = dims.PID()/2.0
		r2 = dims.PID2()/2.0
		h = dims.G+dims.G2
		cone = Part.makeCone(r1, r2, h, aux["p2"], dr)
		# Create a socket 2 and put it at the right side of the cone.
		r = dims.PID2()/2.0
		h = dims.H2 - dims.G2
		cylinder2 = Part.makeCylinder(r, h, aux["p3"], dr)
		# Create vertical part.
		r = dims.PID1()/2.0
		h = dims.H1
		vertical_cylinder = Part.makeCylinder(r, h)
		# Combine all parts.
		return cylinder1.fuse([cone, cylinder2, vertical_cylinder]+cls.createInnerSockets(obj))
								
	def execute(self, obj):	
		# Create the shape of the tee.
		inner = self.createInnerPart(obj)
		outer = self.createOuterPart(obj)
		obj.Shape = outer.cut(inner)
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	@classmethod		
	def getPorts(cls, obj):
		""" Calculate coordinates of the ports. """
		dims = cls.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
				
		port_left = aux["p2"]
		port_right = aux["p3"]
		port_top = aux["p4"]
		return [port_left, port_right, port_top]

class TeeBuilder:
	""" Create a tee using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.dims = teeMod.Dimensions()
		self.document = document
		
	def create(self, obj):
		"""Create a Tee.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Tee")
		"""			
		tee = Tee(obj, PSize="", dims=self.dims)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		return tee

# Create a test tee.
def Test():
	document = FreeCAD.activeDocument()
	builder = TeeBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-Tee")
	builder.create(feature)
	document.recompute()
	
#Test()
