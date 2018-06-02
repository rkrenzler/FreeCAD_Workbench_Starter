# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04 February 2018
# Create a pipe.

import math
import csv
import os.path

import FreeCAD
import Part

import OSEBasePiping
from piping import *

tu = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OSEBasePiping.TABLE_PATH, 'pipe.csv')
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["OD", "Thk"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
# On my version of freecad 0.16 The macro works even with RELATIVE_EPSILON = 0.0.
# Maybe there is no more problems with boolean operations.
RELATIVE_EPSILON = 0.1


class Pipe:
    def __init__(self, document):
        self.document = document
        self.OD = tu("3 cm")
        self.Thk = tu("0.5 cm")
        self.H = tu("1 m")

    def checkDimensions(self):
        if not (self.OD > tu("0 mm")):
            raise UnplausibleDimensions(
                "OD (inner diameter) of the pipe must be positive. It is %s instead" % (self.OD))
        if not (2 * self.Thk <= self.OD):
            raise UnplausibleDimensions(
                "2*Thk (2*Thickness) %s must be less than or equlat to OD (outer diameter)%s " % (2 * self.Thk, self.OD))
        if not (self.H > tu("0 mm")):
            raise UnplausibleDimensions(
                "Height H=%s must be positive" % self.H)

    def create(self, convertToSolid):
        """ A pipe which is a differences of two cilinders: outer cylinder - inner cylinder.
        :param convertToSolid: if true, the resulting part will be solid.
                if false, the resulting part will be a cut.
        :return resulting part.
        """
        self.checkDimensions()
        # Create outer cylinder.
        outer_cylinder = self.document.addObject(
            "Part::Cylinder", "OuterCylinder")
        outer_cylinder.Radius = self.OD / 2
        outer_cylinder.Height = self.H

        # Create inner cylinder. It is a little bit longer than the outer cylider in both ends.
        # This should prevent numerical problems when calculating difference
        # between the outer and innter cylinder.
        inner_cylinder = self.document.addObject(
            "Part::Cylinder", "InnerCylinder")
        inner_cylinder.Radius = self.OD / 2 - self.Thk
        inner_cylinder.Height = self.H * (1 + 2 * RELATIVE_EPSILON)
        inner_cylinder.Placement.Base = FreeCAD.Vector(
            0, 0, -self.H * RELATIVE_EPSILON)
        pipe = self.document.addObject("Part::Cut", "Pipe")
        pipe.Base = outer_cylinder
        pipe.Tool = inner_cylinder

        if convertToSolid:
            # Before making a solid, recompute documents. Otherwise there will be
            #    s = Part.Solid(Part.Shell(s))
            #    <class 'Part.OCCError'>: Shape is null
            # exception.
            self.document.recompute()
            # Now convert all parts to solid, and remove intermediate data.
            solid = toSolid(self.document, pipe, "pipe (solid)")
            # Remove previous (intermediate parts).
            parts = nestedObjects(pipe)
            # Document.removeObjects can remove multple objects, when we use
            # parts directly. To prevent exceptions with deleted objects,
            # use the name list instead.
            names_to_remove = []
            for part in parts:
                if part.Name not in names_to_remove:
                    names_to_remove.append(part.Name)
            for name in names_to_remove:
                print("Deleting temporary objects %s." % name)
                self.document.removeObject(name)
            return solid
        return pipe


class PipeFromTable:
    """Create a part with dimensions from a CSV table."""

    def __init__(self, document, table):
        self.document = document
        self.table = table

    def create(self, partName, length, outputType):
        row = self.table.findPart(partName)
        if row is None:
            print("Part not found")
            return
        if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
            pipe = Pipe(self.document)
            pipe.OD = tu(row["OD"])
            pipe.Thk = tu(row["Thk"])
            pipe.H = length
            part = pipe.create(outputType == OUTPUT_TYPE_SOLID)
            #part.Label = partName
            return part
        elif outputType == OUTPUT_TYPE_FLAMINGO:
            # See Code in pipeCmd.makePipe in the Flamingo workbench.
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-Pipe")
            import pipeFeatures
            DN = GetDnString(row)
            OD = tu(row["OD"])
            Thk = tu(row["Thk"])
            part = pipeFeatures.Pipe(feature, DN=DN, OD=OD, thk=Thk, H=length)
            feature.PRating = GetPressureRatingString(row)
            # Currently I do not know how to interprite table data as a profile.
            feature.Profile = ""
            PSize = ""
            if "PSize" in row.keys():
                feature.PSize = row["PSize"]

            feature.ViewObject.Proxy = 0
            #feature.Label = partName
            return part

# Test macros.


def TestPipe():
    document = FreeCAD.activeDocument()
    pipe = Pipe(document)
    pipe.create(False)
    document.recompute()


def TestTable():
    document = FreeCAD.activeDocument()
    table = CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    pipe = PipeFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partName = table.getPartName(i)
        print("Creating part %s" % partName)
        pipe.create(partName, tu("1m"), False)
        document.recompute()
