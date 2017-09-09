import json
import uuid
import math
import logging

from .task import Task
from opv_api_client import ressources
from opv_tasks.third_party.reconstructionUtils import ReconstructionUtils

from path import Path

class OpensfmTask(Task):
    """
    Launch opensfm with data of a campaign and will generate path between lot with opensfm output data.
    Input format :
        opv-task opensfm '{"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE }'
    Output format :
        {"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "opensfm"
    requiredArgsKeys = ["id_campaign", "id_malette"]

    def createDataDir(self):
        """
        Create opensfm data dir, make config file with default config and put photosphere in images directory.
        """

        default_config = """
        # OpenSfM will use the default parameters from opensfm/config.py
        # Set here any parameter that you want to override for this dataset
        # For example:
        processes: 8                  # Number of threads to use
        """

        tmp = "/tmp/"

        #make campaign directory
        self.campaign_data_dir = Path(tmp) / str(uuid.uuid4())
        image_dir = self.campaign_data_dir / "images"
        config_files = self.campaign_data_dir / "config.yaml"

        self.logger.info("Opensfm campaign data dir : "+self.campaign_data_dir)

        #create campaign and images directory
        self.campaign_data_dir.mkdir_p()
        image_dir.mkdir_p()

        #put default config in config file
        with open(config_files, "w+") as config:
            config.write(default_config)

        #this list will contain all panorama put in opensfm
        self.panorama_put_opensfm = []

        #link photosphere in images directory
        for lot in self.campaign.lots:
            #lot must be stiched ,tiled and photosphere must had photosphere tag
            if lot.tile["id_tile"] is not None:
                tile = self._client_requestor.make(ressources.Tile, lot.tile["id_tile"], lot.tile["id_malette"])
                if tile.panorama.id_panorama is not None:
                    if tile.panorama.is_photosphere:
                        #get the panorama path with opv directory manager
                        panorama_path = Path(self._opv_directory_manager.Open(tile.panorama.equirectangular_path).local_directory+"/panorama.jpg")
                        #copy panorama to our opensfm image data dir
                        panorama_path.link(image_dir / str(tile.panorama.id_panorama)+".jpg")

                        #add panorama to the list of panorama
                        self.panorama_put_opensfm.append(tile.panorama)
                        self.logger.debug("Panorama "+str(tile.panorama.id_panorama)+" (lot "+str(lot.id_lot)+") will be put in opensfm")


    def launchOpensfm(self):
        """Launch all task of opensfm in our data dir"""
        self._run_cli("opensfm_run_all", self.campaign_data_dir, stdout_level=logging.INFO, stderr_level=logging.INFO)
        #Path("/home/opv/reconstruction.meshed.json").link(self.campaign_data_dir+"/reconstruction.meshed.json")

    def getOutputData(self):
        """Read opensfm output data to convert them in usable data"""
        output_opensfm_file = self.campaign_data_dir / "reconstruction.meshed.json"

        #read file to get data of opensfm
        with open(output_opensfm_file, "r") as output_opensfm_data:
            #convert file data in json
            output_opensfm_json = json.load(output_opensfm_data)

            #first list in json is useless we can ignore here
            output_opensfm_json = output_opensfm_json[0]


        #list of  tuple : (1, 2)
        #1 --> gps cord
        #2 --> opensfm cord or None if opensfm can't treat the panorama
        self.output_data = {}

        #store data needed for every panorama put in opensfm
        for panorama in self.panorama_put_opensfm:
            sensors = self._client_requestor.make(ressources.Lot, panorama.cp.lot.id_lot, panorama.cp.lot.id_malette).sensors
            #if opensfm treat our panorama we will use opensfm data to generate path
            try:
                #get data for just our panorama
                panorama_data =  output_opensfm_json["shots"][str(panorama.id_panorama)+".jpg"]

                data = ReconstructionUtils().opticalCenter(panorama_data)

                self.output_data[panorama.id_panorama] = (sensors.gps_pos["coordinates"], data)

            #else we will use geolocalisation to generate path
            except KeyError:
                self.logger.warning("Panorama "+str(panorama.id_panorama)+" can't be treat by opensfm ! we must use geolocalisation to generate path (just for this pano)")
                #put gps cord and None in output data
                self.output_data[panorama.id_panorama] = (sensors.gps_pos["coordinates"], None)

    def getDistance(self, gpsCord1, gpsCord2):
        """Return the distance between 2 point in meter"""
        earth_radius = 6378
        #we want him in meter
        earth_radius = earth_radius * 1000

        #we must convert gps cord who are in degrees in radians
        gpsCord1 = [math.radians(gpsCord1[0]), math.radians(gpsCord1[1])]
        gpsCord2 = [math.radians(gpsCord2[0]), math.radians(gpsCord2[1])]

        #... found here https://www.zeguigui.com/weblog/archives/2006/05/calcul-de-la-di.php
        distance = earth_radius * (math.pi/2 - math.asin( math.sin(gpsCord2[0]) * math.sin(gpsCord1[0]) + math.cos(gpsCord2[1] - gpsCord1[1]) * math.cos(gpsCord2[0]) * math.cos(gpsCord1[0])))
        return distance

    def findNearPano(self):
        """Find panorama who are near another panorama"""
        min_distance = 15
        min_angle = 45

        #create a list of tuple who store panorama who are near
        #(1, 2, 3)
        #1 --> first pano
        #2 --> second pano
        #3 --> gps or opensfm --> if we need to use gps cord or opensfm cord
        self.near_panoramas = []

        for panorama in self.panorama_put_opensfm:
            panorama_not_far = []

            for anotherPanorama in self.panorama_put_opensfm:
                if panorama.id_panorama is not anotherPanorama.id_panorama:
                    distance = self.getDistance(self.output_data[panorama.id_panorama][0], self.output_data[anotherPanorama.id_panorama][0])

                    #if panorama is not to far another panorama
                    if distance <= min_distance:
                        #add him to panorama not far list
                        panorama_not_far.append((distance, anotherPanorama))


            angle_panorama_not_far_uses = []
            panorama_not_far.sort()

            for anotherPanorama in panorama_not_far:
                #if we can use opensfm translation
                if self.output_data[panorama.id_panorama][1] is not None and self.output_data[anotherPanorama[1].id_panorama][1] is not None:
                    diff_cord = [self.output_data[panorama.id_panorama][1][0] - self.output_data[anotherPanorama[1].id_panorama][1][0], self.output_data[panorama.id_panorama][1][1] - self.output_data[anotherPanorama[1].id_panorama][1][1]]
                else:
                    diff_cord = [self.output_data[panorama.id_panorama][0][0] - self.output_data[anotherPanorama[1].id_panorama][0][0], self.output_data[panorama.id_panorama][0][1] - self.output_data[anotherPanorama[1].id_panorama][0][1]]

                angle = math.degrees(math.atan2(diff_cord[0], diff_cord[1]))


                if len(angle_panorama_not_far_uses) is 0:
                    angle_panorama_not_far_uses.append(angle)
                    self.near_panoramas.append((panorama, anotherPanorama[1], "opensfm" if self.output_data[panorama.id_panorama][1] is not None and self.output_data[anotherPanorama[1].id_panorama][1] is not None else "gps"))

                else:
                    bad = 0
                    for angle_panorama_not_far_use in angle_panorama_not_far_uses:
                        result = angle - angle_panorama_not_far_use
                        if result < 0:
                            result = - result
                        if result <= min_angle:
                            bad += 1
                    if bad is  0:
                        angle_panorama_not_far_uses.append(angle)
                        self.near_panoramas.append((panorama, anotherPanorama[1], "opensfm" if self.output_data[panorama.id_panorama][1] is not None and self.output_data[anotherPanorama[1].id_panorama][1] is not None else "gps"))


    def generatePath(self):
        """Generate path between 2 pano using opensfm data"""
        #we treat every panorama
        for near_panorama in self.near_panoramas:
            #to know if we need to use opensfm translation or gps cord
            #0 --> gps cord
            #1 --> opensfm translation
            cord_use = 1 if near_panorama[2] is "opensfm" else 0

            diff_cord = [self.output_data[near_panorama[0].id_panorama][cord_use][0] - self.output_data[near_panorama[1].id_panorama][cord_use][0], self.output_data[near_panorama[0].id_panorama][cord_use][1] - self.output_data[near_panorama[1].id_panorama][cord_use][1]]

            lot = near_panorama[0].cp.lot
            lot_to = near_panorama[1].cp.lot

            yaw = math.degrees(math.atan2(diff_cord[0], diff_cord[1])) + 180

            while yaw < 0:
                yaw += 360

            while yaw > 360:
                yaw -= 360

            trackedge = self._client_requestor.make(ressources.TrackEdge)
            trackedge.lot_from = lot
            trackedge.lot_to = lot_to
            trackedge.id_malette = lot.id_malette
            trackedge.pitch = -45
            trackedge.yaw = yaw
            trackedge.targetPitch = 0
            trackedge.targetYaw = yaw
            trackedge.create()


        self.logger.info(str(len(self.near_panoramas))+" trackedge had been generate !")

    def deleteDataDir(self):
        """Delete opensfm data directory after used"""
        self.campaign_data_dir.rmtree_p()

    def runWithExceptions(self, options={}):
        self.checkArgs(options)

        #get the campaign
        self.campaign = self._client_requestor.make(ressources.Campaign, options["id_campaign"], options["id_malette"])

        self.createDataDir()
        self.launchOpensfm()
        self.getOutputData()
        self.findNearPano()
        self.generatePath()
        self.deleteDataDir()

        return self.campaign.id_campaign
