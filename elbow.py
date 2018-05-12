# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 16 December 2017
# Create a elbow-fitting.

import math
import csv
import os.path

import FreeCAD
import FreeCADGui
import Sketcher
import Part

import OSEBasePiping
from piping import *

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBasePiping.TABLE_PATH, "elbow.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["BendAngle", "POD", "PThk", "H", "J", "M"]


class Dimensions:
	def __init__(self):
		# Init class with test values
		self.BendAngle = parseQuantity("45 deg")
		self.H = parseQuantity("3 cm")
		self.J = parseQuantity("2 cm")
		self.M = parseQuantity("3 cm")
		self.POD = parseQuantity("2 cm")
		self.PThk = parseQuantity("0.5 cm")

	def isValid(self):
		errorMsg = ""
		if not (self.POD > 0):
			errorMsg = "Pipe outer diameter %s must be positive"%self.POD
		elif not (self.PThk <= self.POD/2.0):
			errorMsg = "Pipe thickness %s is too larg: larger than POD/2 %s."%(self.PThk, self.POD/2.0)
		elif not (self.M > self.POD):
			errorMsg = "Socket outer diameter %s must be greater than pipe outer diameter =%s."%(self.M, self.POD)
		elif not (self.J > 0):
			errorMsg = "Length J=%s must be positive."%(self.J)
		elif not (self.H > self.J):
			errorMsg = "Length H=%s must be larger than J=%s"%(self.H, self.J)
		return (len(errorMsg)==0, errorMsg)

	def calculateAuxiliararyPoints(self):
		"""Calculate auxiliarary points influenced by bentAngle, bentRadius (self.M/2)
		and the distannce J.
		
		See documentation picture elbow-cacluations.png
		"""
		rBend = self.M/2.0
		alpha = float(self.BendAngle.getValueAs("deg"))
		J=self.J
		H = self.H
		
		p1 = FreeCAD.Vector(0,0,-H)
		p2 = FreeCAD.Vector(0,0,-math.tan(math.radians(alpha)/2)*rBend)
		p3 = FreeCAD.Vector(rBend,0,p2.z)
		# Calculate coordinates of the base cirle at the end of sweep.
		# It will be necessary to create a solid body base+walls+cap
		# Create an auxiliary vector, rotate around (0,0,0)
		# and translated it to the center of the bent trajectory.
		aux = FreeCAD.Vector(-p3.x,0,0)
		rot = FreeCAD.Rotation(FreeCAD.Vector(0,1,0),alpha)
		aux = rot.multVec(aux)
		p4 = aux + p3
		
		p5 = FreeCAD.Vector(0,0,-J)
		aux = FreeCAD.Vector(0,0,J)
		rot = FreeCAD.Rotation(FreeCAD.Vector(0,1,0),alpha)
		p6 = rot.multVec(aux)
	
		return {"p1":p1, "p2":p2, "p3":p3, "p4":p4, "p5":p5, "p6":p6}
		
		
