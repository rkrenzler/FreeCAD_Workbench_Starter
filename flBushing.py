# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create a bushing using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class


class Bushing(pypeType):
	def __init__(self, obj, PSize="", L=30, N=20, POD=40, POD1=20, PID1=10):
		"""Create a bushing"""
	
		# Run parent __init__ and define common attributes
		super(Bushing, self).__init__(obj)
		obj.PType="OSE_Bushing"
		obj.PRating=""
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","L","Bushing","Bushing length").L=L
		obj.addProperty("App::PropertyLength","N","Bushing","N").N=N
		obj.addProperty("App::PropertyLength","POD","Bushing","Large pipe outer diameter.").POD=POD
		obj.addProperty("App::PropertyLength","POD1","Bushing","Small pipe outer diameter.").POD1=POD1
		obj.addProperty("App::PropertyLength","PID1","Bushing","Small pipe inner diameter.").PID1=PID1
		obj.addProperty("App::PropertyVectorList","Ports","Bushing","Ports relative positions.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# Attributes changed, adjust the rest.
		if prop in ["N"]:
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)
	@staticmethod
	def createOctaThing(obj):
		""" Create Octagonal thing at the end of the bushing. I do not know its name."""
		L = obj.L
		N = obj.N
		POD = obj.POD
		# I do not know how to calculate X, there fore I just
		# take a half of (L-N)
		X1 = (L-N)/2
		# I also do not know what is the size of the thing.
		# I take 1.2 of the inner diameter of the larger pipe
		X2 = POD*1.1
		# Move the box into the center of the X,Y plane.
		center_pos = FreeCAD.Vector(-X2/2, -X2/2, L-X1)
		box1 = Part.makeBox(X2,X2,X1, center_pos)
		# rotate a box by 45° around the z.axis.
		box2 = Part.makeBox(X2,X2,X1, center_pos)
		box2.rotate(FreeCAD.Vector(0,0,0),FreeCAD.Vector(0,0,1),45)
		return box1.common(box2)
		
	@staticmethod
	def createOuterPart(obj):
		L = obj.L
		POD = obj.POD
		outer_cylinder = Part.makeCylinder(POD/2, L)
		thing = Bushing.createOctaThing(obj)
		return outer_cylinder.fuse(thing)
		
	@staticmethod
	def createInnerPart(obj):
		L = obj.L
		N = obj.N
		POD = obj.POD
		PID1 = obj.PID1
		POD1 = obj.POD1
		
		# Remove inner part of the sockets.
		inner_cylinder = Part.makeCylinder(PID1/2, L)
		inner_socket = Part.makeCylinder(POD1/2, L - N, FreeCAD.Vector(0,0,N))

		# Make a cone for a larger socket. There are no dimensions for this con. Therefore 
		# use simbolically a Radius such that the wall at the lower end is twice as thick
		# as in the upper end of socket.
		W2 = (POD-PID1)/2
		hcone = N/2 # I do not know what the hight of the cone should be.
				# I just take a half. 

		socket_cone = Part.makeCone(PID1/2 + W2/2, PID1/2, hcone)
		
		return inner_cylinder.fuse([inner_socket, socket_cone])
		
	@staticmethod	
	def createShape(obj):
		outer = Bushing.createOuterPart(obj)
		inner = Bushing.createInnerPart(obj)
		return outer.cut(inner)

	def execute(self, obj):
		# Create the shape of the bushing.
		shape = Bushing.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		port_bottom = FreeCAD.Vector(0,0, 0)
		port_top = FreeCAD.Vector(0,0, obj.N)
		return [port_bottom, port_top]

class BushingBuilder:
	""" Create a bushing using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.L = 30
		self.N = 20
		self.POD = 40
		self.POD1 = 20
		self.PID1 = 10
		
	def create(self, obj):
		"""Create a bushing.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Bushing")
		"""			
		bushing = Bushing(obj, PSize="", L=self.L, N=self.N, POD=self.POD, POD1=self.POD1, PID1=self.PID1)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		return bushing

# Create a test bushing.
def Test():
	document = FreeCAD.activeDocument()
	builder = BushingBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-Bushing")
	builder.create(feature)
	document.recompute()
	
Test()
