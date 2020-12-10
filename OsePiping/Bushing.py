# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 27 January 2018
# Create a bushing-fitting.

import os.path
import FreeCAD
import OsePipingBase
import OsePiping.Piping as Piping


parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, "bushing.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["POD", "POD1", "PThk1", "L", "N"]


# The value RELATIVE_EPSILON is used to slightly change the size of a subtracted part
# to prevent problems with boolean operations.
# This value does not change the appearance of part and can be large.
# If the original value is L then we often use the value L*(1+RELATIVE_EPSILON) instead.
# The relative deviation is then (L*(1+RELATIVE_EPSILON)-L)/L = RELATIVE_EPSILON.
# That is why the constant has "relative" in its name.
# On my version of freecad 0.16 The macro works even with RELATIVE_EPSILON = 0.0.
# Maybe there is no more problems with boolean operations.
RELATIVE_EPSILON = 0.1

# !!Warming: Several dimensions are not from specifications, they are just generated to "look nice".
# Be cariful if you need a bushing with particular mechanical properties.
# The unknown dimensions are of the inner cone and of the hexadecimal/octoganal thing.


class Dimensions:
    def __init__(self):
        """Inititialize with test dimensions."""
        self.POD = parseQuantity("4 cm")
        self.POD1 = parseQuantity("2 cm")
        self.PThk1 = parseQuantity("0.5 cm")
        self.N = parseQuantity("2 cm")
        self.L = parseQuantity("3 cm")

    def isValid(self):
        errorMsg = ""
        if not (self.POD > 0):
            errorMsg = "Pipe outer diameter {} must be positive.".format(
                self.POD)
        elif not (self.POD1 > 0):
            errorMsg = "Other pipe outer diameter {} must be positive.".format(
                self.POD)
        elif not (self.PThk1 <= self.POD1 / 2.0):
            errorMsg = "Pipe thickness PThk1 {} is too large: larger than POD1/2 {}.".format(
                self.PThk1, self.POD1 / 2.0)
        elif not (self.N > 0):
            errorMsg = "Length N={} must be positive".format(self.N)
        elif not (self.L > self.N):
            errorMsg = "The length L {} must be larger than the length N {}".format(
                self.L, self.N)

        return (len(errorMsg) == 0, errorMsg)

    def PID1(self):
        return self.POD1 - self.PThk1 * 2

    def ThingThicknessA1(self):
        """Return thickness of a hexagonal or octoganal thing."""
        # This dimension is missing in specification.
        # I just take a half of (L-N)
        return (self.L - self.N) / 2.0

    def ThingLengthA2(self):
        """Return distance between paralal sides of a x-gonal thing."""
        # This dimension is missing in specification.
        # I just take 1.2 of the outer diameter of the larger pipe
        return self.POD * 1.1

    def ThicknessA3(self):
        # I do not know this dimension. I just return pipe thickness of the other end.
        return self.PThk1

    def ConeLengthA4(self):
        # I do know this dimensions. I just use half of N
        return self.N / 2.0

    def auxiliararyPoints(self):
        """Calculate auxiliarary points which are used to build a cross from cylinders.

        See documentation picture bushing-cacluations.png
        """
        result = {}
        result["p1"] = FreeCAD.Vector(0, 0, 0)
        result["p2"] = FreeCAD.Vector(0, 0, self.ConeLengthA4())
        result["p3"] = FreeCAD.Vector(0, 0, self.N)
        result["p4"] = FreeCAD.Vector(0, 0, self.L - self.ThingThicknessA1())

        return result


