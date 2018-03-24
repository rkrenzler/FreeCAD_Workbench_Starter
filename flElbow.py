# -*- coding: utf-8 -*-
# Authors: oddtopus, Ruslan Krenzler
# Date: 24 March 2018
# Create a elbow-fitting using Flamingo workbench.


tu = FreeCAD.Units.parseQuantity

import FreeCAD, Part
from math import *
from pipeFeatures import pypeType #the parent class

class Elbow(pypeType):
	def __init__(self, obj, name="90degBend20x10", alpha=90, M=30, POD=20, PID=10, H=30, J=20):
		# run parent __init__ and define common attributes
		super(Elbow,self).__init__(obj)
		obj.PType="OSE_Elbow"
		obj.PRating="ElbowFittingFromAnyCatalog"
		obj.PSize=name
		# define specific attributes
		obj.addProperty("App::PropertyLength","M","Elbow","Outside diameter").M=M
		obj.addProperty("App::PropertyLength","POD","Elbow","Pipe Outer Diameter").POD=POD
		obj.addProperty("App::PropertyLength","PID","Elbow","Pipe Inside Diameter").PID=PID
		obj.addProperty("App::PropertyAngle","alpha","Elbow","Bend Angle").alpha=alpha
		obj.addProperty("App::PropertyLength","H","Elbow","[..]").H=H
		obj.addProperty("App::PropertyLength","J","Elbow","[..]").J=J
	def onChanged(self, obj, prop):
		# if you aim to do something when an attribute is changed
		# place the code here:
		# e.g. -> change PSize according the new alpha, PID and POD
		pass
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
		obj.Shape=sol
		# define Ports, i.e. where the tube have to be placed
		obj.Ports=[n1*(J+delta),n2*(J+delta)]
		
def makeElbow(propList=["90degBend20x10", 90, 30, 20, 10, 30, 20], pos=None, Z=None):
	'''
	proplist = [name, alpha, M, POD, PID, H, J]
	pos = the Base point
	Z = defines the plane of the curve
	'''
	if pos==None:
		pos=FreeCAD.Vector(0,0,0)
	if Z==None:
		Z=FreeCAD.Vector(0,0,1)
	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","OSE-elbow")
	Elbow(a,*propList)
	a.ViewObject.Proxy=0
	a.Placement.Base=pos
	rot=FreeCAD.Rotation(FreeCAD.Vector(0,0,1),Z)
	a.Placement.Rotation=rot.multiply(a.Placement.Rotation)
	a.ViewObject.Transparency=70
	FreeCAD.ActiveDocument.recompute()
	return a

