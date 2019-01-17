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
# Description: Manage picture rotation in portrait mode

from PIL import Image
import os
from path import Path

from opv_api_client import ressources

from opv_tasks.task import Task, TaskStatusCode, TaskException
from opv_tasks import Const


class RotateTask(Task):
    """
    Manage rotation for source set of images.
    Input format :
        opv-task rotate '{"id_lot": ID_LOT, "id_malette": ID_MALETTE }'
    Output format :
        {"id_lot": ID_LOT, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "rotate"
    requiredArgsKeys = ["id_lot", "id_malette"]

    def getPictureSizes(self, picPath):
        """Return (width, height) of the specified picture (picPath)."""
        with Image.open(picPath) as pic:
            width, height = pic.size

        return (width, height)

    def isPortrait(self, picPath):
        """Return true if a picture is in portrait mode."""
        x, y = self.getPictureSizes(picPath)
        self.logger.debug("Width: " + str(x) + "  Height: " + str(y))
        return x < y

    def rotatePic(self, rotation_angle, picPath):
        """
        Rotate picPath with rotation_angle.

        Modify picture in place !
        """
        self.logger.debug("Rotate pic " + picPath + " angle : " + str(rotation_angle))
        cli_code = self._run_cli('mogrify', ["-rotate", str(rotation_angle), picPath])

        if cli_code != 0:
            self.logger.debug("Rotate exceptions")
            raise RotateException(picPath, rotation_angle)

    def rotateToPortrait(self, picPath):
        """Rotate a picture to portrait format if necessary."""
        if not self.isPortrait(picPath):
            self.rotatePic(90, picPath)

    def rotateToPortraitAll(self):
        """Rotate all picture of lot to portrait."""
        if self.lot is not None and self.lot.pictures_path is not None:
            with self._opv_directory_manager.Open(self.lot.pictures_path) as (uuid, dir_path):
                for apnNo in range(Const.PIC_PER_LOT):
                    pic_path = Path(dir_path) / "APN{}.JPG".format(apnNo)
                    if os.path.exists(pic_path):
                        self.rotateToPortrait(pic_path)
                    else:
                        raise RotateException(filePath=dir_path, rotationAngle=90)

    def runWithExceptions(self, options={}):
        """
            Run a rotatetask.
            Requires id_lot and id_malette as inputData.
        """
        self.logger.debug("runWithExceptions start")
        self.checkArgs(options)
        self.lot = self._client_requestor.make(ressources.Lot, options['id_lot'], options['id_malette'])
        self.rotateToPortraitAll()
        return self.lot.id


class RotateException(TaskException):
    """
    Raised when file rotation fail.
    """

    def __init__(self, filePath, rotationAngle):
        self.filePath = filePath
        self.rotationAngle = rotationAngle

    def getErrorMessage(self):
        return "failed to rotate " + str(self.filePath) + ", with rotation angle : " + str(self.rotationAngle)
