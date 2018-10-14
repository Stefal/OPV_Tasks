from opv_tasks.task import Task
from opv_tasks.utils import runTask
import tempfile


class OsfmallTask(Task):
    """
        Launch taks osfmextract osfmlaunch osfmsave
        Input format :
            opv-task osfmall '{"ids_pano": IDS_PANO, "id_malette": ID_MALETTE }'
    """
    TASK_NAME = "osfmall"
    requiredArgsKeys = ["id_malette", "ids_pano"]

    def runWithExceptions(self, options={}):
        self.checkArgs(options)
        options["osfm_dir"] = tempfile.mkdtemp()
        self.logger.info("Osfm dir : {}".format(options["osfm_dir"]))
        self.logger.info("Launching task osfm extract")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmextract", options)
        self.logger.info("Launching task osfm launch")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmlaunch", options)
        self.logger.info("Launching task osfm save")
        runTask(self._opv_directory_manager, self._client_requestor, "osfmsave", options)
