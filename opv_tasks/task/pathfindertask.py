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
# Description: Task to get the nearest stitchable cp

import json
import math
import copy
import queue
import operator

from opv_tasks.task import Task
from opv_tasks.task import TaskException
from opv_api_client import ressources, Filter
from opv_api_client.exceptions import RequestAPIException

from atrevrix.graphe import Point, Node, Graphe, GrapheHelper


class PathfinderTask(Task):
    """
    Create path between panorama.
    Input format :
        opv-task findnearestcp '{
            "id_campaign": ID_CAMPAIGN,
            "id_malette": ID_MALETTE,
            "panos": [],
            "radius": 15.0,
            "angle": 90.0,
            "reduction": 15
        }'
        Inputs:
            panos => List of panorama id to use, if not set, it will take all the panorama of the campaign
            raduis => The maximum distance between node to consider them nears (in meters)
            angle => The minimum angle between node to create an edge (in °)
            reduction => The minimum distance between two nodes for the final path (in meters)
    Output format :

    """

    TASK_NAME = "pathfinder"
    requiredArgsKeys = ["id_campaign", "id_malette"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def getStitchableCps(lot):
        """
        get stitchable CP of a lot if it as some, or empty list.

        :param lot: a lot.
        :return: a list of stitchable CPs
        """
        return [cp for cp in lot.cps if cp.stichable]

    def is_usable_lot(self, lot, malette_id):
        """
        Check if a lot is usable (have a photosphere)
        :param lot:
        :return: Boolean
        """

        if isinstance(lot, int):
            # Get the lot
            try:
                panorama = self._client_requestor.make(ressources.Panorama, lot, malette_id)
                lot_used = panorama.cp.lot
            except RequestAPIException:
                self.logger.warning("%s is not a valid panorama id!" % lot)
                return None
        else:
            lot_used = lot

        pano = None
        for cp in lot_used.cps:
            for panorama in cp.panorama:
                if panorama.id_panorama is None:
                    continue
                if not panorama.is_photosphere:
                    continue
                pano = panorama
                break
        if pano is None:
            self.logger.info("Lot %s is not usable!" % lot_used.id)
            return None

        sensors = self._client_requestor.make(ressources.Sensors, lot_used.sensors.id_sensors, malette_id)
        coord = sensors.gps_pos["coordinates"]
        gps = {}
        gps["latitude"] = coord[0]
        gps["longitude"] = coord[1]
        gps["altitude"] = coord[2]

        return {
            "id": pano.id,
            "id_panorama": pano.id["id_panorama"],
            "id_malette": pano.id["id_malette"],
            "gps": gps
        }

    def found_panorama(self, campaign_id, malette_id):
        """
        Found the panorama to use for making the path
        :param campaign_id:
        :param malette_id:
        :return: panoramas founds
        """

        self.logger.info("Search panorama for campaign %s with malette id %s to make path" % (
            campaign_id, malette_id
        ))

        campaign = self._client_requestor.make(ressources.Campaign, campaign_id, malette_id)

        panoramas = {}
        for lot in campaign.lots:
            pano = self.is_usable_lot(lot, malette_id)
            if pano is not None:
                #print(pano)
                panoramas[pano["id_panorama"]] = pano

        self.logger.info("Found %s lot: %s" % (
            len(panoramas), sorted(panoramas.keys())
        ))
        return panoramas

    def get_panoramas_from_id(self, panoramas_id, malette_id):
        """
        Get panoramas form id
        :param panoramas_id:
        :param malette_id:
        :return:
        """
        panoramas = {}
        for panorama_id in panoramas_id:
            pano = self.is_usable_lot(panorama_id, malette_id)
            if pano is not None:
                panoramas[pano["id_panorama"]] = pano
        return panoramas

    def runWithExceptions(self, options={}):
        """
        Create the path between panorama.

        :param options: {"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE, "panos": []}
        """

        campaign_id = options["id_campaign"]
        malette_id = options["id_malette"]

        self.logger.info("============================== %s ==============================" % (
            "Found panorama"
        ))

        ref_radius = options["raduis"] if "raduis" in options else 15.0
        ref_angle = options["angle"] if "angle" in options else 90.0
        reduction = options["reduction"] if "reduction" in options else 15

        # If panos is in options
        if "panos" in options:
            # Get panoramas from id
            panos = self.get_panoramas_from_id(options["panos"], malette_id)
        else:
            # Get all panorama from the campaign
            panos = self.found_panorama(campaign_id, malette_id)

        # Create the intial graphe
        graphe = Graphe("pathfinder-%s-%s" % (campaign_id, malette_id))

        for name, obj in panos.items():
            gps = obj["gps"]
            graphe.create_node(
                name,
                point=Point(
                    x=gps["latitude"],
                    y=gps["longitude"],
                    z=gps["altitude"]
                )
            )

        # Search nears nodes
        graphe.detect_nears_nodes(ref_angle=ref_angle, ref_radius=ref_radius)

        # Get all subgraphe and merge them
        graphes = graphe.get_sub_graphes()
        graphe_helper = GrapheHelper()
        graphe = graphe_helper.merge_subgraphe(graphes)

        # Compute the endpoints
        graphe.get_end_points()

        # Reduce the graphe
        final_graphe = graphe_helper.reduce_path(graphe)

        # Reduce the node numbers
        reduce_path = graphe_helper.reduce_nodes(final_graphe, reduce=reduction)
        graphes = reduce_path.get_sub_graphes(near_node=False)
        final_graphe = graphe_helper.merge_subgraphe(graphes)

        # Create the PathDetailed
        path_detailed = self._client_requestor.make(ressources.PathDetails)
        path_detailed.id_malette = malette_id

        path_detailed.campaign = self._client_requestor.make(ressources.Campaign, campaign_id, malette_id)

        path_detailed.name = "PathFinder-%s-%s" % (
            campaign_id, malette_id
        )
        path_detailed.description = "Generated by pathfinder"

        toto = path_detailed.create()

        id_path_details = toto.json()["id_path_details"]

        path_detailed = self._client_requestor.make(ressources.PathDetails, id_path_details, id_malette=malette_id)

        transco_table = {}

        # Create all the path_node
        for name, nodes in final_graphe.nodes.items():
            path_node = self._client_requestor.make(ressources.PathNode, id_malette=malette_id)
            path_node.id_malette = malette_id
            path_node.panorama = self._client_requestor.make(ressources.Panorama, int(name), malette_id)
            path_node.path_details = path_detailed
            path_node.disabled = False
            path_node.hotspot = name in final_graphe.hotpoints

            response = path_node.create().json()

            transco_table[name] = response["id_path_node"]
            # Todo: Make a better implementation for the start and stop point
            if name == final_graphe.path[0]:
                path_detailed.start_node = self._client_requestor.make(
                    ressources.PathNode, response["id_path_node"], malette_id
                )
                path_detailed.save()
            if name == final_graphe.path[-1]:
                path_detailed.stop_node = self._client_requestor.make(
                    ressources.PathNode, response["id_path_node"], malette_id
                )
                path_detailed.save()

        # Create all the path_edge
        for name, edge in final_graphe.edges.items():
            path_edge = self._client_requestor.make(ressources.PathEdge, id_malette=malette_id)
            path_edge.id_malette = malette_id
            path_edge.path_details = path_detailed
            path_edge.source_path_node = self._client_requestor.make(
                ressources.PathNode, int(transco_table[edge.source]), id_malette=malette_id
            )
            path_edge.dest_path_node = self._client_requestor.make(
                ressources.PathNode, int(transco_table[edge.dest]), id_malette=malette_id
            )
            path_edge.create()

        return
