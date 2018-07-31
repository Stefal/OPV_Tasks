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
import queue
import operator

from opv_tasks.task import Task
from opv_tasks.task import TaskException
from opv_api_client import ressources, Filter
from opv_api_client.exceptions import RequestAPIException

class PanoramaNotFound(Exception):
    """Not found exception"""
    pass


import logging

class OPV_GRAPHE_EXCEPTION(Exception):
    pass


class Node(object):

    def __init__(self, name, data=None):
        """
        :param name:
        :param data:
        """
        self.__name = str(name)
        self.__data = data if data is not None else {}
        self.__edges = []

    @property
    def name(self):
        """
        :return:
        """
        return self.__name

    @name.setter
    def name(self, name):
        """
        :param name:
        :return:
        """
        self.__name = str(name)

    @property
    def data(self):
        """
        :return:
        """
        return self.__data

    @data.setter
    def data(self, data):
        """
        :param data:
        :return:
        """
        self.__data = data

    @property
    def edges(self):
        return self.__edges

    @edges.setter
    def edges(self, edges):
        self.__edges = edges

    def merge(self, node):
        """Merge Node"""
        for edge in node.edges:
            if edge not in self.edges:
                self.edges.append(edge)

    def get(self, name, default=None):
        """
        :param name:
        :param default:
        :return:
        """
        return self.data[str(name)] if str(name) in self.data else default

    def set(self, name, value):
        """
        :param name:
        :param value:
        :return:
        """
        self.data[str(name)] = value

    def format(self):
        """
        :return:
        """
        return {
            "name": self.name,
            "data": self.data,
            "edges": [edge.name for edge in self.edges]
        }

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)


class Edge(object):

    def __init__(self, name, source=None, dest=None, data=None, distance=None):
        """
        :param source:
        :param dest:
        """
        self.name = name
        self.source = source
        self.dest = dest
        self.__data = data if data is not None else {}
        self.__distance = distance

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data):
        self.__data =data

    @property
    def distance(self):
        return self.__distance

    @distance.setter
    def distance(self, distance):
        self.__distance = distance

    def get(self, name, default=None):
        if name in self.data:
            return self.data[name]
        return default

    def set(self, name, value):
        self.data[name] = value

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, item):
        return self.__getattribute__(item)


class Graphe(object):

    def __init__(self, name, logger=None):
        self.__name = name
        self.__nodes = {}
        self.__edges = {}
        self.__endpoints = []
        self.logger = logger if logger is not None else logging.getLogger(
            "%s:%s" % (__name__, self.__class__.__name__)
        )

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def nodes(self):
        """
        :return:
        """
        return self.__nodes

    @nodes.setter
    def nodes(self, nodes):
        """
        :param nodes:
        :return:
        """
        self.__nodes = nodes

    @property
    def edges(self):
        """

        :return:
        """
        return self.__edges

    @edges.setter
    def edges(self, edges):
        """

        :param edges:
        :return:
        """
        self.__edges = edges

    @property
    def endpoints(self):
        return self.__endpoints

    @endpoints.setter
    def endpoints(self, endpoints):
        self.__endpoints = endpoints

    def node_exist(self, name: str):
        """
        Check if a node exit
        :param name: The name of the node
        :return:
        """
        if name in self.nodes:
            return True
        return False

    def create_node(self, name, data):
        """Create a node"""
        real_name = str(name)

        if self.node_exist(real_name):
            self.logger.warning("Node %s already exist!" % real_name)
            return None

        self.logger.info("Graphe %s: Creating node %s" % (self.name, real_name))

        node = Node(real_name, data)
        self.add_node(node)
        return node

    def add_node(self, node):
        """
        Add a node
        :param node:
        :return:
        """
        if self.node_exist(node.name):
            self.logger.warning("Node %s already exit!" % node.name)
        self.logger.info("Graphe %s: add node %s" % (self.name, node.name))
        self.__nodes[node.name] = node

    def get_node(self, name):
        """
        Get a node by its name
        :param name:
        :return:
        """
        if self.node_exist(str(name)):
            return self.nodes[str(name)]
        return None

    def add_edge(self, node0, node1, distance=None):
        """
        Add edge
        :param node0:
        :param node1:
        :return:
        """

        if isinstance(node0, int):
            name0 = str(node0)
        elif isinstance(node0, str):
            name0 = node0
        else:
            name0 = node0.name

        if isinstance(node0, int):
            name1 = str(node1)
        elif isinstance(node0, str):
            name1 = node1
        else:
            name1 =node1.name

        if not self.node_exist(name0):
            raise OPV_GRAPHE_EXCEPTION("Node %s doesn't exist!" % name0)

        if not self.node_exist(name1):
            raise OPV_GRAPHE_EXCEPTION("Node %s doesn't exist!" % name1)

        if name0 == name1:
            self.logger.info("You are trying to create an edge between the same node (%s)!" % name0)
            return False

        names = sorted([name0, name1])
        name = "%s-%s" % tuple(names)

        if name in self.edges:
            print("%s Already exist" % name)
            return False

        if distance is None:
            first_node = self.get_node(names[0])

            distance = 0.0
            if names[1] in first_node.data["near_panoramas"]:
                distance = first_node.data["near_panoramas"][names[1]]["distance"]

        self.logger.info("Add edge between %s with distance %s" % (
            name, distance
        ))
        edge = Edge(
            name,
            source=name0,
            dest=name1,
            distance=distance
        )

        self.logger.info("")
        self.edges[name] = edge

        # Add edges to Node
        self.logger.info("Add edge %s to node %s" % (name, name0))
        self.get_node(name0).add_edge(edge)
        self.logger.info("Add edge %s to node %s" % (name, name1))
        self.get_node(name1).add_edge(edge)

        return edge

    def merge(self, graphe):
        """Merge graphe"""
        for name, value in graphe.nodes.items():
            if name in self.nodes:
                self.nodes[name].merge(value)
            else:
                self.nodes[name] = value
        for name, value in graphe.edges.items():
            self.edges[name] = value

    def __add_endpoints(self, end_point):
        if end_point not in self.endpoints:
            self.endpoints.append(end_point)

    def add_end_points(self, endpoints):
        """Add end_points"""
        if isinstance(endpoints, list):
            for endpoint in endpoints:
                self.__add_endpoints(endpoint)
        else:
            self.__add_endpoints(endpoints)

    def generate_json(self, filename):
        """
        :param filename:
        :return:
        """

        data = {
            "nodes": {name: node.format() for name, node in self.nodes.items()},
            "edges": [],
            "endpoints": self.endpoints
        }

        for name, edge in self.edges.items():
            data["edges"].append(
                {
                    "name": name,
                    "source": edge["source"],
                    "dest": edge["dest"]
                }
            )

        with open(filename, "w") as fic:
            fic.write(json.dumps(data))


