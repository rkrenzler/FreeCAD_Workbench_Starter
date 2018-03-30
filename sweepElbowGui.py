# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 30 March February 2018
# Create a sweepElbow-fitting.

import sweepElbow
import createPartGui


class MainDialog(createPartGui.BaseDialog):
	def __init__(self, document, table):
		params = createPartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Sweep Elbow"
		params.fittingType = "SweepElbow"
		params.dimensionsPixmap = "sweep-elbow-dimensions.png"
		params.explanationText = "<html><head/><body><p>Only dimensions used are: G, H, M POD, PThk. All other dimensions are used for inromation.</p></body></html>"
		params.settingsName = "sweep elbow user input"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = sweepElbow.SweepElbowFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)

def GuiCheckTable():
	return createPartGui.GuiCheckTable(sweepElbow.CSV_TABLE_PATH, sweepElbow.DIMENSIONS_USED)
