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

# Contributors: Christophe NOUCHET <christophe.nouchet@openpathview.fr>
# Email: team@openpathview.fr
# Description: Just a little workaround to launch cli command

import sys
import subprocess


def run_cli(cmd, args=[], stdout=sys.stdout, stderr=subprocess.STDOUT):
    """
    Run a command.

    :param cmd: Command to use
    :param args: Args to pass to the command
    :param stdout:
    :param stderr:
    :return: return code of the cli
    """
    my_cmd = cmd if isinstance(cmd, list) else [cmd]
    my_args = args if isinstance(args, list) else [args]
    ret = subprocess.run(my_cmd + my_args, stdout=stdout, stderr=stderr)
    return ret.returncode


def runTask(dm_c, db_c, task_name, inputData):
    """
    Run task.
    Return a TaskReturn.
    """
    Task = find_task(task_name)
    if not Task:
        raise Exception('Task %s not found' % task_name)

    task = Task(client_requestor=db_c, opv_directorymanager_client=dm_c)
    return task.run(options=inputData)


def find_task(taskName):
    """Find the task with taskName."""
    try:
        moduleTask = __import__("opv_tasks.task.{}task".format(taskName))
        task = getattr(moduleTask, "{}Task".format(taskName.title()))
        return task
    except (ImportError, AttributeError) as e:
        return None  # Task not found


def generateHelp(taskName):
    Task = find_task(taskName)
    lines = Task.__doc__.split("\n")
    lines = [l for l in lines if not l.isspace() and '' != l]
    baseLeadingSpaces = len(lines[0]) - len(lines[0].lstrip(' '))
    baseSpaces = "    "                         # base margin
    descriptionSpaces = "                "      # padding between command description lines
    linesStriped = [l[baseLeadingSpaces:] for l in lines]   # removing margin for __doc__
    firstline = baseSpaces + taskName + ' ' * (len(descriptionSpaces) - len(taskName)) + linesStriped[0]
    othersLines = [baseSpaces + descriptionSpaces + l for l in linesStriped[1:]]
    return firstline + "\n" + "\n".join(othersLines)
