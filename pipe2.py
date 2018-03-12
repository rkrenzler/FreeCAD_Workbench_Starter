# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04  March 2018
# Declare a general pipe geometry, it used to move and rotating
# pipe and fitting objects

import math

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
		obj.addProperty("App::PropertyPlacement","Port1","Pipe2", "Position of the port1").Port1 = Pipe2.getPort1(obj)
		obj.addProperty("App::PropertyLength","Port1Radius","Pipe2", "Radius of the port1").Port1Radius = Pipe2.getPortRadius(obj)
		obj.addProperty("App::PropertyPlacement","Port2","Pipe2", "Position of the port2").Port2 = Pipe2.getPort2(obj)
		obj.addProperty("App::PropertyLength","Port2Radius","Pipe2", "Radius of the port2").Port2Radius = Pipe2.getPortRadius(obj)
		# Set port property as read only
		obj.setEditorMode("Port1", 1) 
		obj.setEditorMode("Port2", 1) 
		# Hide radius properties
		obj.setEditorMode("Port1Radius", 2) 
		obj.setEditorMode("Port1Radius", 2) 
		
		obj.Proxy = self

	@staticmethod
	def getPort1(obj):
		# Base normal must point from (0,0,0) downwards along the z axes.
		return FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),180), FreeCAD.Vector(0,0,0))
		
	@staticmethod
	def getPort2(obj):
		# Base normal must point from (0,0,Height) upwards along the z axes.
		return FreeCAD.Placement(FreeCAD.Vector(0,0,obj.Height), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),0), FreeCAD.Vector(0,0,0))
		
	@staticmethod
	def getPortRadius(obj):
		# Radius of the port is 3/4 of the outer diamter.
		return obj.OD*0.75
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
			
	@staticmethod	
	def updatePorts(obj):
		"""Update ports coordinates and dimensions."""
		FreeCAD.Console.PrintMessage("Updateding ports data.\n")
		obj.Port1 = Pipe2.getPort1(obj)
		obj.Port2 = Pipe2.getPort2(obj)
		obj.Port1Radius = Pipe2.getPortRadius(obj)
		obj.Port2Radius = Pipe2.getPortRadius(obj)
		
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
			self.updatePorts(fp)
		except UnplausibleDimensions as er:
			FreeCAD.Console.PrintMessage(er)
			# Create a red error-cube 
			fp.Shape = Part.makeBox(100,100,100)
			fp.ShapeColor = (1.00,0.00,0.00)
			return

		'''Do something when doing a recomputation, this method is mandatory'''
		FreeCAD.Console.PrintMessage("Recompute pipe2 feature.\n")
		

		
# I porobably should better use something like adapter pattern than a builder.
# Such that the new port attributes will automatically update the corresponding segment object.
		
class PortToCoinAdaptor:
	"""This class maps placement and radius into a coin separator."""
	def __init__(self):
		self.placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),180), FreeCAD.Vector(0,0,0))
		self.r = 7.0
		
		self.sep = coin.SoSeparator()

		# Add translation.
		self._trans = coin.SoTranslation()
		self.sep.addChild(self._trans)
		# Add freecad Rotation
		self._fcad_rot = coin.SoRotation()
		self.sep.addChild(self._fcad_rot)
		# Create axis correction rotation. It makes coin cylinder
		# more like a FreeCAD cylinder.
		# The standard coin (open inventor) cylinder is along the
		#  y-axis, but in FreeCAD it is along the z achsis. (Also,
		# in coin, the origin is in the center of cylinder and in
		# FreeCAD the origin is in the center of the bottom part of the
		# cylinder. For the port we will keep the coin version of
		# cylinder coordinates).
		corr_rot = coin.SoRotation()
		corr_rot.rotation = coin.SbRotation(coin.SbVec3f(1,0,0), math.pi/2)
		self.sep.addChild(corr_rot)
		self._cyl = sphere=coin.SoCylinder()
		self.sep.addChild(self._cyl)
		self.update()
		
				
	def getHeight(self):
		""" Calculatate height from the port cylinder. It is the 1/64 of the cylinder radius.
		The value 1/64 is arbitrary choice by me, to make the port cylinder very thin.
		"""
		return 0.015625*self.r
	
	def update(self):
		self._cyl.radius = float(self.r)
		FreeCAD.Console.PrintMessage("Port radius is %s\n"%self.r)
		self._cyl.height = float(self.getHeight())
		self._trans.translation = self.placement.Base
		self._fcad_rot.rotation = self.placement.Rotation.Q # Use quaternions.
	
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
 		# Add ports
	        self.port1 = PortToCoinAdaptor()
	        self.port2 = PortToCoinAdaptor()
	        self.ports.addChild(self.port1.sep)
	        self.ports.addChild(self.port2.sep)
	        
	def updateData(self, fp, prop):
		'''If a property of the handled feature has changed we have the chance to handle this here'''
	        # Ports are not updated in 3D view unless I try to change the placement. Why?
	        
	        # Show cube at ports.
	        if prop == "Shape":
		        FreeCAD.Console.PrintMessage("updateData, shape was changed.\n")
		        # Update port information.	
	       		self.port1.placement = fp.Port1
		        self.port1.r = fp.Port1Radius
	        	self.port1.update()
		        self.port2.placement = fp.Port2
		        self.port2.r = fp.Port2Radius
		        self.port2.update()
       		        
	def getDisplayModes(self,obj):
		'''Return a list of display modes.'''
		modes=[]
		modes.append("Shaded")
		modes.append("Wireframe")
		modes.append("PipeMovement")
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
