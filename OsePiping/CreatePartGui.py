# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 25 March 2018
# Create a part with dimensions stored in a table.
# Use the BaseDialog to derive other

import os.path
from PySide import QtCore, QtGui
import FreeCAD
import FreeCADGui
import OsePipingBase
import OsePiping.Piping as Piping
import OsePiping.PipingGui as PipingGui
# import rpdb2
import OsePiping.Port as Port


class DialogParams:
    def __init__(self):
        self.document = None
        self.table = None
        self.dialogTitle = None
        self.selectionDialogTitle = None
        self.fittingType = None  # Elbow, Tee, Coupling etc..
        self.dimensionsPixmap = None
        self.explanationText = None
        self.settingsName = None
        self.selectionMode = False
        # Old style column name for the unique ID of the part.
        self.keyColumnName = "Name"


def UnicodeUTF8():
    """Return UnicodeUTF8 if it is defined or 0 otherwise.

    The old FreeCAD code for Qt4 uses enum QtGui.QApplication.UnicodeUTF8
    but it is not defined for new Qt5. With Qt5 we must to use 0 instead.
    """
    if hasattr(QtGui.QApplication, "UnicodeUTF8"):
        QtGui.QApplication.UnicodeUTF8
    else:
        return 0


class BaseDialog(QtGui.QDialog):
    QSETTINGS_APPLICATION = "OSE piping workbench"

    def __init__(self, params):
        super(BaseDialog, self).__init__()
        self.params = params
        self.initUi()
        if Piping.HasFlamingoSupport() and not Piping.HasDodoSupport():
            self.labelFlamingoIsDepricated.show()
        else:
            self.labelFlamingoIsDepricated.hide()

        if Piping.HasDodoSupport() or Piping.HasFlamingoSupport():
            self.radioButtonDodoFlamingo.setEnabled(True)
        else:
            self.radioButtonDodoFlamingo.setEnabled(False)

    def initUi(self):
        self.result = -1
        self.setupUi(self)
        # Fill table with dimensions.
        self.initTable()

        # Restore previous user input. Ignore exceptions to prevent this part
        # part of the code to prevent GUI from starting, once settings are broken.
        try:
            self.restoreInput()
        except Exception as e:
            print("Could not restore old user input!")
            print(e)
        try:
            self.restoreWindowGeometry()
        except Exception as e:
            print("Could not restore old window geometry")
            print(e)
#            pass # Do nothing
        self.show()

