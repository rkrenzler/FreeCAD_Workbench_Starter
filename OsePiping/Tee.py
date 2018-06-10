# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 06 February 2018
# Create a tee-fitting.


import math
import csv
import os.path

import FreeCAD
import Part

import OsePipingBase
import Piping

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, "tee.csv")

DIMENSIONS_USED = ["G", "G1", "G2", "H", "H1", "H2",  "M", "M1", "M2", "POD", "POD1", "POD2", "PThk", "PThk1", "PThk2"]

class Dimensions:
	def __init__(self):
		self.G = parseQuantity("3 cm")
		self.G1 = parseQuantity("2 cm")
		self.G2 = parseQuantity("3 cm")
		self.H = parseQuantity("4 cm") # It is L/2 for symetrical Tee. Why extra dimension?
		self.H1 = parseQuantity("3 cm")
		self.H2 = parseQuantity("5 cm")
		self.PThk = parseQuantity("0.5 cm")
		self.PThk1 = parseQuantity("0.5 cm")
		self.PThk2 = parseQuantity("0.5 cm")
		self.POD = parseQuantity("4 cm")
		self.POD1 = parseQuantity("3 cm")
		self.POD2 = parseQuantity("2 cm")
		self.M = parseQuantity("5 cm")
		self.M1 = parseQuantity("4 cm")
		self.M2 = parseQuantity("3 cm")

	def isValid(self):
		errorMsg = ""
		if not (self.POD > 0):
			errorMsg = "Pipe outer diameter POD %s must be positive."%self.POD
		elif not (self.POD1 > 0):
			errorMsg = "Pipe outer diameter POD1 %s must be positive."%self.POD
		elif not (self.POD2 > 0):
			errorMsg = "Pipe outer diameter POD2 %s must be positive."%self.POD
		elif not (self.PThk <= self.POD/2.0):
			errorMsg = "Pipe thickness PThk %s is too large: larger than POD/2 %s."%(self.PThk, self.POD/2.0)
		elif not (self.PThk1 <= self.POD1/2.0):
			errorMsg = "Pipe thickness PThk1 %s is too large: larger than POD1/2 %s."%(self.PThk1, self.POD1/2.0)
		elif not (self.PThk2 <= self.POD2/2.0):
			errorMsg = "Pipe thickness PThk2 %s is too large: larger than POD2/2 %s."%(self.PThk2, self.POD2/2.0)
		elif not (self.M > self.POD):
			errorMsg = "Outer diameter M %s must be larger than outer pipe diameter POD %s"%(self.M, self.POD)
		elif not (self.M1 > self.POD1):
			errorMsg = "Outer diameter M1 %s must be larger than outer pipe diameter POD1 %s"%(self.M1, self.POD1)
		elif not (self.M2 > self.POD2):
			errorMsg = "Outer diameter M2 %s must be larger than outer pipe diameter POD2 %s"%(self.M2, self.POD2)
		elif not ( self.G > 0):
			errorMsg = "G=%s must be positive."%(self.G)
		elif not ( self.G1 > 0):
			errorMsg = "G1=%s must be positive."%(self.G1)
		elif not ( self.G2 > 0):
			errorMsg = "G2=%s must be positive."%(self.G2)
		elif not ( self.H > self.G):
			errorMsg = "H=%s must be larger than G=%s."%(self.H, self.G)
		elif not ( self.H1 > self.G1):
			errorMsg = "H1=%s must be larger than G1=%s."%(self.H1, self.G1)
		elif not ( self.H2 > self.G2):
			errorMsg = "H1=%s must be larger than G2=%s."%(self.H2, self.G2)

		return (len(errorMsg)==0, errorMsg )

	def shiftA1(self):
		"""Determine an additional length a1 of the socket 1, such that the wall size of the intermediate
		section on it thin part is not smaller than the walls of the sockets.
		The size a1 does not come from some document or standard. It is only chosen to avoid thin walls
		in the intermediate section of thecoupling. Probably a1 must be even larger.

		a1 is positive if POD > POD1, it is negative if POD < POD1.

		See Dimensions.shiftA1 in coupling module, for explanation how calclulate a1.
		"""
		a2 = max(self.M-self.POD, self.M1-self.POD1) / 2
		x = (self.POD-self.POD1)
		N = (self.G+self.G1)
		# The math.sqrt will return Float. That is why
		# we need to convert x in float too.
		factor = x.Value/math.sqrt(4*N**2+x**2)
		a1 = factor*a2
		return a1

	def leftSocketOuterLength(self):
		"""Return outer length of the socket on the bottom in FreeCAD
		(on the left size in the picture).
		"""
		return self.H-self.G+self.shiftA1()

	def rightSocketOuterLength(self):
		"""Return outer length of the socket on the to in FreeCAD
		(on the right size in the picture).
		"""
		return self.H1-self.G1-self.shiftA1()

	def calculateAuxiliararyPoints(self):
		"""Calculate auxiliarary points which are used to build a coupling from cylinders and cones.

		See documentation picture coupling-cacluations.png
		"""
		result = {}
		result["p1"] = FreeCAD.Vector(-self.H,0,0)
		result["p2"] = FreeCAD.Vector(-self.G,0,0)
		result["p3"] = FreeCAD.Vector(self.G1,0,0)
		result["p4"] = FreeCAD.Vector(0,0,self.G2)
		result["p5"] = FreeCAD.Vector(-self.G+self.shiftA1(),0,0)
		result["p6"] = FreeCAD.Vector(self.G1+self.shiftA1(),0,0)
		return result

	def PID(self):
		return self.POD-2*self.PThk

	def PID1(self):
		return self.POD1-2*self.PThk1

	def PID2(self):
		return self.POD2-2*self.PThk2

