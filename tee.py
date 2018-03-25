# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 06 February 2018
# Create a tee-fitting.


import math
import csv
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "tee.csv")

DIMENSIONS_USED = ["G", "G1", "H", "H1", "PID", "PID1", "POD", "POD1", "M", "M1"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
# On my version of freecad 0.16 The macro works even with RELATIVE_EPSILON = 0.0.
# Maybe there is no more problems with boolean operations.
RELATIVE_EPSILON = 0.1


class Tee:
	def __init__(self, document):
		self.document = document
		# Fill data with test values
		self.G = tu("3 cm")
		self.G1 = tu("3 cm")
		self.H = tu("4 cm") # It is L/2 for symetrical Tee. Why extra dimension?
		self.H1 = tu("5 cm")
		self.PID = tu("2 cm")
		self.PID1 = tu("1 in")
		self.POD = tu("3 cm")
		self.POD1 = tu("2 in")
		self.M = tu("5 cm")
		self.M1 = tu("4 cm")

	def checkDimensions(self):
		if not ( self.PID > tu("0 mm") and self.PID1 > tu("0 mm") ):
			raise UnplausibleDimensions("Inner pipe dimensions must be positive. They are %s and %s instead"%(self.PID, self.PID1))
		if not ( self.M > self.POD and self.POD > self.PID ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(self.M, self.POD, self.PID))
		if not ( self.M1 > self.POD1 and self.POD1 > self.PID1 ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(self.M1, self.POD1, self.PID1))
		if not ( self.G > tu("0 mm") and self.G1 > tu("0 mm") ):
			raise UnplausibleDimensions("Lengths G=%s, G1=%s, G=%s, must be positive"%(self.G, self.G1))
		if not ( self.H > self.G):
			raise UnplausibleDimensions("H=%s must be larger than G=%s."%(self.H, self.G))
		if not ( self.H1 > self.G1):
			raise UnplausibleDimensions("H1=%s must be larger than G1=%s."%(self.H1, self.G1))


	def create(self, convertToSolid):
		self.checkDimensions()
		L = 2*self.H
		vertical_outer_cylinder = self.document.addObject("Part::Cylinder","VerticalOuterCynlider")
		vertical_outer_cylinder.Radius = self.M1/2
		vertical_outer_cylinder.Height = self.H1
		vertical_inner_cylinder = self.document.addObject("Part::Cylinder","VerticalInnerCynlider")
		vertical_inner_cylinder.Radius = self.PID1/2
		vertical_inner_cylinder.Height =self.H1 * (1+RELATIVE_EPSILON)
		
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
		
		# Fuse outer parts to a tee, fuse inner parts to a tee, substract both parts
		outer_fusion = self.document.addObject("Part::MultiFuse","OuterTeeFusion")
		outer_fusion.Shapes = [vertical_outer_cylinder,horizontal_outer_cylinder]
		inner_fusion = self.document.addObject("Part::MultiFuse","InnerTeeFusion")
		inner_fusion.Shapes = [vertical_inner_cylinder,horizontal_inner_cylinder]
		basic_tee = self.document.addObject("Part::Cut","Cut")
		basic_tee.Base = outer_fusion
		basic_tee.Tool = inner_fusion
		
		# Remove place for sockets.
		socket_left = self.document.addObject("Part::Cylinder","SocketLeft")
		socket_left.Radius = self.POD /2
		socket_left.Height = (self.H-self.G)*(1+RELATIVE_EPSILON)
		socket_left.Placement = FreeCAD.Placement(FreeCAD.Vector(-socket_left.Height - self.G,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
#		socket_left.Placement = FreeCAD.Placement(FreeCAD.Vector(-(self.H-self.G),0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		socket_right = self.document.addObject("Part::Cylinder","SocketRight")
		socket_right.Radius = self.POD /2
		socket_right.Height = (self.H-self.G)*(1+RELATIVE_EPSILON)
		socket_right.Placement = FreeCAD.Placement(FreeCAD.Vector(self.G,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		socket_top = self.document.addObject("Part::Cylinder","SocketTop")
		socket_top.Radius = self.POD1 /2
		socket_top.Height = (self.H1 - self.G1)*(1+RELATIVE_EPSILON)
		socket_top.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,self.G1), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),0), FreeCAD.Vector(0,0,0))
		
		sockets_fusion = self.document.addObject("Part::MultiFuse","Sockets")
		sockets_fusion.Shapes = [socket_left,socket_right,socket_top]
		# remove sockets from the basic tee
		tee = self.document.addObject("Part::Cut","Tee")
		tee.Base = basic_tee
		tee.Tool = sockets_fusion
		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, tee, "tee (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(tee)
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
		return tee

class TeeFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, outputType):
		tee = Tee(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return

		if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
			tee.G = tu(row["G"])
			tee.G1 = tu(row["G1"])
			tee.H = tu(row["H"]) 
			tee.H1 = tu(row["H1"])
			tee.PID = tu(row["PID"])
			tee.PID1 = tu(row["PID1"])
			tee.POD = tu(row["POD"])
			tee.POD1 = tu(row["POD1"])
			tee.M = tu(row["M"])
			tee.M1 = tu(row["M1"])

			part = tee.create(outputType == OUTPUT_TYPE_SOLID)
			part.Label = partName
			return part

		elif outputType == OUTPUT_TYPE_FLAMINGO:
			feature = self.document.addObject("Part::FeaturePython", "OSE-Tee")
			import flTee
			builder = flTee.TeeBuilder(self.document)
			tee.G = tu(row["G"])
			tee.G1 = tu(row["G1"])
			tee.H = tu(row["H"]) 
			tee.H1 = tu(row["H1"])
			tee.PID = tu(row["PID"])
			tee.PID1 = tu(row["PID1"])
			tee.POD = tu(row["POD"])
			tee.POD1 = tu(row["POD1"])
			tee.M = tu(row["M"])
			tee.M1 = tu(row["M1"])
			part = builder.create(feature)	
			feature.PRating = GetPressureRatingString(row)
			feature.PSize = ""
			feature.ViewObject.Proxy = 0
			feature.Label = partName
    			return part


# Test macros.
def TestTee():
	document = FreeCAD.activeDocument()
	tee = Tee(document)
	tee.create(True)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = TeeFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		builder.create(partName, OUTPUT_TYPE_FLAMINGO)
		document.recompute()
		break

#TestTee()
TestTable()

