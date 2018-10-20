# coding: utf-8

# Copyright (C) 2017 Open Path View, Maison Du Libre
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Contributors: Benjamin BERNARD <benjamin.bernard@openpathview.fr>
# Email: team@openpathview.fr
# Description: Utils from OpenSFM reconstruction viewer (based on JS scripts converted into python)

import numpy as np


class ReconstructionUtils:
    """
    Utils fonctions for openSFM computation.
    """

    def math_clamp(self, x, a, b):
        """
        a if x < a else(b if x > b else x)
        :param x: numeric value
        :param a: numeric value
        :param b: numeric value
        :return: a if x < a else(b if x > b else x)
        """
        return a if x < a else(b if x > b else x)

    def angleTo(self, vectA, vectB):
        """
        Return angle between 2 vectors. Equivalent to Three.JS.Vect3.angleTo

        :param vectA: First vector.
        :param vectB: Second vector.
        :return: Angle between vectA and vectB in radian.
        """
        theta = np.vdot(vectA, vectB) / (np.linalg.norm(vectA) * np.linalg.norm(vectB))
        return np.arccos(self.math_clamp(theta, -1, 1))

    def projectOnVector(self, originalVector, projToVector):
        """
        Project originalVector to projToVector.

        :param originalVector: Vector that will on projected.
        :param projToVector: originalVector is projected on this vector.
        :return: resulted vector from the projection.
        """
        projToVector = self.normalize(projToVector)
        dot = np.vdot(originalVector, projToVector)
        return np.multiply(projToVector, dot)

    def projectOnPlane(self, originalVector, planeNormal):
        """
        Project on a plane using it's normal.

        :param originalVector: Vector to be projected.
        :param planeNormal: Plane normal.
        :return: originalVector projected on the plane defined by it's normal.
        """
        normalComponents = self.projectOnVector(originalVector, planeNormal)
        return np.subtract(originalVector, normalComponents)

    def normalize(self, v):
        """
        Noramlize a vector.

        :param v: vector to normalize.
        """
        norm = np.linalg.norm(v)
        if norm == 0:
            norm = np.finfo(v.dtype).eps
        return v / norm

    def make_axis_rotation_matrix(self, direction, angle):
        """
         Create a rotation matrix corresponding to the rotation around a general
         axis by a specified angle.

         R = dd^T + cos(a) (I - dd^T) + sin(a) skew(d)

         Parameters:

             angle : float a
             direction : array d
        """
        d = np.array(direction, dtype=np.float64)
        d /= np.linalg.norm(d)

        eye = np.eye(3, dtype=np.float64)
        ddt = np.outer(d, d)
        skew = np.array([[0, d[2], -d[1]],
                        [-d[2], 0, d[0]],
                        [d[1], -d[0], 0]], dtype=np.float64)

        mtx = ddt + np.cos(angle) * (eye - ddt) + np.sin(angle) * skew
        return mtx

    def rotate(self, vector, angleaxis):
        """
        Generate a rotation matix.

        :param vector: axis vector.
        :param angleaxis: angle axis.
        """
        angle = np.linalg.norm(angleaxis)
        vect = np.array(vector)
        normalizeAxis = self.normalize(angleaxis)
        matrix = self.make_axis_rotation_matrix(normalizeAxis, angle)
        r = vect.dot(matrix)
        return r

    def getImageOrientationVector(self, shot):
        """
        Do not return north, return image orientation
        """
        return self.rotate(
            [
                -shot["translation"][0],
                -shot["translation"][1],
                2-shot["translation"][2]
            ],
            np.negative(shot["rotation"])
        )

    def cordToVector(self, a, b):
        v = []
        if len(a) == len(b):
            for i in range(len(a)):
                v.append(a[i] - b[i])
        else:
            raise Exception("Cord must have the same dimention")

        return v

    def opticalCenter(self, shot):
        """
        Get the optical center (GPS corrected location optical center of the taken shot).

        :param shot: The shot. For instance : shot = {"rotation":[1.2844845146884538,-0.4039567957344671,0.49863528547935765],
        "translation":[0.17679172885835495,2.113070257988568,0.6904518682891717]}
        """
        angleaxis = [-shot["rotation"][0],
                     -shot["rotation"][1],
                     -shot["rotation"][2]]
        rt = self.rotate(shot["translation"], angleaxis)
        return np.negative(rt)
