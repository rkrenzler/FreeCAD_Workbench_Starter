# -*- coding: utf-8 -*-
# Authors: oddtopus, Ruslan Krenzler
# Date: 24 March 2018
# Create a elbow-fitting using Flamingo workbench.

import FreeCAD, Part
from math import *
from pipeFeatures import pypeType #the parent class


class Elbow(pypeType):
	def __init__(self, obj, PSize="90degBend20x10", alpha=90, M=30, POD=20, PID=10, H=30, J=20):
		# run parent __init__ and define common attributes
		super(Elbow,self).__init__(obj)
		obj.PType="OSE_Elbow"
		obj.PRating="ElbowFittingFromAnyCatalog"
		obj.PSize=PSize # What is it for?
		# define specific attributes
		obj.addProperty("App::PropertyLength","M","Elbow","Outside diameter").M=M
		obj.addProperty("App::PropertyLength","POD","Elbow","Pipe Outer Diameter").POD=POD
		obj.addProperty("App::PropertyLength","PID","Elbow","Pipe Inside Diameter").PID=PID
		obj.addProperty("App::PropertyAngle","alpha","Elbow","Bend Angle").alpha=alpha
		obj.addProperty("App::PropertyLength","H","Elbow","[..]").H=H
		obj.addProperty("App::PropertyLength","J","Elbow","[..]").J=J
		obj.addProperty("App::PropertyVectorList","Ports","Elbow","Ports relative position")
		obj.Ports = self.getPorts(obj)
		# Make Ports read only.
		obj.setEditorMode("Ports", 1)
#		FreeCAD.Console.PrintMessage("\n Init finished\n") 
	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD

		if prop == "J" or prop == "alpha":
			# This function is called within __init__ too. Thus we need to wait untill 
			# we have all the required attributes.
			if "Ports" in obj.PropertiesList:
				obj.Ports = self.getPorts(obj)

	def execute(self,obj):
		# define some convenient vector
		Z=FreeCAD.Vector(0,0,1)
		bisect=FreeCAD.Vector(1,1,0).normalize()
		O=FreeCAD.Vector()
		# building the elbow shape
		M=float(obj.M)
		alpha=float(obj.alpha)
		H=float(obj.H)
		J=float(obj.J)
		PID=float(obj.PID)
		POD=float(obj.POD)
		c1=Part.makeCircle(M/2.0,O,Z.cross(bisect))
		c2=c1.copy()
		R=Part.makeCircle(M/2,bisect*(M/2.0),Z,225-alpha/2.0,225+alpha/2.0)
		s1=Part.makeSweepSurface(R,c1)
		c1.rotate(bisect*(M/2.0),Z,alpha/2.0)
		b1=Part.Face(Part.Wire(c1))
		n1=b1.normalAt(0,0).negative()*(H-M/2.0*sin(radians(alpha/2.0)))
		s2=c1.extrude(n1)
		b1.translate(n1)
		c2.rotate(bisect*(M/2.0),Z,-alpha/2.0)
		b2=Part.Face(Part.Wire(c2))
		n2=b2.normalAt(0,0)*(H-M/2.0*sin(radians(alpha/2.0)))
		s3=c2.extrude(n2)
		b2.translate(n2)
		sol=Part.Solid(Part.Shell([s1,s2,s3,b1,b2]))
		n1.normalize(); n2.normalize()
		# moving the shape so that (0,0,0) is the intersection of ports' axis
		delta=M/2*(cos(radians(alpha/2))**-1-1)
		sol.translate(bisect*delta)
		b1.translate(bisect*delta)
		b2.translate(bisect*delta)
		####
		for P,n in [(b1.CenterOfMass,n1),(b2.CenterOfMass,n2)]:
			b=Part.Face(Part.Wire(Part.makeCircle(PID/2,P,n)))
			sol=sol.cut(b.extrude(n*(M/2.0*sin(radians(alpha/2.0))-H)))
			b=Part.Face(Part.Wire(Part.makeCircle(POD/2,P,n)))
			sol=sol.cut(b.extrude(n*(J-H)))
		# assign the shape to obj
		# Rotate sol along the x axis, to put it into x-z plane.
		# The code below does not work.
		#sol.rotate(FreeCAD.Vector(0,0,0),FreeCAD.Vector(1,0,0),90)
		obj.Shape=sol
		# define Ports, i.e. where the tube have to be placed
		obj.Ports=[n1*(J+delta),n2*(J+delta)]
		
	def getPorts(self, obj):
		""" Calculate coordinates of the elbow's ports. """
		# Oddtopus' implimentation use symmetric to the x-y axis in x-y plane.
		rotAxis = FreeCAD.Vector(0,0,1) # Z axis
		bisect=FreeCAD.Vector(1,1,0).normalize() # line to which the elbow is symmetric.
		alpha=float(obj.alpha)
		J=float(obj.J)
		rot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), 90 - alpha/2.0)
		port1 = rot.multVec(bisect)
		port1.Length = J
		rot = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), -90 + alpha/2.0)
		port2 = rot.multVec(bisect)
		port2.Length = J
		return [port1, port2]

class ElbowBuilder:
	""" Create elbow using flamingo. """
	def __init__(self, document):
		self.pos = FreeCAD.Vector(0,0,0) # Define default initial position.
		self.alpha = 90
		self.Z = FreeCAD.Vector(0,0,1) # Rotation of the Z axis. Default -- no rotation.
		self.H = 30
		self.J = 20
		self.M = 30
		self.POD = 20
		self.PID = 10

	def create(self, obj):
		"""Create an elbow. """
#			feature = self.document.addObject("Part::FeaturePython","OSE-elbow")
		elbow = Elbow(obj, PSize="", alpha=self.alpha, M=self.M, POD=self.POD,
				PID=self.PID, H=self.H, J=self.J)
		obj.ViewObject.Proxy = 0
		obj.Placement.Base = self.pos
		#rot=FreeCAD.Rotation(FreeCAD.Vector(0,0,1), self.Z)
		#obj.Placement.Rotation=rot.multiply(obj.Placement.Rotation)
		#feature.ViewObject.Transparency=70
		return elbow

