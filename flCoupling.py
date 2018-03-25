# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 24 March 2018
# Create a coupling using Flamingo workbench.

import FreeCAD, Part
from math import *
from pipeFeatures import pypeType #the parent class


class Coupling(pypeType):
	def __init__(self, obj, PSize="", L=90, M=50, M1=30, N=10, POD=40, POD1=20, PID=20, PID1=10):
		"""Create a coupling:
	
		:param L: Lenght of the coupling.
		:param M: Outer diameter of socket 1.
		:param 1M: Outer diameter of socket 2.
		:param N: Lenght of the intemidate section of the coupling.
		:param POD: Pipe outer diameter at the socket 1.
		:param POD1: Pipe outer diameter at the socket 2.
		:param PID: Pipe inner diameter at the socket 1.
		:param PID1: Pipe inner diameter at the socket 2.
		"""
		# Run parent __init__ and define common attributes
		super(Coupling, self).__init__(obj)
		obj.PType="OSE_Coupling"
		obj.PRating="ElbowFittingFromAnyCatalog"
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","L","Coupling","Length of the coupling").L=L
		obj.addProperty("App::PropertyLength","M","Coupling","Coupling outside diameter.").M=M
		obj.addProperty("App::PropertyLength","M1","Coupling","Coupling outside diameter of the thin end.").M1=M1
		obj.addProperty("App::PropertyLength","N","Coupling","Length of the middle part of the coupling.").N=N
		obj.addProperty("App::PropertyLength","POD","Coupling","Coupling pipe outer diameter at the socket 1.").POD=POD
		obj.addProperty("App::PropertyLength","POD1","Coupling","Coupling pipe outer diameter at the socket 2.").POD1=POD1
		obj.addProperty("App::PropertyLength","PID","Coupling","Coupling pipe inner diameter at the socket 1.").PID=PID
		obj.addProperty("App::PropertyLength","PID1","Coupling","Coupling pipe inner diameter at thte socket 2.").PID1=PID1
		obj.addProperty("App::PropertyVectorList","Ports","Coupling","Ports relative positions.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		if prop in ["L", "N"]:
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)
	@staticmethod
	def createOuterPart(obj):
		M = obj.M
		M1 = obj.M1
		if M == M1 or True:
			return Coupling.createOuterPartEqual(obj)
		else:
			return Coupling.createOuterPartReduced(obj)

	@staticmethod
	def createOuterPartEqual(obj):
		""" Create the outer part is a simple cylinder. This is when M and M1 are the equal."""
		# Create complete outer cylinder.
		radius = obj.M/2
		height = obj.L
		outer = Part.makeCylinder(radius, height)
		return outer
		
	@staticmethod
	def createInnerPart(obj):
		PID = obj.PID
		PID1 = obj.PID1
		# Create parts which must be removed from the coupling.
		if PID == PID1 or True:
			return Coupling.createInnerPartEqual(obj)
		else:
			return Coupling.createInnerPartReduced(obj)
	
	@staticmethod
	def createInnerPartEqual( obj):
		""" Create the inner part from cylinders. This is when PID and PID1 are the equal."""
		SL = (obj.L-obj.N)/2 # The length of the inner part of the socket.
		POD = obj.POD
		POD1 = obj.POD1
		N = obj.N
		
		# Create lower inner cylinder.
		height1 = SL
		cylinder1i = Part.makeCylinder(POD/2, height1)
		# Create intermediatiate inner cylinder
		height2 = N
		cylinder2i = Part.makeCylinder(POD1/2, N, FreeCAD.Vector(0,0,height1))
		# Create upper inner cylinder.
		cylinder3i = Part.makeCylinder(POD/2, height1+height2, FreeCAD.Vector(0,0,height1+height2))
		inner = cylinder1i.fuse([cylinder2i, cylinder3i])
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
		SL = (obj.L-obj.N)/2 # Inner socket length.
		N = obj.N
		port1 = FreeCAD.Vector(0,0,SL) # Z axis
		port2 = FreeCAD.Vector(0,0,N-SL) # Z axis
		return [port1, port2]

class CouplingBuilder:
	""" Create a coupling using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.L = 90 # Length of the coupling.
		self.M = 50 # Outer diameter of socket 1.
		self.M1 = 30 # Outer diameter of socket 2.
		self.N = 10  # Lenght of the intemidate section of the coupling.
		self.POD = 40 # Pipe outer diameter at the socket 1.
		self.POD1 = 20 # Pipe outer diameter at the socket 2.
		self.PID = 30 # Pipe inner diameter at the socket 1.
		self.PID1 = 1 # Pipe inner diameter at the socket 2.
		
	def create(self, obj):
		"""Create a couzpling.
		 
		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-coupling")
		"""			
		coupling = Coupling(obj, PSize="", L=self.L, M=self.M, M1=self.M1, N=self.N,
				POD=self.POD, POD1=self.POD1, PID=self.PID, PID1=self.PID1)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		return coupling

# Test a coupling.
def Test():
	document = FreeCAD.activeDocument()
	builder = CouplingBuilder(document)
	feature = document.addObject("Part::FeaturePython","OSE-coupling")
	builder.create(feature)
	document.recompute()
	
#Test()
