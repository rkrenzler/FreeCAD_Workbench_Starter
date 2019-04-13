# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 Januar December 2018
# Create a coupling fitting.


import math
import csv
import os.path

import FreeCAD
import Part

import OsePipingBase
import OsePiping.Piping as Piping

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, "coupling.csv")

# The table must contain unique values in the column "PartNumber" and also, dimensions listened below.
DIMENSIONS_USED = ["L", "M", "M1", "N", "POD1", "POD", "PThk", "PThk1"]

class Dimensions:
	def __init__(self):
		self.M = parseQuantity("5 cm") # Outer diameter of socket 1.
		self.M1 = parseQuantity("3 cm") # Outer diameter of socket 2.
		self.N = parseQuantity("1 cm") # Lenght of the intemidate section of the coupling.
		self.POD = parseQuantity("4 cm") # Pipe outer diameter at the socket 1.
		self.POD1 = parseQuantity("2 cm") # Pipe outer diameter at the socket 2.
		self.PThk = parseQuantity("0.5 cm") # Pipe inner diameter at the socket 1.
		self.PThk1 = parseQuantity("0.5 cm") # Pipe inner diameter at the socket 2.
		self.L = parseQuantity("9 cm") # Length of the socket1.

	def isValid(self):
		errorMsg = ""
		if not (self.POD > 0):
			errorMsg = "Pipe outer diameter POD %s must be positive."%self.POD
		elif not (self.POD1 > 0):
			errorMsg = "Pipe outer diameter POD1 %s must be positive."%self.POD
		elif not (self.PThk <= self.POD/2.0):
			errorMsg = "Pipe thickness PThk %s is too large: larger than POD/2 %s."%(self.PThk, self.POD/2.0)
		elif not (self.PThk1 <= self.POD1/2.0):
			errorMsg = "Pipe thickness PThk1 %s is too large: larger than POD1/2 %s."%(self.PThk1, self.POD1/2.0)
		elif not (self.M > self.POD):
			errorMsg = "Outer diameter M %s must be larger than outer pipe diameter POD %s"%(self.M, self.POD)
		elif not (self.M1 > self.POD1):
			errorMsg = "Outer diameter M1 %s must be larger than outer pipe diameter POD1 %s"%(self.M1, self.POD1)
		elif not ( self.L > self.N):
			errorMsg = "The total length L=%s must be larger than the length N"%(self.L, self.N)
		elif not ( self.N > 0):
			errorMsg = "Length N=%s must be positive"%self.N
		return (len(errorMsg)==0, errorMsg )

	def shiftA1(self):
		"""Determine an additional length a1 of the socket 1, such that the wall size of the intermediate
		section on it thin part is not smaller than the walls of the sockets.
		The size a1 does not come from some document or standard. It is only chosen to avoid thin walls
		in the intermediate section of thecoupling. Probably a1 must be even larger.

		a1 is positive if POD > POD1, it is negative if POD < POD1.
		"""
		a2 = max(self.M-self.POD, self.M1-self.POD1) / 2
		x = (self.POD-self.POD1)
		# The math.sqrt will return Float. That is why
		# we need to convert x in float too.
		factor = x.Value/math.sqrt(4*self.N**2+x**2)
		a1 = factor*a2
		return a1

	def socketDepthA5(self):
		"""Determin the length of the bottom (or left) socket.
		We assume that the socket lengthes are the same on both ends.
		"""
		return (self.L - self.N)/2.0

	def bottomSocketOuterLength(self):
		"""Return outer length of the socket on the bottom in FreeCAD
		(on the left size in the picture).
		"""
		return self.socketDepthA5()+self.shiftA1()

	def topSocketOuterLength(self):
		"""Return outer length of the socket on the to in FreeCAD
		(on the right size in the picture).
		"""
		return self.socketDepthA5()-self.shiftA1()

	def calculateAuxiliararyPoints(self):
		"""Calculate auxiliarary points which are used to build a coupling from cylinders and cones.

		See documentation picture coupling-cacluations.png
		"""
		result = {}
		result["p1"] = FreeCAD.Vector(0,0,0)
		result["p2"] = FreeCAD.Vector(0,0,self.socketDepthA5())
		result["p3"] = FreeCAD.Vector(0,0,self.L - self.socketDepthA5())
		result["p4"] = FreeCAD.Vector(0,0,self.socketDepthA5() + self.shiftA1())
		result["p5"] = FreeCAD.Vector(0,0,self.L - self.socketDepthA5() + self.shiftA1())
		return result

	def PID(self):
		return self.POD-2*self.PThk

	def PID1(self):
		return self.POD1-2*self.PThk1

