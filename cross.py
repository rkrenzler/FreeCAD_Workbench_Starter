# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 Januar 2018
# Create a cross-fitting.

import math
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "cross.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["POD", "POD1", "PThk", "PThk1", "G", "G1", "H", "H1", "M", "M1"]


class Dimensions:
	def __init__(self):
		# Fill data with test values
		self.G = parseQuantity("3 cm")
		self.G1 = parseQuantity("3 cm")
		self.H = parseQuantity("4 cm") # It is L/2 for symetrical cross. Why extra dimension in documentation?
		self.H1 = parseQuantity("5 cm")
		self.L = self.H*2
		self.L1 = self.H1*2
		self.M = parseQuantity("5 cm")
		self.M1 = parseQuantity("4 cm")
		self.POD = parseQuantity("3 cm")
		self.POD1 = parseQuantity("2 cm")
		self.PThk = parseQuantity("0.5 cm")
		self.PThk1 = parseQuantity("0.5 cm")

	def isValid(self):
		errorMsg = ""
		if not (self.POD > 0):
			errorMsg = "Pipe outer diameter %s must be positive."%self.POD
		elif not (self.PThk <= self.POD/2.0):
			errorMsg = "Pipe thickness PThk %s is too large: larger than POD/2 %s."%(self.PThk, self.POD/2.0)
		elif not (self.POD1 > 0):
			errorMsg = "Other pipe outer diameter %s must be positive."%self.POD
		elif not (self.PThk1 <= self.POD1/2.0):
			errorMsg = "Pipe thickness PThk1 %s is too larg: larger than POD1/2 %s."%(self.PThk1, self.POD1/2.0)
		elif not (self.M > self.POD):
			errorMsg = "Outer diameter M %s must be larger than outer pipe diameter POD %s"%(self.M, self.POD)
		elif not (self.M1 > self.POD1):
			errorMsg = "Outer diameter M1 %s must be larger than outer pipe diameter POD1 %s"%(self.M1, self.POD1)
		elif not (self.H > self.G):
			errorMsg = "Length H=%s must be larger then length G=%s"%(self.H, self.G)
		elif not (self.H1 > self.G1):
			errorMsg = "Length H1=%s must be larger then length G1=%s"%(self.H1, self.G1)
		return (len(errorMsg)==0, errorMsg )
		
	def PID(self):
		return self.POD - self.PThk*2
	
	def PID1(self):
		return self.POD1 - self.PThk1*2
		
	def socketDepthRight(self):
		return (self.H - self.G)
		
	def socketDepthLeft(self):
		return (self.L - self.H - self.G)
		
	def socketDepthBottom(self):
		return (self.H1 - self.G1)

	def socketDepthTop(self):
		return (self.L1 - self.H1 - self.G1)

	def calculateAuxiliararyPoints(self):
		"""Calculate auxiliarary points which are used to build a cross from cylinders.
		
		See documentation picture cross-cacluations.png
		"""
		result = {}
		result["p1"] = FreeCAD.Vector(-self.H,0,0)
		result["p2"] = FreeCAD.Vector(-self.G,0,0)
		result["p3"] = FreeCAD.Vector(self.G,0,0) # This is an assumption, because the drawing of
							  # of Aetnoplastics does not contain this value							
		result["p4"] = FreeCAD.Vector(0,0,-self.H1)
		result["p5"] = FreeCAD.Vector(0,0,-self.G1)
		result["p6"] = FreeCAD.Vector(0,0,self.G1) # This is an assumption, because not		
							   # of Aetnoplastics does not contain this value
	
		return result

