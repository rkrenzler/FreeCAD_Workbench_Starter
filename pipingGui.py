# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 February 2018
# General classes for piping dialogs

from PySide import QtCore

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
