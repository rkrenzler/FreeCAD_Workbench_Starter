# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 Januar 2018
# Create a cross-fitting.

import math
import os.path

import cross
import createPartGui

import OSEBase
from cross import *
from piping import *
import pipingGui

class MainDialog(createPartGui.BaseDialog):
	def __init__(self, document, table):
		params = createPartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Cross"
		params.fittingType = "Cross"
		params.dimensionsPixmap = "cross-dimensions.png"
		params.explanationText = "<html><head/><body><p>To construct an cross only these dimensions are used: G, G1, H, H1, L, L1, M, M1, POD, POD1, PThk, Pthk1. In Additinon, Flamingo uses the Schedule dimension if it is present in the table. All other dimensions are used for inromation only. </p></body></html>"
		params.settingsName = "cross user input"
		params.keyColumnName = "PartNumber"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = cross.CrossFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)
		
def GuiCheckTable():
	return createPartGui.GuiCheckTable2(cross.CSV_TABLE_PATH, cross.DIMENSIONS_USED)

