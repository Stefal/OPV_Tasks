from opv_tasks.task import Task
from opv_api_client import ressources, Filter
from opv_tasks.utils import runTask



class OsfmcampaignTask(Task):
    """
        Launch the tasks osfm on all campaign panorama 
        Input format :
            opv-task osfmcampaign '{"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE, "active": ACTIVE}'
        Note that active tag is optional, if you set it to true, it will just use active panorama,
    """
    TASK_NAME = "osfmcampaign"
    requiredArgsKeys = ["id_malette", "id_campaign"]

    def runWithExceptions(self, options={}):
        self.checkArgs(options)
        
        if "active" in options and options["active"] == True:
            panoramas = self._client_requestor.make_all(ressources.Panorama, filters=(Filter("id_campaign")==options["id_campaign"], Filter("active")==True))
        else:
            panoramas = self._client_requestor.make_all(ressources.Panorama, filters=(Filter("id_campaign")==options["id_campaign"]))
        
        ids_panorama = [panorama.id_panorama for panorama in panoramas]

        self.logger.info("Panorama selected are : {}".format(ids_panorama))

        task_option = {
            "ids_pano": ids_panorama,
            "id_malette": options["id_malette"]
        }

        runTask(self._opv_directory_manager, self._client_requestor, "osfmall", task_option)