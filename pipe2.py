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
class Pipe2:
	def __init__(self, obj):
		'''Add some custom properties to our box feature'''
		obj.addProperty("App::PropertyLength","Height","Pipe2", "Height of the pipe.").Height=1.0
		# Wall thinkness
		obj.addProperty("App::PropertyLength","OD","Pipe2", "Output diameter of the pipe.").OD=1.0
		obj.addProperty("App::PropertyLength","Thk","Pipe2", "Thinkness of the walls.").Thk=0.1
		obj.Proxy = self

	@staticmethod
	def getPort1(obj):
		return FreeCAD.Vector(0,0,0)
		
	@staticmethod
	def getPort2(obj):
		return FreeCAD.Vector(0,0,obj.Height)
		
	def onChanged(self, fp, prop):
		'''Do something when a property has changed'''
		FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

	def checkDimensions(self, obj):
		if not (obj.OD > parseQuantity("0 mm")):
			raise UnplausibleDimensions("OD (inner diameter) of the pipe must be positive. It is %s instead"%(obj.OD))
		if not (2*obj.Thk <= obj.OD):
			raise UnplausibleDimensions("2*Thk (2*Thickness) %s must be less than or equlat to OD (outer diameter)%s "%(2*obj.Thk, obj.OD))
		if not (obj.Height > parseQuantity("0 mm")):
			raise UnplausibleDimensions("Height=%s must be positive"%obj.Height)
			
	def createShape(self, fp):
		self.checkDimensions(fp)
		outer_cylinder = Part.makeCylinder(fp.OD/2, fp.Height)
		# Create inner cylinder. It is a little bit longer than the outer cylider in both ends.
		# This should prevent numerical problems when calculating difference
		# between the outer and innter cylinder.
		base = FreeCAD.Vector(0,0,-fp.Height*RELATIVE_EPSILON)
		h = fp.Height*(1+2*RELATIVE_EPSILON)
		inner_cylinder = Part.makeCylinder(fp.OD/2 - fp.Thk, h, base)
		return outer_cylinder.cut(inner_cylinder)

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

class ViewProviderPipe2:
	""" Provide different views for the pipe2 object."""
	def __init__(self, obj):
		FreeCAD.Console.PrintMessage("ViewProviderPipe2.init.\n")
		'''Set this object to the proxy object of the actual view provider'''
		obj.Proxy = self

 		
	def attach(self, obj):
		FreeCAD.Console.PrintMessage("ViewProviderPipe2.attach.\n")
		'''Setup the scene sub-graph of the view provider, this method is mandatory'''
		self.ports = coin.SoSeparator() # Add here virtual shapes elements like dragging points.
 		obj.RootNode.addChild(self.ports)
 
	def updateData(self, fp, prop):
		'''If a property of the handled feature has changed we have the chance to handle this here'''
	        # Show cube at ports.
	        if prop == "Shape":
		        FreeCAD.Console.PrintMessage("updateData try to add a cube.\n")

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


def makePipe2():
	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Pipe2")
	Pipe2(a)
	ViewProviderPipe2(a.ViewObject)
	a.recompute()
	
	
makePipe2() 
