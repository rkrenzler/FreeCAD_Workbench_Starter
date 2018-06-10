# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 Januar December 2018
# Create a coupling fitting using a gui.

import Coupling
import CreatePartGui


class MainDialog(CreatePartGui.BaseDialog):
	def __init__(self, document, table):
		params = CreatePartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Coupling"
		params.fittingType = "Coupling"
		params.dimensionsPixmap = "coupling-dimensions.png"
		params.explanationText = "<html><head/><body><p>To construct a coupling we use these dimensions, elbow only these dimensions are used: alpha, L, N,  M, M1, POD, POD1, PThk, and PThk1. In Additinon, Flamingo uses the Schedule dimension if it is present in the table. All other dimensions are used for inromation only. </p></body></html>"
		params.settingsName = "coupling user input"
		params.keyColumnName = "PartNumber"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = Coupling.CouplingFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)


def GuiCheckTable():
	return CreatePartGui.GuiCheckTable(Coupling.CSV_TABLE_PATH, Coupling.DIMENSIONS_USED)
