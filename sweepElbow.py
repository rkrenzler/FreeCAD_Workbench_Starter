# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 30. March 2018
# Create a sweep-elbow-fitting.

import math
import csv
import os.path

import FreeCAD
import Part

import OSEBasePiping
from piping import *

parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OSEBasePiping.TABLE_PATH, "sweep-elbow.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["BendAngle", "G", "J", "M", "POD", "PThk"]


class Dimensions:
    def __init__(self):
        # Init class with test values
        self.BendAngle = parseQuantity("90 deg")
        self.H = parseQuantity("6 cm")
        self.J = parseQuantity("5 cm")
        self.M = parseQuantity("3 cm")
        self.POD = parseQuantity("2 cm")
        self.PThk = parseQuantity("0.5 cm")

    def isValid(self):
        fitThk = (self.M - self.POD) / 2.0
        errorMsg = ""
        if not (self.POD > 0):
            errorMsg = "Pipe outer diameter %s must be positive" % self.PID
        elif not (self.PThk <= self.POD / 2.0):
            errorMsg = "Pipe thickness %s is too larger: larger than POD/2 %s." % (
                self.PThk, self.POD / 2.0)
        elif not (self.M > self.POD):
            errorMsg = "Socket outer diameter %s must be greater than pipe outer diameter =%s." % (
                self.M, self.POD)
        elif not (self.G > self.M / 2 + fitThk):
            errorMsg = "Length G=%s must be larger than M/2 + fitting thickness (M-POD)/2 =%s." % (self.G,
                                                                                                   self.M / 2 + fitThk)
        elif not (self.H > self.G):
            errorMsg = "Length H=%s must be larger than G=%s" % (
                self.H, self.G)
        return (len(errorMsg) == 0, errorMsg)


class SweepElbow:
    def __init__(self, document):
        self.document = document
        self.dims = Dimensions()

    def checkDimensions(self):
        valid, msg = self.dims.isValid()
        if not valid:
            raise UnplausibleDimensions(msg)

    @staticmethod
    def createBentCylinder(doc, group, r, l):
        """ Create 90° bent cylinder in x-z plane with radius r.

        :param group: Group where to add created objects.
        :param r: Radius of the cylinder.
        :param l: Distance to the origin (0,0,0).

        See documentation picture sweep-elbow-cacluations.png
        """
        p1 = FreeCAD.Vector(0, 0, -l)
        # Add cylinder
        base = doc.addObject("Part::Circle", "Base")
        base.Radius = r
        base.Placement.Base = p1
        # Add trajectory
        p3 = FreeCAD.Vector(l, 0, -l)
        trajectory = doc.addObject("Part::Circle", "Trajectory")
        trajectory.Radius = l
        trajectory.Angle0 = 90
        trajectory.Angle1 = 180
        trajectory.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(
            FreeCAD.Vector(1, 0, 0), 90), FreeCAD.Vector(0, 0, 0))
        # Sweep the circle along the trajectory.
        sweep = doc.addObject('Part::Sweep', 'Sweep')
        sweep.Sections = [base]
        sweep.Spine = trajectory
        sweep.Solid = True
        group.addObjects([trajectory, sweep])
        return sweep

    def createOuterPart(self, group):
        """Create bending part and socket cylinders.

        See documentation picture sweep-elbow-cacluations.png.
        """
        # Create a bent part.
        bentPart = SweepElbow.createBentCylinder(
            self.document, group, self.dims.POD / 2.0, self.dims.G)
        # Create vertical socket (on the bottom).
        socket1 = self.document.addObject("Part::Cylinder", "Socket1")
        # Calculate wall thickness of the fitting.
        fitThk = (self.dims.M - self.dims.POD) / 2.0
        socket1.Radius = self.dims.M / 2.0
        # Calculate socket Height.
        a2 = self.dims.H - self.dims.G + fitThk
        socket1.Height = a2
        # Calculate socket position.
        p2 = FreeCAD.Vector(0, 0, -self.dims.H)
        socket1.Placement.Base = p2
        # Calculate second socket (on the right).
        socket2 = self.document.addObject("Part::Cylinder", "Socket2")
        socket2.Radius = self.dims.M / 2.0
        socket2.Height = a2
        p3 = FreeCAD.Vector(self.dims.H - a2, 0, 0)
        # Rotate the socket and bring it to the right end of the fitting.
        socket2.Placement = FreeCAD.Placement(p3, FreeCAD.Rotation(
            FreeCAD.Vector(0, 1, 0), 90), FreeCAD.Vector(0, 0, 0))
        outer = self.document.addObject("Part::MultiFuse", "Outer")
        outer.Shapes = [bentPart, socket1, socket2]
        group.addObject(outer)
        return outer

    def createInnerPart(self, group):
        """Create inner bending part and socket cylinders.
        See documentation picture sweep-elbow-cacluations.png.

        Note: The inner part differs from the outer part not only by socket sizes
        and the size of the bent part, the sockets positions are also different.
        In the inner part the sockets justs touch the inner parts.
        In the outer part the sockets intesects with bent part (the intersection
        width corresponds to the wall thickness of the fitting).
        """

        # Create a bent part.
        socketR = self.dims.POD / 2.0
        innerR = self.dims.POD / 2.0 - self.dims.PThk
        bentPart = SweepElbow.createBentCylinder(
            self.document, group, innerR, self.dims.G)
        # Create vertical socket (on the bottom).
        socket1 = self.document.addObject("Part::Cylinder", "Socket1")
        # Calculate wall thickness of the fitting.
        socket1.Radius = socketR
        # Calculate socket Height.
        a1 = self.dims.H - self.dims.G
        socket1.Height = a1
        # Calculate socket position.
        p2 = FreeCAD.Vector(0, 0, -self.dims.H)
        socket1.Placement.Base = p2
        # Calculate horizonal socket (on the right).
        socket2 = self.document.addObject("Part::Cylinder", "Socket2")
        socket2.Radius = socketR
        socket2.Height = a1
        p4 = FreeCAD.Vector(self.dims.H - a1, 0, 0)
        # Rotate the socket and bring it to the right end of the fitting.
        socket2.Placement = FreeCAD.Placement(p4, FreeCAD.Rotation(
            FreeCAD.Vector(0, 1, 0), 90), FreeCAD.Vector(0, 0, 0))
        inner = self.document.addObject("Part::MultiFuse", "Inner")
        inner.Shapes = [bentPart, socket1, socket2]
        group.addObject(inner)
        return inner

    def create(self, convertToSolid):
        self.checkDimensions()
        # Create new group to put all the temporal data.
        group = self.document.addObject(
            "App::DocumentObjectGroup", "ElbowGroup")
        outer = self.createOuterPart(group)
        inner = self.createInnerPart(group)
        elbow = self.document.addObject("Part::Cut", "SweepElbow")
        elbow.Base = outer
        elbow.Tool = inner
        group.addObject(elbow)
        if convertToSolid:
            # Before making a solid, recompute documents. Otherwise there will be
            #    s = Part.Solid(Part.Shell(s))
            #    <class 'Part.OCCError'>: Shape is null
            # exception.
            self.document.recompute()
            # Now convert all parts to solid, and remove intermediate data.
            solid = toSolid(self.document, elbow, "sweep elbow (solid)")
            # Remove previous (intermediate parts).
            parts = nestedObjects(group)
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
        return group


