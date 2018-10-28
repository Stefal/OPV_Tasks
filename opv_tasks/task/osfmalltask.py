from opv_tasks.task import Task
from opv_tasks.utils import runTask
from opv_tasks.const import Const
from opv_api_client import ressources
from path import Path

import datetime


class OsfmallTask(Task):
    """
        Launch taks osfmextract osfmlaunch osfmsave
        Input format :
            opv-task osfmall '{"ids_pano": IDS_PANO, "id_malette": ID_MALETTE }'
    """
    TASK_NAME = "osfmall"
    requiredArgsKeys = ["id_malette", "ids_pano"]

    def getReconstructionFolder(self, id_panorama, id_malette):
        panoramaSensor = self._client_requestor.make(ressources.PanoramaSensors, id_panorama, id_malette)
        id_campaign = panoramaSensor.id_campaign

        date = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")
        dir = Path(Const.OPENSFM_RECONSTRUCTION_FOLDER) / "{id_campaign}-{id_malette}_{date}".format(id_campaign=id_campaign, id_malette=id_malette, date=date)
        dir.makedirs()
        return dir

    def runWithExceptions(self, options={}):
        self.checkArgs(options)
        options["osfm_dir"] = self.getReconstructionFolder(id_panorama=options["ids_pano"][0], id_malette=options["id_malette"])
        self.logger.info("Osfm dir : {}".format(options["osfm_dir"]))
        self.logger.info("Launching task osfm extract")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmextract", options)
        self.logger.info("Launching task osfm launch")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmlaunch", options)
        self.logger.info("Launching task osfm save")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmsave", options)
