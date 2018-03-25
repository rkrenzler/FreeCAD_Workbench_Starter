# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 16 December 2017
# Create a elbow-fitting.


import elbow
import createPartGui


class MainDialog(createPartGui.BaseDialog):
	def __init__(self, document, table):
		params = createPartGui.DialogParams()
		params.document = document
		params.table = table
		params.dialogTitle = "Create Elbow"
		params.fittingType = "Elbow"
		params.dimensionsPixmap = "elbow-dimensions.png"
		params.explanationText = "<html><head/><body><p>To construct an elbow only these dimensions are used: alpha, H, J, M, PID and POD. In Additinon, Flamingo uses the Schedule dimension if it is present in the table. All other dimensions are used for inromation only. </p></body></html>"
		params.settingsName = "elbow user input"
		super(MainDialog, self).__init__(params)

	def createNewPart(self, document, table, partName, outputType):
			builder = elbow.ElbowFromTable(self.params.document, self.params.table)
			return builder.create(partName, outputType)
		
def GuiCheckTable():
	return createPartGui.GuiCheckTable(elbow.CSV_TABLE_PATH, elbow.DIMENSIONS_USED)

