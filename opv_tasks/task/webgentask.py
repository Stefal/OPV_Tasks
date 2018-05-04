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
# Description: Generate the camapaign pannellum config and copy config asset.

from opv_tasks.task import Task
from opv_api_client import ressources
from path import Path
import json
import tempfile
import os
import shutil


class WebgenTask(Task):
    """
        Generate the camapaign pannellum config and copy config asset.
        Input format :
            opv-task webgen '{"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE }'
        Output format :
            WEB_PATH
    """
    TASK_NAME = "webgen"
    requiredArgsKeys = ["id_campaign", "id_malette"]
    BASE_TEMPLATE_REL_PATH = "../ressources/base.html"

    def findLot(self):
        """
            Generate a list of lot who are usable and who will be put in pannellum
            A lot is usable when it is assemble and he had trackedge
        """
        self.campaign = self._client_requestor.make(ressources.Campaign, self.campaign_id, self.malette_id)
        self.usable_lot = []

        self.logger.info("Find usable lot")

        for lot in self.campaign.lots:
            if lot.tile is not None:
                if len(lot.track_edges) != 0:
                    self.usable_lot.append(lot)
                    self.logger.info("Lot number {}-{} is an usable lot and will be put in pannellum config".format(lot.id_lot, lot.id_malette))

    def generateConf(self):
        """
            Take the list of usable lot given by findLot to generate pannellum conf.
        """

        self.logger.info("Generate config for pannellum")
        self.conf = {}

        self.conf["default"] = {}
        self.conf["default"]["autoLoad"] = True
        self.conf["default"]["author"] = "Open Path View CC-BY-SA"
        self.conf["default"]["title"] = "Redebro"
        self.conf["default"]["firstScene"] = "{}-{}".format(self.usable_lot[0].id_lot, self.usable_lot[0].id_malette)

        scenes = {}

        for lot in self.usable_lot:
            lot_name = "{}-{}".format(lot.id_lot, lot.id_malette)

            scenes[lot_name] = {}
            scenes[lot_name]["title"] = lot_name
            sensors = self._client_requestor.make(ressources.Sensors, lot.sensors.id_sensors, lot.sensors.id_malette)
            scenes[lot_name]["gps"] = sensors.gps_pos["coordinates"]
            scenes[lot_name]["type"] = "multires"
            scenes[lot_name]["multiRes"] = {}
            scenes[lot_name]["multiRes"]["extension"] = lot.tile.extension
            scenes[lot_name]["multiRes"]["tileResolution"] = lot.tile.resolution
            scenes[lot_name]["multiRes"]["basePath"] = "poc/"+lot.tile.param_location
            scenes[lot_name]["multiRes"]["cubeResolution"] = lot.tile.cube_resolution
            scenes[lot_name]["multiRes"]["path"] = "/%l/%s%y_%x"
            scenes[lot_name]["multiRes"]["maxLevel"] = lot.tile.max_level
            scenes[lot_name]["multiRes"]["preview"] = "poc/"+lot.tile.panorama.equirectangular_path
            scenes[lot_name]["multiRes"]["fallbackPath"] = "poc/"+lot.tile.fallback_path
            scenes[lot_name]["hotSpots"] = []

            for track_edge in lot.track_edges:
                track_edge = self._client_requestor.make(ressources.TrackEdge, track_edge["id_track_edge"], track_edge["id_malette"])

                hotspot = {}
                hotspot["type"] = "scene"
                hotspot["text"] = "{}-{}".format(track_edge.lot_to.id_lot, track_edge.lot_to.id_malette)
                hotspot["sceneId"] = "{}-{}".format(track_edge.lot_to.id_lot, track_edge.lot_to.id_malette)
                hotspot["yaw"] = track_edge.yaw
                hotspot["pitch"] = track_edge.pitch
                hotspot["targetYaw"] = track_edge.targetYaw
                hotspot["targetPitch"] = track_edge.targetPitch

                scenes[lot_name]["hotSpots"].append(hotspot)

        self.conf["scenes"] = scenes
        self.conf = json.dumps(self.conf)

        self.logger.info("Apply config")

        with open(self.html_file, "br") as f:
            html_code = f.read().decode("utf-8")

        html_code = html_code.replace("JSON_DATA", self.conf)

        with open(self.html_file, "w") as f:
            f.write(html_code)

    def createDir(self):
        """
            Create data dir who contain web site of the campaign and put the asset of the usable lot
        """
        self.logger.info("Create web directory")
        self.web_path = Path(tempfile.TemporaryDirectory().name)
        self.web_path.mkdir_p()
        self.poc_path = self.web_path / "poc"
        self.poc_path.mkdir_p()
        self.html_file = Path(os.path.split(__file__)[0]) / self.BASE_TEMPLATE_REL_PATH
        self.html_file.copyfile(self.web_path / "{}.html".format(self.campaign.name))
        self.html_file = self.web_path / "{}.html".format(self.campaign.name)

        self.logger.info("The web directory is store here : "+self.web_path)

        self.logger.info("Put asset in the web directory")
        for lot in self.usable_lot:
            with self._opv_directory_manager.Open(lot.tile.param_location) as (name, dir_path):
                loc = Path(dir_path)
                shutil.copytree(loc, self.poc_path / name, copy_function=os.link)
            with self._opv_directory_manager.Open(lot.tile.fallback_path) as (name, dir_path):
                loc = Path(dir_path)
                shutil.copytree(loc, self.poc_path / name, copy_function=os.link)
            with self._opv_directory_manager.Open(lot.tile.panorama.equirectangular_path) as (name, dir_path):
                loc = Path(dir_path)
                shutil.copytree(loc, self.poc_path / name, copy_function=os.link)

    def runWithExceptions(self, options={}):
        """
            Run webgen task with exception
        """
        self.checkArgs(options)

        self.campaign_id = options["id_campaign"]
        self.malette_id = options["id_malette"]

        self.findLot()
        self.createDir()
        self.generateConf()
        self.logger.info("Done ! You can find you website here "+self.web_path+" but be careful you must add the pannellum lib !")
        return self.web_path
