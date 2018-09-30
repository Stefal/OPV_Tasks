#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from setuptools import setup, find_packages

# Merci Sam & Max : http://sametmax.com/creer-un-setup-py-et-mettre-sa-bibliotheque-python-en-ligne-sur-pypi/

setup(
    name='opv_tasks',
    version='0.0.1',
    packages=find_packages(),
    author="Christophe NOUCHET",
    author_email="team@openpathview.fr",
    description="Open Path View Tasks",
    long_description=open('README.md').read(),
    dependency_links=[
        "git+https://github.com/OpenPathView/OPV_DBRest-client.git#egg=opv_api_client-0.2",
        "git+https://github.com/OpenPathView/DirectoryManagerClient.git#egg=opv_directorymanagerclient-0.1",
        "git+https://github.com/Valdimus/Atrevrix-Graphe.git#egg=atrevrix-graphe-0.0.1"
    ],
    install_requires=["path.py",
                      "docopt",
                      "pillow",
                      "python-xmp-toolkit",
                      "opv_api_client",
                      "opv_directorymanagerclient",
                      "atrevrix-graphe"
                      ],
    # Active la prise en compte du fichier MANIFEST.in
    include_package_data=True,
    url='https://github.com/OpenPathView/OPV_Tasks',
    entry_points={
        'console_scripts': [
            'opv-task = opv_tasks.__main__:main']
    },
    scripts=[],

    license="GPL3",
)
