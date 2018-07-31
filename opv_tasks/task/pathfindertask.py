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

import math

from opv_tasks.task import Task
from opv_tasks.task import TaskException
from opv_api_client import ressources, Filter
from opv_api_client.exceptions import RequestAPIException


class PathfinderTask(Task):
    """
    Find nearest stitchable cp. Takes lot in input (id_lot and id_malette needed).
    Input format :
        opv-task findnearestcp '{"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE }'
    Output format :
        {"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE }
    """

    TASK_NAME = "pathfinder"
    requiredArgsKeys = ["id_campaign", "id_malette"]

    # Earth radius in meter
    EARTH_RADIUS = 6378000

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
        return EARTH_RADIUS * (
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

    def is_usable_lot(self, lot):
        """
        Check if a lot is usable (have a photosphere)
        :param lot:
        :return: Boolean
        """
        pano = None
        for cp in lot.cps:
            for panorama in cp.panorama:
                if panorama.id_panorama is None:
                    continue
                if not panorama.is_photosphere:
                    continue
                pano = panorama
                break
        if pano is None:
            self.logger.info("Lot %s is not usable!" % lot.id)
            return False
        return True

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

        lots = []
        for lot in campaign.lots:
            if self.is_usable_lot(lot):
                lots.append(lot)

        self.logger.info("Found %s lot: %s" % (
            len(lots), lots
        ))
        return lots

    def runWithExceptions(self, options={}):
        """
        Search nearest cp stitchable to inject it.

        :param options: {"id_campaign": ID_CAMPAIGN, "id_malette": ID_MALETTE}
        """

        campaign_id = options["id_campaign"]
        malette_id = options["id_malette"]

        pano = self.found_panorama(campaign_id, malette_id)

        return ""
