#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.conf.urls import patterns, url

from knowledge_server import views
from knowledge_server import api

urlpatterns = [
    url(r'^debug/$', views.debug),
    url(r'^json/$', views.json),
    url(r'^cron/$', views.cron, name='cron'),
    url(r'^ks_explorer_form/$', views.ks_explorer_form, name='ks_explorer_form'),
    url(r'^ks_explorer/$', views.ks_explorer, name='ks_explorer'),
    url(r'^datasets_of_type/(?P<ks_url>[\w|=|%|.]+)/(?P<UKCL>[\w|=|%|.]+)/(?P<response_format>.*)/$', views.datasets_of_type, name='datasets_of_type'),
    url(r'^disclaimer/$', views.disclaimer, name="disclaimer"),
    url(r'^subscriptions/$', views.subscriptions, name="subscriptions"),
    url(r'^this_ks_subscribes_to/(?P<UKCL>[\w|=|%|.]+)/$', views.this_ks_subscribes_to, name='this_ks_subscribes_to'),
    url(r'^this_ks_unsubscribes_to/(?P<UKCL>[\w|=|%|.]+)/$', views.this_ks_unsubscribes_to, name='this_ks_unsubscribes_to'),
    url(r'^release_dataset/(?P<Dataset_UKCL>[\w|=|%|.]+)/$', views.release_dataset, name='release_dataset'),

                       ###################   API   ####################
    #36:
    url(r'^api/dataset/(?P<DataSet_UKCL>[\w|=|%|.]+)/(?P<response_format>.*)/$', api.api_dataset, name='api_dataset'),
    url(r'^api/dataset_view/(?P<DataSet_UKCL>[\w|=|%|.]+)/(?P<root_id>[0-9]+)/(?P<response_format>.*)/$', api.api_dataset_view, name='api_dataset_view'),
    #64: 
    url(r'^api/datasets/(?P<DataSetStructure_UKCL>[\w|=|%|.]+)/(?P<response_format>.*)/$', api.api_datasets, name='api_datasets'),
    #46:
    url(r'^api/dataset_types/(?P<response_format>.*)/$', api.api_dataset_types, name='api_dataset_types'), 
    #52
    url(r'^api/dataset_info/(?P<DataSet_UKCL>[\w|=|%|.]+)/(?P<response_format>.*)/$', api.api_dataset_info, name='api_dataset_info'),
    #80:
    url(r'^api/ks_info/(?P<response_format>.*)/$', api.api_ks_info, name='api_ks_info'), 
    #35 
    url(r'^api/subscribe/(?P<UKCL>[\w|=|%|.]+)/(?P<remote_url>[\w|=|%|.]+)/$', api.api_subscribe, name='api_subscribe'),
    #123
    url(r'^api/unsubscribe/(?P<UKCL>[\w|=|%|.]+)/(?P<URL>[\w|=|%|.]+)/$', api.api_unsubscribe, name='api_unsubscribe'),
    #37
    url(r'^api/notify/$', api.api_notify, name='api_notify'),
    url(r'^api/dataset_structure_code/(?P<DataSetStructure_UKCL>[\w|=|%|.]+)/$', api.api_dataset_structure_code, name='api_dataset_structure_code'),
                       ###################   API ^ ####################
]