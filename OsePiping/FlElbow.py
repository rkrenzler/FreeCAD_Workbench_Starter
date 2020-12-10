# -*- coding: utf-8 -*-
# Authors: oddtopus, Ruslan Krenzler
# Date: 24 March 2018
# Create a elbow-fitting using Dodo/Flamingo workbench.

import FreeCAD
import Part
# Parent class from Dodo or Flamingo.
try:
    from pFeatures import pypeType
except ModuleNotFoundError:
    from pipeFeatures import pypeType
import OsePiping.Elbow as ElbowMod


# The value RELATIVE_EPSILON is used to slightly change the size of parts
# to prevent problems with boolean operations.
# Keep this value very small.
# For example, the outer bent part of the elbow dissaperas when it has
# the same radius as the cylinder at the ends.
RELATIVE_EPSILON = 0.000001


class Elbow(pypeType):
    def __init__(self, obj, PSize="90degBend20x10", BendAngle=90, M=30, POD=20, PThk=10, H=30, J=20):
        # run parent __init__ and define common attributes
        super(Elbow, self).__init__(obj)
        obj.PType = "OSE_Elbow"
        obj.PRating = "ElbowFittingFromAnyCatalog"
        obj.PSize = PSize  # Pipe size
        # define specific attributes
        obj.addProperty("App::PropertyLength", "M", "Elbow",
                        "Outer diameter of the elbow.").M = M
        obj.addProperty("App::PropertyLength", "POD", "Elbow",
                        "Pipe Outer Diameter.").POD = POD
        obj.addProperty("App::PropertyLength", "PThk", "Elbow",
                        "Pipe wall thickness").PThk = PThk
        obj.addProperty("App::PropertyAngle", "BendAngle",
                        "Elbow", "Bend Angle.").BendAngle = BendAngle
        obj.addProperty("App::PropertyLength", "H", "Elbow",
                        "Distance between the center and a elbow end").H = H
        obj.addProperty("App::PropertyLength", "J", "Elbow",
                        "Distnace from the center to begin of innerpart of the socket").J = J
        obj.addProperty("App::PropertyVectorList", "Ports", "Elbow",
                        "Ports relative position.").Ports = self.getPorts(obj)
        obj.addProperty("App::PropertyVectorList", "PortRotationAngles", "Elbow",
                        "Ports rotation angles.").PortRotationAngles = self.getPortRotationAngles(obj)
        obj.addProperty("App::PropertyString", "PartNumber",
                        "Elbow", "Part number").PartNumber = ""
        # Make Ports read only.
        obj.setEditorMode("Ports", 1)
        obj.setEditorMode("PortRotationAngles", 1)

    def onChanged(self, obj, prop):
        # if you aim to do something when an attribute is changed
        # place the code here:
        # e.g. -> change PSize according the new alpha, PID and POD

        # Dimensions which can change port coordinates.
        dim_properties = ["BendAngle", "J"]
        if prop in dim_properties:
            # This function is called within __init__ too.
            # We wait for all dimension.
            if set(ElbowMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
                obj.Ports = self.getPorts(obj)
                # Wait until PortRotationAngles are defined.
                if hasattr(obj, "PortRotationAngles"):
                    obj.PortRotationAngles = self.getPortRotationAngles(obj)

    @staticmethod
    def extractDimensions(obj):
        dims = ElbowMod.Dimensions()
        dims.BendAngle = obj.BendAngle
        dims.H = obj.H
        dims.J = obj.J
        dims.M = obj.M
        dims.POD = obj.POD
        dims.PThk = obj.PThk
        return dims

    @staticmethod
    def createBentCylinderDoesNotWork(obj, rCirc):
        """Create a cylinder of radius rCirc in x-y plane which is bent in the middle and is streight in the ends.

        The little streight part is necessary, because otherwise the part is not displayed
        correctly after performing a boolean operations. Thus we need some overlapping
        between bent part and the socket.

        :param group: Group where to add created objects.
        :param rCirc: Radius of the cylinder.

        See documentation picture elbow-cacluations.png
        """
        # Convert alpha to degree value
        dims = Elbow.extractDimensions(obj)

        aux = dims.calculateAuxiliararyPoints()

        alpha = float(dims.BendAngle.getValueAs("deg"))
        rBend = dims.M / 2.0

        # Put a base on the streight part.
        base = Part.makeCircle(rCirc, aux["p5"], aux["p5"])

        # Add trajectory
        line1 = Part.makeLine(aux["p5"], aux["p2"])
        arc = Part.makeCircle(
            rBend, aux["p3"], FreeCAD.Vector(0, 0, 1), 225 - alpha / 2, 225 + alpha / 2)
        line2 = Part.makeLine(aux["p4"], aux["p6"])

        trajectory = Part.Shape([line1, arc, line2])
        # Show trajectory for debugging.
        # W Part.Wire([line1, arc, line2])
        # Part.show(W)
        # Add a cap (circle, at the other end of the bent cylinder).
        cap = Part.makeCircle(rCirc, aux["p5"], aux["p5"])
        # Sweep the circle along the trajectory.
        sweep = Part.makeSweepSurface(trajectory, base)  # Does not work
        sweep = Part.makeSweepSurface(W, base)  # Does not work.
        # The sweep is only a 2D service consisting of walls only.
        # Add circles on both ends of this wall.
        end1 = Part.Face(Part.Wire(base))
        # Create other end.
        end2 = Part.Face(Part.Wire(cap))
        solid = Part.Solid(Part.Shell([end1, sweep, end2]))
        return solid

    @staticmethod
    def createBentCylinder(obj, rCirc):
        """Create a cylinder of radius rCirc in x-y plane which is bent in the middle.

        :param group: Group where to add created objects.
        :param rCirc: Radius of the cylinder.

        See documentation picture elbow-cacluations.png
        """
        # Convert alpha to degree value
        dims = Elbow.extractDimensions(obj)

        aux = dims.calculateAuxiliararyPoints()

        alpha = float(dims.BendAngle.getValueAs("deg"))
        rBend = dims.M / 2.0

        # Put a base on the streight part.
        base = Part.makeCircle(rCirc, aux["p2"], aux["p2"])

        # Add trajectory
        trajectory = Part.makeCircle(
            rBend, aux["p3"], FreeCAD.Vector(0, 0, 1), 225 - alpha / 2, 225 + alpha / 2)
        # Show trajectory for debugging.
        # W = W1.fuse([trajectory.Edges])
        # Part.Show(W)
        # Add a cap (circle, at the other end of the bent cylinder).
        cap = Part.makeCircle(rCirc, aux["p4"], aux["p4"])
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
        dims = Elbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        r = dims.M / 2
        # For unknow reasons, witoutm the factor r*0.999999 the middle part disappears.
        bentPart = Elbow.createBentCylinder(obj, r * (1 + RELATIVE_EPSILON))
        # Create socket along the z axis.
        h = float(dims.H) - aux["p2"].Length
        socket1 = Part.makeCylinder(r, h, aux["p2"], aux["p2"])
        # Create socket along the bent part.
        socket2 = Part.makeCylinder(r, h, aux["p4"], aux["p4"])

        outer = bentPart.fuse([socket1, socket2])
        return outer

    @staticmethod
    def createInnerPart(obj):
        dims = Elbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()

        r = dims.POD / 2 - dims.PThk

        bentPart = Elbow.createBentCylinder(obj, r * (1 + RELATIVE_EPSILON))
        # Create a channel along the z axis. It is longer then necessaryself.
        # But it possible can prevent problems with boolean operations.
        h = float(dims.H)
        chan1 = Part.makeCylinder(r, h, aux["p2"], aux["p2"])
        # Create a channel along the bent part.
        chan2 = Part.makeCylinder(r, h, aux["p4"], aux["p4"])
        # Create corresponding socktes.

        rSocket = dims.POD / 2
        # The socket length is actually dims.H - dims.J. But we do it longer
        # to prevent problems with bulean operations
        hSocket = dims.H
        socket1 = Part.makeCylinder(rSocket, hSocket, aux["p5"], aux["p5"])
        socket2 = Part.makeCylinder(rSocket, hSocket, aux["p6"], aux["p6"])

        inner = bentPart.fuse([chan1, chan2, socket1, socket2])
        return inner

    @staticmethod
    def createShape(obj):
        outer = Elbow.createOuterPart(obj)
        inner = Elbow.createInnerPart(obj)
        return outer.cut(inner)

    def execute(self, obj):
        # Create the shape of the elbow.
        shape = Elbow.createShape(obj)
        obj.Shape = shape
        # Recalculate ports.
        obj.Ports = self.getPorts(obj)

    def getPorts(self, obj):
        dims = Elbow.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        # FreeCAD.Console.PrintMessage("Ports are %s and %s"%(aux["p5"], aux["p6"]))
        return [aux["p5"], aux["p6"]]

    def getPortRotationAngles(self, obj):
        """Calculate coordinates of the ports rotation and return them as vectorsself.

        x = Yaw
        y = Pitch
        z = Roll
        """
        dims = Elbow.extractDimensions(obj)
        half = dims.BendAngle / 2
        # -45° and 135° are rotation of 0° elbow. They acts as a refence for a bent elbow.
        end0 = FreeCAD.Vector(-45 + half.Value, 0, 0)
        end1 = FreeCAD.Vector(135 - half.Value, 0, 0)
        return [end0, end1]


class ElbowBuilder:
    """Create elbow using Dodo/Flamingo."""

    def __init__(self, document):
        self.dims = ElbowMod.Dimensions()
        self.pos = FreeCAD.Vector(0, 0, 0)  # Define default initial position.
        self.document = document

    def create(self, obj):
        """Create an elbow."""
        elbow = Elbow(obj, PSize="", BendAngle=self.dims.BendAngle, M=self.dims.M, POD=self.dims.POD,
                      PThk=self.dims.PThk, H=self.dims.H, J=self.dims.J)
        obj.ViewObject.Proxy = 0
        obj.Placement.Base = self.pos

        return elbow


# Test builder.
def TestElbow():
    document = FreeCAD.activeDocument()
    builder = ElbowBuilder(document)
    feature = document.addObject("Part::FeaturePython", "OSE-Elbow")
    # builder.dims.BendAngle = FreeCAD.Units.parseQuantity("90 deg")
    builder.create(feature)
    document.recompute()

# TestElbow()
