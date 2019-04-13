# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 30 March February 2018
# Create a sweepElbow-fitting.

import OsePiping.SweepElbow as SweepElbow
import OsePiping.CreatePartGui as CreatePartGui
import OsePiping.Piping as Piping


class MainDialog(CreatePartGui.BaseDialog):
    def __init__(self, document, table):
        params = CreatePartGui.DialogParams()
        params.document = document
        params.table = table
        params.dialogTitle = "Create Sweep Elbow"
        params.fittingType = "SweepElbow"
        params.dimensionsPixmap = "sweep-elbow-dimensions.png"
        params.explanationText = """<html><head/><body><p>
Only dimensions used are:
BendAngle, H, J, M POD, PThk.
All other dimensions are used for inromation.
</p></body></html>"""
        params.settingsName = "sweep elbow user input"
        params.keyColumnName = "PartNumber"
        super(MainDialog, self).__init__(params)

    def createNewPart(self, document, table, partName, outputType):
        builder = SweepElbow.SweepElbowFromTable(
            self.params.document, self.params.table)
        part = builder.create(partName, outputType)
        if outputType == Piping.OUTPUT_TYPE_FLAMINGO:
            self.moveFlamingoPartToSelection(document, part)
        return part


def GuiCheckTable():
    return CreatePartGui.GuiCheckTable(SweepElbow.CSV_TABLE_PATH, SweepElbow.DIMENSIONS_USED)
