# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 Januar December 2018
# Create a coupling fitting.


import math
import csv
import os.path

import FreeCAD
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "coupling.csv")

# Note only columns "Name", "POD", "PID", "POD1", "PID1", "L", "M", "M1", and "N"
# are used for calculations, all other are used for information. For example
# "PipeSize", "Schedule", "PipeSize1" show pipe sizing in more readable form.
# The table must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["POD", "PID", "POD1", "PID1", "L", "M", "M1", "N"]


class Coupling:
	def __init__(self, document):
		self.document = document
		# Set default values.
		self.M = tu("5 cm") # Outer diameter of socket 1.
		self.M1 = tu("3 cm") # Outer diameter of socket 2.
		self.N = tu("1 cm") # Lenght of the intemidate section of the coupling.
		self.POD = tu("4 cm") # Pipe outer diameter at the socket 1.
		self.POD1 = tu("2 cm") # Pipe outer diameter at the socket 2.
		self.PID = tu("3 cm") # Pipe inner diameter at the socket 1.
		self.PID1 = tu("1 cm") # Pipe inner diameter at the socket 2.
		self.X1 = tu("4 cm") # Length of the socket1.
		self.X2 = tu("4 cm") # Length of the socket2.

	def checkDimensions(self):
		if not ( self.PID > tu("0 mm") and self.PID1 > tu("0 mm") ):
			raise UnplausibleDimensions("Inner pipe dimensions must be positive. They are %s and %s instead"%(self.PID, self.PID1))
		if not ( self.M > self.POD and self.POD > self.PID ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(self.M, self.POD, self.PID))
		if not ( self.M1 > self.POD1 and self.POD1 > self.PID1 ):
			raise UnplausibleDimensions("It must hold outer diameter %s > Outer pipe diameter %s > Inner pipe diameter %s"%(self.M1, self.POD1, self.PID1))
		if not ( self.X1 > 0):
			raise UnplausibleDimensions("Length X1=%s must be positive"%self.X1)
		if not ( self.X2 > 0):
			raise UnplausibleDimensions("Length X2=%s must be positive"%self.X2)
		if not ( self.N > 0):
			raise UnplausibleDimensions("Intermediate length N=%s must be positive"%self.N)
			
	def calculateShiftA2(self):
		"""Determine an additional length a2 of the socket 1, such that the wall size of the intermediate
		section on it thin part is not smaller than the walls of the sockets.
		The size a2 does not come from some document or standard. It is only chosen to avoid thin walls
		in the intermediate section of thecoupling. Probably a2 must be even larger.
		"""
		a2 = max(self.M-self.POD, self.M1-self.POD1) / 2
		x = (self.POD-self.POD1)
		# The math.sqrt will return Float. That is why
		# we need to convert x in float too.
		factor = x.Value/math.sqrt(4*self.N**2+x**2)
		a1 = factor*a2
		return a1
		
	def createOuterPart(self):
		if self.M == self.M1:
			return self.createOuterPartEqual()
		else:
			return self.createOuterPartReduced()

	def createOuterPartEqual(self):
		""" Create a outer part which is cylinder only. This is when M and M1 are the same"""
		# Create socket 1.
		outer = self.document.addObject("Part::Cylinder","Cylinder")
		outer.Radius = self.M/2
		outer.Height = self.X1+self.N+self.X2
		return outer

	def createOuterPartReduced(self):
		""" Create a outer part which is cylinder+cone+cylinder."""
		# Create socket 1.
		cylinder1 = self.document.addObject("Part::Cylinder","Cylinder1")
		cylinder1.Radius = self.M/2
		a1 = self.calculateShiftA2()
		cylinder1.Height = self.X1+a1
		# Create a cone and put it on the cylinder 1
		cone = self.document.addObject("Part::Cone","Cone")
		cone.Radius1 = self.M/2
		cone.Radius2 = self.M1/2
		cone.Height = self.N
		cone.Placement.Base = FreeCAD.Vector(0,0,cylinder1.Height)
		# Create a socket 2 and put it on the cone 
		cylinder2 = self.document.addObject("Part::Cylinder","Cylinder2")
		cylinder2.Radius = self.M1/2
		cylinder2.Height = self.X2-a1
		cylinder2.Placement.Base = FreeCAD.Vector(0,0,cylinder1.Height+cone.Height)
		# Combine all outer parts.
		outer = self.document.addObject("Part::MultiFuse","OuterParts")
		outer.Shapes = [cylinder1, cone, cylinder2]
		return outer

	def createInnerPart(self):
		# Create parts which must be removed from the coupling.
		if self.PID == self.PID1:
			return self.createInnerPartEqual()
		else:
			return self.createInnerPartReduced()

	def createInnerPartEqual(self):
		""" Create inner part from cylinders. This is when PID and PID1 are the same"""
		cylinder1i = self.document.addObject("Part::Cylinder","Cylinder1i")
		cylinder1i.Radius = self.POD/2
		cylinder1i.Height = self.X1
		cylinder3i = self.document.addObject("Part::Cylinder","Cylinder3i")
		cylinder3i.Radius = self.PID1/2
		cylinder3i.Height = self.N
		cylinder3i.Placement.Base = FreeCAD.Vector(0,0,cylinder1i.Height)
		cylinder2i = self.document.addObject("Part::Cylinder","Cylinder2i")
		cylinder2i.Radius = self.POD1/2
		cylinder2i.Height = self.X2
		cylinder2i.Placement.Base = FreeCAD.Vector(0,0,cylinder1i.Height+cylinder3i.Height)
		inner = self.document.addObject("Part::MultiFuse","InnerParts")
		inner.Shapes = [cylinder1i, cylinder3i, cylinder2i]
		return inner

	def createInnerPartReduced(self):
		""" Create an innter part which is cylinder+cone+cylinder."""
		cylinder1i = self.document.addObject("Part::Cylinder","Cylinder1i")
		cylinder1i.Radius = self.POD/2
		cylinder1i.Height = self.X1
		conei = self.document.addObject("Part::Cone","Cone")
		conei.Radius1 = self.PID/2
		conei.Radius2 = self.PID1/2
		conei.Height = self.N
		conei.Placement.Base = FreeCAD.Vector(0,0,cylinder1i.Height)
		cylinder2i = self.document.addObject("Part::Cylinder","Cylinder2i")
		cylinder2i.Radius = self.POD1/2
		cylinder2i.Height = self.X2
		cylinder2i.Placement.Base = FreeCAD.Vector(0,0,cylinder1i.Height+conei.Height)
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
			solid = toSolid(self.document, coupling, "coupling (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(coupling)
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
		return coupling


class CouplingFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, convertToSolid = True):
		coupling = Coupling(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return
			
		coupling.M = tu(row["M"]) # Outer diameter of socket 1.
		coupling.POD = tu(row["POD"]) # Pipe outer diameter at the socket 1.
		coupling.PID = tu(row["PID"]) # Pipe inner diameter at the socket 1.
		coupling.X1 = (tu(row["L"])-tu(row["N"]))/2# Length of the socket1.
		coupling.M1 = tu(row["M1"]) # Outer diameter of socket 2.
		coupling.POD1 = tu(row["POD1"])  # Pipe outer diameter at the socket 2.
		coupling.PID1 = tu(row["PID1"]) # Pipe inner diameter at the socket 2.
		coupling.X2 = coupling.X1 # Length of the socket2.
		coupling.N = tu(row["N"]) # Lenght of the intemidate section of the coupling.

		part = coupling.create(convertToSolid)
		part.Label = partName
		return part


# Test macros.
def TestCoupling():
	document = FreeCAD.activeDocument()
	coupling = Coupling(document)
	coupling.create(True)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	corner = OuterCornerFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		coupling.create(partName, True)
		document.recompute()

#TestCoupling()
#TestTable()

