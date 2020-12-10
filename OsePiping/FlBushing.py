# -*- coding: utf-8 -*-
# Authors: Ruslan Krenzler, oddtopus.
# Date: 25 March 2018
# Create a bushing using Flamingo workbench.

import FreeCAD
import Part
# Parent class from Dodo or Flamingo.
try:
    from pFeatures import pypeType
except ModuleNotFoundError:
    from pipeFeatures import pypeType
import OsePiping.Bushing as BushingMod


class Bushing(pypeType):
    def __init__(self, obj, PSize="", dims=BushingMod.Dimensions()):
        """Create a bushing."""
        # Run parent __init__ and define common attributes
        super(Bushing, self).__init__(obj)
        obj.PType = "OSE_Bushing"
        obj.PRating = "BushingFittingFromAnyCatalog"
        obj.PSize = PSize  # What is it for?
        # Define specific attributes and set their values.
        obj.addProperty("App::PropertyLength", "L", "Bushing",
                        "Bushing length").L = dims.L
        obj.addProperty("App::PropertyLength", "N", "Bushing", "N").N = dims.N
        obj.addProperty("App::PropertyLength", "POD", "Bushing",
                        "Large pipe outer diameter.").POD = dims.POD
        obj.addProperty("App::PropertyLength", "POD1", "Bushing",
                        "Small pipe outer diameter.").POD1 = dims.POD1
        obj.addProperty("App::PropertyLength", "PThk1", "Bushing",
                        "Small pipe thickness.").PThk1 = dims.PThk1
        obj.addProperty("App::PropertyVectorList", "Ports", "Bushing",
                        "Ports relative positions.").Ports = self.getPorts(obj)
        obj.addProperty("App::PropertyVectorList", "PortRotationAngles", "Bushing",
                        "Ports rotation angles.").PortRotationAngles = self.getPortRotationAngles(obj)
        obj.addProperty("App::PropertyString", "PartNumber",
                        "Bushing", "Part number").PartNumber = ""
        # Make Ports read only.
        obj.setEditorMode("Ports", 1)
        obj.setEditorMode("PortRotationAngles", 1)

    def onChanged(self, obj, prop):
        # Attributes changed, adjust the rest.
        dim_properties = ["L", "N"]  # Dimensions which change port locations
        if prop in dim_properties:
            # This function is called within __init__ too.
            # We wait for all dimension.
            if set(BushingMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
                obj.Ports = self.getPorts(obj)
                # We also wait until PortRotationAngles are defined.
                # We do not need to call getPortRotationAngles, when the fitting is created,
                # because during the createion getPortRotationAngles is called directly.
                if hasattr(obj, "PortRotationAngles"):
                    obj.PortRotationAngles = self.getPortRotationAngles(obj)

    @classmethod
    def extractDimensions(cls, obj):
        dims = BushingMod.Dimensions()
        dims.L = obj.L
        dims.N = obj.N
        dims.POD = obj.POD
        dims.POD1 = obj.POD1
        dims.PThk1 = obj.PThk1
        return dims

    @classmethod
    def createOctaThing(cls, obj):
        """Create Octagonal thing at the end of the bushing. I do not know its name."""
        dims = cls.extractDimensions(obj)
        aux = dims.auxiliararyPoints()
        X1 = dims.ThingThicknessA1()
        X2 = dims.ThingLengthA2()
        # Move the box into the center of the X,Y plane.
        center_pos = FreeCAD.Vector(-X2 / 2, -X2 / 2, 0) + aux["p4"]
        box1 = Part.makeBox(X2, X2, X1, center_pos)
        # rotate a box by 45° around the z.axis.
        box2 = Part.makeBox(X2, X2, X1, center_pos)
        box2.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), 45)
        return box1.common(box2)

    @classmethod
    def createOuterPart(cls, obj):
        dims = cls.extractDimensions(obj)
        aux = dims.auxiliararyPoints()
        outer_cylinder = Part.makeCylinder(dims.POD / 2, dims.L, aux["p1"])
        thing = Bushing.createOctaThing(obj)
        return outer_cylinder.fuse(thing)

    @classmethod
    def createInnerPart(cls, obj):
        dims = cls.extractDimensions(obj)
        aux = dims.auxiliararyPoints()

        # Remove inner part of the sockets.
        inner_cylinder = Part.makeCylinder(dims.PID1() / 2, dims.L, aux["p1"])
        inner_socket = Part.makeCylinder(
            dims.POD1 / 2, dims.L - dims.N, aux["p3"])

        # Make a cone for a larger socket. There are no dimensions for this con. Therefore
        # use simbolically a Radius such that the wall at the lower end is twice as thick
        # as in the upper end of socket.
        r1 = dims.POD / 2 - dims.ThicknessA3()
        r2 = dims.PID1() / 2
        hcone = dims.ConeLengthA4()
        socket_cone = Part.makeCone(r1, r2, hcone, aux["p1"])

        return inner_cylinder.fuse([inner_socket, socket_cone])

    @classmethod
    def createShape(cls, obj):
        outer = cls.createOuterPart(obj)
        inner = cls.createInnerPart(obj)
        return outer.cut(inner)

    def execute(self, obj):
        # Create the shape of the bushing.
        shape = self.createShape(obj)
        obj.Shape = shape
        # Recalculate ports.
        obj.Ports = self.getPorts(obj)

    def getPorts(self, obj):
        """Calculate coordinates of the ports."""
        dims = self.extractDimensions(obj)
        aux = dims.auxiliararyPoints()
        # For the bottom port use p3 too. Because there is no a1 dimension in my specification.
        return[aux["p3"], aux["p3"]]

    @classmethod
    def getPortRotationAngles(cls, obj):
        """Calculate coordinates of the ports rotation and return them as vectorsself.

        x = Yaw
        y = Pitch
        z = Roll
        """
        outer = FreeCAD.Vector(0, 90, 0)
        inner = FreeCAD.Vector(0, -90, 0)

        return [outer, inner]


class BushingBuilder:
    """Create a bushing using Dodo/Flamingo."""

    def __init__(self, document):
        self.dims = BushingMod.Dimensions()
        self.pos = FreeCAD.Vector(0, 0, 0)  # Define default initial position.
        self.document = document

    def create(self, obj):
        """Create a bushing.

        Before call it, call
        feature = self.document.addObject("Part::FeaturePython","OSE-Bushing")
        """
        bushing = Bushing(obj, PSize="", dims=self.dims)
        obj.ViewObject.Proxy = 0
        obj.Placement.Base = self.pos

        return bushing

# Create a test bushing.


def Test():
    document = FreeCAD.activeDocument()
    builder = BushingBuilder(document)
    feature = document.addObject("Part::FeaturePython", "OSE-Bushing")
    builder.create(feature)
    document.recompute()

# Test()
