# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create a tee using Flamingo workbench.

import FreeCAD, Part
import math
from pipeFeatures import pypeType #the parent class


class Tee(pypeType):
	def __init__(self, obj, PSize="", G=30, G1=30, H=40, H1=50, M=50, M1=40, POD=40, POD1=20, PID=20, PID1=10):
		"""Create a Tee:
		
		Create a tee fitting __|__ with a signle vertical socket and two horizonal sockets.
		:param G:
		:param G1:
		:param H: 
		:param H1:
		:param M: Outer diameter of the horizonal socket.
		:param M1: Outer diameter of the vertical socket.
		:param POD: 
		:param POD1: 
		:param PID:
		:param PID1:
		"""
		# Run parent __init__ and define common attributes
		super(Tee, self).__init__(obj)
		obj.PType="OSE_Tee"
		obj.PRating=""
		obj.PSize=PSize # What is it for?
		# Define specific attributes and set their values.
		obj.addProperty("App::PropertyLength","G","Tee","Distnace from the center to begin of horizontal socket").G=G
		obj.addProperty("App::PropertyLength","G1","Tee","Distnace from the center to begin of vertical socket").G1=G1
		obj.addProperty("App::PropertyLength","H","Tee","Distance between the center its horizonal end.").H=H
		obj.addProperty("App::PropertyLength","H1","Tee","Distance between the center its vertical end.").H1=H1
		obj.addProperty("App::PropertyLength","M","Tee","Tee outside diameter of the horizontal socket.").M=M
		obj.addProperty("App::PropertyLength","M1","Tee","Tee outside diameter of the vertical socket.").M1=M1
		obj.addProperty("App::PropertyLength","POD","Tee","Tee pipe outer diameter at the horizonal socket.").POD=POD
		obj.addProperty("App::PropertyLength","POD1","Tee","Tee pipe outer diameter at the horizonal socket.").POD1=POD1
		obj.addProperty("App::PropertyLength","PID","Tee","Tee pipe inner diameter at the horizontal socket.").PID=PID
		obj.addProperty("App::PropertyLength","PID1","Tee","Tee pipe inner diameter at the vertical socket.").PID1=PID1
		obj.addProperty("App::PropertyVectorList","Ports","Tee","Ports relative positions.").Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)

	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		if prop in ["G", "G1", "M"]:
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)
	@staticmethod	
	def createShape(obj):
		G = obj.G
		G1 = obj.G1
		H = obj.H
		H1 = obj.H1
		M = obj.M
		M1 = obj.M1
		PID = obj.PID
		PID1 = obj.PID1
		POD = obj.POD
		POD1 = obj.POD1
		
		vr = M1/2
		vh = H1
		vertical_outer_cylinder = Part.makeCylinder(vr, vh)
		hr = M/2
		hh = 2*H
		horizontal_outer_cylinder = Part.makeCylinder(hr, hh, FreeCAD.Vector(-H,0,0),
						FreeCAD.Vector(1,0,0))
		vri = PID1/2
		vertical_inner_cylinder = Part.makeCylinder(vri, H1)
		hri = PID/2
		horizontal_inner_cylinder = Part.makeCylinder(hri, hh, FreeCAD.Vector(-H,0,0),
						FreeCAD.Vector(1,0,0))
		# Add sockets to the inner part
		hsr = POD/2
		hsh = H-G
		socket_left = Part.makeCylinder(hsr, hsh, FreeCAD.Vector(-H,0,0),
						FreeCAD.Vector(1,0,0))

		socket_right = Part.makeCylinder(hsr, hsh, FreeCAD.Vector(H,0,0),
						FreeCAD.Vector(-1,0,0))

		vsr = POD1/2
		vsh = H1-G1
		socket_top = Part.makeCylinder(vsr, vsh, FreeCAD.Vector(0,0,G1))
		outer = horizontal_outer_cylinder.fuse(vertical_outer_cylinder)
		inner = horizontal_inner_cylinder.fuse([vertical_inner_cylinder, socket_top, socket_left, socket_right])
		return outer.cut(inner)

	def execute(self, obj):
		# Create the shape of the tee.
		shape = Tee.createShape(obj)
		obj.Shape = shape
		# Recalculate ports.
		obj.Ports = self.getPorts(obj)
		
	def getPorts(self, obj):
		""" Calculate coordinates of the ports. """
		port_left = FreeCAD.Vector(-obj.G,0, 0)
		port_right = FreeCAD.Vector(obj.G,0, 0)
		port_top = FreeCAD.Vector(0,0,obj.M/2+obj.G1)
		return [port_left, port_right, port_top]

class TeeBuilder:
	""" Create a tee using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.G = 30
		self.G1 = 30
		self.H = 40
		self.H1 = 50
		self.M = 50
		self.M1 = 40
		self.PID = 20
		self.PID1 = 10
		self.POD = 30
		self.POD1 = 20
		
	def create(self, obj):
		"""Create a Tee.

		Before call it, call
		feature = self.document.addObject("Part::FeaturePython","OSE-Tee")
		"""			
		tee = Tee(obj, PSize="", G=self.G, G1=self.G1, H=self.H, H1=self.H1,
				 M=self.M, M1=self.M1, POD=self.POD, POD1=self.POD1, PID=self.PID, PID1=self.PID1)
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
