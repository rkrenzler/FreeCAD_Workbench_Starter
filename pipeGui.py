# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04 February 2018
# Create a pipe.

import math
import csv
import os.path

from PySide import QtCore, QtGui
import FreeCAD

import OSEBase
from pipe import *
from piping import *
import pipingGui


class MainDialog(QtGui.QDialog):
	QSETTINGS_APPLICATION = "OSE piping workbench"
	QSETTINGS_NAME = "pipe user input"

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

		if HasFlamingoSupport():
			self.radioButtonFlamingo.setEnabled(True)			
		else:
			self.radioButtonFlamingo.setEnabled(False)
			
		self.show()

# The following lines are from QtDesigner .ui-file processed by pyside-uic
# pyside-uic --indent=0 create-pipe.ui -o tmp.py
# You need to adjust image paths to
# os.path.join(OSEBase.IMAGE_PATH, "pipe-dimensions.png")
	def setupUi(self, Dialog):
		Dialog.setObjectName("Dialog")
		Dialog.resize(836, 633)
		self.verticalLayout = QtGui.QVBoxLayout(Dialog)
		self.verticalLayout.setObjectName("verticalLayout")
		self.horizontalWidget = QtGui.QWidget(Dialog)
		self.horizontalWidget.setMinimumSize(QtCore.QSize(0, 55))
		self.horizontalWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
		self.horizontalWidget.setObjectName("horizontalWidget")
		self.groupBox = QtGui.QGroupBox(self.horizontalWidget)
		self.groupBox.setGeometry(QtCore.QRect(10, 0, 263, 58))
		self.groupBox.setObjectName("groupBox")
		self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
		self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
		self.horizontalLayout.setObjectName("horizontalLayout")
		self.radioButtonSolid = QtGui.QRadioButton(self.groupBox)
		self.radioButtonSolid.setEnabled(True)
		self.radioButtonSolid.setChecked(True)
		self.radioButtonSolid.setObjectName("radioButtonSolid")
		self.horizontalLayout.addWidget(self.radioButtonSolid)
		self.radioButtonFlamingo = QtGui.QRadioButton(self.groupBox)
		self.radioButtonFlamingo.setEnabled(False)
		self.radioButtonFlamingo.setChecked(False)
		self.radioButtonFlamingo.setObjectName("radioButtonFlamingo")
		self.horizontalLayout.addWidget(self.radioButtonFlamingo)
		self.radioButtonParts = QtGui.QRadioButton(self.groupBox)
		self.radioButtonParts.setObjectName("radioButtonParts")
		self.horizontalLayout.addWidget(self.radioButtonParts)
		self.verticalLayout.addWidget(self.horizontalWidget)
		self.widgetHeight = QtGui.QWidget(Dialog)
		self.widgetHeight.setMinimumSize(QtCore.QSize(0, 27))
		self.widgetHeight.setObjectName("widgetHeight")
		self.labelHeight = QtGui.QLabel(self.widgetHeight)
		self.labelHeight.setGeometry(QtCore.QRect(0, 0, 121, 27))
		sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.labelHeight.sizePolicy().hasHeightForWidth())
		self.labelHeight.setSizePolicy(sizePolicy)
		self.labelHeight.setMinimumSize(QtCore.QSize(0, 27))
		self.labelHeight.setMaximumSize(QtCore.QSize(200, 16777215))
		self.labelHeight.setObjectName("labelHeight")
		self.lineEditLength = QtGui.QLineEdit(self.widgetHeight)
		self.lineEditLength.setGeometry(QtCore.QRect(120, 0, 91, 27))
		self.lineEditLength.setObjectName("lineEditLength")
		self.verticalLayout.addWidget(self.widgetHeight)
		self.horizontalLayoutWithTable = QtGui.QHBoxLayout()
		self.horizontalLayoutWithTable.setContentsMargins(-1, -1, -1, 19)
		self.horizontalLayoutWithTable.setObjectName("horizontalLayoutWithTable")
		self.labelImage = QtGui.QLabel(Dialog)
		self.labelImage.setText("")
		self.labelImage.setPixmap(os.path.join(OSEBase.IMAGE_PATH, "pipe-dimensions.png"))
		self.labelImage.setAlignment(QtCore.Qt.AlignCenter)
		self.labelImage.setObjectName("labelImage")
		self.horizontalLayoutWithTable.addWidget(self.labelImage)
		self.tableViewParts = QtGui.QTableView(Dialog)
		self.tableViewParts.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.tableViewParts.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableViewParts.setObjectName("tableViewParts")
		self.horizontalLayoutWithTable.addWidget(self.tableViewParts)
		self.verticalLayout.addLayout(self.horizontalLayoutWithTable)
		self.labelExplanation = QtGui.QLabel(Dialog)
		self.labelExplanation.setTextFormat(QtCore.Qt.AutoText)
		self.labelExplanation.setWordWrap(True)
		self.labelExplanation.setObjectName("labelExplanation")
		self.verticalLayout.addWidget(self.labelExplanation)
		self.buttonBox = QtGui.QDialogButtonBox(Dialog)
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		self.verticalLayout.addWidget(self.buttonBox)

		self.retranslateUi(Dialog)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
		QtCore.QMetaObject.connectSlotsByName(Dialog)
		Dialog.setTabOrder(self.radioButtonSolid, self.radioButtonFlamingo)
		Dialog.setTabOrder(self.radioButtonFlamingo, self.radioButtonParts)
		Dialog.setTabOrder(self.radioButtonParts, self.lineEditLength)
		Dialog.setTabOrder(self.lineEditLength, self.buttonBox)

	def retranslateUi(self, Dialog):
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create pipe", None, QtGui.QApplication.UnicodeUTF8))
		self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Output type:", None, QtGui.QApplication.UnicodeUTF8))
		self.radioButtonSolid.setText(QtGui.QApplication.translate("Dialog", "Solid", None, QtGui.QApplication.UnicodeUTF8))
		self.radioButtonFlamingo.setText(QtGui.QApplication.translate("Dialog", "Flamingo", None, QtGui.QApplication.UnicodeUTF8))
		self.radioButtonParts.setText(QtGui.QApplication.translate("Dialog", "Parts", None, QtGui.QApplication.UnicodeUTF8))
		self.labelHeight.setText(QtGui.QApplication.translate("Dialog", "Height (Length):", None, QtGui.QApplication.UnicodeUTF8))
		self.lineEditLength.setText(QtGui.QApplication.translate("Dialog", "1 m", None, QtGui.QApplication.UnicodeUTF8))
		self.labelExplanation.setText(QtGui.QApplication.translate("Dialog", "<html><head/><body><p>To construct a part, only these dimensions are used: OD, Thk and the pipe height (length). Flamingo also uses Schedule and DN if they are present in the table. All other dimensions are used for inromation.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
	def initTable(self):
		# Read table data from CSV
		self.model = pipingGui.PartTableModel(self.table.headers, self.table.data)
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
		# If there is no active document, show a warning message and exit dialog.
		if self.document is None:
			text = "I have not found any active document were I can create a corner fitting.\n"\
				"Use menu File->New to create a new document first, "\
				"then try to create the corner fitting again."
			msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the corner fitting failed.", text)
			msgBox.exec_()
			super(MainDialog, self).accept()
			return

		# Get suitable row from the the table.
		length = tu(self.lineEditLength.text())
		if length == "":
			msgBox = QtGui.QMessageBox()
			msgBox.setText("Set length.")
			msgBox.exec_()
			return

		partName = self.getSelectedPartName()

		if partName is not None:
			outputType = self.getOutputType()
			pipe = PipeFromTable(self.document, self.table)
			part = pipe.create(partName, length, outputType)
			if part is not None:
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

		if self.radioButtonFlamingo.isChecked():
			settings.setValue("radioButtonsOutputType", OUTPUT_TYPE_FLAMINGO)
		elif self.radioButtonParts.isChecked():
			settings.setValue("radioButtonsOutputType", OUTPUT_TYPE_PARTS)
		else : # Default is solid.
			settings.setValue("radioButtonsOutputType", OUTPUT_TYPE_SOLID)
		
		settings.setValue("LastSelectedPartName", self.getSelectedPartName())
		settings.setValue("lineEditLength", self.lineEditLength.text())
		
		settings.sync()

	def restoreInput(self):
		settings = QtCore.QSettings(MainDialog.QSETTINGS_APPLICATION, MainDialog.QSETTINGS_NAME)

		output = int(settings.value("radioButtonsOutputType", OUTPUT_TYPE_SOLID))
		if output == OUTPUT_TYPE_FLAMINGO and HasFlamingoSupport():
			self.radioButtonFlamingo.setChecked(True)			
		elif  output == OUTPUT_TYPE_PARTS:
			self.radioButtonParts.setChecked(True)
		else: # Default is solid. output == OUTPUT_TYPE_SOLID
			self.radioButtonSolid.setChecked(True)

		self.selectPartByName(settings.value("LastSelectedPartName"))
		text = settings.value("lineEditLength")
		if text is not None:
			self.lineEditLength.setText(text)

	def showForSelection(self, partName=None):
		""" Show pipe dialog, to select pipe and not to create it.
		:param partName: name of the part to be selected. Use None if you do not want to select
		anything.
		"""
		# If required select
		self.selectionMode = True
		self.setWindowTitle(QtGui.QApplication.translate("Dialog", "Select pipe", None, QtGui.QApplication.UnicodeUTF8))
		self.selectedPart = None
		if partName is not None:
			self.selectPartByName(partName)
		self.exec_()
		return self.selectedPart
		
	def showForCreation(self):
		self.selectionMode = False
		Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create pipe", None, QtGui.QApplication.UnicodeUTF8))
		self.exec_()
		
	def getOutputType(self):
		if self.radioButtonFlamingo.isChecked():
			return OUTPUT_TYPE_FLAMINGO
		elif self.radioButtonParts.isChecked():
			return OUTPUT_TYPE_PARTS
		else: # Default is solid.
			return OUTPUT_TYPE_SOLID

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

#doc=FreeCAD.activeDocument()
#table = GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#form = MainDialog(doc, table)



