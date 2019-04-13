# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 09 February 2018
# Create a corner-fitting.

import os.path
import FreeCAD
import OsePipingBase
import OsePiping.Piping as Piping

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, "corner.csv")
# It must contain unique values in the column "PartNumber" and also, dimensions listened below.
DIMENSIONS_USED = ["G", "H", "M", "POD", "PThk"]


class Dimensions:
    def __init__(self):
        self.G = parseQuantity("2 cm")
        self.H = parseQuantity("3 cm")
        self.M = parseQuantity("3 cm")
        self.POD = parseQuantity("2 cm")
        self.PThk = parseQuantity("0.5 cm")

    def isValid(self):
        errorMsg = ""
        if not (self.POD > 0):
            errorMsg = "Pipe outer diameter POD {} must be positive.".format(
                self.POD)
        elif not (self.PThk <= self.POD / 2.0):
            errorMsg = "Pipe thickness PThk {} is too large: larger than POD/2 {}.".foramt(
                self.PThk, self.POD / 2.0)
        elif not (self.M > self.POD):
            errorMsg = "Outer diameter M {} must be larger than outer pipe diameter POD {}".format(
                self.M, self.POD)
        elif not (self.G > 0):
            errorMsg = "Length G {} be positive".format(self.G)
        elif not (self.H > self.G):
            errorMsg = "Length H {} must be larger than length G {}".format(
                self.H, self.G)
        if not (self.G > self.PID() / 2.0):
            errorMsg = "Length G {} must be larger than inner pipe radius PID/2={}.".format(
                self.G, self.PID() / 2.0)

        return (len(errorMsg) == 0, errorMsg)

    def PID(self):
        return self.POD - 2 * self.PThk

    def calculateAuxiliararyPoints(self):
        """Calculate auxiliarary points which are used to build a corner from cylinders.

        See documentation picture corner-cacluations.png.
        """
        result = {}
        result["p1"] = FreeCAD.Vector(self.G, 0, 0)
        result["p2"] = FreeCAD.Vector(0, self.G, 0)
        result["p3"] = FreeCAD.Vector(0, 0, self.G)
        return result


class Corner:
    def __init__(self, document):
        self.document = document
        # Set default values.
        self.dims = Dimensions()

    def checkDimensions(self):
        valid, msg = self.dims.isValid()
        if not valid:
            raise Piping.UnplausibleDimensions(msg)

    def createPrimitiveCorner(self, L, D):
        """Create corner consisting of two cylinder along x-,y- and y axis and a ball in the center."""
        x_cylinder = self.document.addObject("Part::Cylinder", "XCynlider")
        x_cylinder.Radius = D / 2
        x_cylinder.Height = L
        x_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(
            0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90), FreeCAD.Vector(0, 0, 0))
        y_cylinder = self.document.addObject("Part::Cylinder", "YCynlider")
        y_cylinder.Radius = D / 2
        y_cylinder.Height = L
        y_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(
            FreeCAD.Vector(1, 0, 0), -90), FreeCAD.Vector(0, 0, 0))
        z_cylinder = self.document.addObject("Part::Cylinder", "ZCynlider")
        z_cylinder.Radius = D / 2
        z_cylinder.Height = L
        sphere = self.document.addObject("Part::Sphere", "Sphere")
        sphere.Radius = D / 2
        fusion = self.document.addObject("Part::MultiFuse", "Fusion")
        fusion.Shapes = [x_cylinder, y_cylinder, z_cylinder, sphere]
        return fusion

    def addSockets(self, fusion):
        """Add socket cylinders to the fusion."""
        x_socket = self.document.addObject("Part::Cylinder", "XSocket")
        x_socket.Radius = self.dims.POD / 2
        x_socket.Height = self.dims.H - self.dims.G
        x_socket.Placement = FreeCAD.Placement(FreeCAD.Vector(self.dims.G, 0, 0), FreeCAD.Rotation(
            FreeCAD.Vector(0, 1, 0), 90), FreeCAD.Vector(0, 0, 0))
        y_socket = self.document.addObject("Part::Cylinder", "YSocket")
        y_socket.Radius = self.dims.POD / 2
        y_socket.Height = self.dims.H - self.dims.G
        y_socket.Placement = FreeCAD.Placement(FreeCAD.Vector(0, self.dims.G, 0), FreeCAD.Rotation(
            FreeCAD.Vector(1, 0, 0), -90), FreeCAD.Vector(0, 0, 0))
        z_socket = self.document.addObject("Part::Cylinder", "ZSocket")
        z_socket.Radius = self.dims.POD / 2
        z_socket.Height = self.dims.H - self.dims.G
        z_socket.Placement.Base = FreeCAD.Vector(0, 0, self.dims.G)
        # fusion.Shapes.append does not work.
        fusion.Shapes = fusion.Shapes + [x_socket, y_socket, z_socket]
        return fusion

    def createOuterPart(self):
        return self.createPrimitiveCorner(self.dims.H, self.dims.M)

    def createInnerPart(self):
        inner = self.createPrimitiveCorner(self.dims.H, self.dims.PID())
        inner = self.addSockets(inner)
        return inner

    def create(self, convertToSolid):
        self.checkDimensions()
        outer = self.createOuterPart()
        inner = self.createInnerPart()
        # Remove inner part of the sockets.
        corner = self.document.addObject("Part::Cut", "Cut")
        corner.Base = outer
        corner.Tool = inner

        if convertToSolid:
            # Before making a solid, recompute documents. Otherwise there will be
            #    s = Part.Solid(Part.Shell(s))
            #    <class 'Part.OCCError'>: Shape is null
            # exception.
            self.document.recompute()
            # Now convert all parts to solid, and remove intermediate data.
            solid = Piping.toSolid(self.document, corner, "corner (solid)")
            Piping.removePartWithChildren(self.document, corner)
            return solid
        return corner


