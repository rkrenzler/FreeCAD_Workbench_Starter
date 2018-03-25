# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 09 February 2018
# Create a corner-fitting. 

import math
import csv
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "corner.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["G", "H", "M", "POD", "PID"]


class Corner:
	def __init__(self, document):
		self.document = document
		self.G = tu("2 cm")
		self.H = tu("3 cm")
		self.M = tu("3 cm")
		self.POD = tu("2 cm")
		self.PID = tu("1 cm")

		
	def checkDimensions(self):
		if not ( self.POD > tu("0 mm") and self.PID > tu("0 mm") ):
			raise UnplausibleDimensions("Pipe dimensions must be positive. They are POD=%s and PID=%s instead"%(self.POD, self.PID))
		if not (self.M > self.POD and self.POD > self.PID):
			raise UnplausibleDimensions("Outer diameter M %s must be larger than outer pipe POD %s diamter. ",
						"Outer pipe diameter POD %s must be larger than inner pipe diameter PID %s"%(self.M, self.POD, self.PID))
		if not (self.G > self.PID/2):
			raise UnplausibleDimensions("Length G %s must be larger than inner pipe radius PID/2=%s."%(self.G, self.PID/2))

		if not (self.H > self.G):
			raise UnplausibleDimensions("Length G %s must be larger than H %s."%(self.G, self.H))

	def createPrimitiveCorner(self, L, D):
		"""Create corner consisting of two cylinder along x-,y- and y axis and a ball in the center."""
		x_cylinder = self.document.addObject("Part::Cylinder","XCynlider")
		x_cylinder.Radius = D/2
		x_cylinder.Height = L
		x_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		y_cylinder = self.document.addObject("Part::Cylinder","YCynlider")
		y_cylinder.Radius = D/2
		y_cylinder.Height = L
		y_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),-90), FreeCAD.Vector(0,0,0))
		z_cylinder = self.document.addObject("Part::Cylinder","ZCynlider")
		z_cylinder.Radius = D/2
		z_cylinder.Height = L
		sphere = self.document.addObject("Part::Sphere","Sphere")
		sphere.Radius = D/2
		fusion = self.document.addObject("Part::MultiFuse","Fusion")
		fusion.Shapes = [x_cylinder,y_cylinder,z_cylinder,sphere]
		return fusion

	def addSockets(self, fusion):
		"""Add socket cylinders to the fusion."""
		x_socket = self.document.addObject("Part::Cylinder","XSocket")
		x_socket.Radius = self.POD / 2
		x_socket.Height = self.H - self.G
		x_socket.Placement = FreeCAD.Placement(FreeCAD.Vector(self.G, 0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		y_socket = self.document.addObject("Part::Cylinder","YSocket")
		y_socket.Radius = self.POD / 2
		y_socket.Height = self.H - self.G
		y_socket.Placement = FreeCAD.Placement(FreeCAD.Vector(0, self.G,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0),-90), FreeCAD.Vector(0,0,0))
		z_socket = self.document.addObject("Part::Cylinder","ZSocket")
		z_socket.Radius = self.POD / 2
		z_socket.Height = self.H - self.G
		z_socket.Placement.Base = FreeCAD.Vector(0, 0, self.G)
		fusion.Shapes = fusion.Shapes + [x_socket, y_socket, z_socket] # fusion.Shapes.append does not work.
		return fusion

	def createOuterPart(self):
		return self.createPrimitiveCorner(self.H, self.M)

	def createInnerPart(self):
		return self.createPrimitiveCorner(self.H, self.PID)

	def create(self, convertToSolid):
		self.checkDimensions()
		outer = self.createOuterPart()
		inner = self.createInnerPart()
		inner = self.addSockets(inner)

		# Remove inner part of the sockets.
		corner = self.document.addObject("Part::Cut","Cut")
		corner.Base = outer
		corner.Tool = inner
		
		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, corner, "corner (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(corner)
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
		return corner


class CornerFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, outputType):
		corner = Corner(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return

		if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
			corner.G = tu(row["G"])
			corner.H = tu(row["H"])
			corner.M = tu(row["M"])
			corner.POD = tu(row["POD"])
			corner.PID = tu(row["PID"])

			part = corner.create(outputType == OUTPUT_TYPE_SOLID)
			part.Label = partName
			return part

		elif outputType == OUTPUT_TYPE_FLAMINGO:
			feature = self.document.addObject("Part::FeaturePython", "OSE-Corner")
			import flCorner
			builder = flCorner.CornerBuilder(self.document)
			builder.G = tu(row["G"])
			builder.H = tu(row["H"]) 
			builder.M = tu(row["M"])
			builder.POD = tu(row["POD"])
			builder.PID = tu(row["PID"])
			part = builder.create(feature)	
			feature.PRating = GetPressureRatingString(row)
			feature.PSize = ""
			feature.ViewObject.Proxy = 0
			feature.Label = partName
    			return part


# Test macros.
def TestCorner():
	document = FreeCAD.activeDocument()
	corner = Corner(document)
	corner.create(True)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = CornerFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		builder.create(partName, OUTPUT_TYPE_FLAMINGO)
		document.recompute()
		break

#TestCorner()
#TestTable()

