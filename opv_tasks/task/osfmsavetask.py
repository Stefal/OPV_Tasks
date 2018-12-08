from opv_tasks.task import Task
from path import Path
import json
from opv_api_client import ressources
from opensfm.geo import lla_from_topocentric
from geojson import Point
from math import degrees
from opv_tasks.third_party.reconstructionUtils import ReconstructionUtils


class OsfmsaveTask(Task):
    """
        Save osfm data
        Input format :
            opv-task osfmsave '{"osfm_dir": OSFM_DIR, "id_malette": ID_MALETTE }'
    """
    TASK_NAME = "osfmsave"
    requiredArgsKeys = ["id_malette", "osfm_dir"]

    def angleToNorthSigned(self, camVect):
        """
        Returns the angle to the north (y(0,1) vect) signed.
        :param camVect: camera vector
        :return: The angle to the north clock wise signed.
        """
        x = 0
        y = 1
        camVectNorm = self.reconstructionUtils.normalize(camVect)
        northVect = [0, 1]

        sin = camVectNorm[x]*northVect[y] - camVectNorm[y]*northVect[x]
        sinSign = 1 if sin >= 0 else -1

        return sinSign * self.reconstructionUtils.angleTo(
            northVect,
            camVect
        )

    def getPanosData(self):
        with open(self.dir / "reconstruction.json") as reconstructions:
            self.reconstructions = json.load(reconstructions)
            for reconstruction in self.reconstructions:
                for pano in reconstruction["shots"]:
                    data = reconstruction["shots"][pano]
                    pano = int(pano.split(".")[0])
                    self.logger.info("Panorama {} had been treat by opensfm".format(pano))
                    corrected_sensors = self._client_requestor.make(ressources.Sensors)
                    optical_center = self.reconstructionUtils.opticalCenter(data)
                    corrected_sensors.gps_pos = Point(
                        coordinates=lla_from_topocentric(
                            optical_center[0],
                            optical_center[1],
                            optical_center[2],
                            self.refLla["latitude"],
                            self.refLla["longitude"],
                            self.refLla["altitude"]
                        )
                    )
                    orientation = self.reconstructionUtils.cordToVector(self.reconstructionUtils.getImageOrientationVector(data), optical_center)
                    camVect = [orientation[i] for i in range(2)]
                    north_offset = degrees(self.angleToNorthSigned(camVect))

                    corrected_sensors.degrees = int(north_offset)
                    corrected_sensors.minutes = int((north_offset - int(north_offset)) * 60)
                    corrected_sensors.create()

                    pano = self._client_requestor.make(ressources.Panorama, pano, self.id_malette)
                    pano.sensors_reconstructed["id_sensors"] = corrected_sensors.id_sensors
                    pano.sensors_reconstructed["id_malette"] = corrected_sensors.id_malette
                    pano.save()

    def runWithExceptions(self, options={}):
        """
            Run webgen task with exception
        """
        self.checkArgs(options)
        self.reconstructionUtils = ReconstructionUtils()
        self.id_malette = options["id_malette"]

        self.dir = Path(options["osfm_dir"])

        with open(self.dir / "reference_lla.json", "r") as refLla:
            self.refLla = json.load(refLla)
            self.getPanosData()
