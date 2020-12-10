# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 16 December 2017
# Create a elbow-fitting.

import OsePiping.Elbow as Elbow
import OsePiping.CreatePartGui as CreatePartGui
import OsePiping.Piping as Piping


class MainDialog(CreatePartGui.BaseDialog):
    def __init__(self, document, table):
        params = CreatePartGui.DialogParams()
        params.document = document
        params.table = table
        params.dialogTitle = "Create Elbow"
        params.fittingType = "Elbow"
        params.dimensionsPixmap = "elbow-dimensions.png"
        params.explanationText = """<html><head/><body><p>
To construct an elbow only these dimensions are used:
BendingAngle, H, J, M, POD, and PThk.
In Additinon, Dodo/Flamingo uses the Schedule dimension if it is present in the table.
All other dimensions are used for inromation only.
</p></body></html>"""
        params.settingsName = "elbow user input"
        params.keyColumnName = "PartNumber"
        super(MainDialog, self).__init__(params)

    def createNewPart(self, document, table, partName, outputType):
        builder = Elbow.ElbowFromTable(self.params.document, self.params.table)
        part = builder.create(partName, outputType)
        if outputType == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO:
            self.moveFlamingoPartToSelection(document, part)
        return part


def GuiCheckTable():
    return CreatePartGui.GuiCheckTable(Elbow.CSV_TABLE_PATH, Elbow.DIMENSIONS_USED)
