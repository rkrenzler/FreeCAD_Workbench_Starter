# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 Januar 2018
# Create a cross-fitting.

import OsePiping.Cross as Cross
import OsePiping.CreatePartGui as CreatePartGui
import OsePiping.Piping as Piping


class MainDialog(CreatePartGui.BaseDialog):
    def __init__(self, document, table):
        params = CreatePartGui.DialogParams()
        params.document = document
        params.table = table
        params.dialogTitle = "Create Cross"
        params.fittingType = "Cross"
        params.dimensionsPixmap = "cross-dimensions.png"
        params.explanationText = """<html><head/><body><p>
To construct an cross only these dimensions are used:
G, G1, H, H1, L, L1, M, M1, POD, POD1, PThk, Pthk1.
In Additinon, Flamingo uses the Schedule dimension if it is present in the table.
All other dimensions are used for inromation only.
</p></body></html>"""
        params.settingsName = "cross user input"
        params.keyColumnName = "PartNumber"
        super(MainDialog, self).__init__(params)

    def createNewPart(self, document, table, partName, outputType):
        builder = Cross.CrossFromTable(self.params.document, self.params.table)
        part = builder.create(partName, outputType)
        if outputType == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO:
            self.moveFlamingoPartToSelection(document, part)
        return part


def GuiCheckTable():
    return CreatePartGui.GuiCheckTable(Cross.CSV_TABLE_PATH, Cross.DIMENSIONS_USED)
