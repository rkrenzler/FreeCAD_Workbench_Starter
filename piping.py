# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 17 February 2018
# General classes for pipe and fittng parts.

import csv
import Part


class Error(Exception):
	"""Base class for exceptions in this module."""
	def __init__(self, message):
		super(Error, self).__init__(message)


class UnplausibleDimensions(Error):
	"""Exception raised when dimensions are unplausible. For example if
	outer diameter is larger than the iner one.

	Attributes:
	message -- explanation of the error
	"""

	def __init__(self, message):
		super(UnplausibleDimensions, self).__init__(message)

def nestedObjects(parent):
	"""
	Return a list of a nested object contained in the parent parts.
	Children are added before the parents."""
	res = []
	if parent.OutList == []:
		res.append(parent)
	else:
		# Append children first.
		for o in parent.OutList:
			res += nestedObjects(o)
		res.append(parent)
	return res

def removePartWithChildren(document, part):
	parts = nestedObjects(part)
	# Document.removeObjects can remove multple objects, when we use
	# parts directly. To prevent exceptions with deleted objects,
	# use the name list instead.
	names_to_remove = []
	for part in parts:
		if part.Name not in names_to_remove:
			names_to_remove.append(part.Name)
	for name in names_to_remove:
		print("Deleting temporary objects %s."%name)
		document.removeObject(name)
				
def toSolid(document, part, name):
	"""Convert object to a solid.
	
	These are commands, which FreeCAD runs when a user converts a part to a solid.
	"""
	s = part.Shape.Faces
	s = Part.Solid(Part.Shell(s))
	o = document.addObject("Part::Feature", name)
	o.Label = name
	o.Shape = s
	return o


class CsvError(Error):
	"""Base class for exceptions in this module."""
	def __init__(self, message):
		super(Error, self).__init__(message)


class CsvTable2:
	""" Read pipe dimensions from a csv file.
	one part of the column must be unique and contains a unique key.

	Store the data as a list of rows. Each row is a list of values.
	"""
	def __init__(self, mandatoryDims=None, keyColumnName="PartNumber"):
		"""
		@param mandatoryDims: list of column names which must be presented in the CSV files apart
		the "keyColumnName" column
		"""
		self.headers = []
		self.data = []
		self.hasValidData = False
		if mandatoryDims is None:
			mandatoryDims = []
		self.mandatoryDims = mandatoryDims
		self._keyColumnName = keyColumnName
		self._keyColumnIndex = None
		
	def keyColumnName(self):
		return self._keyColumnName
	
	def load(self, filename):
		"""Load data from a CSV file."""
		self.hasValidData = False
		with open(filename, "r") as csvfile:
			csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
			self.headers = csv_reader.next()
			# Fill the talble
			self.data = []
			keys = []
			self._keyColumnIndex = self.headers.index(self._keyColumnName)
			for row in csv_reader:
				# Check if the keys is unique
				key = row[self._keyColumnIndex]
				if key in keys:
					msg = 'Error: Not unique key "%s" in column %s found in %s'%(key, self._keyColumnName, filename)
					raise CsvError(msg)
				else:
					keys.append(key)
				self.data.append(row)
			csvfile.close() # Should I close this file explicitely?
			self.hasValidData = self.hasNecessaryColumns()

	def hasNecessaryColumns(self):
		""" Check if the data contains all the columns required to create a part."""
		return all(h in self.headers for h in (self.mandatoryDims + [self._keyColumnName]))

	def findPart(self, key):
		"""Return first row with with key (part name) as a dictionary."""
		# Search for the first appereance of the name in this column.
		for row in self.data:
			if row[self._keyColumnIndex] == key:
				# Convert row to dicionary.
				return dict(zip(self.headers, row))
		return None

	def getPartKey(self, index):
		"""Return part key of a row with the index *index*."""
		return self.data[index][self._keyColumnIndex]

		
OUTPUT_TYPE_PARTS = 1
OUTPUT_TYPE_SOLID = 2
OUTPUT_TYPE_FLAMINGO = 3


def GetPressureRatingString(row):
	"""Extract presssure rating string from a row of a fitting table.
	
	The Pressure rating has a form "SCH-[Schedule]". For example "SCH-40".
	
	:param	row: a dictionary wich contains non empty elements "Schedule" or "SCH".
	:return: String like "SCH-40" or "SCH-80".
	:return "": if there is no schedule data in the row.
	"""
	if row.get("Schedule") is not None and len(row["Schedule"]) > 0:
		return "SCH-%s"%row["Schedule"]
	if row.get("SCH") is not None and len(row["SCH"]) > 0:
		return "SCH-%s"%row["SCH"]
	else:
		return "" # Nothing found


def GetDnString(row):
	"""Extract DN (diamètre nominal, nominal pipe size) string from a row of a fitting table.
	
	The Pressure rating has a form "DN[DN-Value]". For example "DN25".
	
	:param	row: a dictionary wich contains non empty elements "ND".
	:return: String like "DN10" or "DN25".
	:return "": if there is no DN data in the row.
	"""
	if row.get("DN") is not None and len(row["DN"]) > 0:
		return "DN%s"%row["DN"]
	else:
		return "" # Nothing found


def HasFlamingoSupport():
	import pkgutil
	mod = pkgutil.find_loader("pipeFeatures")
	return mod is not None	


