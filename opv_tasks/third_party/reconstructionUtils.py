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
