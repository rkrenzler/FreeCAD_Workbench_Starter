# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04  March 2018
# Declare a general pipe geometry, it used to move and rotating
# pipe and fitting objects


import FreeCAD
import Part
from pivy import coin
import pipe as pipeModule
from piping import *

RELATIVE_EPSILON = 0.1
parseQuantity= FreeCAD.Units.parseQuantity

# The code is derived from https://www.freecadweb.org/wiki/Scripted_objects
class Tee2:
	def __init__(self, obj):
		obj.addProperty("App::PropertyLength","G","Pipe2", "G of the tee.").G=parseQuantity("3 cm")
		obj.addProperty("App::PropertyLength","G1","Pipe2", "G1 of the tee.").G1=parseQuantity("3 cm")
		obj.addProperty("App::PropertyLength","G2","Pipe2", "G2 of the tee.").G2=parseQuantity("3 cm")
		obj.addProperty("App::PropertyLength","H","Pipe2", "H of the tee.").H=parseQuantity("4 cm")
		obj.addProperty("App::PropertyLength","H1","Pipe2", "H1 of the tee.").H1=parseQuantity("4 cm")
		obj.addProperty("App::PropertyLength","H2","Pipe2", "H2 of the tee.").H2=parseQuantity("4 cm")
		obj.addProperty("App::PropertyLength","M","Pipe2", "M of the tee.").M=parseQuantity("3 cm")
		obj.addProperty("App::PropertyLength","M1","Pipe2", "M1 of the tee.").M1=parseQuantity("3 cm")
		obj.addProperty("App::PropertyLength","PID","Pipe2", "PID of the tee.").PID=parseQuantity("1 cm")
		obj.addProperty("App::PropertyLength","PID1","Pipe2", "PID1 of the tee.").PID1=parseQuantity("1 cm")
		obj.addProperty("App::PropertyLength","POD","Pipe2", "POD of the tee.").POD=parseQuantity("2 cm")
		obj.addProperty("App::PropertyLength","POD1","Pipe2", "POD1 of the tee.").POD1=parseQuantity("2 cm")
		obj.Proxy = self

	def onChanged(self, fp, prop):
		'''Do something when a property has changed'''
		FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

	def checkDimensions(self, obj):
		if not ( obj.PID > parseQuantity("0 mm") and obj.PID1 > parseQuantity("0 mm") ):
			raise UnplausibleDimensions("Inner pipe dimensions must be positive. They are %s and %s instead"%(obj.PID, obj.PID1))
		if not ( obj.M > obj.POD and obj.POD > obj.PID ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(obj.M, obj.POD, obj.PID))
		if not ( obj.M1 > obj.POD1 and obj.POD1 > obj.PID1 ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(obj.M1, obj.POD1, obj.PID1))
		if not ( obj.G > parseQuantity("0 mm") and obj.G1 > parseQuantity("0 mm") and obj.G2 > parseQuantity("0 mm")):
			raise UnplausibleDimensions("Lengths G=%s, G1=%s, G=%s, must be positive"%(obj.G, obj.G1, obj.G2))
		if not ( obj.H > obj.G):
			raise UnplausibleDimensions("H=%s must be larger than G=%s."%(obj.H, obj.G))
		if not ( obj.H1 > obj.G1):
			raise UnplausibleDimensions("H1=%s must be larger than G1=%s."%(obj.H1, obj.G1))
		if not ( obj.H2 > obj.G2):
			raise UnplausibleDimensions("H2=%s must be larger than G2=%s."%(obj.H2, obj.G2))
			
	def createShape(self, fp):
		self.checkDimensions(fp)
		L = fp.H+fp.H2
	
		vertical_outer_cylinder = Part.makeCylinder(fp.M1/2, fp.H1)
		vertical_inner_cylinder = Part.makeCylinder(fp.PID1/2, fp.H1 * (1+RELATIVE_EPSILON))
		
		horizontal_outer_cylinder = Part.makeCylinder(fp.M/2,  L)
		horizontal_outer_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(-fp.H,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		horizontal_inner_cylinder = Part.makeCylinder(fp.PID/2,  L*(1+RELATIVE_EPSILON))
		horizontal_inner_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(-fp.H*(1+RELATIVE_EPSILON),0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))

		# Fuse outer parts to a tee, fuse inner parts to a tee, substract both parts
		outer_fusion = vertical_outer_cylinder.fuse(horizontal_outer_cylinder)
		inner_fusion = vertical_inner_cylinder.fuse(horizontal_inner_cylinder)
		base_tee = outer_fusion.cut(inner_fusion)
		
		# Remove place for sockets.
		r = fp.POD /2
		h = (fp.H-fp.G)*(1+RELATIVE_EPSILON)
		socket_left =  Part.makeCylinder(r, h)
		socket_left.Placement = FreeCAD.Placement(FreeCAD.Vector(-h - fp.G,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		r = fp.POD /2
		h = (fp.H2-fp.G2)*(1+RELATIVE_EPSILON)
		socket_right = Part.makeCylinder(r, h)
		socket_right.Placement = FreeCAD.Placement(FreeCAD.Vector(fp.G2,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		r = fp.POD1 /2
		h = (fp.H1 - fp.G1)*(1+RELATIVE_EPSILON)
		socket_top = Part.makeCylinder(r, h)
		socket_top.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,fp.G1), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),0), FreeCAD.Vector(0,0,0))
		
		sockets_fusion = socket_left.fuse(socket_right).fuse(socket_top)
		# Remove sockets from the basic tee.
		tee = base_tee.cut(sockets_fusion)
		return tee

	def execute(self, fp):
		# Add dimensions check here.
		try:
			fp.Shape = self.createShape(fp)
		except UnplausibleDimensions as er:
			FreeCAD.Console.PrintMessage(er)
			# Create a red error-cube 
			fp.Shape = Part.makeBox(100,100,100)
			fp.ShapeColor = (1.00,0.00,0.00)
			return

		'''Do something when doing a recomputation, this method is mandatory'''
		FreeCAD.Console.PrintMessage("Recompute pipe2 feature.\n")

class ViewProviderTee2:
	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		obj.addProperty("App::PropertyColor","Color","Box","Color of the box").Color=(1.0,0.0,0.0)
		obj.Proxy = self
 
	def attach(self, obj):
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		"Setup the scene sub-graph of the view provider, this method is mandatory"
		self.color = coin.SoBaseColor()
		self.onChanged(obj,"Color")


	def updateData(self, fp, prop):
		'''If a property of the handled feature has changed we have the chance to handle this here'''
		# fp is the handled feature, prop is the name of the property that has changed
		pass

	def getDisplayModes(self,obj):
		'''Return a list of display modes.'''
		modes=[]
		modes.append("Shaded")
		modes.append("Wireframe")
		return modes

	def getDefaultDisplayMode(self):
		'''Return the name of the default display mode. It must be defined in getDisplayModes.'''
		return "Shaded"

	def setDisplayMode(self,mode):
		'''Map the display mode defined in attach with those defined in getDisplayModes.\
			Since they have the same names nothing needs to be done. This method is optional'''
		return mode

	def onChanged(self, vp, prop):
		'''Here we can do something when a single property got changed'''
		pass

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
			Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
			to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
			Since no data were serialized nothing needs to be done here.'''
		return None


def makeTee2():
	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Tee2")
	Tee2(a)
	ViewProviderTee2(a.ViewObject)
	a.recompute()
makeTee2() 
