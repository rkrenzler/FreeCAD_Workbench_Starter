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

import FreeCAD, Part, OSEBase
import pipeGui, couplingGui, bushingGui, teeGui
import outerCornerGui
from FreeCAD import Gui

class OSE_CreatePipeClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreatePipe.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a pipe",
                'ToolTip' : "Adds a pipe into the center of the document."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = pipeGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
 #       FreeCAD.Console.PrintMessage("Showing pipe UI.")
	form = pipeGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OSE_CreateCouplingClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreateCoupling.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a coupling",
                'ToolTip' : "Adds a coupling."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = couplingGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer coupling UI.")
	form = couplingGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OSE_CreateBushingClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreateBushing.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a bushing",
                'ToolTip' : "Adds a bushing."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = bushingGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer bushing UI.")
	form = bushingGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

class OSE_CreateTeeClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreateTee.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a tee",
                'ToolTip' : "Adds a tee."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = teeGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer tee UI.")
	form = teeGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True


class OSE_CreateOuterCornerClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreateOuterCorner.svg', # the name of a svg file available in the resources
#                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a outer corner",
                'ToolTip' : "Adds a outer corner."}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = outerCornerGui.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
#        FreeCAD.Console.PrintMessage("Showing outer corner UI.")
	form = outerCornerGui.MainDialog(doc, table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

Gui.addCommand('OSE_CreatePipe', OSE_CreatePipeClass())
Gui.addCommand('OSE_CreateCoupling', OSE_CreateCouplingClass())
Gui.addCommand('OSE_CreateBushing', OSE_CreateBushingClass())
Gui.addCommand('OSE_CreateTee', OSE_CreateTeeClass())
Gui.addCommand('OSE_CreateOuterCorner', OSE_CreateOuterCornerClass())
