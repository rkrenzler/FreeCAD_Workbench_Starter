# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 06 February 2018
# Create a tee-fitting.

import tee
import createPartGui

class MainDialog(createPartGui.BaseDialog):
	def __init__(self, document, table):
		params = createPartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Tee"
		params.fittingType = "Tee"
		params.dimensionsPixmap = "tee-dimensions.png"
		params.explanationText = "<html><head/><body><p>Only dimensions used are: M, M1, G, G1, G2, H1, H1, H2, POD, POD1, PID, PID2. All other dimensions are used for inromation.</p></body></html>"
		params.settingsName = "tee user input"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = tee.TeeFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)

def GuiCheckTable():
	return createPartGui.GuiCheckTable(tee.CSV_TABLE_PATH, tee.DIMENSIONS_USED)
