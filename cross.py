# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 Januar 2018
# Create a cross-fitting.

import math
import csv
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "cross.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["POD", "PID", "POD1", "PID1", "G", "G1", "G2", "G3", "H", "H1", "H2", "H3", "M", "M1"]


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


class Cross:
	def __init__(self, document):
		self.document = document
		# Fill data with test values
		self.G = tu("3 in")
		self.G1 = tu("3 in")
		self.G2 = tu("3 in")
		self.G3 = tu("3 in")
		self.H = tu("4 in") # It is L/2 for symetrical cross. Why extra dimension in documentation?
		self.H1 = tu("5 in")
		self.H2 = tu("6 in")
		self.H3 = tu("7 in")
		self.PID = tu("2 in")
		self.PID1 = tu("1 in")
		self.POD = tu("3 in")
		self.POD1 = tu("2 in")
		self.M = tu("5 in")
		self.M1 = tu("4 in")

	def checkDimensions(self):
		if not ( self.PID > tu("0 mm") and self.PID1 > tu("0 mm") ):
			raise UnplausibleDimensions("Pipe dimensions must be positive. They are PID=%s and PID1=%s instead"%(self.PID, self.PID1))
		if not ( self.POD > self.PID):
			raise UnplausibleDimensions("Outer pipe diameter POD %s must be larger than inner pipe diameter PID %s"%(self.POD, self.PID))
		if not ( self.POD1 > self.PID1):
			raise UnplausibleDimensions("Outer diameter POD1 %s must be larger than inner diameter PID1 %s"%(self.POD1, self.PID1))
		if not ( self.M > self.POD):
			raise UnplausibleDimensions("Outer diameter M %s must be larger than outer pipe diameter POD %s"%(self.M, self.POD))
		if not ( self.M1 > self.POD1):
			raise UnplausibleDimensions("Outer diameter M1 %s must be larger than outer pipe diameter POD1 %s"%(self.M1, self.POD1))
		if not ( self.H > self.G):
			raise UnplausibleDimensions("Length H=%s must be larger then length G=%s"%(self.H, self.G))
		if not ( self.H1 > self.G1):
			raise UnplausibleDimensions("Length H1=%s must be larger then length G1=%s"%(self.H1, self.G1))
		if not ( self.H2 > self.G2):
			raise UnplausibleDimensions("Length H2=%s must be larger then length G2=%s"%(self.H2, self.G2))
		if not ( self.H3 > self.G3):
			raise UnplausibleDimensions("Length H3=%s must be larger then length G3=%s"%(self.H3, self.G3))

	def create(self, convertToSolid):
		self.checkDimensions()
		L = self.H+self.H2
		vertical_outer_cylinder = self.document.addObject("Part::Cylinder","VerticalOuterCynlider")
		vertical_outer_cylinder.Radius = self.M1/2
		vertical_outer_cylinder.Height = self.H1+self.H3
		vertical_outer_cylinder.Placement.Base = FreeCAD.Vector(0,0,-self.H3)
		vertical_inner_cylinder = self.document.addObject("Part::Cylinder","VerticalInnerCynlider")
		vertical_inner_cylinder.Radius = self.PID1/2
		vertical_inner_cylinder.Height = vertical_outer_cylinder.Height * (1+RELATIVE_EPSILON)
		vertical_inner_cylinder.Placement.Base = FreeCAD.Vector(0,0,-self.H3 *(1+RELATIVE_EPSILON))

		horizontal_outer_cylinder = self.document.addObject("Part::Cylinder","HorizontalOuterCynlider")
		horizontal_outer_cylinder.Radius = self.M/2
		horizontal_outer_cylinder.Height = L
		# I do not understand the logic here. Why when I use GUI the vector is FreeCAD.Vector(0,0,-L/2)
		# and with the macros it is FreeCAD.Vector(-L/2,0,0). Differne systems?
		horizontal_outer_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(-self.H,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		horizontal_inner_cylinder = self.document.addObject("Part::Cylinder","HorizontalInnerCynlider")
		horizontal_inner_cylinder.Radius = self.PID/2
		horizontal_inner_cylinder.Height = L*(1+RELATIVE_EPSILON)
		horizontal_inner_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(-self.H*(1+RELATIVE_EPSILON),0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		# Fuse outer parts to a cross, fuse inner parts to a cross, substract both parts
		outer_fusion = self.document.addObject("Part::MultiFuse","OuterCrossFusion")
		outer_fusion.Shapes = [vertical_outer_cylinder,horizontal_outer_cylinder]
		inner_fusion = self.document.addObject("Part::MultiFuse","InnerCrossFusion")
		inner_fusion.Shapes = [vertical_inner_cylinder,horizontal_inner_cylinder]
		basic_cross = self.document.addObject("Part::Cut","Cut")
		basic_cross.Base = outer_fusion
		basic_cross.Tool = inner_fusion
		
		# Remove place for sockets.
		socket_left = self.document.addObject("Part::Cylinder","SocketLeft")
		socket_left.Radius = self.POD /2
		socket_left.Height = (self.H-self.G)*(1+RELATIVE_EPSILON)
		socket_left.Placement = FreeCAD.Placement(FreeCAD.Vector(-socket_left.Height - self.G,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
#		socket_left.Placement = FreeCAD.Placement(FreeCAD.Vector(-(self.H-self.G),0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		socket_right = self.document.addObject("Part::Cylinder","SocketRight")
		socket_right.Radius = self.POD /2
		socket_right.Height = (self.H2-self.G2)*(1+RELATIVE_EPSILON)
		socket_right.Placement = FreeCAD.Placement(FreeCAD.Vector(self.G2,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		socket_top = self.document.addObject("Part::Cylinder","SocketTop")
		socket_top.Radius = self.POD1 /2
		socket_top.Height = (self.H1 - self.G1)*(1+RELATIVE_EPSILON)
		socket_top.Placement.Base = FreeCAD.Vector(0,0,self.G1)
		
		socket_bottom = self.document.addObject("Part::Cylinder","SocketBottom")
		socket_bottom.Radius = self.POD1 /2
		socket_bottom.Height = (self.H3 - self.G3)*(1+RELATIVE_EPSILON)
		socket_bottom.Placement.Base = FreeCAD.Vector(0,0,-socket_bottom.Height-self.G3)

		sockets_fusion = self.document.addObject("Part::MultiFuse","Sockets")
		sockets_fusion.Shapes = [socket_left,socket_right,socket_top,socket_bottom]
		# Remove sockets from the basic cross
		cross = self.document.addObject("Part::Cut","Cross")
		cross.Base = basic_cross
		cross.Tool = sockets_fusion
		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, cross, "cross (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(cross)
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
		return cross

class CrossFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, convertToSolid = True):
		cross = Cross(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return
		cross.G = tu(row["G"])
		cross.G1 = tu(row["G1"])
		cross.G2 = tu(row["G2"])
		cross.G3 = tu(row["G3"])
		cross.H = tu(row["H"])
		cross.H1 = tu(row["H1"])
		cross.H2 = tu(row["H2"])
		cross.H3 = tu(row["H3"])
		cross.PID = tu(row["PID"])
		cross.PID1 = tu(row["PID1"])
		cross.POD = tu(row["POD"])
		cross.POD1 = tu(row["POD1"])
		cross.M = tu(row["M"])
		cross.M1 = tu(row["M1"])

		part = cross.create(convertToSolid)
		part.Label = partName
		return part
# Test macros.
def TestCross():
	document = FreeCAD.activeDocument()
	cross = Cross(document)
	cross.create(True)
	document.recompute()

# Test macro.
def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	cross = CrossFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		cross.create(partName, False)
		document.recompute()

#TestCross()
#TestTable()