# The following lines are from QtDesigner .ui-file processed by pyside-uic
# pyside-uic --indent=0 create-coupling.ui -o tmp.py
#
# The file paths needs to be adjusted manually. For example
# self.label.setPixmap(QtGui.QPixmap(GetMacroPath()+"coupling-dimensions.png"))
# os.path.join(OSEBasePiping.IMAGE_PATH, self.params.dimensionsPixmap)
# access datata in some special FreeCAD directory.
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(800, 733)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.labelFlamingoIsDepricated = QtGui.QLabel(Dialog)
        self.labelFlamingoIsDepricated.setEnabled(True)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.labelFlamingoIsDepricated.setFont(font)
        self.labelFlamingoIsDepricated.setTabletTracking(False)
        self.labelFlamingoIsDepricated.setAutoFillBackground(False)
        self.labelFlamingoIsDepricated.setObjectName("labelFlamingoIsDepricated")
        self.verticalLayout.addWidget(self.labelFlamingoIsDepricated)
        self.outputTypeWidget = QtGui.QWidget(Dialog)
        self.outputTypeWidget.setMinimumSize(QtCore.QSize(0, 55))
        self.outputTypeWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.outputTypeWidget.setObjectName("outputTypeWidget")
        self.groupBox = QtGui.QGroupBox(self.outputTypeWidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 0, 301, 58))
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.radioButtonSolid = QtGui.QRadioButton(self.groupBox)
        self.radioButtonSolid.setEnabled(True)
        self.radioButtonSolid.setChecked(True)
        self.radioButtonSolid.setObjectName("radioButtonSolid")
        self.horizontalLayout.addWidget(self.radioButtonSolid)
        self.radioButtonDodoFlamingo = QtGui.QRadioButton(self.groupBox)
        self.radioButtonDodoFlamingo.setEnabled(False)
        self.radioButtonDodoFlamingo.setChecked(False)
        self.radioButtonDodoFlamingo.setObjectName("radioButtonDodoFlamingo")
        self.horizontalLayout.addWidget(self.radioButtonDodoFlamingo)
        self.radioButtonParts = QtGui.QRadioButton(self.groupBox)
        self.radioButtonParts.setObjectName("radioButtonParts")
        self.horizontalLayout.addWidget(self.radioButtonParts)
        self.verticalLayout.addWidget(self.outputTypeWidget)
        self.tableViewParts = QtGui.QTableView(Dialog)
        self.tableViewParts.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection)
        self.tableViewParts.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.tableViewParts.setObjectName("tableViewParts")
        self.verticalLayout.addWidget(self.tableViewParts)
        self.labelExplanation = QtGui.QLabel(Dialog)
        self.labelExplanation.setTextFormat(QtCore.Qt.AutoText)
        self.labelExplanation.setWordWrap(True)
        self.labelExplanation.setObjectName("labelExplanation")
        self.verticalLayout.addWidget(self.labelExplanation)
        self.labelImage = QtGui.QLabel(Dialog)
        self.labelImage.setText("")
        self.labelImage.setPixmap(os.path.join(
            OsePipingBase.IMAGE_PATH, self.params.dimensionsPixmap))
        self.labelImage.setAlignment(QtCore.Qt.AlignCenter)
        self.labelImage.setObjectName("labelImage")
        self.verticalLayout.addWidget(self.labelImage)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(
            self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(
            self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate(
            "Dialog", self.params.dialogTitle, None, UnicodeUTF8()))
        self.labelFlamingoIsDepricated.setText(QtGui.QApplication.translate(
             "Dialog",
             "<html><head/><body><p><span style=\" color:#ef2929;\">The Flamingo-Workbench is deprecated, please install Dodo instead.</span></p></body></html>", None, -1))

        self.groupBox.setTitle(QtGui.QApplication.translate(
            "Dialog", "Output type:", None, UnicodeUTF8()))
        self.radioButtonSolid.setText(QtGui.QApplication.translate(
            "Dialog", "Solid", None, UnicodeUTF8()))
        self.radioButtonDodoFlamingo.setText(QtGui.QApplication.translate(
            "Dialog", "Dodo/Flamingo", None, UnicodeUTF8()))
        self.radioButtonParts.setText(QtGui.QApplication.translate(
            "Dialog", "Parts", None, UnicodeUTF8()))
        self.labelExplanation.setText(QtGui.QApplication.translate(
            "Dialog", self.params.explanationText, None, UnicodeUTF8()))

    def initTable(self):
        # Read table data from CSV
        self.model = PipingGui.PartTableModel(
            self.params.table.headers, self.params.table.data)
        self.model.keyColumnName = self.params.keyColumnName
        self.tableViewParts.setModel(self.model)

    def getSelectedPartName(self):
        sel = self.tableViewParts.selectionModel()
        if sel.isSelected:
            if len(sel.selectedRows()) > 0:
                rowIndex = sel.selectedRows()[0].row()
                return self.model.getPartKey(rowIndex)
        return None

    def selectPartByName(self, partName):
        """Select first row with a part with a name partName."""
        if partName is not None:
            row_i = self.model.getPartRowIndex(partName)
            if row_i >= 0:
                self.tableViewParts.selectRow(row_i)

    def createNewPart(self, document, table, partName, outputType):
        """This function must be implement by the parent class.

        It must return a part if succees and None if fail.
        """
        pass

    def acceptCreationMode(self):
        """User clicked OK."""
        # If there is no active document, show a warning message and do nothing.
        if self.params.document is None:
            text = "I have not found any active document were I can create an {0}.\n"\
                "Use menu File->New to create a new document first, "\
                "then try to create the {0} again.".format(
                    self.params.fittingType)
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Creating of the %s failed.".format(
                self.params.fittingType), text)
            msgBox.exec_()
            super(BaseDialog, self).accept()
            return

        # Get suitable row from the the table.
        partName = self.getSelectedPartName()

        if partName is not None:
            outputType = self.getOutputType()
            part = self.createNewPart(
                self.params.document, self.params.table, partName, outputType)
            if part is not None:
                self.params.document.recompute()
                # Save user input for the next dialog call.
                self.saveInput()
                # Save window Geometry
                self.saveWindowGeometry()
                # Call parent class.
                super(BaseDialog, self).accept()

        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Select part")
            msgBox.exec_()

    def acceptSelectionMode(self):
        self.selectedPart = self.getSelectedPartName()

        if self.selectedPart is None:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Select part")
            msgBox.exec_()
        else:
            super(BaseDialog, self).accept()

    def accept(self):
        if self.params.selectionMode:
            return self.acceptSelectionMode()
        else:
            self.acceptCreationMode()

    def saveAdditionalData(self, settings):
        pass

    def saveWindowGeometry(self):
        settings = QtCore.QSettings(BaseDialog.QSETTINGS_APPLICATION, self.params.settingsName)
        settings.setValue("Window/Geometry", self.saveGeometry())
        settings.sync()

    def restoreWindowGeometry(self):
        settings = QtCore.QSettings(BaseDialog.QSETTINGS_APPLICATION, self.params.settingsName)
        geometry = settings.value("Window/Geometry", None)
        if geometry is not None:
            self.restoreGeometry(geometry)

    def saveInput(self):
        """Store user input for the next run."""
        settings = QtCore.QSettings(
            BaseDialog.QSETTINGS_APPLICATION, self.params.settingsName)

        if self.radioButtonDodoFlamingo.isChecked():
            settings.setValue("radioButtonsOutputType",
                              Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO)
        elif self.radioButtonParts.isChecked():
            settings.setValue("radioButtonsOutputType",
                              Piping.OUTPUT_TYPE_PARTS)
        else:  # Default is solid.
            settings.setValue("radioButtonsOutputType",
                              Piping.OUTPUT_TYPE_SOLID)

        settings.setValue("LastSelectedPartNumber", self.getSelectedPartName())
        self.saveAdditionalData(settings)
        settings.sync()

    def restoreAdditionalInput(self, settings):
        pass

    def restoreInput(self):
        settings = QtCore.QSettings(
            BaseDialog.QSETTINGS_APPLICATION, self.params.settingsName)

        output = int(settings.value(
            "radioButtonsOutputType", Piping.OUTPUT_TYPE_SOLID))
        if output == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO  \
                and (Piping.HasDodoSupport() or Piping.HasFlamingoSupport()):
            self.radioButtonDodoFlamingo.setChecked(True)
        elif output == Piping.OUTPUT_TYPE_PARTS:
            self.radioButtonParts.setChecked(True)
        else:  # Default is solid. output == piping.OUTPUT_TYPE_SOLID
            self.radioButtonSolid.setChecked(True)

        self.selectPartByName(settings.value("LastSelectedPartNumber"))
        self.restoreAdditionalInput(settings)

    def getOutputType(self):
        if self.radioButtonDodoFlamingo.isChecked():
            return Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO
        elif self.radioButtonParts.isChecked():
            return Piping.OUTPUT_TYPE_PARTS
        else:  # Default is solid.
            return Piping.OUTPUT_TYPE_SOLID

    def showForSelection(self, partName=None):
        """Show pipe dialog, to select pipe and not to create it.

        :param partName: name of the part to be selected. Use None if you do not want to select
        anything.
        """
        # If required select
        self.params.selectionMode = True
        self.setWindowTitle(QtGui.QApplication.translate("Dialog", self.params.selectionDialogTitle,
                                                         None, UnicodeUTF8()))
        self.selectedPart = None
        if partName is not None:
            self.selectPartByName(partName)
        self.exec_()
        return self.selectedPart

    def showForCreation(self):
        self.params.selectionMode = False
        self.setWindowTitle(QtGui.QApplication.translate("Dialog", self.params.dialogTitle,
                                                         None, UnicodeUTF8()))
        self.exec_()

    @staticmethod
    def moveFlamingoPartToSelection(document, part):
        # Place the part with Dodo. If Dodo not found, use Flamingo instead.
        try:
            import pCmd as dfCmd
        except ModuleNotFoundError:
            import pipeCmd as dfCmd

        # Check if something is selected:
        if (len(FreeCADGui.Selection.getSelectionEx()) > 0
                and len(FreeCADGui.Selection.getSelectionEx()[-1].SubObjects) > 0):
            # Only a pipe has ports on creation. The other fitting can be accessed only through their objects.
            obj_of_part = document.getObject(part.Name)
            # Get last selection
            target = FreeCADGui.Selection.getSelectionEx()[-1].Object
            sub = FreeCADGui.Selection.getSelectionEx()[-1].SubObjects[-1]
            # Check if the part has ports.
            if obj_of_part.Ports == []:
                FreeCAD.Console.PrintMessage(
                    "The new part has an empty port list. Cannot move the part.\n")
                return
            try:
                # Check if the new part support advancedPorts
                # sel = FreeCADGui.Selection.getSelectionEx()
                # rpdb2.start_embedded_debugger("test")

                if Port.supportsAdvancedPort(obj_of_part) and Port.supportsAdvancedPort(target):
                    # Use new placement methos.
                    # Ports of the moved objects.

                    moved_ports = Port.extractAdvancedPorts(obj_of_part)
                    # Ports of the object to whom the object will be moved.
                    fix_ports = Port.extractAdvancedPorts(target)

                    # Find nearest pod.
                    closest_port = Port.getNearestPort(
                        target.Placement, fix_ports, sub.CenterOfMass)

                    # Now adjust new part to closet port
                    # print(obj_of_part.Placement)
                    obj_of_part.Placement = moved_ports[0].getPartPlacement(
                        target.Placement, closest_port)
                    # print(obj_of_part.Placement)
                else:
                    FreeCAD.Console.PrintWarning(
                        "Not all parts are OSE Fittings. I will try to use Dodo/Flamingo for positioning.\n")
                    nearest_ports = dfCmd.nearestPort(
                        target, sub.CenterOfMass)
                    if nearest_ports != []:
                        FreeCAD.Console.PrintMessage("Move new part to port {0}.\n".format(
                            nearest_ports[0]))
                        dfCmd.placeThePype(
                            obj_of_part, 0, target, nearest_ports[0])
                    else:
                        FreeCAD.Console.PrintMessage(
                            "No nearest ports found.\n")
            except Exception as e:
                FreeCAD.Console.PrintMessage(
                    "Positioning of Flamingo parts failed: {}\n".format(e))
        else:
            FreeCAD.Console.PrintMessage(
                "No flamngo parts selected. Insert to the standard position,\n")


# Before working with macros, try to load the dimension table.
def GuiCheckTable(tablePath, dimensionsUsed):
    # Check if the CSV file exists.
    if os.path.isfile(tablePath) is False:
        text = "This tablePath requires %s  but this file does not exist." % (
            tablePath)
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                   "Creating of the part failed.", text)
        msgBox.exec_()
        exit(1)  # Error

    # FreeCAD.Console.PrintMessage("Trying to load CSV file with dimensions: %s\n"%tablePath)
    table = Piping.CsvTable(dimensionsUsed)
    table.load(tablePath)

    if table.hasValidData is False:
        text = 'Invalid %s.\n'\
            'It must contain columns %s.' % (
                tablePath, ", ".join(dimensionsUsed))
        msgBox = QtGui.QMessageBox(
            QtGui.QMessageBox.Warning, "Creating of the part failed.", text)
        msgBox.exec_()
        exit(1)  # Error

    return table


# doc=FreeCAD.activeDocument()
# table = GuiCheckTable() # Open a CSV file, check its content, and return it as a piping.CsvTable object.
# form = BaseDialog(doc, table)
