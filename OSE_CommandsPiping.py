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
import pipe
from FreeCAD import Gui

class OSE_CreatePipeClass():
    """Command to add the printer frame"""

    def GetResources(self):
        return {'Pixmap'  : OSEBase.ICON_PATH + '/CreatePipe.svg', # the name of a svg file available in the resources
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Add a pipe",
                'ToolTip' : "Adds a pipe"}

    def Activated(self):
        "Do something here when button is clicked"
        if Gui.ActiveDocument == None:
            FreeCAD.newDocument()
        doc=FreeCAD.activeDocument()
	table = pipe.GuiCheckTable() # Open a CSV file, check its content, and return it as a CsvTable object.
        FreeCAD.Console.PrintMessage("Showing pipe UI.")
	form = pipe.MainDialog(table)
	form.exec_()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

Gui.addCommand('OSE_CreatePipe', OSE_CreatePipeClass()) 
