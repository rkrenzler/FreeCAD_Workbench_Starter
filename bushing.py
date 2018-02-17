# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 January 2018
# Create a bushing-fitting.
# Version 0.3

import math
import csv
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "bushing.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["PID", "PID1", "POD1", "L", "N"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
# On my version of freecad 0.16 The macro works even with RELATIVE_EPSILON = 0.0.
# Maybe there is no more problems with boolean operations.
RELATIVE_EPSILON = 0.1


class Error(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self, message):
		super(Error, self).__init__(message)


class UnplausibleDimensions(Error):
	"""Exception raised when dimensions are unplausible. For example if
	outer diameter is larger than the iner one.

	Attributes:
	message -- explanation of the error
	"""

	def __init__(self, message):
		super(UnplausibleDimensions, self).__init__(message)


class Bushing:
	def __init__(self, document):
		self.document = document
		self.PID = tu("4 cm")
		self.PID1 = tu("1 cm")
		self.POD1 = tu("2 cm")
		self.N = tu("2 cm")
		self.L = tu("3 cm")
		
	def checkDimensions(self):
		if not ( self.PID > tu("0 mm") and self.PID1 > tu("0 mm") ):
			raise UnplausibleDimensions("Pipe dimensions must be positive. They are PID=%s and PID1=%s instead"%(self.PID, self.PID1))
		if not ( self.POD1 > self.PID1):
			raise UnplausibleDimensions("Outer diameter POD1 %s must be larger than inner diameter PID1 %s"%(self.POD1, self.PID1))
		if not ( self.N > 0):
			raise UnplausibleDimensions("Length N=%s must be positive"%self.N)
		if not ( self.PID > self.POD1):
			raise UnplausibleDimensions("Inner diameter of the larger pipe PID %s must be larger than outer diameter of the smaller pipe POD1 %s."%(self.PID, self.PID1))
		if not ( self.L > self.N):
			raise UnplausibleDimensions("The length L %s must be larger than the length N %s"%(self.L, self.N))

	def createHexaThing(self):
		# Create hexagonal thing. I do not know its name.

		# I do not know how to calculate X, there fore I just
		# take a half of (L-N)
		X1 = (self.L-self.N)/2
		# I also do not know what is the size of the thing.
		# I take 1.2 of the inner diameter of the larger pipe
		X2 = self.PID*1.1
		box1 = self.document.addObject("Part::Box","Box")
		box1.Height = X1
		box1.Length = X2
		box1.Width = X2*2
		# Move the box into the center of the X,Y plane.
		center_pos = FreeCAD.Vector(-X2/2, -X2,0)
		box_center  = FreeCAD.Vector(X2/2, X2,0)
		box1.Placement.Base = center_pos
		# Add another box, but rotated by 60° around the z axis.
		box2 = self.document.addObject("Part::Box","Box")	
		box2.Height = box1.Height
		box2.Length = box1.Length
		box2.Width = box1.Width
		box2.Placement=FreeCAD.Placement(center_pos, FreeCAD.Rotation(FreeCAD.Vector(0,0,1),60), box_center)
		# Add another box, but rotated by 120° around the z axis.
		box3 = self.document.addObject("Part::Box","Box")	
		box3.Height = box1.Height
		box3.Length = box1.Length
		box3.Width = box1.Width
		box3.Placement=FreeCAD.Placement(center_pos, FreeCAD.Rotation(FreeCAD.Vector(0,0,1),120), box_center)
		# Cut both boxes
		common = self.document.addObject("Part::MultiCommon","Common")
		common.Shapes = [box1,box2,box3]
		# Put the thing at the top of the bushing
		common.Placement.Base = FreeCAD.Vector(0,0,self.L-X1)
		return common

	def createOctaThing(self):
		# Create Octagonal thing. I do not know its name.

		# I do not know how to calculate X, there fore I just
		# take a half of (L-N)
		X1 = (self.L-self.N)/2
		# I also do not know what is the size of the thing.
		# I take 1.2 of the inner diameter of the larger pipe
		X2 = self.PID*1.1
		box1 = self.document.addObject("Part::Box","Box")
		box1.Height = X1
		box1.Length = X2
		box1.Width = X2
		# Move the box into the center of the X,Y plane.
		center_pos = FreeCAD.Vector(-X2/2, -X2/2,0)
		box_center  = FreeCAD.Vector(X2/2, X2/2,0)
		box1.Placement.Base = center_pos
		# Add another box, but rotated by 45° around the z axis.
		box2 = self.document.addObject("Part::Box","Box")	
		box2.Height = box1.Height
		box2.Length = box1.Length
		box2.Width = box1.Width
		box2.Placement=FreeCAD.Placement(center_pos, FreeCAD.Rotation(FreeCAD.Vector(0,0,1),45), box_center)
		# Cut both boxes
		common = self.document.addObject("Part::MultiCommon","Common")
		common.Shapes = [box1,box2,]
		# Put the thing at the top of the bushing
		common.Placement.Base = FreeCAD.Vector(0,0,self.L-X1)
		return common

	def createOuterPart(self):
		outer_cylinder = self.document.addObject("Part::Cylinder","OuterCynlider")
		outer_cylinder.Radius = self.PID/2
		outer_cylinder.Height = self.L
		thing = self.createOctaThing()
		# Bind two parts.
		fusion = self.document.addObject("Part::MultiFuse","Fusion")
		fusion.Shapes = [outer_cylinder,thing,]
		return fusion

	def create(self, convertToSolid):
		self.checkDimensions()
		outer = self.createOuterPart()
		# Remove inner part of the sockets.
		inner_cylinder = self.document.addObject("Part::Cylinder","OuterCynlider")
		inner_cylinder.Radius = self.PID1/2
		inner_cylinder.Height = self.L

		inner_socket = self.document.addObject("Part::Cylinder","OuterCynlider")
		inner_socket.Radius = self.POD1/2
		inner_socket.Height = self.L - self.N
		inner_socket.Placement.Base = FreeCAD.Vector(0,0,self.N)

		# Make a cone for a larger socket. There are no dimensions for this con. There fore 
		# use simbolically a Radius such that the wall at the lower end is twice as ting
		# as in the upper end of socket.
		W2 = (self.PID-self.PID1)/2
		socket_cone = self.document.addObject("Part::Cone","Cone")
		socket_cone.Radius2 = self.PID1/2
		socket_cone.Radius1 = self.PID1/2 + W2/2
		socket_cone.Height = self.N/2 # I do not know what the hight of the cone should be.
						# I just take a half. 
		inner = self.document.addObject("Part::MultiFuse","Fusion")
		inner.Shapes = [inner_cylinder,inner_socket,socket_cone]
		bushing = self.document.addObject("Part::Cut","Cut")
		bushing.Base = outer
		bushing.Tool = inner

		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, bushing, "bushing (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(bushing)
			# Document.removeObjects can remove multple objects, when we use
			# parts directly. To prevent exceptions with deleted objects,
			# use the name list instead.
			names_to_remove = []
			for part in parts:
				if part.Name not in names_to_remove:
					names_to_remove.append(part.Name)
			for name in names_to_remove:
				print("Deleting temporary objects %s."%name)
				self.document.removeObject(name)
			return solid
		return bushing


class BushingFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, convertToSolid = True):
		bushing = Bushing(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return
		bushing.PID = tu(row["PID"])
		bushing.PID1 = tu(row["PID1"])
		bushing.POD1 = tu(row["POD1"])
		bushing.N = tu(row["N"])
		bushing.L = tu(row["L"])

		part = bushing.create(convertToSolid)
		part.Label = partName
		return part


# Test macros.
def TestBushing():
	document = FreeCAD.activeDocument()
	bushing = Bushing(document)
	bushing.create(True)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	bushing = BushingFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		bushing.create(partName, True)
		document.recompute()

#TestBushing()
#TestTable()

