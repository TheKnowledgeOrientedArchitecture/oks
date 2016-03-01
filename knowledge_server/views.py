# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import json
import logging
import urllib

from urllib.request import urlopen

from django.db import transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

import knowledge_server.forms as myforms 
from knowledge_server.models import ApiResponse, DataSet, Event, KnowledgeServer, Notification
from knowledge_server.models import NotificationReceived, SubscriptionToOther, SubscriptionToThis
from knowledge_server.utils import KsUrl

logger = logging.getLogger(__name__)


def ks_explorer(request):
    try:
        ks_url = urllib.parse.parse_qs('url=' + request.GET['ks_complete_url'])['url'][0]
    except:
        ks_url = request.POST['ks_complete_url']
    try:
        this_ks = KnowledgeServer.this_knowledge_server()
        # info on the remote ks
        ar_ks_info = ApiResponse()
        ar_ks_info.invoke_oks_api(ks_url, 'api_ks_info', args=("JSON",))
        if ar_ks_info.status == ApiResponse.success:
            organization = ar_ks_info.content['DataSet']['ActualInstance']['Organization']
            for ks in organization['knowledgeserver_set']:
                if ks['this_ks']:
                    explored_ks = ks
                
            # info about structures on the remote ks
            ar_ds_types = ApiResponse()
            ar_ds_types.invoke_oks_api(ks_url, 'api_dataset_types', args=("JSON",))
            owned_structures = []
            other_structures = []
            for ei in ar_ds_types.content['DataSets']:
                entity = {}
                entity['actual_instance_name'] = ei['ActualInstance']['DataSetStructure']['name']
                entity['UKCL'] = urllib.parse.urlencode({'':ei['ActualInstance']['DataSetStructure']['UKCL']})[1:]
                entity['oks_name'] = ei['knowledge_server']['name']
                external_oks_url = KsUrl(ei['knowledge_server']['UKCL']).home()
                entity['oks_home'] = urllib.parse.urlencode({'':external_oks_url})[1:]
                if ei['knowledge_server']['UKCL'] == explored_ks['UKCL']:
                    owned_structures.append(entity)
                else:
                    other_structures.append(entity)
        else:
            HttpResponse("Error invoking api_ks_info on " + ks_url + " - " + ar_ks_info.message)
    except Exception as ex:
        return HttpResponse(str(ex))
    cont = RequestContext(request, {'owned_structures':owned_structures, 'other_structures':other_structures, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True), 'organization': organization, 'explored_ks': explored_ks, 'ks_url':urllib.parse.urlencode({'':ks_url})[1:]})
    return render_to_response('knowledge_server/ks_explorer_entities.html', context_instance=cont)


def ks_explorer_form(request):
    form = myforms.ExploreOtherKSForm()
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'form':form, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True)})
    return render_to_response('knowledge_server/ks_explorer_form.html', context_instance=cont)


