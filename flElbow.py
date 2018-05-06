# -*- coding: utf-8 -*-
# Authors: oddtopus, Ruslan Krenzler
# Date: 24 March 2018
# Create a elbow-fitting using Flamingo workbench.

import FreeCAD, Part
from math import *
from pipeFeatures import pypeType #the parent class
import elbow as elbowMod


# The value RELATIVE_EPSILON is used to slightly change the size of parts
# to prevent problems with boolean operations.
# Keep this value very small.
# For example, the outer bent part of the elbow dissaperas when it has
# the same radius as the cylinder at the ends.
RELATIVE_EPSILON = 0.000001

class Elbow(pypeType):
	def __init__(self, obj, PSize="90degBend20x10", BendAngle=90, M=30, POD=20, PThk=10, H=30, J=20):
		# run parent __init__ and define common attributes
		super(Elbow,self).__init__(obj)
		obj.PType="OSE_Elbow"
		obj.PRating="ElbowFittingFromAnyCatalog"
		obj.PSize=PSize # Pipe size
		# define specific attributes
		obj.addProperty("App::PropertyLength","M","Elbow","Outer diameter of the elbow.").M=M
		obj.addProperty("App::PropertyLength","POD","Elbow","Pipe Outer Diameter.").POD=POD
		obj.addProperty("App::PropertyLength","PThk","Elbow","Pipe wall thickness").PThk=PThk
		obj.addProperty("App::PropertyAngle","BendAngle","Elbow","Bend Angle.").BendAngle=BendAngle
		obj.addProperty("App::PropertyLength","H","Elbow","Distance between the center and a elbow end").H=H
		obj.addProperty("App::PropertyLength","J","Elbow","Distnace from the center to begin of innerpart of the socket").J=J
		obj.addProperty("App::PropertyVectorList","Ports","Elbow","Ports relative position.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)
		obj.addProperty("App::PropertyString","PartNumber","Elbow","Part number").PartNumber=""
		

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		dim_properties = ["BendAngle", "J"] # Dimensions which can change port coordinates.
		if prop in dim_properties:
			# This function is called within __init__ too.
			# We wait for all dimension.
			if set(elbowMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
				obj.Ports = self.getPorts(obj)

	@staticmethod
	def extractDimensions(obj):
		dims = elbowMod.Dimensions()
		dims.BendAngle = obj.BendAngle
		dims.H = obj.H
		dims.J = obj.J
		dims.M = obj.M
		dims.POD = obj.POD
		dims.PThk = obj.PThk
		return dims

	@staticmethod
	def createBentCylinder(obj, rCirc):
		""" Create alpha° bent cylinder in x-z plane with radius r. 
		
		:param group: Group where to add created objects.
		:param rCirc: Radius of the cylinder.
		:param rBend: Distance from the bend center to the origin (0,0,0).
		
		See documentation picture elbow-cacluations.png
		"""
		# Convert alpha to degree value
		dims = Elbow.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		p2 = aux["p2"]
		p3 = aux["p3"]
		p4 = aux["p4"]

		alpha = float(dims.BendAngle.getValueAs("deg"))
		rBend = dims.M/2.0
		
		# Calculate coordinates of the base circle.
		base = Part.makeCircle(rCirc, p2)
		
		# Add trajectory
		trajectory = Part.makeCircle(rBend, p3, FreeCAD.Vector(0,-1,0), 180-alpha,180)

		# Add a cap (circle, at the other end of the bent cylinder).

		cap = Part.makeCircle(rCirc, p4, p4)
		# Sweep the circle along the trajectory.
		sweep = Part.makeSweepSurface(trajectory, base)
		# The sweep is only a 2D service consisting of walls only.
		# Add circles on both ends of this wall.
		end1=Part.Face(Part.Wire(base))
		# Create other end.
		end2=Part.Face(Part.Wire(cap))
		solid = Part.Solid(Part.Shell([end1, sweep, end2]))
		return solid
		

	@staticmethod
	def createOuterPart(obj):
		dims = Elbow.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		p1 = aux["p1"]
		p2 = aux["p2"]
		p4 = aux["p4"]
		
		r = dims.M/2
		# For unknow reasons, witoutm the factor r*0.999999 the middle part disappears.
		bentPart = Elbow.createBentCylinder(obj, r*(1+RELATIVE_EPSILON))
		# Create socket along the z axis.
		h = float(dims.H)+p2.z
		socket1 = Part.makeCylinder(r, h, p1)
		# Create socket along the bent part.
		socket2 = Part.makeCylinder(r, h, p4, p4)

		outer = bentPart.fuse([socket1, socket2])
		return outer
		
	@staticmethod
	def createInnerPart(obj):
		dims = Elbow.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
		p1 = aux["p1"]
		p2 = aux["p2"]
		p4 = aux["p4"]
		p6 = aux["p6"]

		r = dims.POD/2-dims.PThk
		
		bentPart = Elbow.createBentCylinder(obj, r*(1+RELATIVE_EPSILON))
		# Create a channel along the z axis.
		h = float(dims.H)+p2.z
		chan1 = Part.makeCylinder(r, h, p1)
		# Create a channel along the bent part.
		chan2 = Part.makeCylinder(r, h, p4, p4)
		# Create corresponding socktes.
		
		rSocket = dims.POD/2
		hSocket = dims.H-dims.J
		socket1 = Part.makeCylinder(rSocket, hSocket, p1)
		socket2 = Part.makeCylinder(rSocket, hSocket, p6, p6)
		
		inner = bentPart.fuse([chan1, chan2, socket1, socket2])
		return inner
		
	@staticmethod	
	def createShape(obj):
		outer = Elbow.createOuterPart(obj)
		inner = Elbow.createInnerPart(obj)
		return outer.cut(inner)
		#return outer
		#return inner
		
	def execute(self,obj):
		# Create the shape of the tee.
		shape = Elbow.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	def getPorts(self, obj):
		dims = Elbow.extractDimensions(obj)
		aux = dims.calculateAuxiliararyPoints()
#	 	FreeCAD.Console.PrintMessage("Ports are %s and %s"%(aux["p5"], aux["p6"]))
		return [aux["p5"], aux["p6"]]


class ElbowBuilder:
	""" Create elbow using flamingo. """
	def __init__(self, document):
		self.dims = elbowMod.Dimensions()
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.document = document
		
	def create(self, obj):
		"""Create an elbow. """
#			feature = self.document.addObject("Part::FeaturePython","OSE-elbow")
		elbow = Elbow(obj, PSize="", BendAngle=self.dims.BendAngle, M=self.dims.M, POD=self.dims.POD,
				PThk=self.dims.PThk, H=self.dims.H, J=self.dims.J)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		#rot=FreeCAD.Rotation(FreeCAD.Vector(0,0,1), self.Z)
		#obj.Placement.Rotation=rot.multiply(obj.Placement.Rotation)
		#feature.ViewObject.Transparency=70
		return elbow

# Test builder.
def TestElbow():
	document = FreeCAD.activeDocument()
	builder = ElbowBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-Elbow")
	#builder.dims.BendAngle = FreeCAD.Units.parseQuantity("90 deg")
	builder.create(feature)
	document.recompute()
	
#TestElbow()
