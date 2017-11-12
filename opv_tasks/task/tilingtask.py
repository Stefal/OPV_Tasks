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

# Contributors: tristan GOUGE <gouge.tristan@openpathview.fr>
# Email: team@openpathview.fr
# Description: Tile the Panorama

from path import Path
import json
import tempfile

from opv_api_client import ressources

from .task import Task
from opv_tasks.const import Const
from opv_tasks.third_party.tile import tile

class TilingTask(Task):
    """
    Tile the panorama, for pannellum.
    Input format :
        opv-task tiling '{"id_panorama": ID_PANORAMA, "id_malette": ID_MALETTE }'
    Output format :
        {"id_tile": ID_TILE, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "tiling"
    requiredArgsKeys = ["id_panorama", "id_malette"]

    TILESIZE = 512
    CUBESIZE = 0
    QUALITY = 75
    PNG = False

    def tile(self, pano_path):
        """A tile."""
        with tempfile.TemporaryDirectory() as output_dirpath:
            output_dirpath = Path(output_dirpath) / "output"

            tile(
                inputFile=pano_path,
                output=output_dirpath,
                tileSize=self.TILESIZE,
                cubeSize=self.CUBESIZE,
                quality=self.QUALITY,
                png=self.PNG)

            self.tile = self._client_requestor.make(ressources.Tile)
            self.tile.id_malette = self.pano.id_malette

            with self._opv_directory_manager.Open() as (param_uuid, param_location):
                for loc in output_dirpath.glob("[0-9]*"):
                    loc.move(param_location)
                self.tile.param_location = param_uuid

            with self._opv_directory_manager.Open() as (fallback_uuid, fallback_location):
                (output_dirpath / "fallback").move(fallback_location)
                self.tile.fallback_path = fallback_uuid

            with open(output_dirpath / "config.json") as fp:
                tile_config = json.load(fp)["multiRes"]

                self.tile.extension = tile_config["extension"]
                self.tile.max_level = tile_config['maxLevel']
                self.tile.resolution = tile_config['tileResolution']
                self.tile.cube_resolution = tile_config['cubeResolution']

            self.tile.panorama = self.pano
            self.tile.create()

            self.pano.cp.get()
            self.pano.cp.lot.get()
            self.logger.debug(self.pano.cp.lot)
            lot = self.pano.cp.lot

            lot.tile = self.tile
            lot.save()

    def runWithExceptions(self, options={}):
        """Run the tilling task my faverite one."""
        self.checkArgs(options)
        self.pano = self._client_requestor.make(ressources.Panorama, options["id_panorama"], options["id_malette"])
        with self._opv_directory_manager.Open(self.pano.equirectangular_path) as (_, pano_dirpath):
            pano_path = Path(pano_dirpath) / Const.PANO_FILENAME

            self.tile(pano_path)

        return self.tile.id
