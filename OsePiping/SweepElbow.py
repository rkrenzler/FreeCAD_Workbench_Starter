# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 30. March 2018
# Create a sweep-elbow-fitting.

import math
import os.path
import FreeCAD
import OsePipingBase
import OsePiping.Piping as Piping


parseQuantity = FreeCAD.Units.parseQuantity

# This is the path to the dimensions table.
CSV_TABLE_PATH = os.path.join(OsePipingBase.TABLE_PATH, "sweep-elbow.csv")
# It must contain unique values in the column "Name" and also, dimensions listened below.
DIMENSIONS_USED = ["BendAngle", "H", "J", "M", "POD", "PThk"]

# The value RELATIVE_EPSILON is used to slightly change the size of parts
# to prevent problems with boolean operations.
# Keep this value very small.
# For example, the outer bent part of the elbow dissaperas when it has
# the same radius as the cylinder at the ends.
RELATIVE_EPSILON = 0.000001


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
        elif not (self.BendAngle > 0):
            errorMsg = "Bend Angle {}  must be positive.".format(
                self.PThk, self.POD / 2.0)
        elif not (self.PThk <= self.POD / 2.0):
            errorMsg = "Pipe thickness %s is too larger: larger than POD/2 %s." % (
                self.PThk, self.POD / 2.0)
        elif not (self.M > self.POD):
            errorMsg = "Socket outer diameter %s must be greater than pipe outer diameter =%s." % (
                self.M, self.POD)
        elif not (self.J > self.M / 2 + fitThk):
            errorMsg = "Length G=%s must be larger than M/2 + fitting thickness (M-POD)/2 =%s." % (self.J,
                                                                                                   self.M / 2 + fitThk)
        elif not (self.H > self.J):
            errorMsg = "Length H=%s must be larger than J=%s" % (
                self.H, self.G)
        return (len(errorMsg) == 0, errorMsg)

    def calculateAuxiliararyPoints(self):
        """Calculate auxiliarary points influenced by bentAngle, bentRadius (self.M/2) and the distannce J.

        See documentation picture sweep-elbow-cacluations.png. The code is similar to
        Elbow.Dimensions.calculateAuxiliararyPoints.
        """
        beta = 180 - float(self.BendAngle.getValueAs("deg"))
        beta_rad = math.pi - float(self.BendAngle.getValueAs("rad"))

        # Start with a normalized vector along th bisectrix of the x and y-axis.
        # Then stretch and rotate this vector by -beta/2 and +beta/2 along the z axis.
        bs = FreeCAD.Vector(1, 1, 0).normalize()
        neg_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), -beta / 2)

        p1 = neg_rot.multVec(bs * float(self.H))
        p5 = neg_rot.multVec(bs * float(self.J))

        pos_rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), +beta / 2)
        p6 = pos_rot.multVec(bs * float(self.J))

        # p3 lies on the bissectrix.
        p3 = bs * float(self.J / math.cos(beta_rad / 2.0))
        # Calculate coordinates of the base cirle at the end of sweep.
        a = self.calculateAuxiliararyLengths()
        l = float(self.H) - float(a["a2"])
        p2 = neg_rot.multVec(bs * l)
        p4 = pos_rot.multVec(bs * l)

        return {"p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5, "p6": p6}

    def PID(self):
        """Return the inner diamter of the pipe."""
        return self.POD - 2 * self.PThk

    def fitThk(self):
        """Return thinckness of the fitting wall."""
        return (self.M - self.POD) / 2.0

    def calculateAuxiliararyLengths(self):

        a1 = self.H - self.J
        # Calculate socket Height.
        a2 = self.H - self.J + self.fitThk()
        return {"a1": a1, "a2": a2}


class SweepElbow:
    def __init__(self, document):
        self.document = document
        self.dims = Dimensions()

    def checkDimensions(self):
        valid, msg = self.dims.isValid()
        if not valid:
            raise Piping.UnplausibleDimensions(msg)

    def createBentCylinder(self, group, rCirc, bendEps=0):
        """Create 90° bent cylinder in x-z plane with radius r.

        :param group: Group where to add created objects.
        :param rCirc: Radius of the cylinder.
        :param bendEps: Make some dimensions smaller by (1+endEps) factor. A positive bendEps
            is used when creating outer part, to prevent some artifacts, when substracting
            the inner part from the outher part.
            This parameter is not used now.

        See documentation picture sweep-elbow-cacluations.png.
        """
        # Convert alpha to degree value
        aux = self.dims.calculateAuxiliararyPoints()

        alpha = float(self.dims.BendAngle.getValueAs("deg"))
        rBend = (aux["p3"] - aux["p5"]).Length

        # Calculate coordinates of the base circle.
        # Add cylinder.
        base = self.document.addObject("Part::Circle", "Base")
        base.Radius = rCirc
        base.Placement.Base = aux["p5"]
        base.Placement.Rotation = FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), aux["p5"])

        # Add trajectory
        trajectory = self.document.addObject("Part::Circle", "Trajectory")
        trajectory.Radius = rBend
        trajectory.Angle0 = 225 - alpha / 2
        trajectory.Angle1 = 225 + alpha / 2
        trajectory.Placement.Base = aux["p3"]

        # Sweep the circle along the trajectory.
        sweep = self.document.addObject('Part::Sweep', 'Sweep')
        sweep.Sections = [base]
        sweep.Spine = trajectory
        sweep.Solid = True
        group.addObjects([trajectory, base, sweep])
        return sweep

    def createOuterPart(self, group):
        aux = self.dims.calculateAuxiliararyPoints()
        # Make the outer part slightly larger. Otherwise it can be shown incorrectly after
        # the substraction of the inner part.
        r = ((self.dims.PID() / 2 + self.dims.fitThk()) * (1 + RELATIVE_EPSILON))
        bentPart = self.createBentCylinder(
            group, r, RELATIVE_EPSILON)
        # Create socket along the z axis.
        socket1 = self.document.addObject("Part::Cylinder", "OuterSocket1")
        socket1.Radius = self.dims.M / 2
        socket1.Height = float(self.dims.H) - aux["p2"].Length
        socket1.Placement.Base = aux["p2"]
        socket1.Placement.Rotation = FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), aux["p2"])