class Bushing:
    def __init__(self, document):
        self.document = document
        self.dims = Dimensions()

    def checkDimensions(self):
        valid, msg = self.dims.isValid()
        if not valid:
            raise Piping.UnplausibleDimensions(msg)

    def createHexaThing(self):
        """Create hexagonal thing. I do not know its name."""
        aux = self.dims.auxiliararyPoints()
        X1 = self.dims.ThingThicknessA1()
        X2 = self.dims.ThingLengthA2()
        box1 = self.document.addObject("Part::Box", "Box")
        box1.Height = X1
        box1.Length = X2
        box1.Width = X2 * 2
        # Move the box into the center of the X,Y plane.
        center_pos = FreeCAD.Vector(-X2 / 2, -X2, 0)
        box_center = FreeCAD.Vector(X2 / 2, X2, 0)
        box1.Placement.Base = center_pos
        # Add another box, but rotated by 60° around the z axis.
        box2 = self.document.addObject("Part::Box", "Box")
        box2.Height = box1.Height
        box2.Length = box1.Length
        box2.Width = box1.Width
        box2.Placement = FreeCAD.Placement(
            center_pos, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 60), box_center)
        # Add another box, but rotated by 120° around the z axis.
        box3 = self.document.addObject("Part::Box", "Box")
        box3.Height = box1.Height
        box3.Length = box1.Length
        box3.Width = box1.Width
        box3.Placement = FreeCAD.Placement(center_pos, FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), 120), box_center)
        # Cut both boxes
        common = self.document.addObject("Part::MultiCommon", "Common")
        common.Shapes = [box1, box2, box3]
        # Put the thing at the top of the bushing
        common.Placement.Base = aux["p4"]
        return common

    def createOctaThing(self):
        """Create Octagonal thing. I do not know its name."""
        aux = self.dims.auxiliararyPoints()
        X1 = self.dims.ThingThicknessA1()
        X2 = self.dims.ThingLengthA2()
        box1 = self.document.addObject("Part::Box", "Box")
        box1.Height = X1
        box1.Length = X2
        box1.Width = X2
        # Move the box into the center of the X,Y plane.
        center_pos = FreeCAD.Vector(-X2 / 2, -X2 / 2, 0)
        box_center = FreeCAD.Vector(X2 / 2, X2 / 2, 0)
        box1.Placement.Base = center_pos
        # Add another box, but rotated by 45° around the z axis.
        box2 = self.document.addObject("Part::Box", "Box")
        box2.Height = box1.Height
        box2.Length = box1.Length
        box2.Width = box1.Width
        box2.Placement = FreeCAD.Placement(
            center_pos, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 45), box_center)
        # Cut both boxes
        common = self.document.addObject("Part::MultiCommon", "Common")
        common.Shapes = [box1, box2, ]
        # Put the thing at the top of the bushing
        common.Placement.Base = aux["p4"]
        return common

    def createOuterPart(self):
        aux = self.dims.auxiliararyPoints()
        outer_cylinder = self.document.addObject(
            "Part::Cylinder", "OuterCynlider")
        outer_cylinder.Radius = self.dims.POD / 2
        outer_cylinder.Height = self.dims.L
        outer_cylinder.Placement.Base = aux["p1"]
        thing = self.createOctaThing()
        # Bind two parts.
        fusion = self.document.addObject("Part::MultiFuse", "Fusion")
        fusion.Shapes = [outer_cylinder, thing, ]
        return fusion

    def createInnerPart(self):
        aux = self.dims.auxiliararyPoints()
        # Create central cilinder.
        inner_cylinder = self.document.addObject(
            "Part::Cylinder", "OuterCynlider")
        inner_cylinder.Radius = self.dims.PID1() / 2
        inner_cylinder.Height = self.dims.L
        inner_cylinder.Placement.Base = aux["p1"]
        # Add upper sucket (left on the picture)
        inner_socket = self.document.addObject(
            "Part::Cylinder", "OuterCynlider")
        inner_socket.Radius = self.dims.POD1 / 2
        inner_socket.Height = self.dims.L - self.dims.N
        inner_socket.Placement.Base = aux["p3"]

        # Make a cone for a larger socket. These dimension are missing in documentation use
        # -- the Dimension class will try to create them to look nice. But there is no guaranty
        # that the cone will have desired mechanical properties.
        socket_cone = self.document.addObject("Part::Cone", "Cone")
        socket_cone.Radius2 = self.dims.PID1() / 2
        socket_cone.Radius1 = self.dims.POD / 2 - self.dims.ThicknessA3()
        socket_cone.Height = self.dims.ConeLengthA4()
        socket_cone.Placement.Base = aux["p1"]
        inner = self.document.addObject("Part::MultiFuse", "Fusion")
        inner.Shapes = [inner_cylinder, inner_socket, socket_cone]
        return inner

    def create(self, convertToSolid):
        self.checkDimensions()
        outer = self.createOuterPart()
        inner = self.createInnerPart()

        bushing = self.document.addObject("Part::Cut", "Cut")
        bushing.Base = outer
        bushing.Tool = inner

        if convertToSolid:
            # Before making a solid, recompute documents. Otherwise there will be
            #    s = Part.Solid(Part.Shell(s))
            #    <class 'Part.OCCError'>: Shape is null
            # exception.
            self.document.recompute()
            # Now convert all parts to solid, and remove intermediate data.
            solid = Piping.toSolid(self.document, bushing, "bushing (solid)")
            Piping.removePartWithChildren(self.document, bushing)
            return solid
        return bushing


class BushingFromTable:
    """Create a part with dimensions from a CSV table."""

    def __init__(self, document, table):
        self.document = document
        self.table = table

    @classmethod
    def getPThk1(cls, row):
        """For compatibility results, if there is no "Thk1" dimension, calculate it from "PID1" and "POD1"."""
        if "PThk" not in row.keys():
            return (parseQuantity(row["POD1"]) - parseQuantity(row["PID1"])) / 2.0
        else:
            return parseQuantity(row["PThk1"])

    def create(self, partNumber, outputType):

        row = self.table.findPart(partNumber)
        if row is None:
            print("Part not found")
            return
        dims = Dimensions()

        dims.N = parseQuantity(row["N"])
        dims.L = parseQuantity(row["L"])
        dims.POD = parseQuantity(row["POD"])
        dims.POD1 = parseQuantity(row["POD1"])
        dims.PThk1 = self.getPThk1(row)

        if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
            bushing = Bushing(self.document)
            bushing.dims = dims
            part = bushing.create(outputType == Piping.OUTPUT_TYPE_SOLID)
            part.Label = "OSE-Bushing"
            return part

        elif outputType == Piping.OUTPUT_TYPE_DODO_OR_FLAMINGO:
            # See Code in pipeCmd.makePipe in the Flamingo workbench.
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-Bushing")
            import OsePiping.FlBushing as FlBushing
            builder = FlBushing.BushingBuilder(self.document)
            builder.dims = dims
            part = builder.create(feature)
            feature.PRating = Piping.GetPressureRatingString(row)
            feature.PSize = row["PSize"]  # What to do for multiple sizes?
            feature.ViewObject.Proxy = 0
            # feature.Label = partName # Part name must be unique, that is qhy use partNumber instead.
            feature.PartNumber = partNumber
            return part


# Test macros.
def TestBushing():
    document = FreeCAD.activeDocument()
    bushing = Bushing(document)
    bushing.create(False)
    document.recompute()


def TestTable():
    document = FreeCAD.activeDocument()
    table = Piping.CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    builder = BushingFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partNumber = table.getPartKey(i)
        print("Creating part %s" % partNumber)
        builder.create(partNumber, Piping.OUTPUT_TYPE_SOLID)
        document.recompute()

# TestBushing()
# TestTable()
