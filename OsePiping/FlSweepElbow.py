# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus
# Date: 30. March 2018
# Create a sweep-elbow-fitting using flamingo workbench

import FreeCAD
import Part
from pipeFeatures import pypeType  # the parent class
import SweepElbow as SweepElbowMod


# The value RELATIVE_EPSILON is used to slightly change the size of parts
# to prevent problems with boolean operations.
# Keep this value very small.
# For example, the outer bent part of the elbow dissaperas when it has
# the same radius as the cylinder at the ends.
RELATIVE_EPSILON = 0.000001


class SweepElbow(pypeType):
    def __init__(self, obj, PSize="", dims=SweepElbowMod.Dimensions()):
        """Create a sweep elbow with the center at (0,0,0) sockets along the z and y axis."""
        # Run parent __init__ and define common attributes.
        super(SweepElbow, self).__init__(obj)
        obj.PType = "OSE_SweepElbow"
        obj.PRating = ""
        obj.PSize = PSize
        # Define specific attributes and set their values.
        obj.addProperty("App::PropertyAngle", "BendAngle",
                        "SweepElbow", "Bend Angle.").BendAngle = dims.BendAngle
        obj.addProperty("App::PropertyLength", "J", "SweepElbow",
                        "Distnace from the center to begin of innerpart of the socket").J = dims.J
        obj.addProperty("App::PropertyLength", "H", "SweepElbow",
                        "Distance between the center and a elbow end").H = dims.H
        obj.addProperty("App::PropertyLength", "M", "SweepElbow",
                        "Outer diameter of the elbow.").M = dims.M
        obj.addProperty("App::PropertyLength", "POD", "SweepElbow",
                        "Pipe outer diameter.").POD = dims.POD
        obj.addProperty("App::PropertyLength", "PThk",
                        "SweepElbow", "Pipe wall thickness").PThk = dims.PThk
        obj.addProperty("App::PropertyVectorList", "Ports", "SweepElbow",
                        "Ports relative positions.").Ports = self.getPorts(obj)
        obj.addProperty("App::PropertyVectorList", "PortRotationAngles", "SweepElbow",
                        "Ports rotation angles.").PortRotationAngles = self.getPortRotationAngles(obj)
        obj.addProperty("App::PropertyString", "PartNumber",
                        "SweepElbow", "Part number").PartNumber = ""

        # Make Ports read only.
        obj.setEditorMode("Ports", 1)
        obj.setEditorMode("PortRotationAngles", 1)

    def onChanged(self, obj, prop):
        # if you aim to do something when an attribute is changed
        # place the code here:
        # e.g. -> change PSize according the new alpha, PID and POD

        # Dimensions which can change port positions.
        dim_properties = ["BendAngle", "J"]
        if prop in dim_properties:
            # This function is called within __init__ too.
            # We wait for all dimension.
            if set(SweepElbowMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
                obj.Ports = self.getPorts(obj)

    @staticmethod
    def extractDimensions(obj):
        dims = SweepElbowMod.Dimensions()
        dims.BendAngle = obj.BendAngle
        dims.H = obj.H
        dims.J = obj.J
        dims.M = obj.M
        dims.POD = obj.POD
        dims.PThk = obj.PThk
        return dims

    @staticmethod
    def createBentCylinder(obj, rCirc):
        """Create a cylinder of radius rCirc in x-y plane wich is bent in the middle.

        :param group: Group where to add created objects.
        :param rCirc: Radius of the cylinder.

        See documentation picture sweep-elbow-cacluations.png.
        """
        # Convert alpha to degree value
        dims = SweepElbow.extractDimensions(obj)

        aux = dims.calculateAuxiliararyPoints()

        alpha = float(dims.BendAngle.getValueAs("deg"))
        rBend = (aux["p3"] - aux["p5"]).Length

        # Put a base on the streight part.
        base = Part.makeCircle(rCirc, aux["p5"], aux["p5"])

        # Add trajectory
        trajectory = Part.makeCircle(
            rBend, aux["p3"], FreeCAD.Vector(0, 0, 1), 225 - alpha / 2, 225 + alpha / 2)
        # Show trajectory for debugging.
        # W = W1.fuse([trajectory.Edges])
        # Part.Show(W)
        # Add a cap (circle, at the other end of the bent cylinder).
        cap = Part.makeCircle(rCirc, aux["p6"], aux["p6"])
        # Sweep the circle along the trajectory.
        sweep = Part.makeSweepSurface(trajectory, base)
        # The sweep is only a 2D service consisting of walls only.
        # Add circles on both ends of this wall.
        end1 = Part.Face(Part.Wire(base))
        # Create other end.
        end2 = Part.Face(Part.Wire(cap))
        solid = Part.Solid(Part.Shell([end1, sweep, end2]))
        return solid

    @staticmethod
    def createOuterPart(obj):
        dims = SweepElbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        # Make the outer part slightly larger. Otherwise it can be shown incorrectly after
        # the substraction of the inner part.
        r = ((dims.PID() / 2 + dims.fitThk()) * (1 + RELATIVE_EPSILON))
        bentPart = SweepElbow.createBentCylinder(obj, r)
        # Create socket along the z axis.
        h = float(dims.H) - aux["p2"].Length
        r = dims.M / 2
        socket1 = Part.makeCylinder(r, h, aux["p2"], aux["p2"])
        # Create socket along the bent part.
        socket2 = Part.makeCylinder(r, h, aux["p4"], aux["p4"])

        outer = bentPart.fuse([socket1, socket2])
        return outer

    @staticmethod
    def createInnerPart(obj):
        dims = SweepElbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()

        r = dims.POD / 2 - dims.PThk

        bentPart = SweepElbow.createBentCylinder(
            obj, r * (1 + RELATIVE_EPSILON))

        rSocket = dims.POD / 2
        # The socket length is actually dims.H - dims.J. But we do it longer
        # to prevent problems with bulean operations
        hSocket = dims.H
        socket1 = Part.makeCylinder(rSocket, hSocket, aux["p5"], aux["p5"])
        socket2 = Part.makeCylinder(rSocket, hSocket, aux["p6"], aux["p6"])

        inner = bentPart.fuse([socket1, socket2])
        return inner

    @staticmethod
    def createShape(obj):
        outer = SweepElbow.createOuterPart(obj)
        inner = SweepElbow.createInnerPart(obj)
        return outer.cut(inner)

    def execute(self, obj):
        # Create the shape of the tee.
        shape = SweepElbow.createShape(obj)
        obj.Shape = shape
        # Recalculate ports.
        obj.Ports = self.getPorts(obj)

    def getPorts(self, obj):
        dims = SweepElbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        # FreeCAD.Console.PrintMessage("Ports are %s and %s"%(aux["p5"], aux["p6"]))
        return [aux["p5"], aux["p6"]]

    def getPortRotationAngles(self, obj):
        """Calculate coordinates of the ports rotation and return them as vectorsself.

        x = Yaw
        y = Pitch
        z = Roll
        """
        dims = SweepElbow.extractDimensions(obj)
        half = dims.BendAngle / 2
        end0 = FreeCAD.Vector(45 - half.Value, 0, 0)
        end1 = FreeCAD.Vector(45 + half.Value, 0, 0)
        return [end0, end1]


class SweepElbowBuilder:
    """Create a sweep elbow using flamingo."""

    def __init__(self, document):
        self.dims = SweepElbowMod.Dimensions()
        self.pos = FreeCAD.Vector(0, 0, 0)  # Define default initial position.
        self.document = document

    def create(self, obj):
        """Create a sweep elbow.

        Before call it, call
        feature = self.document.addObject("Part::FeaturePython","OSE-SweepElbow")
        """
        elbow = SweepElbow(obj, PSize="", dims=self.dims)
        obj.ViewObject.Proxy = 0
        obj.Placement.Base = self.pos
        return elbow


# Test builder.
def TestSweepElbow():
    document = FreeCAD.activeDocument()
    builder = SweepElbowBuilder(document)
    feature = document.addObject("Part::FeaturePython", "OSE-SweepElbow")
    builder.create(feature)
    document.recompute()

# TestSweepElbow()