class SweepElbowFromTable:
    """Create a part with dimensions from CSV table."""

    def __init__(self, document, table):
        self.document = document
        self.table = table

    @classmethod
    def getPThk(cls, row):
        """ For compatibility results, if there is no "PThk" dimension, calculate it
        from "PID" and "POD" """
        if not "PThk" in row.keys():
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
        dims.Thk = SweepElbowFromTable.getPThk(row)

        if outputType == OUTPUT_TYPE_PARTS or outputType == OUTPUT_TYPE_SOLID:
            elbow = SweepElbow(self.document)
            elbow.dims = dims
            part = elbow.create(outputType == OUTPUT_TYPE_SOLID)
            part.Label = "OSE-SweepElbow"
            return part

        elif outputType == OUTPUT_TYPE_FLAMINGO:
            # See Code in pipeCmd.makePipe in the Flamingo workbench.
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-SweepElbow")
            import flSweepElbow
            builder = flSweepElbow.SweepElbowBuilder(self.document)
            builder.dims = dims
            part = builder.create(feature)
            feature.PRating = GetPressureRatingString(row)
            feature.PSize = self.getPSize(row)
            feature.ViewObject.Proxy = 0
            feature.PartNumber = partNumber
            return part


# Testing function.
def TestSweepElbow():
    document = FreeCAD.activeDocument()
    elbow = SweepElbow(document)
    elbow.create(False)
    document.recompute()


def TestSweepElbowTable():
    document = FreeCAD.activeDocument()
    table = CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    builder = SweepElbowFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partNumber = table.getPartKey(i)
        print("Creating part %s" % partNumber)
        builder.create(partNumber, OUTPUT_TYPE_FLAMINGO)
        document.recompute()

# TestSweepElbow()
# TestSweepElbowTable()
