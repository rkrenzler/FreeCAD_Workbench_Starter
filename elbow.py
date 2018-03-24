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

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "elbow.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["alpha", "POD", "PID", "H", "J", "M"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
RELATIVE_EPSILON = 0.1


class Elbow:
	def __init__(self, document):
		self.document = document
		# Init class with test values
		self.alpha = tu("60 deg")
		self.M = tu("3 cm")
		self.POD = tu("2 cm")
		self.PID = tu("1 cm")
		self.H = tu("5 cm")
		self.J = tu("2 cm")


	def checkDimensions(self):
		if not ( (self.alpha > tu("0 deg")) and (self.alpha <= tu("180 deg")) ):
			raise UnplausibleDimensions("alpha %s must be within of range (0,180]"%self.alpha)
		if not ( self.PID > 0):
			raise UnplausibleDimensions("Pipe inner diameter %s must be positive"%self.PID)
		if not ( self.POD > self.PID):
			raise UnplausibleDimensions("Pipe outer diameter OD %s must be greater than pipe inner diameter ID %s"%(self.POD, self.PID))
		if not ( self.M > self.POD):
			raise UnplausibleDimensions("Socket outer diameter %s must be greater than pipe outer diameter =%s"%(self.M, self.POD))
		if not ( self.H > 0):
			raise UnplausibleDimensions("Length H=%s must be positive"%self.H)
		if not ( self.J > 0):
			raise UnplausibleDimensions("Length J=%s must be positive"%self.J)
	
	@staticmethod
	def CreateLineSegment(point_1, point_2):
		""" Create a line segment.
		This function creates the line calling different methods, depending on the version of FreeCAD
		"""
		if hasattr(Part, "LineSegment") and callable(getattr(Part, "LineSegment")):
			return Part.LineSegment(point_1, point_2)
		else:
			return Part.Line(point_1, point_2)

	def createElbowCylinder(self, group, r_cyl, r_bent, alpha, len1, len2):
		"""Create a cylinder with a radius r_cyl with a base on X-Y plane
		and bent it by angle alpha along radius r_bent. Add streight cylinders at the ends

		put all new created objects to a group.
		This should simplify the cleaning up of the intermediate parts.
	
		:param r_cyl: radius of the cylinder in Base.Quantity
		:param r_bent: radius of the path in Base.Quantity
		:param alpha: in Base.Quantity
		:param len1: length of the streight part 1
		:param len2: length of the streight part 2
		"""
		base_sketch = self.document.addObject('Sketcher::SketchObject','BaseSketch')
		base_sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0.000000,0.000000,0.000000),FreeCAD.Rotation(0.000000,0.000000,0.000000,1.000000))

		# When adding a radius, do not forget to convert the units.
		base_sketch.addGeometry(Part.Circle(FreeCAD.Vector(0.000000,0.000000,0),FreeCAD.Vector(0,0,1),r_cyl),False)

		# Add sweeping part into X-Z plane.
		path_sketch = self.document.addObject('Sketcher::SketchObject','PathSketch')
		path_sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0.000000,0.000000,0.000000),FreeCAD.Rotation(-0.707107,0.000000,0.000000,-0.707107))
		# Note the pskecth is rotatet, therefore y and z coordinates are exchanged (? is it still true)
		# Add a line into to the bottom direction (negative Z).
		line1 = self.CreateLineSegment(FreeCAD.Vector(0.000000,0.000000,0),FreeCAD.Vector(-0.000000,-len1,0))
		path_sketch.addGeometry(line1, False)

		# Add the arc part.
		start = (tu("pi rad") - alpha).getValueAs("rad")
		stop = tu("pi rad").getValueAs("rad")
		arc = Part.ArcOfCircle(Part.Circle(FreeCAD.Vector(r_bent,0,0),FreeCAD.Vector(0,0,1),r_bent),start, stop)
		path_sketch.addGeometry(arc,False)

		# Find coordinates of the right point of the arc.
		x1 = (1-math.cos(alpha.getValueAs("rad")))*r_bent
		z1 = math.sin(alpha.getValueAs("rad"))*r_bent

		x2 = x1 + math.cos((tu("pi/2 rad")-alpha).getValueAs("rad"))*len2
		z2 = z1 + math.sin((tu("pi/2 rad")-alpha).getValueAs("rad"))*len2
		# Draw a streight line for the right pipe.
		line2 = self.CreateLineSegment(FreeCAD.Vector(x1,z1,0),FreeCAD.Vector(x2,z2,0))
		line2_geometry = path_sketch.addGeometry(line2,False)
		# Sweep the parts.
		sweep = self.document.addObject('Part::Sweep','Sweep')
		sweep.Sections=[base_sketch, ]
		sweep.Spine=(path_sketch,["Edge1", "Edge2", "Edge3"])
		sweep.Solid=True
		sweep.Frenet=False # Is it necessary?
		# Hide the sketches.
		FreeCADGui.getDocument(self.document.Name).getObject(base_sketch.Name).Visibility = False
		FreeCADGui.getDocument(self.document.Name).getObject(path_sketch.Name).Visibility = False
		# Add all the objects to the group.
		group.addObject(base_sketch)
		group.addObject(path_sketch,)
		group.addObject(sweep)
		return sweep
		
	def createElbowPart(self, group):
		len1 = self.H - self.J
		# Create a ellbow pipe as a difference of two cylinders
		outer_sweep = self.createElbowCylinder(group, self.M/2, self.M/2, self.alpha, len1, len1)
		# Make the inner cylinder a littlebit longer, to prevent nummerical errors
		# wenn calculating the difference.
		inner_sweep = self.createElbowCylinder(group, self.PID/2, self.M/2, self.alpha, 
				len1*(1+RELATIVE_EPSILON), len1*(1+RELATIVE_EPSILON))
		bent_cut = self.document.addObject("Part::Cut","BentCut")
		bent_cut.Base = outer_sweep
		bent_cut.Tool = inner_sweep
		group.addObject(bent_cut)
		return bent_cut
		
	def create(self, convertToSolid):
		self.checkDimensions()
		"""Create elbow."""
		# Create new group to put all the temporal data.
		group = self.document.addObject("App::DocumentObjectGroup", "elbow group")
		# Create the bent part.
		bent_part = self.createElbowPart(group)
		# Remove cyliders from both ends for sockets
		inner_cylinder1 = self.document.addObject("Part::Cylinder","InnerCylinder1")
		inner_cylinder1.Radius = self.POD/2
		inner_cylinder1.Height = (self.H - self.J)*(1+RELATIVE_EPSILON)
		inner_cylinder1.Placement.Base = FreeCAD.Vector(0,0, -inner_cylinder1.Height)

		inner_cylinder2 = self.document.addObject("Part::Cylinder","InnerCylinder2")
		inner_cylinder2.Radius = self.POD/2
		inner_cylinder2.Height = (self.H - self.J)*(1+RELATIVE_EPSILON)
		inner_cylinder2.Placement.Base = FreeCAD.Vector(0,0, -inner_cylinder2.Height)
		x = (1-math.cos(self.alpha.getValueAs("rad"))) *self.M/2
		z = math.sin(self.alpha.getValueAs("rad"))*self.M/2
		inner_cylinder2.Placement = FreeCAD.Placement(FreeCAD.Vector(x,0,z),FreeCAD.Rotation(FreeCAD.Vector(0,1,0),self.alpha))
		cut1 = self.document.addObject("Part::Cut","PipeCut1") 
		cut1.Base = bent_part
		cut1.Tool = inner_cylinder1
		elbow = self.document.addObject("Part::Cut","elbow") 
		elbow.Base = cut1
		elbow.Tool = inner_cylinder2
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
	def create(self, partName, outputType):
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return
			
		if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
			elbow = Elbow(self.document)
			elbow.alpha = tu(row["alpha"])
			elbow.H = tu(row["H"])
			elbow.J = tu(row["J"])
			elbow.M = tu(row["M"])

			elbow.POD = tu(row["POD"])
			elbow.PID = tu(row["PID"])
			part = elbow.create(outputType == OUTPUT_TYPE_SOLID)
			part.Label = partName
			return part
		elif outputType == OUTPUT_TYPE_FLAMINGO:
			# See Code in pipeCmd.makePipe in the Flamingo workbench.
			feature = self.document.addObject("Part::FeaturePython", "OSE-Elbow")
			import flElbow
			builder = flElbow.ElbowBuilder(self.document)
			builder.name = "partName"
			self.alpha = tu(row["alpha"])
			self.H = tu(row["H"])
			self.J = tu(row["J"])
			self.M = tu(row["M"])
			self.POD = tu(row["POD"])
			self.PID = tu(row["PID"])
			part = builder.create(feature)	
			feature.PRating = GetPressureRatingString(row)
			feature.PSize = ""
			feature.ViewObject.Proxy = 0
    			return part


# Test macros.
def TestElbow():
	document = FreeCAD.activeDocument()
	elbow = Elbow(document)
	elbow.create(True)
	document.recompute()


def TestElbowTable():
	document = FreeCAD.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	elbow = ElbowFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		elbow.create(partName, OUTPUT_TYPE_FLAMINGO)
		document.recompute()
		break
		

#TestElbow()
#TestElbowTable()
