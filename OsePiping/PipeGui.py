# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04 February 2018
# Create a pipe.

from PySide import QtCore, QtGui
import FreeCAD
import OsePiping.Pipe as Pipe
import OsePiping.Piping as Piping
import OsePiping.CreatePartGui as CreatePartGui


class MainDialog(CreatePartGui.BaseDialog):
    def __init__(self, document, table):
        params = CreatePartGui.DialogParams()
        params.document = document
        params.table = table
        params.dialogTitle = "Create Pipe"
        params.fittingType = "Pipe"
        params.dimensionsPixmap = "pipe-dimensions.png"
        params.explanationText = """<html><head/><body><p>
To construct a part, only these dimensions are used:
OD, Thk and the pipe height (length).
Dodo/Flamingo also uses Schedule and DN if they are present in the table. All other dimensions are used for inromation.
</p></body></html>"""
        params.keyColumnName = "PartNumber"
        super(MainDialog, self).__init__(params)

    def createLengthWidget(self, Dialog):
        self.widgetLengthInput = QtGui.QWidget(Dialog)
        self.widgetLengthInput.setMinimumSize(QtCore.QSize(0, 27))
        self.widgetLengthInput.setObjectName("widgetLengthInput")
        self.labelHeight = QtGui.QLabel(self.widgetLengthInput)
        self.labelHeight.setGeometry(QtCore.QRect(0, 0, 121, 27))
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.labelHeight.sizePolicy().hasHeightForWidth())
        self.labelHeight.setSizePolicy(sizePolicy)
        self.labelHeight.setMinimumSize(QtCore.QSize(0, 27))
        self.labelHeight.setMaximumSize(QtCore.QSize(200, 16777215))
        self.labelHeight.setObjectName("labelHeight")
        self.lineEditLength = QtGui.QLineEdit(self.widgetLengthInput)
        self.lineEditLength.setGeometry(QtCore.QRect(120, 0, 91, 27))
        self.lineEditLength.setObjectName("lineEditLength")
        # Add text.
        self.labelHeight.setText(QtGui.QApplication.translate(
            "Dialog", "Height (Length):", None, CreatePartGui.UnicodeUTF8()))
        self.lineEditLength.setText(QtGui.QApplication.translate(
            "Dialog", "1 m", None, CreatePartGui.UnicodeUTF8()))
        return self.widgetLengthInput

    # Add customized UI elements after the type. That is the length ui
    def setupUi(self, Dialog):
        super(MainDialog, self).setupUi(Dialog)
        # Append UI for pipe length input after the output type block.
        after_index = self.verticalLayout.indexOf(self.outputTypeWidget) + 1
        widget = self.createLengthWidget(Dialog)
        self.verticalLayout.insertWidget(after_index, widget)

    def saveAdditionalData(self, settings):
        settings.setValue("lineEditLength", self.lineEditLength.text())

    def restoreAdditionalInput(self, settings):
        text = settings.value("lineEditLength")
        if text is not None:
            self.lineEditLength.setText(text)

    def createNewPart(self, document, table, partName, outputType):
        length = FreeCAD.Units.parseQuantity(self.lineEditLength.text())
        builder = Pipe.PipeFromTable(self.params.document, self.params.table)
        part = builder.create(partName, length, outputType)
        if outputType == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO:
            self.moveFlamingoPartToSelection(document, part)
        return part


def GuiCheckTable():
    return CreatePartGui.GuiCheckTable(Pipe.CSV_TABLE_PATH, Pipe.DIMENSIONS_USED)
