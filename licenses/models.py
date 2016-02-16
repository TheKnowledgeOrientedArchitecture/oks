# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.db import models
from knowledge_server.models import ShareableModel


class License(ShareableModel):
    '''
    Licenses from the list on http://opendefinition.org/licenses/
    JUST THOSE WITH DOMAIN DATA
    '''
    name = models.CharField(max_length=200L)
    short_name = models.CharField(max_length=50L)
    # human_readable is a summary of the legal code;
    human_readable = models.TextField(null = True, blank=True)
    legalcode = models.TextField(default = "")
    adaptation_shared = models.NullBooleanField(blank=True, null=True)
    # requires to be shared with the attribution
    attribution = models.NullBooleanField(blank=True, null=True)
    # requires to be shared with the same license
    share_alike = models.NullBooleanField(blank=True, null=True)
    commercial_use = models.NullBooleanField(blank=True, null=True)
    url_info = models.CharField(max_length=160L, null = True, blank=True)
    reccomended_by_opendefinition = models.NullBooleanField(blank=True, null=True)
    conformant_for_opendefinition = models.NullBooleanField(blank=True, null=True)
    image = models.CharField(max_length=160L, null=True, blank=True)
    image_small = models.CharField(max_length=160L, null=True, blank=True)
