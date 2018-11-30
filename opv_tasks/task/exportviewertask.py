from opv_tasks.task import Task, TaskStatusCode
from opv_api_client import ressources, Filter
from path import Path
import tempfile
import json

class ExportviewerTask(Task):
    """
    Export virtual tour information into a static dir
    Input format :
        opv-task exportviewer '{"id_virtualtour": ID_VIRTUALTOUR, "id_malette": ID_MALETTE, "dir": DIR_TO_EXPORT }'
    dir argument is optionnal
    """
    TASK_NAME = "exportviewer"
    requiredArgsKeys = ["id_virtualtour", "id_malette"]

    def createDir(self):
        self.path.mkdir_p()
        self.db = self.path / "db"
        self.db.mkdir_p()
        self.dm = self.path / "dm"
        self.dm.mkdir_p()
        self.virtualtour_dir = self.db / "virtualtour"
        self.virtualtour_dir.mkdir_p()
        self.panorama_dir = self.db / "panorama"
        self.panorama_dir.mkdir_p()
        self.logger.info("Working directory : {}".format(self.path))

    def buildJSON(self):
        self.panorama_to_add = []
        self.virtualtour_dict = {
            "id_virtualtour": self.virtualtour.id_virtualtour,
            "id_malette": self.virtualtour.id_malette,
            "title": self.virtualtour.title,
            "description": self.virtualtour.decription,
            "virtualtour_paths": []
        }
        for virtualtour_path in self.virtualtour_paths:
            path_details = self._client_requestor.make(ressources.PathDetails, virtualtour_path.path_details.id_path_details, virtualtour_path.path_details.id_malette)
            virtualtour_path_dict = {
                "id_virtualtour_path": virtualtour_path.id_virtualtour_path,
                "id_malette": virtualtour_path.id_malette,
                "id_virtualtour": self.virtualtour.id_virtualtour,
                "id_virutaltour_malette": self.virtualtour.id_malette,
                "id_path_details": path_details.id_path_details,
                "id_path_details_malette": path_details.id_malette,
                "path_details": {
                    "id_path_details": path_details.id_path_details,
                    "id_malette": path_details.id_malette,
                    "description": path_details.decription,
                    "name": path_details.name,
                    "id_campaign": path_details.campaign.id_campaign,
                    "id_malette": path_details.campaign.id_malette,
                    "path_nodes": []
                },
                "path_edges": {}
            }
            path_nodes = self.virtualtour_paths = self._client_requestor.make_all(ressources.PathNodeExtended, filters=(
                Filter("id_path_details")==path_details.id_path_details,
                Filter("id_path_details_malette")==path_details.id_malette)
            )
            path_edges = self.virtualtour_paths = self._client_requestor.make_all(ressources.PathEdge, filters=(
                Filter("id_path_details")==path_details.id_path_details,
                Filter("id_path_details_malette")==path_details.id_malette)
            )

            for path_node in path_nodes:
                virtualtour_path_dict["path_details"]["path_nodes"].append({
                    "id_path_node": path_node.id_path_node,
                    "id_malette": path_node.id_malette,
                    "id_panorama": path_node.id_panorama,
                    "id_panorama_malette": path_node.id_panorama_malette,
                    "id_path_details": path_details.id_path_details,
                    "id_path_details_malette": path_details.id_malette,
                    "disabled": path_node.disabled,
                    "original_id_sensors": path_node.original_id_sensors,
                    "original_id_malette": path_node.original_id_malette,
                    "original_gps_pos": path_node.original_gps_pos,
                    "original_minutes": path_node.original_minutes,
                    "original_degrees": path_node.original_degrees,
                    "reconstructed_id_sensors": path_node.reconstructed_id_sensors,
                    "reconstructed_id_malette": path_node.reconstructed_id_malette,
                    "reconstructed_gps_pos": path_node.reconstructed_gps_pos,
                    "reconstructed_minutes": path_node.reconstructed_minutes,
                    "reconstructed_degrees": path_node.reconstructed_degrees
                })
                self.panorama_to_add.append("{}-{}".format(path_node.id_panorama, path_node.id_panorama_malette))

            for path_edge in path_edges:
                virtualtour_path_dict["path_edges"]["{}-{}".format(path_edge.id_malette, path_edge.id_path_edge)] = {
                    "id_path_edge": path_edge.id_path_edge,
                    "id_malette": path_edge.id_malette,
                    "source_id_path_node": path_edge.source_path_node.id_path_node,
                    "source_id_path_node_malette": path_edge.source_path_node.id_malette,
                    "dest_id_path_node": path_edge.dest_path_node.id_path_node,
                    "dest_id_path_node_malette": path_edge.dest_path_node.id_malette,
                    "id_path_details": path_edge.path_details.id_path_details,
                    "id_path_details_malette": path_edge.path_details.id_malette,
                    "source_target_yaw_dest": path_edge.source_target_yaw_dest,
                    "source_yaw_dest": path_edge.source_yaw_dest,
                }

            self.virtualtour_dict["virtualtour_paths"].append(virtualtour_path_dict)
        
        with open(self.virtualtour_dir / "{}-{}.json".format(self.virtualtour.id_virtualtour, self.virtualtour.id_malette), "w") as virtualtour_file:
            json.dump(self.virtualtour_dict, virtualtour_file)

    def buildPanoramaJSON(self):
        for panorama in self.panorama_to_add:
            panorama = panorama.split("-")
            panorama = self._client_requestor.make(ressources.PanoramaSensors, panorama[0], panorama[1])
            panorama_json = {
                "id_panorama": panorama.id_panorama,
                "id_malette": panorama.id_malette,
                "id_cp": panorama.id_cp,
                "id_cp_malette": panorama.id_cp_malette,
                "active": panorama.active,
                "equirectangular_path": panorama.equirectangular_path,
                "is_photosphere": panorama.is_photosphere,
                "reconstructed_id_sensors": panorama.reconstructed_id_sensors,
                "reconstructed_id_malette": panorama.reconstructed_id_malette,
                "reconstructed_gps_pos": panorama.reconstructed_gps_pos,
                "reconstructed_degrees": panorama.reconstructed_degrees,
                "reconstructed_minutes": panorama.reconstructed_minutes,
                "original_id_sensors": panorama.original_id_sensors,
                "original_id_malette": panorama.original_id_malette,
                "original_gps_pos": panorama.original_gps_pos,
                "original_degrees": panorama.original_degrees,
                "original_minutes": panorama.original_minutes,
                "id_campaign": panorama.id_campaign,
                "id_campaign_malette": panorama.id_campaign_malette,
                "tiles": {}
            }
            self.uuid.append(panorama.equirectangular_path)
            tiles = self._client_requestor.make_all(ressources.Tile, filters=(
                Filter("id_panorama")==panorama.id_panorama,
                Filter("id_panorama_malette")==panorama.id_malette
            ))
            for tile in tiles:
                panorama_json["tiles"]["{}-{}".format(tile.id_malette, tile.id_tile)] = {
                    "id_tile": tile.id_tile,
                    "id_malette": tile.id_malette,
                    "param_location": tile.param_location,
                    "fallback_path": tile.fallback_path,
                    "extension": tile.extension,
                    "resolution": tile.resolution,
                    "max_level": tile.max_level,
                    "cube_resolution": tile.cube_resolution,
                    "id_panorama": tile.panorama.id_panorama,
                    "id_panorama_malette": tile.panorama.id_malette
                }
                self.uuid.append(tile.param_location)
                self.uuid.append(tile.fallback_path)
            with open(self.panorama_dir / "{}-{}.json".format(panorama.id_malette, panorama.id_panorama), "w") as panorama_file:
                json.dump(panorama_json, panorama_file)
    
    def storeUUID(self):
        with open(self.dm / "uuid.list", "a") as uuid_file:
            uuid_file.write("\n".join(self.uuid))

    def runWithExceptions(self, options={}):
        self.checkArgs(options)
        if 'dir' in options:
            self.path = Path(options['dir'])
        else: 
            self.path = Path(tempfile.mkdtemp())

        self.createDir()
        self.virtualtour = self._client_requestor.make(ressources.Virtualtour, options["id_virtualtour"], options["id_malette"])
        self.virtualtour_paths = self._client_requestor.make_all(ressources.Virtualtour_path, filters=(
            Filter("id_virtualtour")==self.virtualtour.id_virtualtour,
            Filter("id_virtualtour_malette")==self.virtualtour.id_malette)
        )

        self.uuid = []

        self.buildJSON()
        self.buildPanoramaJSON()
        self.storeUUID()
