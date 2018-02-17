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
from pipe import *
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table. 
# It must contain unique values in the column "Name" and also, dimensions listened below.


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
	QSETTINGS_APPLICATION = "OSE piping freecad macros"
	QSETTINGS_NAME = "pipe user input"
	def __init__(self, table):
		super(MainDialog, self).__init__()
		self.table = table
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
# pyside-uic --indent=0 create-pipe.ui -o tmp.py
# You need to adjust image paths.
	def setupUi(self, Dialog):
		Dialog.setObjectName("Dialog")
		Dialog.resize(614, 666)
		self.verticalLayout = QtGui.QVBoxLayout(Dialog)
		self.verticalLayout.setObjectName("verticalLayout")
		self.horizontalWidget = QtGui.QWidget(Dialog)
		self.horizontalWidget.setMinimumSize(QtCore.QSize(0, 27))
		self.horizontalWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
		self.horizontalWidget.setObjectName("horizontalWidget")
		self.label_3 = QtGui.QLabel(self.horizontalWidget)
		self.label_3.setGeometry(QtCore.QRect(160, 0, 52, 25))
		sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
		self.label_3.setSizePolicy(sizePolicy)
		self.label_3.setMaximumSize(QtCore.QSize(200, 16777215))
		self.label_3.setObjectName("label_3")
		self.lineEditLength = QtGui.QLineEdit(self.horizontalWidget)
		self.lineEditLength.setGeometry(QtCore.QRect(220, 0, 111, 27))
		self.lineEditLength.setObjectName("lineEditLength")
		self.checkBoxCreateSolid = QtGui.QCheckBox(self.horizontalWidget)
		self.checkBoxCreateSolid.setGeometry(QtCore.QRect(0, 0, 121, 26))
		self.checkBoxCreateSolid.setChecked(True)
		self.checkBoxCreateSolid.setObjectName("checkBoxCreateSolid")
		self.verticalLayout.addWidget(self.horizontalWidget)
		self.tableViewParts = QtGui.QTableView(Dialog)
		self.tableViewParts.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.tableViewParts.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableViewParts.setObjectName("tableViewParts")
		self.verticalLayout.addWidget(self.tableViewParts)
		self.label_2 = QtGui.QLabel(Dialog)
		self.label_2.setTextFormat(QtCore.Qt.AutoText)
		self.label_2.setWordWrap(True)
		self.label_2.setObjectName("label_2")
		self.verticalLayout.addWidget(self.label_2)
		self.label = QtGui.QLabel(Dialog)
		self.label.setText("")
		self.label.setPixmap(QtGui.QPixmap(os.path.join(OSEBase.IMAGE_PATH, "pipe-dimensions.png")))
		self.label.setAlignment(QtCore.Qt.AlignCenter)
		self.label.setObjectName("label")
		self.verticalLayout.addWidget(self.label)
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
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create pipe", None, QtGui.QApplication.UnicodeUTF8))
		self.label_3.setText(QtGui.QApplication.translate("Dialog", "Length:", None, QtGui.QApplication.UnicodeUTF8))
		self.lineEditLength.setText(QtGui.QApplication.translate("Dialog", "1ft", None, QtGui.QApplication.UnicodeUTF8))
		self.checkBoxCreateSolid.setText(QtGui.QApplication.translate("Dialog", "Create Solid", None, QtGui.QApplication.UnicodeUTF8))
		self.label_2.setText(QtGui.QApplication.translate("Dialog", "<html><head/><body><p>To construct a part, only these dimensions are used: OD, ID and the pipe length. All other dimensions are used for inromation.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
	def initTable(self):
		# Read table data from CSV
		self.model = PartTableModel(self.table.headers, self.table.data)
		self.tableViewParts.setModel(self.model)
		
	def getSelectedPartName(self):
		sel = form.tableViewParts.selectionModel()
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
		"""User clicked OK"""
		# Update active document.  If there is none, show a warning message and do nothing.
		document = App.activeDocument()
		if document is not None:
		# Get suitable row from the the table.
			length = tu(self.lineEditLength.text())
			if length == "":
				msgBox = QtGui.QMessageBox()
				msgBox.setText("Set length.")
				msgBox.exec_()
				return

			partName = self.getSelectedPartName()
			createSolid = self.checkBoxCreateSolid.isChecked()
			if partName is not None:
				pipe = PipeFromTable(document, self.table)
				pipe.create(partName, length, createSolid)
				document.recompute()
				# Save user input for the next dialog call.
				self.saveInput()
				# Call parent class.
				super(MainDialog, self).accept()
			else:
				msgBox = QtGui.QMessageBox()
				msgBox.setText("Select part")
				msgBox.exec_()
		else:
			text = "I have not found any active document were I can create a pipe fitting.\n"\
				"Use menu File->New to create a new document first, "\
				"then try to create the pipe again."
			msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the pipe failed.", text)
			msgBox.exec_()

	def saveInput(self):
		"""Store user input for the next run."""
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		check = self.checkBoxCreateSolid.checkState()
		settings.setValue("checkBoxCreateSolid", int(check))
		settings.setValue("LastSelectedPartName", self.getSelectedPartName())
		settings.setValue("lineEditLength", self.lineEditLength.text())
		settings.sync()

	def restoreInput(self):
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)
		checkState = QtCore.Qt.CheckState(int(settings.value("checkBoxCreateSolid")))
		self.checkBoxCreateSolid.setCheckState(checkState)
		self.selectPartByName(settings.value("LastSelectedPartName"))
		text = settings.value("lineEditLength")
		if text is not None:
			self.lineEditLength.setText(text)

def GuiCheckTable():
	# Check if the CSV file exists.
	if os.path.isfile(CSV_TABLE_PATH) == False:
		text = "This macro requires %s  but this file does not exist."%(CSV_TABLE_PATH)
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the pipe failed.", text)
		msgBox.exec_()
		exit(1) # Error
        FreeCAD.Console.PrintMessage("Trying to load CSV file with dimensions: %s"%CSV_TABLE_PATH) 
	table = CsvTable(DIMENSIONS_USED)
	table.load(CSV_TABLE_PATH)

	if table.hasValidData == False:
		text = 'Invalid %s.\n'\
			'It must contain columns %s.'%(CSV_TABLE_PATH, ", ".join(DIMENSIONS_USED))
		msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the pipe failed.", text)
		msgBox.exec_()
		exit(1) # Error
	return table

#table = GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#form = MainDialog(table)


