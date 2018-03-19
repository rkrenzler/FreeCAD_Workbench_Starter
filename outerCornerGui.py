# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 09 February 2018
# Create a corner-fitting. 

import math
import os.path

from PySide import QtCore, QtGui
import FreeCAD

import OSEBase
from outerCorner import *
from piping import *


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

class MainDialog(QtGui.QDialog):
	QSETTINGS_APPLICATION = "OSE piping workbench"
	QSETTINGS_NAME = "outer corner user input"
	def __init__(self, document, table):
		super(MainDialog, self).__init__()
		self.document = document
		self.table = table
		self.selectionMode = False
		self.selectedPart = None
		self.initUi()
				
	def initUi(self): 
		Dialog = self # Added 
		self.result = -1 
		self.setupUi(self)
		# Fill table with dimensions. 
		self.initTable()

		# Restore previous user input. Ignore exceptions to prevent this part
		# part of the code to prevent GUI from starting, once settings are broken.
		try:
			self.restoreInput()
		except Exception as e:
			print ("Could not restore old user input!")
			print(e)
		self.show()

# The following lines are from QtDesigner .ui-file processed by pyside-uic
# pyside-uic --indent=0 create-outer-corner.ui -o tmp.py
# You need to adjust image paths to
# os.path.join(OSEBase.IMAGE_PATH, "outer-corner-dimensions.png")
	def setupUi(self, Dialog):
		Dialog.setObjectName("Dialog")
		Dialog.resize(803, 666)
		self.verticalLayout = QtGui.QVBoxLayout(Dialog)
		self.verticalLayout.setObjectName("verticalLayout")
		self.checkBoxCreateSolid = QtGui.QCheckBox(Dialog)
		self.checkBoxCreateSolid.setChecked(True)
		self.checkBoxCreateSolid.setObjectName("checkBoxCreateSolid")
		self.verticalLayout.addWidget(self.checkBoxCreateSolid)
		self.tableViewParts = QtGui.QTableView(Dialog)
		self.tableViewParts.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.tableViewParts.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableViewParts.setObjectName("tableViewParts")
		self.verticalLayout.addWidget(self.tableViewParts)
		self.labelExplanation = QtGui.QLabel(Dialog)
		self.labelExplanation.setTextFormat(QtCore.Qt.AutoText)
		self.labelExplanation.setWordWrap(True)
		self.labelExplanation.setObjectName("labelExplanation")
		self.verticalLayout.addWidget(self.labelExplanation)
		self.labelImage = QtGui.QLabel(Dialog)
		self.labelImage.setText("")
		self.labelImage.setPixmap(os.path.join(OSEBase.IMAGE_PATH, "outer-corner-dimensions.png"))
		self.labelImage.setAlignment(QtCore.Qt.AlignCenter)
		self.labelImage.setObjectName("labelImage")
		self.verticalLayout.addWidget(self.labelImage)
		self.buttonBox = QtGui.QDialogButtonBox(Dialog)
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		self.verticalLayout.addWidget(self.buttonBox)

		self.retranslateUi(Dialog)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
		QtCore.QMetaObject.connectSlotsByName(Dialog)

	def retranslateUi(self, Dialog):
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create outer corner", None, QtGui.QApplication.UnicodeUTF8))
		self.checkBoxCreateSolid.setText(QtGui.QApplication.translate("Dialog", "Create Solid", None, QtGui.QApplication.UnicodeUTF8))
		self.labelExplanation.setText(QtGui.QApplication.translate("Dialog", "<html><head/><body><p>To construct a part, only these dimensions are used: G, H, M, PID, and POD. All other dimensions are used for inromation.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))


	def initTable(self):
		# Read table data from CSV
		self.model = PartTableModel(self.table.headers, self.table.data)
		self.tableViewParts.setModel(self.model)
		
	def getSelectedPartName(self):
		sel = self.tableViewParts.selectionModel()
		if sel.isSelected:
			if len(sel.selectedRows())> 0:
				rowIndex = sel.selectedRows()[0].row()
				return self.model.getPartName(rowIndex)
		return None

	def selectPartByName(self, partName):
		"""Select first row with a part with a name partName."""
		if partName is not None:
			row_i = self.model.getPartRowIndex(partName)
			if row_i >= 0:
				self.tableViewParts.selectRow(row_i)

	def accept(self):
		if self.selectionMode:
			return self.acceptSelectionMode()
		else:
			self.acceptCreationMode()

	def acceptCreationMode(self):
		"""User clicked OK"""
		# If there is no active document, show a warning message and do nothing.
		if self.document is None:
			text = "I have not found any active document were I can create a corner fitting.\n"\
				"Use menu File->New to create a new document first, "\
				"then try to create the corner fitting again."
			msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the corner fitting failed.", text)
			msgBox.exec_()
			super(MainDialog, self).accept()
			return

		# Get suitable row from the the table.
		partName = self.getSelectedPartName()
		createSolid = self.checkBoxCreateSolid.isChecked()
		if partName is not None:
			corner = OuterCornerFromTable(self.document, self.table)
			corner.create(partName, createSolid)
			self.document.recompute()
			# Save user input for the next dialog call.
			self.saveInput()
			# Call parent class.
			super(MainDialog, self).accept()
		else:
			msgBox = QtGui.QMessageBox()
			msgBox.setText("Select part")
			msgBox.exec_()

	def acceptSelectionMode(self):
		self.selectedPart = self.getSelectedPartName()

		if self.selectedPart is None:
			msgBox = QtGui.QMessageBox()
			msgBox.setText("Select part")
			msgBox.exec_()
		else:
			super(MainDialog, self).accept()

	def saveInput(self):
		"""Store user input for the next run."""
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		check = self.checkBoxCreateSolid.checkState()
		settings.setValue("checkBoxCreateSolid", int(check))
		settings.setValue("LastSelectedPartName", self.getSelectedPartName())
		settings.sync()

	def restoreInput(self):
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		checkState = QtCore.Qt.CheckState(int(settings.value("checkBoxCreateSolid")))
		self.checkBoxCreateSolid.setCheckState(checkState)
		self.selectPartByName(settings.value("LastSelectedPartName"))


	def showForSelection(self, partName=None):
		""" Show pipe dialog, to select pipe and not to create it.
		:param partName: name of the part to be selected. Use None if you do not want to select
		anything.
		"""
		# If required select
		self.selectionMode = True
		self.setWindowTitle(QtGui.QApplication.translate("Dialog", "Select outer corner", None, QtGui.QApplication.UnicodeUTF8))
		self.selectedPart = None
		if partName is not None:
			self.selectPartByName(partName)
		self.exec_()
		return self.selectedPart
		
	def showForCreation(self):
		self.selectionMode = False
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create outer corner", None, QtGui.QApplication.UnicodeUTF8))
		self.exec_()
		
# Before working with macros, try to load the dimension table.

def GuiCheckTable():
	# Check if the CSV file exists.
	if os.path.isfile(CSV_TABLE_PATH) == False:
		text = "This macro requires %s  but this file does not exist."%(CSV_TABLE_PATH)
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the corner failed.", text)
		msgBox.exec_()
		exit(1) # Error

        FreeCAD.Console.PrintMessage("Trying to load CSV file with dimensions: %s"%CSV_TABLE_PATH) 
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)

	if table.hasValidData == False:
		text = 'Invalid %s.\n'\
			'It must contain columns %s.'%(CSV_TABLE_PATH, ", ".join(DIMENSIONS_USED))
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the corner failed.", text)
		msgBox.exec_()
		exit(1) # Error

	return table

#doc=FreeCAD.activeDocument()
#table = GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#form = MainDialog(doc, table)


