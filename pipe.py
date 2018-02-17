# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04 February 2018
# Create a pipe.

import math
import csv
import os.path

from PySide import QtCore, QtGui
import FreeCAD
import Spreadsheet
import Sketcher
import Part

import OSEBase
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
CSV_TABLE_PATH = os.path.join(OSEBase.TABLE_PATH, 'pipe.csv' )
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["ID", "OD"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
# On my version of freecad 0.16 The macro works even with RELATIVE_EPSILON = 0.0.
# Maybe there is no more problems with boolean operations.
RELATIVE_EPSILON = 0.1

def nestedObjects(group):
	res = []
	if group.OutList == []:
		res.append(group)
	else:
		# Append children first.
		for o in group.OutList:
			res += nestedObjects(o)
		res.append(group)
	return res

def toSolid(document, part, name):
	"""Convert object to a solid.
		Basically those are commands, which FreeCAD runs when user converts a part to a solid.
	"""
	s = part.Shape.Faces
	s = Part.Solid(Part.Shell(s))
	o = document.addObject("Part::Feature", name)
	o.Label=name
	o.Shape=s
	return o

class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class UnplausibleDimensions(Error):
    """Exception raised when dimensions are unplausible. For example if
         outer diameter is larger than the iner one.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class Pipe:
	def __init__(self, document):
		self.document = document
		self.ID = tu("2 cm")
		self.OD = tu("3 cm")
		self.L = tu("1 m")

	def checkDimensions(self):
		if not (self.ID > tu("0 mm")):
			raise UnplausibleDimensions("ID (inner diameter) of the pipe must be positive. It is %s instead"%(self.ID))
		if not (self.OD > self.ID):
			raise UnplausibleDimensions("OD (outer diameter) %s must be larger than ID (inner dimater) %s "%(self.OD, self.ID))
		if not (self.L > tu("0 mm")):
			raise UnplausibleDimensions("Length L=%s must be positive"%self.L)

	def create(self, convertToSolid):
		""" A pipe which is a differences of two cilinders: outer cylinder - inner cylinder.
		:param convertToSolid: if true, the resulting part will be solid.
			if false, the resulting part will be a cut.
		:return resulting part.
		"""
		self.checkDimensions()
		# Create outer cylinder.
		outer_cylinder = self.document.addObject("Part::Cylinder","OuterCylinder")
		outer_cylinder.Radius = self.OD/2
		outer_cylinder.Height = self.L
		
		# Create inner cylinder. It is a little bit longer than the outer cylider in both ends.
		# This should prevent numerical problems when calculating difference
		# between the outer and innter cylinder.
		inner_cylinder = self.document.addObject("Part::Cylinder","InnerCylinder")
		inner_cylinder.Radius = self.ID/2
		inner_cylinder.Height = self.L*(1+2*RELATIVE_EPSILON)
		inner_cylinder.Placement.Base = App.Vector(0,0,-self.L*RELATIVE_EPSILON)
		pipe = self.document.addObject("Part::Cut","Pipe")
		pipe.Base = outer_cylinder
		pipe.Tool = inner_cylinder

		if convertToSolid:
			# Before making a solid, recompute documents. Otherwise there will be
			#    s = Part.Solid(Part.Shell(s))
			#    <class 'Part.OCCError'>: Shape is null
			# exception.
			self.document.recompute()
			# Now convert all parts to solid, and remove intermediate data.
			solid = toSolid(self.document, pipe, "pipe (solid)")
			# Remove previous (intermediate parts).
			parts = nestedObjects(pipe)
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
		return pipe

class CsvTable:
	""" Read pipe dimensions from a csv file.
	one part of the column must be unique and contains a unique key.
	It is the column "Name".
	"""
	def __init__(self, mandatoryDims=[]):
		"""
		@param mandatoryDims: list of column names which must be presented in the CSV files apart
		the "Name" column
		"""
		self.headers = []
		self.data = []
		self.hasValidData = False
		self.mandatoryDims=mandatoryDims
	def load(self, filename):
		"""Load data from a CSV file."""
		self.hasValidData = False
		with open(filename, "r") as csvfile:
			csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
			self.headers = csv_reader.next()
			# Fill the talble
			self.data = []
			names = []
			ni = self.headers.index("Name")
			for row in csv_reader:
				# Check if the name is unique
				name = row[ni]
				if name in names:
					print('Error: Not unique name "%s" found in %s'%(name, filename))
					exit(1)
				else:
					names.append(name)
				self.data.append(row)
			csvfile.close() # Should I close this file explicitely?
			self.hasValidData = self.hasNecessaryColumns()

	def hasNecessaryColumns(self):
		""" Check if the data contains all the columns required to create a bushing."""
		return all(h in self.headers for h in (self.mandatoryDims + ["Name"]))

	def findPart(self, name):
		"""Return first first raw with the particular part name as a dictionary."""
		# First find out the index of the column "Name".
		ci = self.headers.index("Name")
		# Search for the first appereance of the name in this column.
		for row in self.data:
			if row[ci] == name:
				# Convert row to dicionary.
				return dict(zip(self.headers, row))
		return None

	def getPartName(self, index):
		"""Return part name of a row with the index *index*."""
		ci = self.headers.index("Name")
		return self.data[index][ci]

class PipeFromTable:
	"""Create a part with dimensions from a CSV table."""
	def __init__ (self, document, table):
		self.document = document
		self.table = table
	def create(self, partName, length, convertToSolid = True):
		pipe = Pipe(self.document)
		row = self.table.findPart(partName)
		if row is None:
			print("Part not found")
			return
		pipe.ID = tu(row["ID"])
		pipe.OD = tu(row["OD"])
		pipe.L = length

		part = pipe.create(convertToSolid)
		part.Label = partName
		return part

class PartTableModel(QtCore.QAbstractTableModel): 
	def __init__(self, headers, data, parent=None, *args):
		self.headers = headers
		self.table_data = data
		QtCore.QAbstractTableModel.__init__(self, parent, *args) 
	
	def rowCount(self, parent): 
		return len(self.table_data) 
 
	def columnCount(self, parent):
		return len(self.headers) 
 
	def data(self, index, role):
		if not index.isValid(): 
			return None
		elif role != QtCore.Qt.DisplayRole: 
			return None
		return self.table_data[index.row()][index.column()] 

	def getPartName(self, rowIndex):
		name_index = self.headers.index("Name")
		return self.table_data[rowIndex][name_index]

	def getPartRowIndex(self, partName):
		""" Return row index of the part with name partName.
		:param :partName name of the part
		:return: index of the first row whose part name is equal to partName
				return -1 if no row find.
		"""
		name_index = self.headers.index("Name")
		for row_i in range(name_index, len(self.table_data)):
			if self.table_data[row_i][name_index] == partName:
				return row_i
		return -1
	def headerData(self, col, orientation, role):
		if orientation ==QtCore. Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

# Test macros.
def TestPipe():
	document = App.activeDocument()
	pipe = Pipe(document)
	pipe.create(False)
	document.recompute()

def TestTable():
	document = App.activeDocument()
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)
	pipe = PipeFromTable(document, table)
	for i in range(0, len(table.data)):
		print("Selecting row %d"%i)
		partName = table.getPartName(i)
		print("Creating part %s"%partName)
		pipe.create(partName, tu("1m"), False)
		document.recompute()