class PathfinderTask(Task):
    """
    Create path between panorama with a graphe. This class will alse reduce the graphe if you demand it.
    Input format :
        opv-task findnearestcp '{"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE, "panos": [] }'
    Output format :

    """

    TASK_NAME = "pathfinder"
    requiredArgsKeys = ["id_campaign", "id_malette"]

    # Earth radius in meter
    EARTH_RADIUS = 6378000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__panorama = []

    @staticmethod
    def getStitchableCps(lot):
        """
        get stitchable CP of a lot if it as some, or empty list.

        :param lot: a lot.
        :return: a list of stitchable CPs
        """
        return [cp for cp in lot.cps if cp.stichable]

    @staticmethod
    def getDistance(gpsCord1, gpsCord2):
        """
        Return the distance between 2 point in meter
        :param gpsCord1:
        :param gpsCord2:
        :return:

        To verify if I am not too dumb:
        # Wikipedia saids that Paris and Network are 5 852 km away
        # - https://fr.wikipedia.org/wiki/Orthodromie.
        >>>a = {"gps": {"latitude": 48.850000, "longitude": 2.350000}} # Paris
        >>>b = {"gps": {"longitude": -74.000000, "latitude": 40.716667}} # NewYork
        >>>getDistance(a,b)
        5843114.788446997
        """
        # we must convert gps cord who are in degrees to radians
        gpsCord1 = [math.radians(gpsCord1["latitude"]), math.radians(gpsCord1["longitude"])]
        gpsCord2 = [math.radians(gpsCord2["latitude"]), math.radians(gpsCord2["longitude"])]

        # Les liens utilisés:
        # - https://fr.wikipedia.org/wiki/Orthodromie
        # - http://ressources.univ-lemans.fr/AccesLibre/UM/Pedago/physique/02/divers/ortholoxo.html
        # - https://fr.wikipedia.org/wiki/Identit%C3%A9_trigonom%C3%A9trique
        #         O
        #        | |
        #     R |   | R
        #      |     |
        #     |       |
        #     A        B
        # cos(AOB) = OA / AB = OA . OB
        # Produit scalaire OA . OB
        # OA.x = cos(long1)*cos(lat1)
        # OA.y = sin(long1)*cos(lat1)
        # OA.z = sin(lat1)
        # OB.x = cos(long2)*cos(lat2)
        # OB.y = sin(long2)*cos(lat2)
        # OB.z = sin(lat2)
        # OA . OB = (OA.x * OB.x + OA.y * OB.y + OA.z * OB.z)
        # = cos(long1)*cos(lat1) * cos(long2)*cos(lat2) + sin(long1)*cos(lat1) * sin(long2)*cos(lat2) + sin(lat1) * sin(lat2)
        # = cos(lat1)*cos(lat2) * (cos(long1)*cos(long2) + sin(long1)*sin(long2)) + sin(lat1)*sin(lat2)
        # Identité remarquable cos(b - a) = cos(a)*cos(b) + sin(a)*sin(b)
        # = cos(lat1)*cos(lat2) * (cos(long2 - long1) + sin(lat1)*sin(lat2)
        # Donc
        # cos(AOB) = (cos(lat1)*cos(lat2) * (cos(long2 - long1) + sin(lat1)*sin(lat2))
        # distance = AOB*R
        # Avec R = 6378000 mètres
        # d = R*acos((cos(lat1)*cos(lat2) * (cos(long2 - long1) + sin(lat1)*sin(lat2)))
        return PathfinderTask.EARTH_RADIUS * (
            math.acos(
                math.cos(gpsCord1[0]) * math.cos(gpsCord2[0]) * math.cos(gpsCord2[1] - gpsCord1[1]) +
                math.sin(gpsCord1[0]) * math.sin(gpsCord2[0])
            )
        )

    def getAngle(self, pano1, pano2, pano3):
        """
        Get Angle between pano1, pano2, pano3
        :param pano1:
        :param pano2:
        :param distance:
        :return:
        """

        d_ab = self.getDistance(pano1, pano2)
        d_ac = self.getDistance(pano1, pano3)
        d_bc = self.getDistance(pano2, pano3)

        # On va utiliser le théorème d'Al-Kashi pour calculer CAB:
        # - https://fr.wikipedia.org/wiki/Loi_des_cosinus
        #         C
        #        | |
        #       |   |
        #      |     |
        #     |       |
        #     A________B
        # Donc:
        # - a = AB
        # - b = AC
        # - c = BC
        # c *c = a * a + b * b - 2 * a * b * cos(CAB)
        # - 2 * a * b * cos(OAB) = c * c - a * a - b * b
        # cos(OAB) = (1 / (-2 * a * b)) * (c * c - a * a - b * b)
        # OAB = acos((1 / (-2 * a * b)) * (c * c - a * a - b * b)
        calcul = (-1.0 / (2.0 * d_ab * d_ac)) * (
            d_bc * d_bc -
            d_ab * d_ab -
            d_ac * d_ac
        )
        calcul = 1.00 if calcul > 1.0 else calcul
        calcul = -1.00 if calcul < -1.0 else calcul
        return math.acos(calcul)

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

    def found_near_panorama(self, panoramas, ref_angle=90.0, ref_radius=50.0):
        """
        Found near panorama
        :param panoramas:
        :return:
        """
        self.logger.info("find_near_pano when distance is lesser than %s and angle between panorama is greater than %s" % (
            ref_radius, ref_angle
        ))
        for ref_pano_id, ref_data in panoramas.items():
            self.logger.info("%s Start searching for near panorama" % ref_pano_id)
            near_panoramas = {}

            self.logger.info("%s\tSearch nears panorama by distance" % ref_pano_id)
            # Compare the panorama with the other
            for pano_id, data in panoramas.items():

                # Don't test the same panorama ...
                if ref_pano_id == pano_id:
                    continue

                # Get the distances between panoramas
                distance = self.getDistance(ref_data["gps"], data["gps"])

                if distance > ref_radius:
                    continue
                self.logger.info("%s\t\tFound %s with distance %s" % (ref_pano_id, pano_id, round(distance, 3)))
                near_panoramas[pano_id] = distance

            referential_angle_id = None
            referential_angle = None
            referential_angle_data = None
            final_near_panoram = {}

            self.logger.info("%s\tSearch nears panorama by angle" % ref_pano_id)

            # Get the nearest panorama by a portion of X radian
            for pano_id, distance in sorted(near_panoramas.items(), key=operator.itemgetter(1)):
                # Get the panorama
                panorama = panoramas[pano_id]

                # Get a referential
                if referential_angle is None:
                    self.logger.info("%s\t\tThe referential panorama is %s" % (ref_pano_id, pano_id))
                    referential_angle_id = pano_id
                    referential_angle = panorama
                    referential_angle_data = {
                        "distance": distance,
                        "angle": 0.0
                    }
                    continue

                angle = math.degrees(self.getAngle(ref_data["gps"], referential_angle["gps"], panorama["gps"]))

                self.logger.info("%s\t\tCheck %s with angle %s" % (ref_pano_id, pano_id, round(angle, 3)))

                add_it_to_near = 0

                if angle >= 360 - ref_angle or angle <= ref_angle:
                    self.logger.info("%s\t\t\tPanorama is near the referential! Skipped it" % (ref_pano_id))
                    continue

                for pano_id_to_test, data2 in final_near_panoram.items():
                    ref_angle2 = data2["angle"]

                    def normalise(angle):
                        toto = 360 + angle if angle < 0 else angle
                        return toto % 360

                    angle_to_test = normalise(angle - ref_angle2)
                    self.logger.info("%s\t\t\tCompare it with %s angle=%s, diff=%s" % (
                        ref_pano_id, pano_id_to_test, round(ref_angle2, 3), round(angle_to_test, 3)
                    ))

                    if angle_to_test >= 360 - ref_angle or angle_to_test <= ref_angle:
                        self.logger.info("%s\t\t\tPanorama is near %s! Skipped it" % (ref_pano_id, pano_id_to_test))
                        add_it_to_near = 1
                        continue

                if add_it_to_near == 0:
                    # print("\tpano_tested=%s, angle=%s, OK" % (pano_id, angle))
                    self.logger.info("%s\t\t\tPanorama %s added" % (
                        ref_pano_id, pano_id
                    ))
                    final_near_panoram[pano_id] = {
                        "distance": distance,
                        "angle": angle
                    }

            if referential_angle_id is not None:
                final_near_panoram[referential_angle_id] = referential_angle_data

            ref_data["near_panoramas"] = final_near_panoram

    def setup_for_largeur(self, panoramas):
        """
        Setup for largeur
        :param panoramas:
        :return:
        """
        # Setup for alog
        for pano_id, data in panoramas.items():
            data["largeur"] = 0

    @staticmethod
    def create_node(pano_id, data):
        """Create node"""
        return Node(pano_id, data=data)

    def get_subgraphe(self, panoramas, graphe_name):
        """
        Get subgraphe

        Parcours de graphe en largeur
        :param panoramas:
        :param graphe_name:
        :return:
        """
        self.logger.info("Search subgraphe")

        first_pano = None

        # Get the first node that largeur = False
        for pano_id, data in panoramas.items():
            if data["largeur"] == 0:
                first_pano = data
                break

        if first_pano is None:
            self.logger.info("No node to check left!")
            return None

        self.logger.info("Found node %s, it will be used has referential point" % first_pano["id_panorama"])
        graphe = Graphe(graphe_name)

        node_to_check = queue.Queue()
        node_to_check.put(first_pano)

        while not node_to_check.empty():
            node = node_to_check.get()
            self.logger.info("Check node %s " % node["id_panorama"])
            graphe.create_node(node["id_panorama"], node)
            for succ_id, _ in node["near_panoramas"].items():
                pano = panoramas[succ_id]
                graphe.create_node(succ_id, pano)
                graphe.add_edge(node["id_panorama"], succ_id)
                if pano["largeur"] == 0:
                    self.logger.info("\tNode %s have a successor node %s" % (
                        node["id_panorama"],
                        succ_id
                    ))
                    node_to_check.put(pano)
                    pano["largeur"] = 1
            node["largeur"] = 2
        return graphe

    def get_all_subgraphe(self, panoramas):
        """
        Get all subgrahe
        :param panoramas:
        :return:
        """
        self.logger.info("Search all subgraphe")
        liste = []

        self.setup_for_largeur(panoramas)
        graphe_name = 0

        while True:
            graphe_name += 1
            graphe = self.get_subgraphe(panoramas, graphe_name)
            if graphe is None:
                break
            liste.append(graphe)
        self.logger.info("Found %s subgraphe" % len(liste))
        return liste

    def create_graphe(self, panoramas):
        """Create the graphe"""

        graphe = Graphe()
        def create_node(pano_id, data):
            """Create node"""
            return Node(pano_id, data=data)

        for ref_pano_id, ref_data in panoramas.items():
            for pano_id, angle in ref_data["near_panoramas"].items():
                if pano_id == ref_pano_id:
                    continue
                graphe.add_node(create_node(ref_pano_id, ref_data))
                graphe.add_node(create_node(pano_id, panoramas[pano_id]))

                graphe.add_edge(ref_pano_id, pano_id)

        print("Nodes = %s" % len(graphe.nodes))
        print("Edges = %s" % len(graphe.edges))
        graphe.generate_json("/home/opv/dev/OPV_Graphe/toto.json")

    def get_min_panorama(self, ref_graphe, graphe):
        """
        :param ref_graphe:
        :param graphe:
        :return:
        """

        self.logger.info("Search near panorama between graphe %s and graphe %s" % (
            ref_graphe.name, graphe.name
        ))
        temp = {
            "distance": None,
            "ref_pano_id": 0,
            "pano_id": 0
        }

        for ref_pano_id, ref_pano in ref_graphe.nodes.items():
            for pano_id, pano in graphe.nodes.items():
                distance = self.getDistance(ref_pano.data["gps"], pano.data["gps"])

                if temp["distance"] is None or temp["distance"] > distance:
                    ref_distance = distance
                    temp = {
                        "distance": distance,
                        "ref_pano_id": ref_pano_id,
                        "pano_id": pano_id
                    }

        self.logger.info("\tFound panorama %s with %s with distance=%s" % (
            temp["ref_pano_id"], temp["pano_id"], temp["distance"]
        ))
        return temp

    def merge_subgraphe(self, graphes):
        """
        :param graphes:
        :return:
        """
        if len(graphes) == 0:
            self.logger.error("No graphe to test!")
            return None
        if len(graphes) == 1:
            self.logger.info("No graphe to merge, you only have one graphe")
            return graphes[0]

        ref_graphe = graphes[0]
        graphes_to_test = graphes[1:]

        self.logger.info("I take graphe %s has referential" % ref_graphe.name)

        while True:
            merge_dict = []
            self.logger.info("Search graphe to merge")
            for graphe in graphes_to_test:
                temp = self.get_min_panorama(ref_graphe, graphe)
                merge_dict.append({
                    "pano": temp,
                    "graphe": graphe
                })

            self.logger.info("Search the nearest graphe to merge")
            graphe_to_merge = sorted(merge_dict, key=lambda k: k["pano"]['distance'])[0]

            self.logger.info("Nearest graphe is %s" % graphe_to_merge["graphe"].name)
            ref_graphe.merge(graphe_to_merge["graphe"])
            ref_graphe.add_edge(
                graphe_to_merge["pano"]["ref_pano_id"], graphe_to_merge["pano"]["pano_id"],
                distance=graphe_to_merge["pano"]["distance"]
            )
            graphes_to_test.remove(graphe_to_merge["graphe"])

            if len(graphes_to_test) == 0:
                break

        return ref_graphe

    def get_end_points_simple(self, graphe):
        """
        Get all end points the simple way:
        With this implementation, an endpoint is a node with only one edge.
        :param graphe:
        :return:
        """

        self.logger.info("Launch a simple search for end points")
        endpoints = []

        # Simple search
        for node_name, node in graphe.nodes.items():
            # count = graphe.count_edges(node_name)
            if len(node.edges) == 0:
                self.logger.critical("Node %s has no edge" % node_name)
            if len(node.edges) == 1:
                self.logger.info("Node %s is an end points" % node_name)
                endpoints.append(node_name)

        self.logger.info("Found %s end points in graphe %s" % (
            len(endpoints), graphe.name
        ))

        graphe.endpoints = endpoints

        return endpoints

    def get_end_points(self, graphe):
        """
        Get all the end points of the grahe
        :param graphe:
        :return:
        """
        return self.get_end_points_simple(graphe)

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
        # If panos is in options
        if "panos" in options:
            # Get panoramas from id
            panos = self.get_panoramas_from_id(options["panos"], malette_id)
        else:
            # Get all panorama from the campaign
            panos = self.found_panorama(campaign_id, malette_id)

        self.logger.info("============================== %s ==============================" % (
            "Create path between panorama"
        ))

        # Search near panorama for each panorama
        self.found_near_panorama(panos)
        #
        # # Create the graphe
        # self.create_graphe(panos)

        self.logger.info("============================== %s ==============================" % (
            "Detect subgraphe"
        ))

        # Use "algorithme de parcours en largeur" to get all sub graphe
        graphes = self.get_all_subgraphe(panos)

        print("Found %s graphe" % len(graphes))

        self.logger.info("============================== %s ==============================" % (
            "Merge subgraphe"
        ))

        # Merge subgraphe if asked
        graphe = self.merge_subgraphe(graphes)

        self.logger.info("============================== %s ==============================" % (
            "Get end points of the graphe"
        ))
        # Get end point of the graphe
        end_points = self.get_end_points(graphe)


        print("Nodes = %s" % len(graphe.nodes))
        print("Edges = %s" % len(graphe.edges))
        graphe.generate_json("/home/opv/dev/OPV_Graphe/toto.json")

        # Compute the shortest path between end point


        # Reduce the graphe

        # print(json.dumps(panos, indent=4))
        return ""
