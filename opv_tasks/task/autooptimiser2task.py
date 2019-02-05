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
# Description: Optimise CP geometrie.

import os
from path import Path
from shutil import copyfile

from opv_api_client import ressources

from opv_tasks.const import Const
from opv_tasks.task import Task, TaskException


class Autooptimiser2Task(Task):
    """
    Optimise CP with cli autooptimiser2. Takes CP in input (id_cp and id_malette needed).
    Input format :
        opv-task autooptimiser2 '{"id_cp": ID_CP, "id_malette": ID_MALETTE }'
    Output format :
        {"id_cp": ID_CP, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "autooptimiser2"

    AUTOOPTIMISER_OPTIONS = ["-n", "-m", "-l", "-s"]
    PTO_VAR_OPTIONS = ["--opt=y,p,r,v,b"]
    TMP_PTONAME = "opt.pto"
    TMP_OUTPUT = "out.pto"

    requiredArgsKeys = ["id_cp", "id_malette"]

    def optimise(self):
        """Optimise CP."""
        with self._opv_directory_manager.Open(self.cp.pto_dir) as (_, pto_dirpath):
            proj_pto = Path(pto_dirpath) / Const.CP_PTO_FILENAME

            lot = self._client_requestor.make(ressources.Lot, *self.cp.lot.id.values())

            with self._opv_directory_manager.Open(lot.pictures_path) as (_, pictures_dir):
                local_tmp_pto = Path(pictures_dir) / self.TMP_PTONAME
                local_tmp_output = Path(pictures_dir) / self.TMP_OUTPUT

                self.logger.debug("Copy pto file " + proj_pto + " -> " + local_tmp_pto)
                copyfile(proj_pto, local_tmp_pto)

                options = list(self.AUTOOPTIMISER_OPTIONS)
                options_pto_var = list(self.PTO_VAR_OPTIONS)
                options_pto_var.append("-o")
                options_pto_var.append(local_tmp_pto)
                options_pto_var.append(local_tmp_pto)
                options.append("-o")
                options.append(local_tmp_output)  # Add output
                options.append(local_tmp_pto)  # Add input pto
                self.logger.debug("Running: " + "pto_var" + " ".join(options_pto_var))
                exitCode = self._run_cli("pto_var", options_pto_var)
                self.logger.debug("Running: " + "autooptimiser" + " ".join(options))
                exitCode = self._run_cli("autooptimiser", options)

                if exitCode != 0:
                    raise AutooptimiserException(cli_options=options)

                self.cp.optimized = True

                os.rename(local_tmp_output, proj_pto)  # Copy back optimized verison
                os.unlink(local_tmp_pto)

    def runWithExceptions(self, options={}):
        """Run auto optimiser2 task."""
        self.checkArgs(options)

        self.cp = self._client_requestor.make(ressources.Cp, options['id_cp'], options['id_malette'])

        self.optimise()

        self.cp.save()

        return self.cp.id     # Return id_cp and id_malette in a dict

class Autooptimiser2Exception(TaskException):
    """ Raised when there is an optimisation error"""

    def __init__(self, cli_options):
        """ Exception with command line options """
        self.cli_options = cli_options

    def getErrorMessage(self):
        return "autooptimiser2 failed with the following options : " + repr(self.cli_options)
