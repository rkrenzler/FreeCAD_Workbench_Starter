#***************************************************************************
#*                                                                         *
#*  This file is part of the FreeCAD_Workbench_Starter project.            *
#*                                                                         *
#*                                                                         *
#*  Copyright (C) 2017                                                     *
#*  Stephen Kaiser <freesol29@gmail.com>                                   *
#*                                                                         *
#*  This library is free software; you can redistribute it and/or          *
#*  modify it under the terms of the GNU Lesser General Public             *
#*  License as published by the Free Software Foundation; either           *
#*  version 2 of the License, or (at your option) any later version.       *
#*                                                                         *
#*  This library is distributed in the hope that it will be useful,        *
#*  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU      *
#*  Lesser General Public License for more details.                        *
#*                                                                         *
#*  You should have received a copy of the GNU Lesser General Public       *
#*  License along with this library; if not, If not, see                   *
#*  <http://www.gnu.org/licenses/>.                                        *
#*                                                                         *
#*                                                                         *
#***************************************************************************

import FreeCAD
import Part
import OsePipingBase
import OsePiping.CouplingGui as CouplingGui
import OsePiping.PipeGui as PipeGui
import OsePiping.BushingGui as BushingGui
import OsePiping.TeeGui as TeeGui
import OsePiping.CornerGui as CornerGui
import OsePiping.ElbowGui as ElbowGui
import OsePiping.CrossGui as CrossGui
import OsePiping.SweepElbowGui as SweepElbowGui
import OsePiping.CreatePartGui as CreatePartGui

from FreeCAD import Gui

class OsePiping_PipeClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreatePipe.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a pipe",
                'ToolTip' : "Adds a pipe into the center of the document."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = PipeGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
 #       FreeCAD.Console.PrintMessage("Showing pipe UI.")
	form = PipeGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OsePiping_CouplingClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateCoupling.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a coupling",
                'ToolTip' : "Adds a coupling."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = CouplingGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer coupling UI.")
	form = CouplingGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OsePiping_BushingClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateBushing.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a bushing",
                'ToolTip' : "Adds a bushing."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = BushingGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer bushing UI.")
	form = BushingGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

class OsePiping_ElbowClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateElbow.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add an elbow",
                'ToolTip' : "Adds an elbow."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = ElbowGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer elbow UI.")
	form = ElbowGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

class OsePiping_SweepElbowClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateSweepElbow.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a sweep elbow",
                'ToolTip' : "Adds a sweep elbow."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = SweepElbowGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
	form = SweepElbowGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

class OsePiping_TeeClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateTee.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a tee",
                'ToolTip' : "Adds a tee."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = TeeGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer tee UI.")
	form = TeeGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OsePiping_CornerClass():

    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateCorner.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a outer corner",
                'ToolTip' : "Adds a outer corner."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = CornerGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer corner UI.")
	form = CornerGui.MainDialog(doc, table)
	form.showForCreation()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

class OsePiping_CrossClass():
    def GetResources(self):
        return {'Pixmap'  : OsePipingBase.ICON_PATH + '/CreateCross.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a cross",
                'ToolTip' : "Adds a cross."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = CrossGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer corner UI.")
	form = CrossGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

Gui.addCommand('OsePiping_Pipe', OsePiping_PipeClass())
Gui.addCommand('OsePiping_Coupling', OsePiping_CouplingClass())
Gui.addCommand('OsePiping_Bushing', OsePiping_BushingClass())
Gui.addCommand('OsePiping_Elbow', OsePiping_ElbowClass())
Gui.addCommand('OsePiping_SweepElbow', OsePiping_SweepElbowClass())
Gui.addCommand('OsePiping_Tee', OsePiping_TeeClass())
Gui.addCommand('OsePiping_Corner', OsePiping_CornerClass())
Gui.addCommand('OsePiping_Cross', OsePiping_CrossClass())
