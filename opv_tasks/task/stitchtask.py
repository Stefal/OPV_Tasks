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
# Description: Stitch the panorama

from path import Path
from opv_tasks.task import Task, TaskException
from opv_api_client import ressources

from opv_tasks.const import Const


class StitchTask(Task):
    """
    Stitch the panorama.
    Input format :
        opv-task stitch '{"id_cp": ID_CP, "id_malette": ID_MALETTE }'
    Output format :
        {"id_panorama": ID_PANORAMA, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "stitch"
    requiredArgsKeys = ['id_cp', 'id_malette']

    TMP_PTONAME = 'tmp.pto'

    def stitch(self, proj_pto):
        """Stitch a projection."""
        exit_code = self._run_cli('hugin_executor', ["-s", proj_pto])

        if exit_code != 0:
            raise HuginExecutorException(self.cp.id, ["-s", proj_pto])

        with self._opv_directory_manager.Open() as (path_uuid, panorama_path):
            panorama_path = Path(panorama_path)

            pano_tif = proj_pto.dirname().glob('*.tif')[0]
            pano = panorama_path / Const.PANO_FILENAME

            self.logger.debug("Converting and moving pano from tif -> %s" % (panorama_path / Const.PANO_FILENAME))
            self._run_cli("convert", [pano_tif, pano])

            pano_tif.remove()  # remove tif to save place and transfer time

            self.logger.debug("Adding panorama in DB")
            self.panorama = self._client_requestor.make(ressources.Panorama)
            self.panorama.id_malette = self.cp.id_malette
            self.panorama.equirectangular_path = path_uuid
            self.panorama.cp = self.cp
            self.panorama.create()

    def runWithExceptions(self, options={}):
        """Run a StitchTask with options."""

        self.checkArgs(options)
        self.cp = self._client_requestor.make(ressources.Cp, options["id_cp"], options["id_malette"])

        if not self.cp.stichable:
            raise InvalidNotSitchaleException(self.cp.id)

        with self._opv_directory_manager.Open(self.cp.pto_dir) as (_, pto_dirpath):
            proj_pto = Path(pto_dirpath) / Const.CP_PTO_FILENAME

            with self._opv_directory_manager.Open(self.cp.lot.pictures_path) as (_, pictures_dir):
                local_tmp_pto = Path(pictures_dir) / self.TMP_PTONAME

                self.logger.debug("Copy pto file " + proj_pto + " -> " + local_tmp_pto)
                proj_pto.copyfile(local_tmp_pto)

                self.stitch(local_tmp_pto)

        return self.panorama.id

class HuginExecutorException(TaskException):
    """ hugin executor exception (non 0 exit code). """
    def __init__(self, idCp, cli_param):
        self.cli_param = cli_param
        self.idCp = idCp

    def getErrorMessage(self):
        return "hugin executor failed for CP " + str(self.idCp) + "with the following options : " + str(self.cli_param)

class InvalidNotSitchaleException(TaskException):
    """ When CP isn't stitchable. """
    def __init__(self, idCp):
        self.idCp = idCp

    def getErrorMessage(self):
        return "Panorama isn't stitchable, won't stich it. For idCP : " + str(self.idCp)
