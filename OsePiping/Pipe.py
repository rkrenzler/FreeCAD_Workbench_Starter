# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 04 February 2018
# Create a pipe.

import os.path

import FreeCAD

import OsePipingBase
import Piping

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, 'pipe.csv')
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


class Dimensions:
    def __init__(self):
        """ Inititialize with test dimensions."""
        self.OD = parseQuantity("3 cm")
        self.Thk = parseQuantity("0.5 cm")
        self.H = parseQuantity("1 m")

    def isValid(self):
        errorMsg = ""
        if not (self.OD > 0):
            errorMsg = "OD (inner diameter) of the pipe must be positive. It is {} instead".format(
                self.OD)
        elif not (self.Thk <= self.OD / 2.0):
            errorMsg = "Pipe thickness Thk {} is too large: larger than OD/2 {}.".format(
                self.Thk, self.OD / 2.0)
        elif not (self.H > 0):
            errorMsg = "Height H={} must be positive".format(self.H)

        return (len(errorMsg) == 0, errorMsg)

    def ID(self):
        return self.OD - self.Thk * 2.0


class Pipe:
    def __init__(self, document):
        self.document = document
        self.dims = Dimensions()

    def checkDimensions(self):
        valid, msg = self.dims.isValid()
        if not valid:
            raise Piping.UnplausibleDimensions(msg)


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
            solid = Piping.toSolid(self.document, pipe, "pipe (solid)")
            Piping.removePartWithChildren(self.document, pipe)
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
        if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
            pipe = Pipe(self.document)
            pipe.OD = parseQuantity(row["OD"])
            pipe.Thk = parseQuantity(row["Thk"])
            pipe.H = length
            part = pipe.create(outputType == Piping.OUTPUT_TYPE_SOLID)
            return part
        elif outputType == Piping.OUTPUT_TYPE_FLAMINGO:
            # See Code in pipeCmd.makePipe in the Flamingo workbench.
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-Pipe")
            import pipeFeatures
            DN = Piping.GetDnString(row)
            OD = parseQuantity(row["OD"])
            Thk = parseQuantity(row["Thk"])
            part = pipeFeatures.Pipe(feature, DN=DN, OD=OD, thk=Thk, H=length)
            feature.PRating = Piping.GetPressureRatingString(row)
            # Currently I do not know how to interprite table data as a profile.
            feature.Profile = ""
            if "PSize" in row.keys():
                feature.PSize = row["PSize"]

            feature.ViewObject.Proxy = 0
            return part


# Test macros.
def TestPipe():
    document = FreeCAD.activeDocument()
    pipe = Pipe(document)
    pipe.create(False)
    document.recompute()


def TestTable():
    document = FreeCAD.activeDocument()
    table = Piping.CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    pipe = PipeFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partName = table.getPartName(i)
        print("Creating part %s" % partName)
        pipe.create(partName, parseQuantity("1m"), False)
        document.recompute()
