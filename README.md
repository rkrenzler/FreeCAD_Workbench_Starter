# OSE piping workbench

OSE Piping Workbench creates pipes and fittings. It is a part of Open Source Ecology and Open Source Ecology Germany. To use all its features install the Dodo-Workbench.

## Installation
Use the FreeCAD built-in [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons#1-builtin-addon-manager) to install this workbench.
To start the Addon Manger select menu **Tools -> Addon Manager**.

[See](https://www.freecadweb.org/wiki/How_to_install_additional_workbenches)

### Linux

````
$ mkdir ~/.FreeCAD/Mod
$ cd ~/.FreeCAD/Mod
$ git clone https://github.com/rkrenzler/ose-piping-workbench.git
````

# Screenshots #
![90°-elbow dialog](doc/workbench-screenshot.png)

# Detailed documentation #
https://wiki.freecadweb.org/OSE_Piping_Workbench

# Optional dependencies
To use all features install [Dodo-Workbench](https://wiki.freecadweb.org/Dodo_Workbench). It brings:

 * Changeable parameters of the pipes and fittings.
 * Convenient moving and connection of the parts.

# Deprecated #
If you still use [Flamingo-Workbench](https://wiki.freecadweb.org/Flamingo_Workbench),
please install [Dodo-Workbench]. The support of Flamingo will be dropped in the future.

# Troubleshooting #
If you get an error message "module ... not found", try to remove all .pyc-files in the ose-piping module. Then restart FreeCAD.


# License #

GPLv3 (see LICENSE)

