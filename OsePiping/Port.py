# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 November 2018
# Advanced Ports. Ports with normal vector and rotation references.

import FreeCAD


class AdvancedPort:
    def __init__(self, base=None, rotation=None):

        if base is None:
            base = FreeCAD.Vector(0, 0, 0)

        if rotation is None:
            rotation = FreeCAD.Rotation(0, 0, 0)

        self.placement = FreeCAD.Placement(base, rotation)

    def getNormal(self):
        return self.placement.Rotation.multVec(FreeCAD.Vector(1, 0, 0))

    def getAngleReference(self):
        return self.placement.Rotation.multVec(FreeCAD.Vector(0, 1, 0))

    def getPartRotation(self, other_placement, other_port):
        """Return a rotation matrix wich will rotate this port to the other port.

        param other_part_rot: Rotation of the other pArt.
        param other_port: other pOrt.

        """
        # Note: Multiplication of rotation matrices is commutative!
        # Apply operations from right to left.
        # Rotat itself back, such that normal points to x axis and angle reference
        # r points to y axis.
        A_inv = self.placement.Rotation.inverted()
        print("A_inv " + str(A_inv.toEuler()))
        # Rotate the port such that the x axis shows back, but the angle reference
        # coinsides with previous one.
        A_r = FreeCAD.Rotation(0, 180, 0)
        # print("A_r " + str(A_r.toEuler()))
        A = other_port.placement.Rotation
        # print("A " + str(A.toEuler()))
        R = other_placement.Rotation
        # print("R " + str(R.toEuler()))
        B = R.multiply(A.multiply(A_r.multiply(A_inv)))
        # print("B " + str(B.toEuler()))
        return B

    def getPartBase(self, other_placement, other_port):
        # Check find first the global bosition of the other portself.
        other_g_base = other_placement.Base + \
            other_placement.Rotation.multVec(other_port.placement.Base)
        # Get new rotation.
        B = self.getPartRotation(other_placement, other_port)
        # Get new port positon taking in account the adjusting rotation.
        adjusted_base = B.multVec(self.placement.Base)
        return other_g_base - adjusted_base

    def getPartPlacement(self, other_placement, other_port):
        """Return new part placment adjusted to the port of the other part."""
        return FreeCAD.Placement(self.getPartBase(other_placement, other_port=other_port),
                                 self.getPartRotation(other_placement, other_port=other_port))


def testPorts():
    # Port 0 in a tee.
    port1 = AdvancedPort(FreeCAD.Vector(0, 0, 2), FreeCAD.Rotation(0, -90, 0))
    # Port 2 in a tee.
    port2 = AdvancedPort(FreeCAD.Vector(-2, 0, 0),
                         FreeCAD.Rotation(180, 0, 180))
    part_placement = FreeCAD.Placement()
    # part_placement = FreeCAD.Placement(FreeCAD.Vector(0, 1, 1), FreeCAD.Rotation(0, 0, 0))

    print(port1.placement)
    print(port2.placement)

    print(port2.getPartPlacement(part_placement, port1))


def supportsAdvancedPort(part):
    """Check if the part contains advanced ports."""
    if part is None:
        return False
    if hasattr(part, "PortRotationAngles"):
        return True  # This is an OSE-fitting.
    if hasattr(part, "PType") and part.PType == u"Pipe":
        return True  # This is a Flamingo pipe.
    return False  # This is something else.


def _guessPipeAdvancedPorts(part):
    """Return port advanced port of a vertical streight flamingo pipe."""
    port_bottom = AdvancedPort(base=FreeCAD.Vector(
        part.Ports[0]), rotation=FreeCAD.Rotation(0, 90, 0))
    port_top = AdvancedPort(base=FreeCAD.Vector(
        part.Ports[1]), rotation=FreeCAD.Rotation(0, -90, 0))
    return [port_bottom, port_top]


def _extractAdvancedPorts(part):
    """Extract advanced ports from a FeaturePython part."""
    res = []
    for i in range(0, len(part.Ports)):
        rotation_angles = part.PortRotationAngles[i]
        rotation = FreeCAD.Rotation(
            rotation_angles.x, rotation_angles.y, rotation_angles.z)
        port = AdvancedPort(base=FreeCAD.Vector(
            part.Ports[i]), rotation=rotation)
        res.append(port)
    return res


def extractAdvancedPorts(part):
    if part.PType == u"Pipe":
        return _guessPipeAdvancedPorts(part)
    else:
        return _extractAdvancedPorts(part)


def getNearestPort(part_placement, ports, point):
    d_so_far = float("inf")
    closest_port = None
    for port in ports:
        global_pos = part_placement.Base + \
            part_placement.Rotation.multVec(port.placement.Base)
        d = global_pos.distanceToPoint(point)
        if d < d_so_far:
            d_so_far = d
            closest_port = port
    return closest_port


# testPorts()
