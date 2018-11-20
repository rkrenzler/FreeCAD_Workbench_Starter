# -*- coding: utf-8 -*-
# Author: Ruslan Krenzler.
# Date: 20 November 2018
# Advanced Ports. Ports with normal vector and rotation references.

import copy
import numpy
import FreeCAD


class AdvancedPort:
    def __init__(self, a=None, n=None, r=None):
        if a is None:
            self.a = FreeCAD.Vector(0, 0, 0)
        else:
            self.a = a

        if n is None:
            self.n = FreeCAD.Vector(1, 0, 0)
        else:
            self.n = n

        if r is None:
            self.r = FreeCAD.Vector(0, 0, 1)
        else:
            self.r = r

    def getStandardForm(self):
        """Return normalized version of the port."""
        ret = copy.copy(self)
        ret.n.normalize()
        ret.r.normalize()
        return ret

    def B(self):
        """Return matrix B embedded in tree dimensinal matrix."""
        b = self.n.cross(self.r)
        # Create a matrix (n,r,b)
        ret = numpy.array([list(self.n), list(self.r), list(b)]).transpose()
        return ret

    def C(self):
        """Return Create a matrix (-n,r,-b)."""
        b = self.n.cross(self.r)
        ret = numpy.array([list(-self.n), list(self.r), list(-b)]).transpose()
        return ret

    def _getRotation3DMatrix(self, other):
        """Return a rotation matrix wich will rotate this port to the other port."""
        C = other.getStandardForm().C()
        invB = numpy.linalg.inv(self.getStandardForm().B())
        A = C.dot(invB)
        return A

    def getTranslation(self, other):
        return other.a - self.a

    def _get_4D_matrix(self, other):
        ret = FreeCAD.Matrix()
        # Set rotation submatrix.
        A = self._getRotation3DMatrix(other)
        ret.A11 = A[0, 0]
        ret.A12 = A[0, 1]
        ret.A13 = A[0, 2]
        ret.A21 = A[1, 0]
        ret.A22 = A[1, 1]
        ret.A23 = A[1, 2]
        ret.A31 = A[2, 0]
        ret.A32 = A[2, 1]
        ret.A33 = A[2, 2]
        # Add tragetRutationhe 4-th column of ret.
        t = self.getTranslation(other)
        ret.A14 = t.x
        ret.A24 = t.y
        ret.A34 = t.z

        return ret

    def getRotation(self, other):
        """Get rotation, to orientate this port to the other."""
        m = self._get_4D_matrix(other)
        return FreeCAD.Rotation(m)


def testPorts():
    port1 = AdvancedPort()
    port2 = AdvancedPort()
    port2.va = FreeCAD.Vector(4, 4, 4)
    port2.vn = FreeCAD.Vector(1, 1, 1)

    print(port1)
    print(port1.getRutation(port1))
    print(port1.getTranslation(port1))

    print(port2)
    print(port2.getRutation(port1))
    print(port2.getTranslation(port1))


def supportsAdvancedPort(part):
    """Check if the part contains advanced ports."""
    return hasattr(part, 'PortNormals')


def extractAdvancedPort(part):
    """Extract advanced ports from a FeaturePython part."""
    res = []
    for i in range(0, len(part.Ports)):
        port = AdvancedPort(a=part.Ports[i], n=part.PortNormals[i], r=part.PortRotRefs[i])
        res.append(port)
    return res

def getNearestPort(ports, point):
    d_so_far = float("inf")
    closest_port = None
    for port in ports:
        d = port.a.distanceToPoint(point)
        if d < d_so_far:
            d_so_far = d
            closest_port = port
    return closest_port