class Coupling:
	def __init__(self, document):
		self.document = document
		# Set default values.
		self.dims = Dimensions()

	def checkDimensions(self):
		valid, msg = self.dims.isValid()
		if not valid:
			raise Piping.UnplausibleDimensions(msg)

	def createOuterPart(self):
		if self.dims.M == self.dims.M1:
			return self.createOuterPartEqual()
		else:
			return self.createOuterPartReduced()

	def createOuterPartEqual(self):
		""" Create a outer part which is cylinder only. This is when M and M1 are the same"""
		# Create socket 1.
		outer = self.document.addObject("Part::Cylinder","Cylinder")
		outer.Radius = self.dims.M/2
		outer.Height = self.dims.L
		return outer

	def createOuterPartReduced(self):
		""" Create a outer part which is cylinder+cone+cylinder."""
		# Create socket 1.
		cylinder1 = self.document.addObject("Part::Cylinder","Cylinder1")
		cylinder1.Radius = self.dims.M/2
		cylinder1.Height = self.dims.bottomSocketOuterLength()
		# Create a cone and put it on the cylinder 1
		aux = self.dims.calculateAuxiliararyPoints()
		cone = self.document.addObject("Part::Cone","Cone")
		cone.Radius1 = self.dims.M/2
		cone.Radius2 = self.dims.M1/2
		cone.Height = self.dims.N
		cone.Placement.Base = FreeCAD.Vector(aux["p4"])
		# Create a socket 2 and put it on the cone
		cylinder2 = self.document.addObject("Part::Cylinder","Cylinder2")
		cylinder2.Radius = self.dims.M1/2
		cylinder2.Height = self.dims.topSocketOuterLength()
		cylinder2.Placement.Base = FreeCAD.Vector(aux["p5"])
		# Combine all outer parts.
		outer = self.document.addObject("Part::MultiFuse","OuterParts")
		outer.Shapes = [cylinder1, cone, cylinder2]
		return outer

	def createInnerPart(self):
		# Create parts which must be removed from the coupling.
		if self.dims.PID() == self.dims.PID1():
			return self.createInnerPartEqual()
		else:
			return self.createInnerPartReduced()

	def createInnerPartEqual(self):
		""" Create inner part from cylinders. This is when PID and PID1 are the same"""
		aux = self.dims.calculateAuxiliararyPoints()
		cylinder1i = self.document.addObject("Part::Cylinder","Cylinder1i")
		cylinder1i.Radius = self.dims.POD/2
		cylinder1i.Height = self.dims.socketDepthA5()
		cylinder1i.Placement.Base = FreeCAD.Vector(aux["p1"])
		cylinder3i = self.document.addObject("Part::Cylinder","Cylinder3i")
		cylinder3i.Radius = self.dims.PID()/2
		cylinder3i.Height = self.dims.L
		cylinder3i.Placement.Base = FreeCAD.Vector(aux["p1"])
		cylinder2i = self.document.addObject("Part::Cylinder","Cylinder2i")
		cylinder2i.Radius = self.dims.POD1/2
		cylinder2i.Height = self.dims.socketDepthA5()
		cylinder2i.Placement.Base = FreeCAD.Vector(aux["p3"])
		inner = self.document.addObject("Part::MultiFuse","InnerParts")
		inner.Shapes = [cylinder1i, cylinder3i, cylinder2i]
		return inner

	def createInnerPartReduced(self):
		""" Create an innter part which is cylinder+cone+cylinder."""
		aux = self.dims.calculateAuxiliararyPoints()
		cylinder1i = self.document.addObject("Part::Cylinder","Cylinder1i")
		cylinder1i.Radius = self.dims.POD/2
		cylinder1i.Height = self.dims.socketDepthA5()
		cylinder1i.Placement.Base = aux["p1"]
		conei = self.document.addObject("Part::Cone","Cone")
		conei.Radius1 = self.dims.PID()/2
		conei.Radius2 = self.dims.PID1()/2
		conei.Height = self.dims.N
		conei.Placement.Base = aux["p2"]
		cylinder2i = self.document.addObject("Part::Cylinder","Cylinder2i")
		cylinder2i.Radius = self.dims.POD1/2
		cylinder2i.Height = self.dims.socketDepthA5()
		cylinder2i.Placement.Base = aux["p3"]
		inner = self.document.addObject("Part::MultiFuse","InnerParts")
		inner.Shapes = [cylinder1i, conei, cylinder2i]
		return inner

	def create(self, convertToSolid):
		self.checkDimensions()
		outer = self.createOuterPart()
		inner = self.createInnerPart()
		coupling = self.document.addObject("Part::Cut","coupling")
		coupling.Base = outer
		coupling.Tool = inner

		if convertToSolid:
			# Before making a solid, recompute documents.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = Piping.toSolid(self.document, coupling, "coupling (solid)")
			Piping.removePartWithChildren(self.document, coupling)
			return solid
		return coupling


class CouplingFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table

	@classmethod
	def getPThk(cls, row):
		""" For compatibility results, if there is no "PThk" dimension, calculate it
		from "PID" and "POD" """
		if not "PThk" in row.keys():
			return (parseQuantity(row["POD"])-parseQuantity(row["PID"]))/2.0
		else:
			return parseQuantity(row["PThk"])

	@classmethod
	def getPThk1(cls, row):
		""" For compatibility results, if there is no "PThk1" dimension, calculate it
		from "PID1" and "POD1" """
		if not "PThk1" in row.keys():
			return (parseQuantity(row["POD1"])-parseQuantity(row["PID1"]))/2.0
		else:
			return parseQuantity(row["PThk1"])

	@classmethod
	def getPSize(cls, row):
		if "PSize" in row.keys():
			return row["PSize"]
		else:
			return ""

	def create(self, partNumber, outputType):
		coupling = Coupling(self.document)
		row = self.table.findPart(partNumber)
		if row is None:
			print("Part not found")
			return

		dims = Dimensions()
		dims.L = parseQuantity(row["L"])
		dims.M = parseQuantity(row["M"])
		dims.M1 = parseQuantity(row["M1"])
		dims.N = parseQuantity(row["N"])
		dims.POD = parseQuantity(row["POD"])
		dims.POD1 = parseQuantity(row["POD1"])
		dims.PThk = self.getPThk(row)
		dims.PThk1 = self.getPThk1(row)

		if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
			coupling = Coupling(self.document)
			coupling.dims = dims
			part = coupling.create(outputType == Piping.OUTPUT_TYPE_SOLID)
			part.Label = "OSE-Coupling"
			return part

		elif outputType == Piping.OUTPUT_TYPE_FLAMINGO:
			# See Code in pipeCmd.makePipe in the Flamingo workbench.
			feature = self.document.addObject("Part::FeaturePython", "OSE-Coupling")
			import FlCoupling
			builder = FlCoupling.CouplingBuilder(self.document)
			builder.dims = dims
			part = builder.create(feature)
			feature.PRating = Piping.GetPressureRatingString(row)
			feature.PSize = self.getPSize(row) # What to do for multiple sizes?
			feature.ViewObject.Proxy = 0
			feature.PartNumber = partNumber
			return part

# Test macros.
def TestCoupling():
	document = FreeCAD.activeDocument()
	coupling = Coupling(document)
	coupling.create(False)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = Piping.CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = CouplingFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partNumber = table.getPartKey(i)
		print("Creating part %s"%partNumber)
		builder.create(partNumber, Piping.OUTPUT_TYPE_SOLID)
		document.recompute()


def TestPartFromTable(partNumber, outputType):
	document = FreeCAD.activeDocument()
	table = Piping.CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = CouplingFromTable(document, table)
	print("Creating part %s"%partNumber)
	builder.create(partNumber, outputType)
	document.recompute()

#TestCoupling()
#TestTable()
#TestPartFromTable("429-249", OUTPUT_TYPE_PARTS)