class Elbow:
	def __init__(self, document):
		self.document = document
		self.dims = Dimensions()

	def checkDimensions(self):
		valid, msg = self.dims.isValid()
		if not valid:
			raise UnplausibleDimensions(msg)
		
	def createBentCylinder(self, group, rCirc):
		""" Create alpha° bent cylinder in x-z plane with radius r. 
		
		:param group: Group where to add created objects.
		:param rCirc: Radius of the cylinder.
		:param rBend: Distance from the bend center to the origin (0,0,0).
		
		See documentation picture elbow-cacluations.png
		"""
		# Convert alpha to degree value
		aux = self.dims.calculateAuxiliararyPoints()
		p2 = aux["p2"]
		p3 = aux["p3"]
		p4 = aux["p4"]

		alpha = float(self.dims.BendAngle.getValueAs("deg"))
		rBend = self.dims.M/2.0
		
		# Calculate coordinates of the base circle.
		# Add cylinder
		base = self.document.addObject("Part::Circle","Base")
		base.Radius = rCirc
		base.Placement.Base = p2
		# Add trajectory
		trajectory = self.document.addObject("Part::Circle","Trajectory")
		trajectory.Radius = rBend
		trajectory.Angle0 = 180-alpha
		trajectory.Angle1 = 180
		trajectory.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(FreeCAD.Vector(1,0,0),90), FreeCAD.Vector(0,0,0))

		# Sweep the circle along the trajectory.
		sweep = self.document.addObject('Part::Sweep','Sweep')
		sweep.Sections = [base]
		sweep.Spine = trajectory
		sweep.Solid = True
		group.addObjects([trajectory, base, sweep])
		return sweep
		
	def createOuterPart(self, group):
		aux = self.dims.calculateAuxiliararyPoints()
		p1 = aux["p1"]
		p2 = aux["p2"]
		p4 = aux["p4"]
		bentPart = self.createBentCylinder(group, self.dims.M/2)
		# Create socket along the z axis.
		socket1 = self.document.addObject("Part::Cylinder","OuterSocket1")
		socket1.Radius = self.dims.M/2
		socket1.Height = float(self.dims.H)+p2.z
		socket1.Placement.Base = p1
		# Create socket along the bent part.
		socket2 = self.document.addObject("Part::Cylinder","OuterSocket2")
		socket2.Radius = socket1.Radius
		socket2.Height = socket1.Height
		socket2.Placement = FreeCAD.Placement(p4, FreeCAD.Rotation(FreeCAD.Vector(0,1,0),self.dims.BendAngle),
				FreeCAD.Vector(0,0,0))
		outer = self.document.addObject("Part::MultiFuse","Outer")
		outer.Shapes = [bentPart, socket1, socket2]
		group.addObject(outer)
		return outer
		
	def createInnerPart(self, group):
		aux = self.dims.calculateAuxiliararyPoints()
		p2 = aux["p2"]
		p4 = aux["p4"]
		p6 = aux["p6"]
		pid = self.dims.POD-self.dims.PThk*2
		bentPart = self.createBentCylinder(group, pid/2)
		chan1 = self.document.addObject("Part::Cylinder","InnerChannel1")
		chan1.Radius = pid/2
		chan1.Height = float(self.dims.H)+p2.z
		chan1.Placement.Base = FreeCAD.Vector(0,0,-self.dims.H)
		chan2 = self.document.addObject("Part::Cylinder","InnerChannel2")
		chan2.Radius = chan1.Radius
		chan2.Height = chan1.Height
		chan2.Placement = FreeCAD.Placement(p4, FreeCAD.Rotation(FreeCAD.Vector(0,1,0), self.dims.BendAngle),
					FreeCAD.Vector(0,0,0))
		# Add sockets
		socket1 = self.document.addObject("Part::Cylinder", "Socket1")
		socket1.Radius = self.dims.POD/2
		socket1.Height = self.dims.H-self.dims.J
		socket1.Placement = chan1.Placement
		
		socket2 = self.document.addObject("Part::Cylinder", "Socket2")
		socket2.Radius = socket1.Radius
		socket2.Height = socket1.Height
		socket2.Placement = FreeCAD.Placement(p6, FreeCAD.Rotation(FreeCAD.Vector(0,1,0), self.dims.BendAngle), FreeCAD.Vector(0,0,0))
		
		inner = self.document.addObject("Part::MultiFuse","Inner")
		inner.Shapes = [bentPart, chan1, chan2, socket1, socket2]
		group.addObject(inner)
		return inner
		
	
	def create(self, convertToSolid):
		self.checkDimensions()
		"""Create elbow."""
		# Create new group to put all the temporal data.
		group = self.document.addObject("App::DocumentObjectGroup", "elbow group")
		#----------------------- Test code ---------------
		#self.createBentCylinder(self.document, group, self.M/2, self.M/2, self.alpha)
		outer = self.createOuterPart(group)
		inner = self.createInnerPart(group)
		elbow = self.document.addObject("Part::Cut","Elbow")
		elbow.Base = outer
		elbow.Tool = inner
		group.addObject(elbow)
		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, elbow, "elbow (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(group)
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
		return group

class ElbowFromTable:
	"""Create a part with dimensions from CSV table."""
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
	def getPSize(cls, row):
		if "PSize" in row.keys():
			return row["PSize"]
		else:
			return ""

	def create(self, partNumber, outputType):
		row = self.table.findPart(partNumber)
		if row is None:
			print("Part not found")
			return

		dims = Dimensions()
		dims.BendAngle = parseQuantity(row["BendAngle"])
		dims.H = parseQuantity(row["H"])
		dims.J = parseQuantity(row["J"])
		dims.M = parseQuantity(row["M"])
		dims.POD = parseQuantity(row["POD"])
		dims.PThk = self.getPThk(row)

		if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
			elbow = Elbow(self.document)
			elbow.dims = dims
			part = elbow.create(outputType == OUTPUT_TYPE_SOLID)
			part.Label = "OSE-Elbow"
			return part
		elif outputType == OUTPUT_TYPE_FLAMINGO:
			# See Code in pipeCmd.makePipe in the Flamingo workbench.
			feature = self.document.addObject("Part::FeaturePython", "OSE-Elbow")
			import flElbow
			builder = flElbow.ElbowBuilder(self.document)
			builder.dims = dims
			part = builder.create(feature)	
			feature.PRating = GetPressureRatingString(row)
			feature.PSize = self.getPSize(row)
			feature.ViewObject.Proxy = 0
			feature.PartNumber = partNumber
    			return part

# Test macros.
def TestElbow():
	document = FreeCAD.activeDocument()
	elbow = Elbow(document)
	elbow.create(False)
	document.recompute()

def TestTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	builder = ElbowFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partNumber = table.getPartKey(i)
		print("Creating part %s"%partNumber)
		builder.create(partNumber, OUTPUT_TYPE_SOLID)
		document.recompute()


#TestElbow()
#TestElbowTable()
