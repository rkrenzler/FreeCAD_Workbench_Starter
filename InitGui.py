#***************************************************************************
#*                                                                         *
#*  This file is part of the OSE project.            *
#*                                                                         *
#*                                                                         *
#*  Copyright (C) 2017                                                     *
#*  Ruslan Krenzler                                                        *
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

class OSE_PipingWorkbench (Workbench):

    MenuText = "OSE Piping Workbench"
    ToolTip = "A piping workbench for Open Source Ecology part design"
    #Icon = """paste here the contents of a 16x16 xpm icon"""


    def Initialize(self):
        "This function is executed when FreeCAD starts"
        import OSEBase, OSE_CommandButton # import here all the needed files that create your FreeCAD commands
        self.list = ["OSE_CommandButton"] # A list of command names created in the line above
        self.appendToolbar("Piping", self.list) # creates a new toolbar with your commands
        self.appendMenu("Command Menu", self.list) # creates a new menu

        #FreeCADGui.addIconPath(":/Resources/icons")
        #FreeCADGui.addLanguagePath(":/translations")
        #FreeCADGui.addPreferencePage(":/ui/preferences-ose.ui","OSE")
        #FreeCADGui.addPreferencePage(":/ui/preferences-osedefaults.ui","OSE")
        #self.appendMenu(["An existing Menu", "My submenu"], self.list) # appends a submenu to an existing menu

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("Piping commands", self.list) # add commands to the context menu

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"
       
Gui.addWorkbench(OSE_PipingWorkbench())
