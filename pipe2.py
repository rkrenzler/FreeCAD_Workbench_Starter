# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04  March 2018
# Declare a general pipe geometry, it used to move and rotating
# pipe and fitting objects


import FreeCAD
import Part
from pivy import coin
import pipe as pipeModule

RELATIVE_EPSILON = 0.1

# The code is derived from https://www.freecadweb.org/wiki/Scripted_objects
class Pipe2:
	def __init__(self, obj):
		'''Add some custom properties to our box feature'''
		obj.addProperty("App::PropertyLength","Height","Pipe2", "Height of the pipe.").Height=1.0
		# Wall thinkness
		obj.addProperty("App::PropertyLength","OD","Pipe2", "Output diameter of the pipe.").OD=1.0
		obj.addProperty("App::PropertyLength","Thk","Pipe2", "Thinkness of the walls.").Thk=0.1
		obj.Proxy = self

	def onChanged(self, fp, prop):
		'''Do something when a property has changed'''
		FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

	def createShape(self, fp):
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
		fp.Shape = self.createShape(fp)
		'''Do something when doing a recomputation, this method is mandatory'''
		FreeCAD.Console.PrintMessage("Recompute Python Box feature\n")

class ViewProviderPipe2:
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


def makePipe2():
	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Pipe2")
	Pipe2(a)
	ViewProviderPipe2(a.ViewObject)

makePipe2() 