#        socket1.Placement = FreeCAD.Placement(p2, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), p2),
#                                              FreeCAD.Vector(0, 0, 0))
        # Create socket along the bent part.
        socket2 = self.document.addObject("Part::Cylinder", "OuterSocket2")
        socket2.Radius = socket1.Radius
        socket2.Height = socket1.Height
        socket2.Placement = FreeCAD.Placement(aux["p4"], FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), aux["p4"]),
                                              FreeCAD.Vector(0, 0, 0))
        outer = self.document.addObject("Part::MultiFuse", "Outer")
        outer.Shapes = [bentPart, socket1, socket2]
        group.addObject(outer)
        return outer

    def createInnerPart(self, group):
        aux = self.dims.calculateAuxiliararyPoints()
        pid = self.dims.POD - self.dims.PThk * 2
        bentPart = self.createBentCylinder(group, pid / 2)
        # Add sockets
        socket1 = self.document.addObject("Part::Cylinder", "Socket1")
        socket1.Radius = self.dims.POD / 2
        socket1.Height = self.dims.H
        socket1.Placement.Base = aux["p5"]
        socket1.Placement.Rotation = FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), aux["p5"])

        socket2 = self.document.addObject("Part::Cylinder", "Socket2")
        socket2.Radius = socket1.Radius
        socket2.Height = socket1.Height
        socket2.Placement.Base = aux["p6"]
        socket2.Placement.Rotation = FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), aux["p6"])

        inner = self.document.addObject("Part::MultiFuse", "Inner")
        inner.Shapes = [bentPart, socket1, socket2]
        group.addObject(inner)
        return inner

    def createInnerPartOld(self, group):
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
            solid = Piping.toSolid(self.document, elbow, "sweep elbow (solid)")
            # Remove previous (intermediate parts).
            Piping.removePartWithChildren(self.document, group)
            return solid
        return group


class SweepElbowFromTable:
    """Create a part with dimensions from CSV table."""

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
        dims.H = parseQuantity(row["H"])
        dims.J = parseQuantity(row["J"])
        dims.M = parseQuantity(row["M"])
        dims.POD = parseQuantity(row["POD"])
        dims.Thk = SweepElbowFromTable.getPThk(row)

        if outputType == Piping.OUTPUT_TYPE_PARTS or outputType == Piping.OUTPUT_TYPE_SOLID:
            elbow = SweepElbow(self.document)
            elbow.dims = dims
            part = elbow.create(outputType == Piping.OUTPUT_TYPE_SOLID)
            part.Label = "OSE-SweepElbow"
            return part

        elif outputType == Piping.OUTPUT_TYPE_FLAMINGO:
            # See Code in pipeCmd.makePipe in the Flamingo workbench.
            feature = self.document.addObject(
                "Part::FeaturePython", "OSE-SweepElbow")
            import FlSweepElbow
            builder = FlSweepElbow.SweepElbowBuilder(self.document)
            builder.dims = dims
            part = builder.create(feature)
            feature.PRating = Piping.GetPressureRatingString(row)
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
    table = Piping.CsvTable(DIMENSIONS_USED)
    table.load(CSV_TABLE_PATH)
    builder = SweepElbowFromTable(document, table)
    for i in range(0, len(table.data)):
        print("Selecting row %d" % i)
        partNumber = table.getPartKey(i)
        print("Creating part %s" % partNumber)
        builder.create(partNumber, Piping.OUTPUT_TYPE_FLAMINGO)
        document.recompute()

# TestSweepElbow()
# TestSweepElbowTable()
