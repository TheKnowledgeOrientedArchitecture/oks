# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

"""oks URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from knowledge_server import views
from django.conf.urls import include, url

urlpatterns = [
    url(r'^$', views.home, name='home'),

    url(r'^oks/', include('knowledge_server.urls')),

    #   catch all; if I receive an unrecognized url I try to see whether it is a URIInstance
    # http://stackoverflow.com/questions/6545741/django-catch-all-url-without-breaking-append-slash
    url(r'^(?P<uri_instance>.*)/$', views.api_catch_all, name='api_catch_all'), 
]