def datasets_of_type(request, ks_url, UKCL, response_format):
    '''
    returns the list of datasets of a specific type/structure
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    response_format = response_format.upper()
    ks_url = urllib.parse.unquote(ks_url)
    UKCL = urllib.parse.unquote(UKCL)
    # info on the remote ks{{  }}
    ar_ks_info = ApiResponse()
    ar_ks_info.invoke_oks_api(ks_url, 'api_ks_info', args=("JSON",))
    organization = ar_ks_info.content['DataSet']['ActualInstance']['Organization']
    for ks in organization['knowledgeserver_set']:
        if ks['this_ks']:
            external_ks_json = ks
    external_ks = KnowledgeServer()
    external_ks.name = external_ks_json['name']
    external_ks.scheme = external_ks_json['scheme']
    external_ks.netloc = external_ks_json['netloc']
    external_ks.description = external_ks_json['description']
    # info on the DataSetStructure
    # TODO: the following call relies on api_catch_all; use dataset_info instead
    response = urlopen(UKCL + "/json")
    es_info_json = response.read().decode("utf-8")
    
    if response_format == 'XML':
        local_url = reverse('api_datasets', args=(urllib.parse.quote(UKCL),response_format))
    if response_format == 'JSON' or response_format == 'BROWSE':
        local_url = reverse ('api_datasets', args=(urllib.parse.quote(UKCL).replace("/","%252F"),'JSON'))
    response = urlopen(ks_url + local_url)
    entities = response.read().decode("utf-8")
    if response_format == 'XML':
        return render(request, 'knowledge_server/export.xml', {'xml': entities}, content_type="application/xhtml+xml")
    if response_format == 'JSON':
        return render(request, 'knowledge_server/export.json', {'json': entities}, content_type="application/json")
    if response_format == 'BROWSE':
        # parse
        decoded = json.loads(entities)
        # I prepare a list of UKCL of root so that I can check which I have subscribed to
        first_version_UKCLs = []
        for ei in decoded['content']['DataSets']:
            if 'first_version' in ei:
                first_version_UKCLs.append(ei['first_version']['UKCL'])
            else:
                first_version_UKCLs.append(ei['UKCL'])
        subscribed = SubscriptionToOther.objects.filter(first_version_UKCL__in=first_version_UKCLs)
        subscribed_first_version_UKCLs = []
        for s in subscribed:
            subscribed_first_version_UKCLs.append(s.first_version_UKCL)
        entities = []
        for ei in decoded['content']['DataSets']:
            entity = {}
            if 'ActualInstance' in ei.keys():
                actual_instance_class = list(ei['ActualInstance'].keys())[0]
                entity['actual_instance_name'] = ei['ActualInstance'][actual_instance_class]['name']
            else: #is a view
                entity['actual_instance_name'] = ei['description']
            entity['encodedUKCL'] = urllib.parse.urlencode({'':ei['UKCL']})[1:]
            entity['UKCL'] = urllib.parse.quote(ei['UKCL']).replace("/","%252F")
            subscribed_UKCL = ei['first_version']['UKCL'] if 'first_version' in ei else ei['UKCL']
            if subscribed_UKCL in subscribed_first_version_UKCLs:
                entity['subscribed'] = True
            entities.append(entity)
        cont = RequestContext(request, {'entities':entities, 'organization': organization, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True), 'external_ks': external_ks, 'es_info_json': es_info_json})
        return render_to_response('knowledge_server/datasets_of_type.html', context_instance=cont)
    
    
def home(request):
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True)})
    return render(request, 'knowledge_server/home.html', context_instance=cont)


    
    
def this_ks_unsubscribes_to(request, UKCL):
    '''
    '''
    pass


def release_dataset(request, Dataset_UKCL):
    '''
    '''
    try:
        Dataset_UKCL = urllib.parse.unquote(Dataset_UKCL)
        dataset = DataSet.objects.get(UKCL = Dataset_UKCL)
        dataset.set_released()
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, Dataset_UKCL + " successfully released.").json()}, content_type="application/json")
    except Exception as ex:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, str(ex)).json()}, content_type="application/json")
        
        
def this_ks_subscribes_to(request, UKCL):
    '''
    This ks is subscribing to a data set in another ks
    First I store the subscription locally
    Then I invoke remotely api_subscribe
    If it works I commit locally
    '''
    UKCL = str(urllib.parse.unquote(UKCL).replace("%2F","/"))
    other_ks_uri = KsUrl(UKCL).home()

    KnowledgeServer.get_remote_ks(other_ks_uri)
    
    try:
        with transaction.atomic():
            encoded_UKCL = urllib.parse.urlencode({'':UKCL})[1:]
            # invoke remote API to subscribe
            this_ks = KnowledgeServer.this_knowledge_server()
            url_to_invoke = urllib.parse.urlencode({'':this_ks.url() + reverse('api_notify')})[1:]
            ar = ApiResponse()
            ar.invoke_oks_api(other_ks_uri, 'api_subscribe', args=(encoded_UKCL,url_to_invoke,))
            if ar.status == ApiResponse.success:
                # save locally
                sto = SubscriptionToOther()
                sto.URL = UKCL
                sto.first_version_UKCL = ar.content # it contains the UKCL of the first version
                sto.save()
                return render(request, 'knowledge_server/export.json', {'json': ar.response}, content_type="application/json")
            else:
                return render(request, 'knowledge_server/export.json', {'json': ar.response}, content_type="application/json")
    except Exception as ex:
        return HttpResponse(str(ex))
    
def cron(request):
    '''
        to run tasks that have to be executed periodically on this ks; e.g. 
        * send messages
        * process notifications
        * ...
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    response = this_ks.run_cron()
    return HttpResponse(response)


def disclaimer(request):
    '''
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'this_ks': this_ks})
    return render_to_response('knowledge_server/disclaimer.html', context_instance=cont)


def subscriptions(request):
    '''
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    subscriptions_to_this = SubscriptionToThis.objects.all()
    events = Event.objects.filter(processed=False)
    notifications_to_be_sent = Notification.objects.filter(sent=False)
    received_notifications = NotificationReceived.objects.filter(processed=False)
    subscriptions_to_other = SubscriptionToOther.objects.all()
    cont = RequestContext(request, {'received_notifications': received_notifications, 'notifications_to_be_sent': notifications_to_be_sent, 'events': events, 'subscriptions_to_other': subscriptions_to_other, 'subscriptions_to_this': subscriptions_to_this, 'this_ks': this_ks, 'this_ks_encoded_url':this_ks.url(True)})
    
    return render_to_response('knowledge_server/subscriptions.html', context_instance=cont)


def debug(request):
    '''
    created to debug code
    '''
    try:
        logger.info('Something went wrong!')
        logger.debug("msg")
        logger.warn("msg")
        logger.error('Something went wrong!')
        logger.critical("msg")

    
        return HttpResponse("OK ")
    except Exception as ex:
        return HttpResponse(str(ex))

