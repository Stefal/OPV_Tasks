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

# Contributors: tristan GOUGE <gouge.tristan@openpathview.fr>, Benjamin BERNARD <benjamin.bernard@openpathview.fr>
# Email: team@openpathview.fr
# Description: Set in db isStichable if needed

from path import Path
from opv_tasks.task import Task, TaskException, TaskReturn, TaskStatusCode
from hsi import Panorama, ifstream
from opv_api_client import ressources
from opv_tasks.const import Const

class StitchableTask(Task):
    """
    Check a CP is stitchable, set in db isStichable if needed.
    Input format :
        opv-task stitchable '{"id_cp": ID_CP, "id_malette": ID_MALETTE }'
    Output format :
        {"id_cp": ID_CP, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "stitchable"
    requiredArgsKeys = ["id_cp", "id_malette"]

    def stichable(self, proj_pto):
        """Check if a proj_pto is stichable."""
        ifs = ifstream(proj_pto)

        p = Panorama()
        p.readData(ifs)

        cpv = p.getCtrlPoints()
        picLinkNb = [0 for x in range(4)]
        nbPoints = 0

        for cp in cpv:
            picLinkNb[self.huginPicNumber2Apnid(cp.image1Nr)] += 1
            picLinkNb[self.huginPicNumber2Apnid(cp.image2Nr)] += 1
            nbPoints += 1
        minLinksNeeded = 4

        self.logger.debug("Pic links number : " + str(picLinkNb))
        self.logger.debug("Computing stitchability")
        isStitchable = all(x >= minLinksNeeded for x in picLinkNb)

        self.cp.nb_cp = nbPoints
        self.cp.stichable = isStitchable
        self.cp.save()

        if not isStitchable:
            raise NotStichableException(picLinks=picLinkNb)

        self.logger.debug("CP : " + str(self.cp))

    def huginPicNumber2Apnid(self, huginPicNo):
        """
        Associate hugin APN id to real APN number.

        :param huginPicNo: Hugin image id.
        :retrun: Real APN number ID.
        """
        return Const.CP_HUGIN_IMGID_2_APNID[huginPicNo]

    def runWithExceptions(self, options={}):
        """Run a stichable task with options."""
        self.checkArgs(options)

        self.cp = self._client_requestor.make(ressources.Cp, options['id_cp'], options['id_malette'])
        self.logger.debug("CP : " + str(self.cp))
        with self._opv_directory_manager.Open(self.cp.pto_dir) as (_, pto_dirpath):
            proj_pto = Path(pto_dirpath) / Const.CP_PTO_FILENAME

            self.stichable(proj_pto)

        return self.cp.id

    def run(self, options={}):
        """ """
        try:
            ouput = self.runWithExceptions(options=options)
            return TaskReturn(taskName=self.TASK_NAME, statusCode=TaskStatusCode.SUCCESS, outputData=ouput, inputData=options)
        except NotStichableException as e:
            apnList = e.getPicturesWithNotEnoughLinks()
            if 0 in apnList:
                return TaskReturn(taskName=self.TASK_NAME, statusCode=TaskStatusCode.ERROR_CP_APN0, error="APN0 no CP", inputData=options, outputData=options)



class NotStichableException(TaskException):
    def __init__(self, picLinks):
        """ Exception with picture links """
        self.picLinks = picLinks

    def getPicturesWithNotEnoughLinks(self, minLinksAccepted=4):
        """
        Return the list of camera that to have enough links.

        :param minLinksAccepted: Minimum number of control points accepted (default is 4)
        :return: This list of all picture that have less links/CP than minLinksAccepted.
        """
        picsWithNotEnughLinks = []
        for huginPicNo, linksNb in enumerate(self.picLinks):
            if linksNb < minLinksAccepted:
                picsWithNotEnughLinks.append(huginPicNo)
        return picsWithNotEnughLinks

    def getErrorMessage(self):
        return "The following pictures " + str(self.getPicturesWithNotEnoughLinks()) + " don't have enough links/CP"
