from opv_tasks.task import Task
from opv_api_client import ressources
from path import Path
from PIL import Image
import json


class OsfmextractTask(Task):
    """
        Generate opensfm datadir and generate exif file
        Input format :
            opv-task osfmextract '{"ids_pano": IDS_PANO, "osfm_dir": OSDM_DIR, "id_malette": ID_MALETTE }'
    """
    TASK_NAME = "osfmextract"
    requiredArgsKeys = ["id_malette", "ids_pano", "osfm_dir"]
    DEFAULT_CONF = """processes: 8                  # Number of threads to use
depthmap_min_consistent_views: 2      # Min number of views that should reconstruct a point for it to be valid
"""

    def launch(self):
        self.osfm_dir = Path(self.osfm_dir)
        self.osfm_dir.mkdir_p()
        self.osfm_exif_dir = self.osfm_dir / "exif"
        self.osfm_exif_dir.mkdir_p()
        self.osfm_images_dir = self.osfm_dir / "images"
        self.osfm_images_dir.mkdir_p()

        for pano in self.pano_ids:
            pano = self._client_requestor.make(ressources.Panorama, pano, self.malette_id)

            pano_exif = {}
            pano_exif["projection_type"] = "equirectangular"
            pano_exif["orientation"] = 1
            pano_exif["focal_ratio"] = 0.0
            pano_exif["capture_time"] = 0.0
            pano_exif["make"] = "OpenPathView"
            pano_exif["model"] = "Rederbro"

            with self._opv_directory_manager.Open(pano.equirectangular_path) as (name, dir_path):
                pano_path = Path(dir_path) / "panorama.jpg"
                pano_path.link(self.osfm_images_dir / "{}.jpg".format(pano.id_panorama))
                size = self.getPictureSizes(pano_path)
                pano_exif["width"] = size[0]
                pano_exif["height"] = size[1]

            lot = self._client_requestor.make(ressources.Lot, pano.cp.lot.id_lot, self.malette_id)
            sensors = self._client_requestor.make(ressources.Sensors, lot.sensors.id_sensors, self.malette_id)
            coord = sensors.gps_pos["coordinates"]
            gps = {}
            gps["latitude"] = coord[0]
            gps["longitude"] = coord[1]
            gps["altitude"] = coord[2]
            pano_exif["gps"] = gps

            pano_exif["camera"] = "v2 {} {} {} {} {} {}".format(
                pano_exif["make"],
                pano_exif["model"],
                pano_exif["width"],
                pano_exif["height"],
                pano_exif["projection_type"],
                pano_exif["focal_ratio"]
            )

            with open(self.osfm_exif_dir / "{}.jpg.exif".format(pano.id_panorama), "w+") as f:
                json.dump(pano_exif, f, indent=4)

        with open(self.osfm_dir / "config.yaml", "w+") as conf:
            conf.write(self.DEFAULT_CONF)

    def getPictureSizes(self, picPath):
        """Return (width, height) of the specified picture (picPath)."""
        with Image.open(picPath) as pic:
            width, height = pic.size

        return (width, height)

    def runWithExceptions(self, options={}):
        """
            Run webgen task with exception
        """
        self.checkArgs(options)

        self.pano_ids = options["ids_pano"]
        self.malette_id = options["id_malette"]
        self.osfm_dir = options["osfm_dir"]

        self.launch()
