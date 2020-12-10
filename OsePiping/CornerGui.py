# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 09 February 2018
# Create a corner-fitting.

import OsePiping.Corner as Corner
import OsePiping.CreatePartGui as CreatePartGui
import OsePiping.Piping as Piping


class MainDialog(CreatePartGui.BaseDialog):
    def __init__(self, document, table):
        params = CreatePartGui.DialogParams()
        params.document = document
        params.table = table
        params.dialogTitle = "Create corner"
        params.selectionDialogTitle = "Select corner"
        params.fittingType = "Corner"
        params.dimensionsPixmap = "corner-dimensions.png"
        params.explanationText = """<html><head/><body><p>
To construct a part, only these dimensions are used:
G, H, M, POD and PThk.
All other dimensions are used for inromation.
</p></body></html>"""
        params.settingsName = "corner user input"
        params.keyColumnName = "PartNumber"
        super(MainDialog, self).__init__(params)

    def createNewPart(self, document, table, partName, outputType):
        builder = Corner.CornerFromTable(self.params.document, self.params.table)
        part = builder.create(partName, outputType)
        if outputType == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO:
            self.moveFlamingoPartToSelection(document, part)
        return part


def GuiCheckTable():
    return CreatePartGui.GuiCheckTable(Corner.CSV_TABLE_PATH, Corner.DIMENSIONS_USED)
