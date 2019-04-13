# -*- coding: utf-8 -*-
# Authors: oddtopus, Ruslan Krenzler
# Date: 8. April 2018

# Create a cross-fitting using Flamingo workbench.

import FreeCAD
import Part
from pipeFeatures import pypeType  # the parent class
import OsePiping.Cross as CrossMod


class Cross(pypeType):
    def __init__(self, obj, PSize="90degBend20x10", dims=CrossMod.Dimensions()):
        # run parent __init__ and define common attributes
        super(Cross, self).__init__(obj)
        obj.PType = "OSE_Cross"
        obj.PRating = "CrossFittingFromAnyCatalog"
        obj.PSize = PSize  # Pipe size
        # define specific attributes
        # Properties
        obj.addProperty("App::PropertyLength", "G", "Cross",
                        "G  dimension of the cross.").G = dims.G
        obj.addProperty("App::PropertyLength", "G1", "Cross",
                        "G1  dimension of the cross.").G1 = dims.G1
        obj.addProperty("App::PropertyLength", "H", "Cross",
                        "Distance from the center to the left end.").H = dims.H
        obj.addProperty("App::PropertyLength", "H1", "Cross",
                        "Dimension from the center to the bottom end.").H1 = dims.H1
        obj.addProperty("App::PropertyLength", "L", "Cross",
                        "Horizontal length of the cross.").L = dims.L
        obj.addProperty("App::PropertyLength", "L1", "Cross",
                        "Vertical length of the cross.").L1 = dims.L1
        obj.addProperty("App::PropertyLength", "M", "Cross",
                        "Outer diameter of the horizonal part.").M = dims.M
        obj.addProperty("App::PropertyLength", "M1", "Cross",
                        "Outer diameter of the vertical part.").M1 = dims.M1
        obj.addProperty("App::PropertyLength", "POD", "Cross",
                        "Pipe outer diameter of the horizontal part.").POD = dims.POD
        obj.addProperty("App::PropertyLength", "POD1", "Cross",
                        "Pipe outer Diameter of the vertical part.").POD1 = dims.POD1
        obj.addProperty("App::PropertyLength", "PThk", "Cross",
                        "Pipe wall thickness of the horizonal part").PThk = dims.PThk
        obj.addProperty("App::PropertyLength", "PThk1", "Cross",
                        "Pipe wall thickness of the vertical part").PThk1 = dims.PThk1
        obj.addProperty("App::PropertyString", "PartNumber",
                        "Cross", "Part number").PartNumber = ""
        obj.addProperty("App::PropertyVectorList", "Ports", "Cross",
                        "Ports relative positions.").Ports = self.getPorts(obj)
        obj.addProperty("App::PropertyVectorList", "PortRotationAngles", "Cross",
                        "Ports rotation angles.").PortRotationAngles = self.getPortRotationAngles(obj)
        # Make Ports read only.
        obj.setEditorMode("Ports", 1)
        obj.setEditorMode("PortRotationAngles", 1)

    def onChanged(self, obj, prop):
        # if you aim to do something when an attribute is changed
        # place the code here:
        # e.g. -> change PSize according the new alpha, PID and POD

        # Properties which can change port locations
        dim_properties = ["G", "G1"]

        if prop in dim_properties:
            # This function is called within __init__ too. Thus we need to wait untill
            # we have all dimensions attributes.
            if set(CrossMod.DIMENSIONS_USED).issubset(obj.PropertiesList):
                obj.Ports = self.getPorts(obj)

    @classmethod
    def extractDimensions(cls, obj):
        dims = CrossMod.Dimensions()
        dims.G = obj.G
        dims.G1 = obj.G1
        dims.H = obj.H
        dims.H1 = obj.H1
        dims.L = obj.L
        dims.L1 = obj.L1
        dims.M = obj.M
        dims.M1 = obj.M1
        dims.POD = obj.POD
        dims.POD1 = obj.POD1
        dims.PThk = obj.PThk
        dims.PThk1 = obj.PThk1
        return dims

    @classmethod
    def createOuterPart(cls, obj):
        dims = cls.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        hr = dims.M / 2
        hor_cylinder = Part.makeCylinder(
            hr, dims.L, aux["p1"], FreeCAD.Vector(1, 0, 0))
        vr = dims.M1 / 2
        vert_cylinder = Part.makeCylinder(vr, dims.L1, aux["p4"])
        outer = hor_cylinder.fuse(vert_cylinder)
        return outer

    @classmethod
    def createInnerPart(cls, obj):
        dims = cls.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        p1 = aux["p1"]
        p3 = aux["p3"]
        p4 = aux["p4"]
        p6 = aux["p6"]
        pid = dims.PID()
        pid1 = dims.PID1()
        pod = dims.POD
        pod1 = dims.POD1
        hr = pid / 2
        hor_cylinder = Part.makeCylinder(
            hr, dims.L, p1, FreeCAD.Vector(1, 0, 0))
        vr = pid1 / 2
        vert_cylinder = Part.makeCylinder(vr, dims.L1, p4)

        # Create sockets.
        socket_left = Part.makeCylinder(
            pod / 2, dims.socketDepthLeft(), p1, FreeCAD.Vector(1, 0, 0))
        socket_right = Part.makeCylinder(
            pod / 2, dims.socketDepthRight(), p3, FreeCAD.Vector(1, 0, 0))
        socket_bottom = Part.makeCylinder(
            pod1 / 2, dims.socketDepthBottom(), p4)
        socket_top = Part.makeCylinder(pod1 / 2, dims.socketDepthTop(), p6)

        # Combine all cylinders.
        inner = hor_cylinder.fuse([vert_cylinder, socket_left,
                                   socket_right, socket_bottom, socket_top])
        return inner

    @classmethod
    def createShape(cls, obj):
        outer = cls.createOuterPart(obj)
        inner = cls.createInnerPart(obj)
        return outer.cut(inner)
        # return outer

    def execute(self, obj):
        # Create the shape of the tee.
        shape = self.createShape(obj)
        obj.Shape = shape
        # Recalculate ports.
        obj.Ports = self.getPorts(obj)

    def getPorts(self, obj):
        dims = Cross.extractDimensions(obj)
        aux = dims.calculateAuxiliararyPoints()
        return [aux["p2"], aux["p3"], aux["p5"], aux["p6"]]

    @classmethod
    def getPortRotationAngles(cls, obj):
        """Calculate coordinates of the ports rotation and return them as vectorsself.

        x = Yaw
        y = Pitch
        z = Roll
        """
        left = FreeCAD.Vector(180, 0, 180)
        right = FreeCAD.Vector(0, 0, 0)
        bottom = FreeCAD.Vector(0, 90, 0)
        top = FreeCAD.Vector(0, -90, 0)
        return [left, right, bottom, top]


class CrossBuilder:
    """Create a cross using flamingo."""

    def __init__(self, document):
        self.dims = CrossMod.Dimensions()
        self.pos = FreeCAD.Vector(0, 0, 0)  # Define default initial position.
        self.document = document

    def create(self, obj):
        """Create a cross."""
        cross = Cross(obj, PSize="", dims=self.dims)
        obj.ViewObject.Proxy = 0
        obj.Placement.Base = self.pos
        # rot=FreeCAD.Rotation(FreeCAD.Vector(0,0,1), self.Z)
        # obj.Placement.Rotation=rot.multiply(obj.Placement.Rotation)
        # feature.ViewObject.Transparency=70
        return cross

# Test builder.


def TestPart():
    document = FreeCAD.activeDocument()
    builder = CrossBuilder(document)
    feature = document.addObject("Part::FeaturePython", "OSE-Cross")
    builder.create(feature)
    document.recompute()

# TestPart()
