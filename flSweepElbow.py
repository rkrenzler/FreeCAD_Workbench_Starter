# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus
# Date: 30. March 2018
# Create a sweep-elbow-fitting using flamingo workbench

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class
import sweepElbow as sweepElbowMod

class SweepElbow(pypeType):
	def __init__(self, obj, PSize="", G=50, H=60, M=30, POD=20, PThk=50):
		"""Create a sweep elbow with the center at (0,0,0) sockets along the z and y axis."""
		# Run parent __init__ and define common attributes.
		super(SweepElbow, self).__init__(obj)
		obj.PType="OSE_SweepElbow"
		obj.PRating=""
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","G","SweepElbow","Distnace from the center to begin of innerpart of the socket").G=G
		obj.addProperty("App::PropertyLength","H","SweepElbow","Distance between the center and a elbow end").H=H
		obj.addProperty("App::PropertyLength","M","SweepElbow","Outer diameter of the elbow.").M=M
		obj.addProperty("App::PropertyLength","POD","SweepElbow","Pipe outer diameter.").POD=POD
		obj.addProperty("App::PropertyLength","PThk","SweepElbow","Pipe wall thickness").PThk=PThk
		obj.addProperty("App::PropertyVectorList","Ports","SweepElbow","Ports relative positions.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)
		
	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		if prop in ["G", "H"]:
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)
				
	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		# Vertical port on the bottom.
		portV = FreeCAD.Vector(0,0,-obj.G)
		# Horizonatl port on the right.
		portH = FreeCAD.Vector(0,obj.G,0)

		return [portV, portH]
	
	@staticmethod
	def createBentCylinder(r, l):
		""" Create 90° bent cylinder in x-z plane with radius r. 
		
		:param group: Group where to add created objects.
		:param r: Radius of the cylinder.
		:param l: Distance to the origin (0,0,0).
		
		See documentation picture sweep-elbow-cacluations.png.
		"""
		p1 = FreeCAD.Vector(0,0,-l)
		# Add cylinder
		base = Part.makeCircle(r, p1)
		# makeCylinder
		baseCyl = Part.makeCylinder(r, 0.1, p1)
		# Add trajectory
		p3 = FreeCAD.Vector(l,0,-l)
		trajectory = Part.makeCircle(l,p3, FreeCAD.Vector(0,-1,0), 90,180)
		# Sweep the circle along the trajectory.
		sweep = Part.makeSweepSurface(trajectory, base)
		# The sweep is only a 2D service consisting of walls only.
		# Add circles on both ends of this wall.
		end1=Part.Face(Part.Wire(base))
		# Create other end.
		base2 = Part.makeCircle(r, FreeCAD.Vector(l,0,0), FreeCAD.Vector(1,0,0))
		end2=Part.Face(Part.Wire(base2))
		solid = Part.Solid(Part.Shell([end1, sweep,end2]))
		return solid
		
	@staticmethod
	def createOuterPart(obj):
		"""Create bending part and socket cylinders.
		
		See documentation picture sweep-elbow-cacluations.png.
		"""
		POD = obj.POD
		G = obj.G
		H = obj.H
		M = obj.M
		# Create a bent part.
		bentPart = SweepElbow.createBentCylinder(POD/2.0, G)
		# Create vertical socket (on the bottom).
		socketR = M/2.0
		# Calculate wall thickness of the fitting.
		fitThk = (M - POD)/2.0		
		# Calculate socket Height.
		a2 = H - G + fitThk
		# Calculate socket position.
		p2 = FreeCAD.Vector(0,0,-H)
		socket1 = Part.makeCylinder(socketR, a2, p2)
		# Calculate second socket (on the right).
		# Calculate socket position.
		p3 = FreeCAD.Vector(H-a2,0,0)
		socket2 = Part.makeCylinder(socketR, a2, p3, FreeCAD.Vector(1,0,0))
		outer = bentPart.fuse([bentPart, socket1, socket2])
		return outer
		
	@staticmethod
	def createInnerPart(obj):
		"""Create bending part and socket cylinders.
		
		See documentation picture sweep-elbow-cacluations.png.

		Note: The inner part differs from the outer part not only by socket sizes
		and the size of the bent part, the sockets positions are also different.
		In the inner part the sockets justs touch the inner parts.
		In the outer part the sockets intesects with bent part (the intersection
		width corresponds to the wall thickness of the fitting).
		"""
		G = obj.G
		H = obj.H
		M = obj.M
		PThk = obj.PThk
		POD = obj.POD
		# Create a bent part.
		socketR = POD/2.0
		innerR = POD/2.0 - PThk
		bentPart = SweepElbow.createBentCylinder(innerR, G)
		# Create vertical socket (on the bottom).
		# Calculate wall thickness of the fitting.
		fitThk = (M - POD)/2.0		
		# Calculate socket Height.
		a1 = H - G
		# Calculate socket position.
		p2 = FreeCAD.Vector(0,0,-H)
		socket1 = Part.makeCylinder(socketR, a1, p2)
		# Calculate horizonal socket (on the right).
		# Calculate socket position.
		p4 = FreeCAD.Vector(H - a1,0,0)
		socket2 = Part.makeCylinder(socketR, a1, p4, FreeCAD.Vector(1,0,0))
		inner = bentPart.fuse([bentPart, socket1, socket2])
		return inner
		
	@staticmethod	
	def createShape(obj):
		outer = SweepElbow.createOuterPart(obj)
		inner = SweepElbow.createInnerPart(obj)
		return outer.cut(inner)
		
	def execute(self, obj):
		# Create the shape of the tee.
		shape = SweepElbow.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	
class SweepElbowBuilder:
	""" Create a sweep elbow using flamingo. """
	def __init__(self, document):
		self.dims = sweepElbowMod.Dimensions()
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.document = document
		
	def create(self, obj):
		"""Create a sweep elbow.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-SweepElbow")
		"""			
		elbow = SweepElbow(obj, PSize="", G=self.dims.G, H=self.dims.H, M=self.dims.M, POD=self.dims.POD, PThk=self.dims.PThk)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		return elbow


# Test builder.
def TestSweepElbow():
	document = FreeCAD.activeDocument()
	builder = SweepElbowBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-SweepElbow")
	builder.create(feature)
	document.recompute()

#TestSweepElbow()
