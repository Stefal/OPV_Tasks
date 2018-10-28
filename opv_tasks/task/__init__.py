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

from opv_tasks.task.taskStatusCode import TaskStatusCode
from opv_tasks.task.taskReturn import TaskReturn
from opv_tasks.task.taskException import TaskException
from opv_tasks.task.task import Task, TaskInvalidArgumentsException
from opv_tasks.task.rotatetask import RotateTask
from opv_tasks.task.cpfindtask import CpfindTask
from opv_tasks.task.autooptimisertask import AutooptimiserTask
from opv_tasks.task.stitchabletask import StitchableTask
from opv_tasks.task.stitchtask import StitchTask
from opv_tasks.task.tilingtask import TilingTask
from opv_tasks.task.photospheretask import PhotosphereTask
from opv_tasks.task.injectcpapntask import InjectcpapnTask
from opv_tasks.task.findnearestcptask import FindnearestcpTask
from opv_tasks.task.osfmextracttask import OsfmextractTask
from opv_tasks.task.osfmsavetask import OsfmsaveTask
from opv_tasks.task.osfmlaunchtask import OsfmlaunchTask
from opv_tasks.task.osfmalltask import OsfmallTask
from opv_tasks.task.makealltask import MakeallTask
from opv_tasks.task.pathfindertask import PathfinderTask
from opv_tasks.task.webgentask import WebgenTask
from opv_tasks.task.osfmcampaigntask import OsfmcampaignTask
