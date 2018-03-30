# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 30. March 2018
# Create a sweep-elbow-fitting.

import math
import csv
import os.path

import FreeCAD
import FreeCADGui
import Sketcher
import Part

import OSEBase
from piping import *

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, "sweep-elbow.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["H", "G", "M", "POD", "PThk"]

class Dimensions:
	def __init__(self):
		# Init class with test values
		self.G = parseQuantity("5 cm")
		self.H = parseQuantity("6 cm")
		self.M = parseQuantity("3 cm")
		self.POD = parseQuantity("2 cm")
		self.PThk = parseQuantity("0.5 cm")

	def isValid(self):
		fitThk = (self.M-self.POD)/2.0
		errorMsg = ""
		if not (self.POD > 0):
			errorMsg = "Pipe outer diameter %s must be positive"%self.PID
		elif not (self.PThk <= self.POD/2.0):
			errorMsg = "Pipe thickness %s is too larger: larger than POD/2 %s."%(self.PThk, self.POD/2.0)
		elif not (self.M > self.POD):
			errorMsg = "Socket outer diameter %s must be greater than pipe outer diameter =%s."%(self.M, self.POD)
		elif not (self.G > 0):
			errorMsg = "Length G=%s must be larger than M/2 + fitting thickness (M-POD)/2 =%s."%(self.G,
				self.M/2+fitTh)
		elif not (self.H > self.G):
			errorMsg = "Length H=%s must be larger than G=%s"%(self.H, self.G)
		return (len(errorMsg)==0, errorMsg)

class SweepElbow:
	def __init__(self, document):
		self.document = document
		self.dims = Dimensions()
		# Init class with test values

	def checkDimensions(self):
		valid, msg = self.dims.isValid()
		if not valid:
			raise UnplausibleDimensions(msg)
	
	@staticmethod
	def createBentCylinder(doc, group, r, l):
		""" Create 90° bent cylinder in x-z plane with radius r. 
		
		:param group: Group where to add created objects.
		:param r: Radius of the cylinder.
		:param l: Distance to the origin (0,0,0).
		
		See documentation picture sweep-elbow-cacluations.png
		"""
		p1 = FreeCAD.Vector(0,0,-l)
		# Add cylinder
		base = doc.addObject("Part::Circle","Base")
		base.Radius = r
		base.Placement.Base = p1
		# Add trajectory
		p3 = FreeCAD.Vector(l,0,-l)
		trajectory = doc.addObject("Part::Circle","Trajectory")
		trajectory.Radius = l
		trajectory.Angle0 = 90
		trajectory.Angle1 = 180
		trajectory.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(FreeCAD.Vector(1,0,0),90), FreeCAD.Vector(0,0,0))
		# Sweep the circle along the trajectory.
		sweep = doc.addObject('Part::Sweep','Sweep')
		sweep.Sections = [base]
		sweep.Spine = trajectory
		sweep.Solid = True
		group.addObjects([trajectory, sweep])
		return sweep
		
	def createOuterPart(self, group):
		"""Create bending part and socket cylinders.
		
		See documentation picture sweep-elbow-cacluations.png.
		"""
		# Create a bent part.
		bentPart = SweepElbow.createBentCylinder(self.document, group, self.dims.POD/2.0, self.dims.G)
		# Create vertical socket (on the bottom).
		socket1 = self.document.addObject("Part::Cylinder","Socket1")
		# Calculate wall thickness of the fitting.
		fitThk = (self.dims.M - self.dims.POD)/2.0
		socket1.Radius = self.dims.M/2.0
		# Calculate socket Height.
		a2 = self.dims.H - self.dims.G + fitThk
		socket1.Height = a2
		# Calculate socket position.
		p2 = FreeCAD.Vector(0,0,-self.dims.H)
		socket1.Placement.Base = p2
		# Calculate second socket (on the right).
		socket2 = self.document.addObject("Part::Cylinder","Socket2")
		socket2.Radius = self.dims.M/2.0
		socket2.Height = a2
		p3 = FreeCAD.Vector(self.dims.H-a2,0,0)
		# Rotate the socket and bring it to the right end of the fitting.
		socket2.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		outer = self.document.addObject("Part::MultiFuse","Outer")
		outer.Shapes = [bentPart, socket1, socket2]
		group.addObject(outer)
		return outer
		
	def createInnerPart(self, group):
		"""Create inner bending part and socket cylinders.
		See documentation picture sweep-elbow-cacluations.png.
		
		Note: The inner part differs from the outer part not only by socket sizes
		and the size of the bent part, the sockets positions are also different.
		In the inner part the sockets justs touch the inner parts.
		In the outer part the sockets intesects with bent part (the intersection
		width corresponds to the wall thickness of the fitting).
		"""

		# Create a bent part.
		socketR = self.dims.POD/2.0
		innerR = self.dims.POD/2.0-self.dims.PThk
		bentPart = SweepElbow.createBentCylinder(self.document, group, innerR, self.dims.G)
		# Create vertical socket (on the bottom).
		socket1 = self.document.addObject("Part::Cylinder","Socket1")
		# Calculate wall thickness of the fitting.
		socket1.Radius = socketR
		# Calculate socket Height.
		a1 = self.dims.H - self.dims.G
		socket1.Height = a1
		# Calculate socket position.
		p2 = FreeCAD.Vector(0,0,-self.dims.H)
		socket1.Placement.Base = p2
		# Calculate second socket (on the right).
		socket2 = self.document.addObject("Part::Cylinder","Socket2")
		socket2.Radius = socketR
		socket2.Height = a1
		p3 = FreeCAD.Vector(self.dims.H-a1,0,0)
		# Rotate the socket and bring it to the right end of the fitting.
		socket2.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(FreeCAD.Vector(0,1,0),90), FreeCAD.Vector(0,0,0))
		inner = self.document.addObject("Part::MultiFuse","Inner")
		inner.Shapes = [bentPart, socket1, socket2]
		group.addObject(inner)
		return inner
		
	def create(self, convertToSolid):
		self.checkDimensions()
		# Create new group to put all the temporal data.
		group = self.document.addObject("App::DocumentObjectGroup", "ElbowGroup")
		outer = self.createOuterPart(group)
		inner = self.createInnerPart(group)
		elbow = self.document.addObject("Part::Cut","SweepElbow")
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
			solid = toSolid(self.document, elbow, "sweep elbow (solid)")
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
# Test macros.
def TestSweepElbow():
	document = FreeCAD.activeDocument()
	elbow = SweepElbow(document)
	elbow.create(False)
	document.recompute()


TestSweepElbow()
