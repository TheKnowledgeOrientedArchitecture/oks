#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.conf.urls import patterns, url

from knowledge_server import views

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
    url( r'^upload_page', views.upload_page, name='upload_page' ),
    url( r'^perform_import', views.perform_import, name='perform_import' ),
]