class Tee:
	def __init__(self, document):
		self.document = document
		self.dims = Dimensions()

	def checkDimensions(self):
		valid, msg = self.dims.isValid()
		if not valid:
			raise Piping.UnplausibleDimensions(msg)

	def createOuterPart(self):
		if self.dims.M == self.dims.M1:
			return self.createOuterPartEqualHorizontal()
		else:
			return self.createOuterPartReducedHorizontal()

	def HorizontalWallEnhancement(self):
		""" If the diameter of the vertical part is larger than the diamter of the horizontal part,
		add an additional cylinder to the outer part in the middle.

		For some reasons this code crashes freecad.
		"""
		if self.dims.M2 > self.dims.M or self.dims.M2 > self.dims.M1:
			cylinder = self.document.addObject("Part::Cylinder","HorizontalEnhancement")
			cylinder.Radius = self.dims.M2/2.0
			cylinder.Height = self.dims.M2
			p = FreeCAD.Vector(-self.dims.M2/2.0,0,0)
			cylinder.Placement = FreeCAD.Placement(p, FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
			return cylinder
		else:
			return None

	def createOuterPartEqualHorizontal(self):
		""" Create an outer part, where the left and the right outer dimensions M and M1 are equal.
		"""
		aux = self.dims.calculateAuxiliararyPoints()
		L = self.dims.H+self.dims.H1
		vertical_outer_cylinder = self.document.addObject("Part::Cylinder","VerticalOuterCynlider")
		vertical_outer_cylinder.Radius = self.dims.M2/2.0
		vertical_outer_cylinder.Height = self.dims.H2
		horizontal_outer_cylinder = self.document.addObject("Part::Cylinder","HorizontalOuterCynlider")
		horizontal_outer_cylinder.Radius = self.dims.M/2.0
		horizontal_outer_cylinder.Height = L
		horizontal_outer_cylinder.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		outer_fusion = self.document.addObject("Part::MultiFuse","OuterTeeFusion")
		enh = self.HorizontalWallEnhancement()
		if enh is None:
				outer_fusion.Shapes = [vertical_outer_cylinder, horizontal_outer_cylinder]
		else:
				# Add enhancement to a separate shape because the line below crashes.
				# This is a work around.
				tmp = self.document.addObject("Part::MultiFuse","OuterTeeFusion2")
				tmp.Shapes =  [vertical_outer_cylinder, horizontal_outer_cylinder]
				outer_fusion.Shapes = [enh, tmp]

		return outer_fusion

	def createOuterPartReducedHorizontal(self):
		""" Create a outer part which is cylinder+cone+cylinder+vertical cylinder.
		Also add an additional enhancement if the vertical part has too large diameter.
		"""
		aux = self.dims.calculateAuxiliararyPoints()
		# Create socket 1.
		cylinder1 = self.document.addObject("Part::Cylinder","Cylinder1")
		cylinder1.Radius = self.dims.M/2.0
		cylinder1.Height = self.dims.leftSocketOuterLength()
		cylinder1.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create a cone and put it at the right side of the cylinder 1.
		cone = self.document.addObject("Part::Cone","Cone")
		cone.Radius1 = self.dims.M/2.0
		cone.Radius2 = self.dims.M1/2.0
		cone.Height = self.dims.G+self.dims.G1
		cone.Placement = FreeCAD.Placement(aux["p5"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create a socket 2 and put it at the right side of the cone.
		cylinder2 = self.document.addObject("Part::Cylinder","Cylinder2")
		cylinder2.Radius = self.dims.M1/2.0
		cylinder2.Height = self.dims.rightSocketOuterLength()
		cylinder2.Placement = FreeCAD.Placement(aux["p6"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create vertical part.
		vertical_outer_cylinder = self.document.addObject("Part::Cylinder","VerticalOuterCynlider")
		vertical_outer_cylinder.Radius = self.dims.M2/2.0
		vertical_outer_cylinder.Height = self.dims.H2
		# Combine all four parts and, if necessary, add enhacement.
		outer = self.document.addObject("Part::MultiFuse","OuterParts")
		enh = self.HorizontalWallEnhancement()

		if enh is None:
				outer.Shapes = [cylinder1, cone, cylinder2, vertical_outer_cylinder]
		else:
				# Add enhancement to a separate shape because the line below crashes.
				# This is a work around.
				tmp = self.document.addObject("Part::MultiFuse","OuterTeeFusion2")
				tmp.Shapes =  [cylinder1, cone, cylinder2, vertical_outer_cylinder]
				outer.Shapes = [enh, tmp]

		return outer

	def createInnerPart(self):
		if self.dims.PID() == self.dims.PID1():
			return self.createInnerPartEqualHorizontal()
		else:
			return self.createInnerPartReducedHorizontal()

	def createInnerPartEqualHorizontal(self):
		""" Create a cylindrical inner part simmilar to createOuterPartEqualHorizontal().
		"""
		aux = self.dims.calculateAuxiliararyPoints()
		L = self.dims.H+self.dims.H1
		vertical_inner_cylinder = self.document.addObject("Part::Cylinder","VerticalInnerCynlider")
		vertical_inner_cylinder.Radius = self.dims.PID2()/2.0
		vertical_inner_cylinder.Height = self.dims.H2
		horizontal_inner_cylinder = self.document.addObject("Part::Cylinder","HorizontalInnerCynlider")
		horizontal_inner_cylinder.Radius = self.dims.PID()/2.0
		horizontal_inner_cylinder.Height = L
		horizontal_inner_cylinder.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		inner = self.document.addObject("Part::MultiFuse","InnerParts")
		inner.Shapes = [vertical_inner_cylinder, horizontal_inner_cylinder]+self.createInnerSockets()
		return inner

	def createInnerPartReducedHorizontal(self):
		""" Create a inner part with a connic middle simmilar to createOuterPartReducedHorizontal().
		"""
		aux = self.dims.calculateAuxiliararyPoints()
		# Create cylinder 1.
		cylinder1 = self.document.addObject("Part::Cylinder","InnerCylinder1")
		cylinder1.Radius = self.dims.PID()/2.0
		cylinder1.Height = self.dims.H - self.dims.G
		cylinder1.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create a cone and put itto the right of the cylinder 1.
		cone = self.document.addObject("Part::Cone","InnerCone")
		cone.Radius1 = self.dims.PID()/2.0
		cone.Radius2 = self.dims.PID1()/2.0
		cone.Height = self.dims.G+self.dims.G1
		cone.Placement = FreeCAD.Placement(aux["p2"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create a socket 2 and put it to the right of the cone.
		cylinder2 = self.document.addObject("Part::Cylinder","InnerCylinder2")
		cylinder2.Radius = self.dims.PID1()/2.0
		cylinder2.Height = self.dims.H1 - self.dims.G1
		cylinder2.Placement = FreeCAD.Placement(aux["p3"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		# Create vertical part.
		vertical_inner_cylinder = self.document.addObject("Part::Cylinder","VerticalInnerCynlider")
		vertical_inner_cylinder.Radius = self.dims.PID2()/2.0
		vertical_inner_cylinder.Height = self.dims.H2
		# Combine all four parts.
		inner = self.document.addObject("Part::MultiFuse","InnerParts")
		inner.Shapes = [cylinder1, cone, cylinder2, vertical_inner_cylinder]+self.createInnerSockets()
		return inner

	def createInnerSockets(self):
		aux = self.dims.calculateAuxiliararyPoints()
		socket_left = self.document.addObject("Part::Cylinder","SocketLeft")
		socket_left.Radius = self.dims.POD/2.0
		socket_left.Height = self.dims.H-self.dims.G
		socket_left.Placement = FreeCAD.Placement(aux["p1"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))


		socket_right = self.document.addObject("Part::Cylinder","SocketRight")
		socket_right.Radius = self.dims.POD1/2.0
		socket_right.Height = self.dims.H1-self.dims.G1
		socket_right.Placement = FreeCAD.Placement(aux["p3"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))

		socket_top = self.document.addObject("Part::Cylinder","SocketTop")
		socket_top.Radius = self.dims.POD2/2.0
		socket_top.Height = self.dims.H2 - self.dims.G2
		socket_top.Placement = FreeCAD.Placement(aux["p4"], FreeCAD.Rotation(FreeCAD.Vector(0,1,0),0), FreeCAD.Vector(0,0,0))

		return [socket_left, socket_top, socket_right]

	def create(self, convertToSolid):
		self.checkDimensions()
		outer = self.createOuterPart()
		inner = self.createInnerPart()
		tee = self.document.addObject("Part::Cut","tee")
		tee.Base = outer
		tee.Tool = inner
		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = PipingtoSolid(self.document, tee, "tee (solid)")
			# Remove previous (intermediate parts).
			parts = PipingnestedObjects(tee)
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

	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table

	@classmethod
	def getPThkX(cls, row, postfix=""):
		""" For compatibility results, if there is no "PThkX" dimension, calculate it
		from "PIDX" and "PODX"

		:param psotfix: postfix for dimensions "PThk" "POD" and "PID". If it "2" then
			this function calculateds "PThk2" from "POD2" and "PID2".
		 """
		if not "PThk"+postfix in row.keys():
			return (parseQuantity(row["POD"+postfix])-parseQuantity(row["PID"+postifx]))/2.0
		else:
			return parseQuantity(row["PThk"+postfix])

	@classmethod
	def getPThk(cls, row):
		return cls.getPThkX(row, "")

	@classmethod
	def getPThk1(cls, row):
		return cls.getPThkX(row, "1")

	@classmethod
	def getPThk2(cls, row):
		return cls.getPThkX(row, "2")

	def create(self, partNumber, outputType):
		tee = Tee(self.document)
		row = self.table.findPart(partNumber)
		if row is None:
			print("Part not found {}".format(partNumber))
			return

		dims = Dimensions()
		dims.G = parseQuantity(row["G"])
		dims.G1 = parseQuantity(row["G1"])
		dims.G2 = parseQuantity(row["G2"])
		dims.H = parseQuantity(row["H"])
		dims.H1 = parseQuantity(row["H1"])
		dims.H2 = parseQuantity(row["H2"])
		dims.M = parseQuantity(row["M"])
		dims.M1 = parseQuantity(row["M1"])
		dims.M2 = parseQuantity(row["M2"])
		dims.POD = parseQuantity(row["POD"])
		dims.POD1 = parseQuantity(row["POD1"])
		dims.POD2 = parseQuantity(row["POD2"])
		dims.PThk = self.getPThk(row)
		dims.PThk1 = self.getPThk1(row)
		dims.PThk2 = self.getPThk2(row)

		if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
			tee = Tee(self.document)
			tee.dims = dims
			part = tee.create(outputType == Piping.OUTPUT_TYPE_SOLID)
			part.Label = "OSE-Tee"
			return part

		elif outputType == Piping.OUTPUT_TYPE_FLAMINGO:
			feature = self.document.addObject("Part::FeaturePython", "OSE-Tee")
			import FlTee
			builder = FlTee.TeeBuilder(self.document)
			builder.dims = dims
			part = builder.create(feature)
			feature.PRating = Piping.GetPressureRatingString(row)
			feature.PSize = row["PSize"] # What to do for multiple sizes?
			feature.ViewObject.Proxy = 0
			feature.PartNumber = partNumber
   			return part


# Test macros.
def TestTee():
	document = FreeCAD.activeDocument()
	tee = Tee(document)
	tee.create(False)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = Piping.CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = TeeFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partNumber = table.getPartKey(i)
		print("Creating part %s"%partNumber)
		builder.create(partNumber, Piping.OUTPUT_TYPE_SOLID)
		document.recompute()


def TestPartFromTable(partNumber, outputType):
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = TeeFromTable(document, table)
	print("Creating part %s"%partNumber)
	builder.create(partNumber, outputType)
	document.recompute()

#TestTee()
#TestTable()
# Test a part with an midle enhancement.
#TestPartFromTable("401-053", Piping.OUTPUT_TYPE_PARTS)
