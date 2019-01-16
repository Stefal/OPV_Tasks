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
# Description: Modify the pano settings.

import os
from path import Path
from shutil import copyfile

from opv_api_client import ressources

from opv_tasks.const import Const
from opv_tasks.task import Task, TaskException


class PanomodifyTask(Task):
    """
    Optimise Panorama with cli pano_modify. Takes CP in input (id_cp and id_malette needed).
    Input format :
        opv-task panomodify '{"id_cp": ID_CP, "id_malette": ID_MALETTE }'
    Output format :
        {"id_cp": ID_CP, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "panomodify"

    PANOMODIFY_OPTIONS = ["--straighten", "--fov=360x180"]
    TMP_PTONAME = "opt.pto"
    TMP_OUTPUT = "out.pto"

    requiredArgsKeys = ["id_cp", "id_malette"]

    def modify(self):
        """Modify Pano."""
        with self._opv_directory_manager.Open(self.cp.pto_dir) as (_, pto_dirpath):
            proj_pto = Path(pto_dirpath) / Const.CP_PTO_FILENAME

            lot = self._client_requestor.make(ressources.Lot, *self.cp.lot.id.values())

            with self._opv_directory_manager.Open(lot.pictures_path) as (_, pictures_dir):
                local_tmp_pto = Path(pictures_dir) / self.TMP_PTONAME
                local_tmp_output = Path(pictures_dir) / self.TMP_OUTPUT

                self.logger.debug("Copy pto file " + proj_pto + " -> " + local_tmp_pto)
                copyfile(proj_pto, local_tmp_pto)

                options = list(self.PANOMODIFY_OPTIONS)
                options.append("-o")
                options.append(local_tmp_output)  # Add output
                options.append(local_tmp_pto)  # Add input pto
                self.logger.debug("Running : " + "panomodify" + " ".join(options))
                exitCode = self._run_cli("pano_modify", options)

                if exitCode != 0:
                    raise PanomodifyException(cli_options=options)

                #self.cp.optimized = True
                #import ipdb; ipdb.set_trace()
                os.rename(local_tmp_output, proj_pto)  # Copy back optimized version
                os.unlink(local_tmp_pto)

    def runWithExceptions(self, options={}):
        """Run pano modify task."""
        self.checkArgs(options)

        self.cp = self._client_requestor.make(ressources.Cp, options['id_cp'], options['id_malette'])

        self.modify()

        self.cp.save()

        return self.cp.id     # Return id_cp and id_malette in a dict

class PanomodifyException(TaskException):
    """ Raised when there is an optimisation error"""

    def __init__(self, cli_options):
        """ Exception with command line options """
        self.cli_options = cli_options

    def getErrorMessage(self):
        return "Panomodifiy failed with the following options : " + repr(self.cli_options)
