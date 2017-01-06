#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.conf.urls import patterns, url

from knowledge_server import api

urlpatterns = [

    #36:
    url( r'^dataset/$', api.api_dataset, name='api_dataset'),
    url( r'^dataset_view/$', api.api_dataset_view, name='api_dataset_view'),
    #64: 
    url( r'^datasets/$', api.api_datasets, name='api_datasets'),
    #46:
    url( r'^dataset_types/$', api.api_dataset_types, name='api_dataset_types'),
    #52
    url( r'^dataset_info/$', api.api_dataset_info, name='api_dataset_info'),
    #80:
    url( r'^ks_info/$', api.api_ks_info, name='api_ks_info' ),
    #35
    url( r'^subscribe/$', api.api_subscribe, name='api_subscribe'),
    #123
    url( r'^unsubscribe/$', api.api_unsubscribe, name='api_unsubscribe'),
    #37
    url( r'^notify/$', api.api_notify, name='api_notify'),
    url( r'^dataset_structure_code/$', api.api_dataset_structure_code, name='api_dataset_structure_code'),
]