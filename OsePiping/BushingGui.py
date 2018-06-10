# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 January 2018
# Create a bushing-fitting.

import Bushing
import CreatePartGui


class MainDialog(CreatePartGui.BaseDialog):
	def __init__(self, document, table):
		params = CreatePartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Bushing"
		params.fittingType = "Bushing"
		params.dimensionsPixmap = "bushing-dimensions.png"
		params.explanationText = "<html><head/><body><p>To construct a part, only these dimensions are used: L, N, POD, POD1 and PThk1. All other dimensions are used for inromation.</p></body></html>"
		params.settingsName = "bushing user input"
		params.keyColumnName = "PartNumber"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = Bushing.BushingFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)

def GuiCheckTable():
	return CreatePartGui.GuiCheckTable(Bushing.CSV_TABLE_PATH, Bushing.DIMENSIONS_USED)
