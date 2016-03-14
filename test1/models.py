# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.db import models
from knowledge_server.models import ShareableModel


class Continent(ShareableModel):
    name = models.CharField(max_length=50)
    license = models.ForeignKey("licenses.License", null=True, blank=True)

class SubContinent(ShareableModel):
    name = models.CharField(max_length=50)
    continent = models.ForeignKey("Continent")

class State(ShareableModel):
    name = models.CharField(max_length=50)
    continent = models.ForeignKey("Continent", null=True, blank=True)
    sub_continent = models.ForeignKey("SubContinent", null=True, blank=True)

class Region(ShareableModel):
    name = models.CharField(max_length=50)
    state = models.ForeignKey("State")

class Province(ShareableModel):
    name = models.CharField(max_length=50)
    state = models.ForeignKey("State", null=True, blank=True)
    region = models.ForeignKey("Region", null=True, blank=True)
