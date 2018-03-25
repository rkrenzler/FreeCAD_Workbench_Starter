# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 24 March 2018
# Create a coupling using Flamingo workbench.

import FreeCAD, Part
import math
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
		obj.PRating=""
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
	def calculateShiftA2(obj):
		"""Determine an additional length a2 of the socket 1, such that the wall size of the intermediate
		section on it thin part is not smaller than the walls of the sockets.
		The size a2 does not come from some document or standard. It is only chosen to avoid thin walls
		in the intermediate section of the coupling. Probably a2 must be even larger.
		
		a2 is positive if POD > POD1, it is negative if POD < POD2.
		"""
		N = obj.N
		M = obj.M
		M1 = obj.M1
		POD = obj.POD
		POD1 = obj.POD1
		a2 = max(M-POD, M1-POD1) / 2
		x = (POD-POD1)
		factor = float(x)/math.sqrt(4*N**2+x**2) # Prevent python 2 to use integer "/" operator.
		a1 = factor*a2
		return a1
		
	@staticmethod
	def createOuterPart(obj):
		M = obj.M
		M1 = obj.M1
		if M == M1:
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
	def createOuterPartReduced(obj):
		""" Create a outer part which is cylinder+cone+cylinder."""
		# Create socket 1.
		
		M = obj.M
		M1 = obj.M1
		N = obj.N
		r1 = M/2
		a1 = Coupling.calculateShiftA2(obj)
		SL = (obj.L-obj.N)/2
		h1 = SL+a1
		cylinder1 = Part.makeCylinder(r1, h1)
		# Create a cone and put it on the cylinder 1.
		r2 = M1/2
		hc = N
		cone = Part.makeCone(r1, r2, hc, FreeCAD.Vector(0,0,h1))
		# Create a socket 2 and put it on the cone.
		h2 = SL-a1 # Take in account the higher socket 1.
		cylinder2 = Part.makeCylinder(r2, h2, FreeCAD.Vector(0,0,h1+hc))
		outer = cylinder1.fuse([cone, cylinder2])
		return outer
		
	@staticmethod
	def createInnerPart(obj):
		PID = obj.PID
		PID1 = obj.PID1
		# Create parts which must be removed from the coupling.
		if PID == PID1:
			return Coupling.createInnerPartEqual(obj)
		else:
			return Coupling.createInnerPartReduced(obj)
	
	@staticmethod
	def createInnerPartEqual(obj):
		""" Create the inner part from cylinders. This is when POD and P=D1 are the equal."""
		SL = (obj.L-obj.N)/2 # The length of the inner part of the socket.
		POD = obj.POD
		PID = obj.PID
		N = obj.N
		
		# Create lower inner cylinder.
		height1 = SL
		cylinder1i = Part.makeCylinder(POD/2, height1)
		# Create intermediatiate inner cylinder
		height2 = N
		cylinder2i = Part.makeCylinder(PID/2, N, FreeCAD.Vector(0,0,height1))
		# Create an upper inner cylinder.
		cylinder3i = Part.makeCylinder(POD/2, height1+height2, FreeCAD.Vector(0,0,height1+height2))
		inner = cylinder1i.fuse([cylinder2i, cylinder3i])
		return inner
		
	@staticmethod
	def createInnerPartReduced(obj):
		""" Create a outer part which is cylinder+cone+cylinder."""
		SL = (obj.L-obj.N)/2 # The length of the inner part of the socket.
		POD = obj.POD
		POD1 = obj.POD1
		N = obj.N
		PID = obj.PID
		PID1 = obj.PID1
		r1 = POD/2
		h1 = SL
		# Create a lower cylinder.
		cylinder1i = Part.makeCylinder(r1, h1)
		# Create a cone and put it on the cylinder 1.
		r2 = POD1/2
		hc = N
		cone = Part.makeCone(PID/2, PID1/2, N, FreeCAD.Vector(0,0,h1))
		# Create an upper cylinder.
		h2 = h1
		cylinder2i = Part.makeCylinder(r2, h2, FreeCAD.Vector(0,0,h1+hc))
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
		SL = (obj.L-obj.N)/2 # Inner socket length.
		L = obj.L
		port1 = FreeCAD.Vector(0,0,SL) # Z axis
		port2 = FreeCAD.Vector(0,0,L-SL) # Z axis
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
		feature = self.document.addObject("Part::FeaturePython","OSE-Coupling")
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
	feature = document.addObject("Part::FeaturePython","OSE-Coupling")
	builder.create(feature)
	document.recompute()
	
#Test()