class CornerFromTable:
    """Create a part with dimensions from a CSV table."""

    def __init__(self, document, table):
        self.document = document
        self.table = table

    @classmethod
    def getPThk(cls, row):
        """For compatibility results, if there is no "PThk" dimension, calculate it from "PID" and "POD"."""
        if "PThk" not in row.keys():
            return (parseQuantity(row["POD"]) - parseQuantity(row["PID"])) / 2.0
        else:
            return parseQuantity(row["PThk"])

    @classmethod
    def getPSize(cls, row):
        if "PSize" in row.keys():
            return row["PSize"]
        else:
            return ""

    def create(self, partNumber, outputType):
        row = self.table.findPart(partNumber)
        if row is None:
            print("Part not found")
            return

        dims = Dimensions()
        dims.G = parseQuantity(row["G"])
        dims.H = parseQuantity(row["H"])
        dims.M = parseQuantity(row["M"])
        dims.POD = parseQuantity(row["POD"])
        dims.PThk = self.getPThk(row)

        if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
            corner = Corner(self.document)
            corner.dims = dims
            part = corner.create(outputType == Piping.OUTPUT_TYPE_SOLID)
            part.Label = "OSE-Corner"
            return part

        elif outputType == Piping.OUTPUT_TYPE_FLAMINGO:
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-Corner")
            import FlCorner
            builder = FlCorner.CornerBuilder(self.document)
            builder.dims = dims
            part = builder.create(feature)
            feature.PRating = Piping.GetPressureRatingString(row)
            feature.PSize = self.getPSize(row)
            feature.ViewObject.Proxy = 0
            feature.PartNumber = partNumber
            return part


# Test macros.
def TestCorner():
    document = FreeCAD.activeDocument()
    corner = Corner(document)
    corner.create(True)
    document.recompute()


def TestTable():
    document = FreeCAD.activeDocument()
    table = Piping.CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    builder = CornerFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partNumber = table.getPartKey(i)
        print("Creating part %s" % partNumber)
        builder.create(partNumber, Piping.OUTPUT_TYPE_SOLID)
        document.recompute()


# TestCorner()
# TestTable()
