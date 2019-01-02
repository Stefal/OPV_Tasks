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
# Description: Find control points using hugin cpfind.

import os
from shutil import copyfile
from path import Path
from opv_api_client import ressources

from opv_tasks.const import Const

from opv_tasks.task import Task, TaskException


class CpfindTask(Task):
    """
    Find keypoints using cpfind. Takes lot in input (id_lot and id_malette needed).
    Input format :
        opv-task cpfind '{"id_lot": ID_LOT, "id_malette": ID_MALETTE }'
    Output format :
        {"id_cp": ID_CP, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "cpfind"

    BASE_TEMPLATE_REL_PATH = "../ressources/base.pto"
    TMP_PTONAME = "cp.pto"
    TMP_OUTPUT = "out.pto"
    CPFIND_OPTIONS = [
        "--celeste",
        "--sieve1width", "25",
        "--sieve1height", "25",
        "--sieve1size", "625",
        "--kdtreesteps", "300"]

    requiredArgsKeys = ["id_lot", "id_malette"]

    def searchCP(self):
        """Run cli CP search."""
        # Getting base template
        this_dir, _ = os.path.split(__file__)
        base_pto_path = Path(this_dir) / self.BASE_TEMPLATE_REL_PATH

        with self._opv_directory_manager.Open(self.lot.pictures_path) as (_, pictures_dir):
            local_tmp_pto = Path(pictures_dir) / self.TMP_PTONAME
            tmp_output_pto = Path(pictures_dir) / self.TMP_OUTPUT
            self.logger.debug("Copy base template " + base_pto_path + " -> " + local_tmp_pto)
            copyfile(base_pto_path, local_tmp_pto)  # need pto to be local as pictures path are relatives

            options = list(self.CPFIND_OPTIONS)
            options.append('-o')  # output pto file
            options.append(tmp_output_pto)
            options.append(local_tmp_pto)          # input pto file
            self.logger.debug("Starting CP search with options" + " ".join(options))
            exitCode = self._run_cli("cpfind", options)
            self.logger.debug("cpfind exit code : " + str(exitCode))

            if exitCode != 0:
                raise CpFindException(options)

            cp_pto_dest = Path(self.ptoDirMan.local_directory) / Const.CP_PTO_FILENAME
            self.logger.debug("Moving " + local_tmp_pto + " -> " + cp_pto_dest + " (UUID : " + self.ptoDirMan.uuid + ")")
            os.unlink(local_tmp_pto)  # remove based file
            os.rename(tmp_output_pto, cp_pto_dest)  # copies PTO to is't directory man

    def findCP(self):
        """Initiate cp object and run search."""
        self.logger.info("Running cpfind for lot : " + str(self.lot.id))
        self.cp = self._client_requestor.make(ressources.Cp)
        self.cp.id_malette = self.lot.id_malette

        self.cp.search_algo_version = Const.CP_SEARCHALGO_VERSION

        self.cp.lot = self.lot

        self.ptoDirMan = self._opv_directory_manager.Open()
        self.cp.pto_dir = self.ptoDirMan.uuid

        self.searchCP()

        self.ptoDirMan.save()
        self.cp.create()

        self.logger.debug("Created CP :" + repr(self.cp))

    def runWithExceptions(self, options={}):
        """Run Cp find task."""

        self.checkArgs(options)
        self.lot = self._client_requestor.make(ressources.Lot, options['id_lot'], options['id_malette'])
        self.findCP()

        return self.cp.id


class CpFindException(TaskException):
    """
    Raised when cpfind cmd failed.
    """
    def __init__(self, cliOptions):
        self.cliOptions = cliOptions

    def getErrorMessage(self):
        return "cpfind failed with the following options : " + repr(copyfile)
