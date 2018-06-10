# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 06 February 2018
# Create a tee-fitting.

import Tee
import CreatePartGui


class MainDialog(CreatePartGui.BaseDialog):
	def __init__(self, document, table):
		params = CreatePartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Tee"
		params.fittingType = "Tee"
		params.dimensionsPixmap = "tee-dimensions.png"
		params.explanationText = "<html><head/><body><p>Only dimensions used are: M, M1, M2, G, G1, G2, H, H1, H2, POD, POD1, POD2, PThk, PThk1, PThk2. All other dimensions are used for inromation.</p></body></html>"
		params.settingsName = "tee user input"
		params.keyColumnName = "PartNumber"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = Tee.TeeFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)


def GuiCheckTable():
	return CreatePartGui.GuiCheckTable(Tee.CSV_TABLE_PATH, Tee.DIMENSIONS_USED)