class Cross:
	def __init__(self, document):
		self.document = document
		self.dims = Dimensions()

	def checkDimensions(self):
		valid, msg = self.dims.isValid()
		if not valid:
			raise UnplausibleDimensions(msg)

	def createOuterPart(self):
		aux = self.dims.calculateAuxiliararyPoints()

		horizontal_outer_cylinder = self.document.addObject("Part::Cylinder","HorizontalOuterCynlider")
		horizontal_outer_cylinder.Radius = self.dims.M/2
		horizontal_outer_cylinder.Height = self.dims.L
		# I do not understand the logic here. Why when I use GUI the vector is FreeCAD.Vector(0,0,-L/2)
		# and with the macros it is FreeCAD.Vector(-L/2,0,0). Differne systems?
		horizontal_outer_cylinder.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Fuse outer parts to a cross, fuse inner parts to a cross, substract both parts


		vertical_outer_cylinder = self.document.addObject("Part::Cylinder","VerticalOuterCynlider")
		vertical_outer_cylinder.Radius = self.dims.M1/2
		vertical_outer_cylinder.Height = self.dims.L1
		vertical_outer_cylinder.Placement.Base = aux["p4"]
		
		outer_fusion = self.document.addObject("Part::MultiFuse","OuterCrossFusion")
		outer_fusion.Shapes = [horizontal_outer_cylinder, vertical_outer_cylinder]
		return outer_fusion
	
	def createInnerPart(self):
		aux = self.dims.calculateAuxiliararyPoints()
		PID = self.dims.PID()
		PID1 = self.dims.PID1()
		
		horizontal_inner_cylinder = self.document.addObject("Part::Cylinder","HorizontalInnerCynlider")
		horizontal_inner_cylinder.Radius = PID/2
		horizontal_inner_cylinder.Height = self.dims.L
		horizontal_inner_cylinder.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))

		vertical_inner_cylinder = self.document.addObject("Part::Cylinder","VerticalInnerCynlider")
		vertical_inner_cylinder.Radius = PID1/2
		vertical_inner_cylinder.Height = self.dims.L1
		vertical_inner_cylinder.Placement.Base = aux["p4"]
		
		# Add sockets
		socket_left = self.document.addObject("Part::Cylinder","SocketLeft")
		socket_left.Radius = self.dims.POD /2
		socket_left.Height = self.dims.socketDepthLeft()
		socket_left.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))

		
		socket_right = self.document.addObject("Part::Cylinder","SocketRight")
		socket_right.Radius = self.dims.POD /2
		socket_right.Height = self.dims.socketDepthRight()
		socket_right.Placement = FreeCAD.Placement(aux["p3"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		
		socket_bottom = self.document.addObject("Part::Cylinder","SocketBottom")
		socket_bottom.Radius = self.dims.POD1 /2
		socket_bottom.Height = self.dims.socketDepthBottom()
		socket_bottom.Placement.Base = aux["p4"]

		socket_top = self.document.addObject("Part::Cylinder","SocketTop")
		socket_top.Radius = self.dims.POD1 /2
		socket_top.Height = self.dims.socketDepthTop()
		socket_top.Placement.Base = aux["p6"]

		inner_fusion = self.document.addObject("Part::MultiFuse","InnerCrossFusion")
		inner_fusion.Shapes = [horizontal_inner_cylinder, vertical_inner_cylinder, socket_left,
					socket_right, socket_bottom, socket_top]
		return inner_fusion

	def create(self, convertToSolid):
		self.checkDimensions()
		
		outer = self.createOuterPart()
		inner = self.createInnerPart()
		cross = self.document.addObject("Part::Cut","Cross")
		cross.Base = outer
		cross.Tool = inner

		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, cross, "cross (solid)")
			removePartWithChildren(self.document, cross)
			return solid
	
		return cross

class CrossFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table

	@staticmethod
	def getPThk(row):
		""" For compatibility results, if there is no "Thk" dimension, calculate it
		from "PID" and "POD" """
		if not "PThk" in row.keys():
			return (parseQuantity(row["POD"])-parseQuantity(row["PID"]))/2.0
		else:
			return parseQuantity(row["PThk"])

	@staticmethod
	def getPThk1(row):
		""" For compatibility results, if there is no "Thk1" dimension, calculate it
		from "PID1" and "POD1" """
		if not "PThk1" in row.keys():
			return (parseQuantity(row["POD1"])-parseQuantity(row["PID1"]))/2.0
		else:
			return parseQuantity(row["PThk1"])

	def create(self, partNumber, outputType):
		row = self.table.findPart(partNumber)
		if row is None:
			print("Part not found")
			return
		dims = Dimensions()
		dims.G = parseQuantity(row["G"])
		dims.G1 = parseQuantity(row["G1"])
		dims.H = parseQuantity(row["H"])
		dims.H1 = parseQuantity(row["H1"])
		dims.L = parseQuantity(row["L"])
		dims.L1 = parseQuantity(row["L1"])
		dims.M = parseQuantity(row["M"])
		dims.M1 = parseQuantity(row["M1"])
		dims.POD = parseQuantity(row["POD"])
		dims.POD1 = parseQuantity(row["POD1"])
		dims.PThk = CrossFromTable.getPThk(row)
		dims.PThk1 = CrossFromTable.getPThk1(row)
		

		if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
			cross = Cross(self.document)
			cross.dims = dims
			part = cross.create(outputType == OUTPUT_TYPE_SOLID)
			part.Label = "OSE-Cross"
			return part
		elif outputType == OUTPUT_TYPE_FLAMINGO:
			# See Code in pipeCmd.makePipe in the Flamingo workbench.
			feature = self.document.addObject("Part::FeaturePython", "OSE-Cross")
			import flCross
			builder = flCross.CrossBuilder(self.document)
			builder.dims = dims
			part = builder.create(feature)	
			feature.PRating = GetPressureRatingString(row)
			feature.PSize = row["PSize"] # What to do for multiple sizes?
			feature.ViewObject.Proxy = 0
			#feature.Label = partName # Part name must be unique, that is qhy use partNumber instead.
			feature.PartNumber = partNumber
    			return part

# Test macros.
def TestCross():
	document = FreeCAD.activeDocument()
	cross = Cross(document)
	cross.create(False)
	document.recompute()

# Test macro.
def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	cross = CrossFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartKey(i)
		print("Creating part %s"%partName)
		cross.create(partName, OUTPUT_TYPE_SOLID)
		document.recompute()

#TestCross()
#TestTable()




