# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import json
import socket
import urllib
from urllib.parse import urlparse
from urllib.request import urlopen

from datetime import datetime
from xml.dom import minidom

from django.db import transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from knowledge_server.models import ModelMetadata, DataSetStructure, DataSet, KnowledgeServer
from knowledge_server.models import SubscriptionToOther, SubscriptionToThis, ApiResponse, NotificationReceived, Notification, Event
import knowledge_server.utils as utils
import logging
import knowledge_server.forms as myforms 
from knowledge_server.utils import KsUri

from knowledge_server.orm_wrapper import OrmWrapper

logger = logging.getLogger(__name__)



def api_dataset_view(request, DataSet_URIInstance, root_id, format):
    '''
    it returns the data of the istance with pk=root_id in the dataset (which is a view)
    if we are browsing a view there is not just one single root that we can explore
    but a list of instances that match the criteria; root_id tells us which one to browse
    '''
    format = format.upper()
    DataSet_URIInstance_decoded = urllib.parse.unquote(DataSet_URIInstance)
    dataset = DataSet.retrieve(DataSet_URIInstance_decoded)
    actual_instance = ""
    actual_instance_json = ""
    # this dataset is a view; I shall use root_id to retrieve the actual instance
    module_name = dataset.dataset_structure.root_node.model_metadata.module
    actual_instance_class = OrmWrapper.load_class(module_name, dataset.dataset_structure.root_node.model_metadata.name) 
    actual_instance = actual_instance_class.objects.get(pk=root_id)
    
    if format == 'HTML' or format == 'BROWSE':
        actual_instance_json = '{' + actual_instance.serialize(dataset.dataset_structure.root_node, export_format='json', exported_instances = []) + '}'
    if format == 'JSON':
        ar = ApiResponse()
        ar.content = { "DataSet": dataset.export(export_format = 'DICT') }
        ar.status = ApiResponse.success
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if format == 'XML':
        ar = ApiResponse()
        ar.status = ApiResponse.success
        ar.content = dataset.export(export_format = format)
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if format == 'HTML' or format == 'BROWSE':
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'dataset': dataset, 'actual_instance': actual_instance, 'actual_instance_json': actual_instance_json, 'sn': dataset.dataset_structure.root_node, 'DataSet_URIInstance': DataSet_URIInstance, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
        return render_to_response('knowledge_server/browse_dataset.html', context_instance=cont)


def api_dataset(request, DataSet_URIInstance, format):
    '''
        #36
        It returns the data in the dataset with the URIInstance in the parameter 
        
        parameter:
        * DataSet_URIInstance: URIInstance of the DataSet 
        
        Implementation:
        # it creates the ModelMetadata class, 
        # fetches from the DB the one with pk = DataSet.root_instance_id
        # it runs to_xml of the ModelMetadata using DataSet.dataset_structure.root_node
    '''
    format = format.upper()
    ar = ApiResponse()
    DataSet_URIInstance_decoded = urllib.parse.unquote(DataSet_URIInstance)
    
    uri = KsUri(DataSet_URIInstance_decoded)
    # If it is not a DataSet we try to find the dataset it is in
    uri.search_on_db()
    if uri.actual_instance:
        if isinstance(uri.actual_instance, DataSet):
            dataset = uri.actual_instance
        else:
            dataset = uri.actual_instance.dataset_I_belong_to
    if (not uri.actual_instance) and (not dataset):
        ar.message = "Either the URI requested is not on this database or it is not part of a released dataset."
        if format == 'JSON':
            return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
        if format == 'XML':
            ar.status = ApiResponse.failure
            return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    
    actual_instance_json = ""
    #this dataset is not a view; if not dataset.dataset_structure.is_a_view:
    actual_instance = dataset.root
    
    if format == 'JSON':
        ar.content = { "DataSet": dataset.export(export_format = 'DICT') }
        ar.status = ApiResponse.success
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if format == 'XML':
        ar.status = ApiResponse.success
        ar.content = dataset.export(export_format = format)
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if format == 'HTML' or format == 'BROWSE':
        actual_instance_json = '{' + actual_instance.serialize(dataset.dataset_structure.root_node, export_format='json', exported_instances = []) + '}'
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'dataset': dataset, 'actual_instance': actual_instance, 'actual_instance_json': actual_instance_json, 'sn': dataset.dataset_structure.root_node, 'DataSet_URIInstance': DataSet_URIInstance, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
        return render_to_response('knowledge_server/browse_dataset.html', context_instance=cont)
        

def api_catch_all(request, uri_instance):
    '''
        parameters:
            url: http://rootks.thekoa.org/knowledge_server/Attribute/1
            url: http://rootks.thekoa.org/knowledge_server/Attribute/1/xml
            url: http://rootks.thekoa.org/knowledge_server/Attribute/1/json
        
        Implementation:
            I do something only if it is a URIInstance in my database; otherwise I return a not found message
            If there is a trailing string for the format I use it, otherwise I apply the default xml
            The trailing string can be "/xml", "/xml/", "/json", "/json/" where each character can 
            be either upper or lower case   
    '''
    # I search for a format string, a URIInstance has no trailing slash
    format = 'XML' #default
    if uri_instance[-1:] == "/":
        #I remove a trailing slash
        uri_instance = uri_instance[:-1]
    if uri_instance[-3:].lower() == "xml":
        uri_instance = uri_instance[:-4]
    if uri_instance[-4:].lower() == "json":
        format = 'JSON'
        uri_instance = uri_instance[:-5]
        
    try:
        split_path = uri_instance.split('/')
        if len(split_path) == 3:
            module_name = split_path[0]
            simple_entity_name = split_path[1]
            actual_class = OrmWrapper.load_class(module_name, simple_entity_name)
            this_ks = KnowledgeServer.this_knowledge_server()
            instance = actual_class.retrieve(this_ks.uri() + "/" + uri_instance)
            if format == 'JSON':
                exported_json = '{ "Export" : { "ExportDateTime" : "' + str(datetime.now()) + '", ' + instance.serialize(export_format='JSON', exported_instances = []) + ' } }'
                return render(request, 'knowledge_server/export.json', {'json': exported_json}, content_type="application/json")
            if format == 'XML':
                exported_xml = "<Export ExportDateTime=\"" + str(datetime.now()) + "\">" + instance.serialize(export_format='XML', exported_instances = []) + "</Export>"
                xmldoc = minidom.parseString(exported_xml)
                exported_pretty_xml = xmldoc.toprettyxml(indent="    ")
                return render(request, 'knowledge_server/export.xml', {'xml': exported_pretty_xml}, content_type="application/xhtml+xml")
        else:
            raise(Exception("The url '" + uri_instance + "' does not match the URIInstance format"))
    except Exception as es:
        if format == 'JSON':
            exported_json = '{ "Export" : { "ExportDateTime" : "' + str(datetime.now()) + '", "Error" : "' + str(es) + '" } }'
            return render(request, 'knowledge_server/export.json', {'json': exported_json}, content_type="application/json")
        if format == 'XML':
            exported_xml = "<Export ExportDateTime=\"" + str(datetime.now()) + "\" Error=\"" + str(es) + "\"/>"
            xmldoc = minidom.parseString(exported_xml)
            exported_pretty_xml = xmldoc.toprettyxml(indent="    ")
            return render(request, 'knowledge_server/export.xml', {'xml': exported_pretty_xml}, content_type="application/xhtml+xml")


def api_dataset_types(request, format):
    '''
        parameters:
            None
        
        Implementation:
            Invoking api_datasets #64 with parameter "DataSetStructure"
            so that I get all the Structures in this_ks in a shallow export
    '''
    # Look for all DataSetStructure of type "DataSetStructure-StructureNode-Application" ...
    entities_id = DataSetStructure.objects.filter(name=DataSetStructure.dataset_structure_DSN).values("id")
    # Look for the only DataSet whose DataSetStructure is *incidentally* of the above type (entity_id__in=entities_id)
    # whose instance is ov the above type root_instance_id__in=entities_id
    # and it is released (there must be exactly one!
    ei = DataSet.objects.get(version_released=True, root_instance_id__in=entities_id, dataset_structure_id__in=entities_id)
    dss = DataSetStructure.objects.get(pk=ei.root_instance_id)
    
    return api_datasets(request, DataSetStructure_URIInstance = dss.URIInstance, format=format)


def api_dataset_info(request, DataSet_URIInstance, format):
    '''
        #52 
        
        Parameters:
        * format { 'XML' | 'JSON' | 'HTML' = 'BROWSE' }
        * DataSet_URIInstance: URIInstance of the DataSet 
        
        Implementation:
        it fetches the DataSet, then the list of all that share the same root
        it returns DataSet.export(format) and for each on the above list:
            the URIInstance of the ErtityInstance
            the version status {working | released | obsolete}
            the version number (e.g. 0.1.0)
            the version date
            the version description
            other version metadata

    '''
    format = format.upper()
    DataSet_URIInstance = urllib.parse.unquote(DataSet_URIInstance).replace("%2F","/")
    dataset = DataSet.retrieve(DataSet_URIInstance)
    all_versions = DataSet.objects.filter(first_version = dataset.first_version)
    all_versions_serialized = ""
    all_versions_list = []
    if format != 'HTML' and format != 'BROWSE':
        for v in all_versions:
            if format == 'JSON':
                # note I am using DICT as a format so that I can merge the dict (.update) and then convert it to json
                all_versions_list.append(v.export(export_format = 'DICT', force_external_reference=True))
            else:
                all_versions_serialized += v.export(export_format = format, force_external_reference=True)
    if format == 'XML':
        ar = ApiResponse()
        ar.status = ApiResponse.success
        ar.content = "<DataSet>" + dataset.export(export_format = format, force_external_reference=True) + "</DataSet><Versions>" + all_versions_serialized + "</Versions>"
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if format == 'JSON':
        ar = ApiResponse()
        ar.content = { "DataSet": dataset.export(export_format = "DICT", force_external_reference=True), "Versions": all_versions_list }
        ar.status = ApiResponse.success 
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if format == 'HTML' or format == 'BROWSE':
        if dataset.dataset_structure.is_a_view:
            instances = dataset.get_instances()
        else:
            instances = []
            instances.append(dataset.root)
        all_versions_with_instances = []
        for v in all_versions:
            if v.URIInstance != dataset.URIInstance:
                version_with_instance = {}
                version_with_instance['dataset'] = v
                version_with_instance['model_metadata'] = []
                # views have no version by themselves; only their components have and they can be different
                # so if we are here we are not in a view hence there is just one instance: 
                #         I get root and not .get_instances()
                version_with_instance['model_metadata'].append(v.root)
                all_versions_with_instances.append(version_with_instance)
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'DataSet_URIInstance': DataSet_URIInstance, 'dataset': dataset, 'all_versions_with_instances': all_versions_with_instances, 'ks': dataset.owner_knowledge_server, 'instances': instances, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True) })
        return render_to_response('knowledge_server/api_dataset_info.html', context_instance=cont)
    
    
def api_datasets(request, DataSetStructure_URIInstance, format):
    '''
        http://redmine.davide.galletti.name/issues/64
        all the released datasets of a given structure/type
        
        parameter:
        * format { 'XML' | 'JSON' }
        * DataSetStructure_URIInstance: URIInstance of the DataSetStructure encoded
        
        Implementation:
        # it fetches the structure from the DB, looks for all the datasets
        # with that structure; if it is not a view only those that are released; 
    '''
    format = format.upper()
    dss = DataSetStructure.retrieve(urllib.parse.unquote(DataSetStructure_URIInstance).replace("%2F","/"))
    
    # Now I need to get all the released DataSet of the DataSetStructure passed as a parameter
    if dss.is_a_view:
        # version_released is not relevant for views
        released_dataset = DataSet.objects.filter(dataset_structure = dss)
    else:
        released_dataset = DataSet.objects.filter(dataset_structure = dss, version_released=True)
    serialized = ""
    comma = ""
    dataset_list = []
    for ei in released_dataset:
        if format == 'JSON':
            dataset_list.append(ei.export(export_format = "DICT", force_external_reference=True))
        else:
            serialized += ei.export(export_format = format, force_external_reference=True)
    if format == 'XML':
        ar = ApiResponse()
        ar.status = ApiResponse.success
        ar.content = "<DataSets>" + serialized + "</DataSets>"
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if format == 'JSON':
        ar = ApiResponse()
        ar.content = { "DataSets": dataset_list }
        ar.status = ApiResponse.success 
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")


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
                entity['URIInstance'] = urllib.parse.urlencode({'':ei['ActualInstance']['DataSetStructure']['URIInstance']})[1:]
                entity['oks_name'] = ei['owner_knowledge_server']['name']
                external_oks_url = KsUri(ei['owner_knowledge_server']['URIInstance']).home()
                entity['oks_home'] = urllib.parse.urlencode({'':external_oks_url})[1:]
                if ei['owner_knowledge_server']['URIInstance'] == explored_ks['URIInstance']:
                    owned_structures.append(entity)
                else:
                    other_structures.append(entity)
        else:
            HttpResponse("Error invoking api_ks_info on " + ks_url + " - " + ar_ks_info.message)
    except Exception as ex:
        return HttpResponse(str(ex))
    cont = RequestContext(request, {'owned_structures':owned_structures, 'other_structures':other_structures, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True), 'organization': organization, 'explored_ks': explored_ks, 'ks_url':urllib.parse.urlencode({'':ks_url})[1:]})
    return render_to_response('knowledge_server/ks_explorer_entities.html', context_instance=cont)


def ks_explorer_form(request):
    form = myforms.ExploreOtherKSForm()
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'form':form, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
    return render_to_response('knowledge_server/ks_explorer_form.html', context_instance=cont)


def datasets_of_type(request, ks_url, URIInstance, format):
    '''
    returns the list of datasets of a specific type/structure
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    format = format.upper()
    ks_url = urllib.parse.unquote(ks_url)
    URIInstance = urllib.parse.unquote(URIInstance)
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
    response = urlopen(URIInstance + "/json")
    es_info_json = response.read().decode("utf-8")
    
    if format == 'XML':
        local_url = reverse('api_datasets', args=(urllib.parse.quote(URIInstance),format))
    if format == 'JSON' or format == 'BROWSE':
        local_url = reverse ('api_datasets', args=(urllib.parse.quote(URIInstance).replace("/","%252F"),'JSON'))
    response = urlopen(ks_url + local_url)
    entities = response.read().decode("utf-8")
    if format == 'XML':
        return render(request, 'knowledge_server/export.xml', {'xml': entities}, content_type="application/xhtml+xml")
    if format == 'JSON':
        return render(request, 'knowledge_server/export.json', {'json': entities}, content_type="application/json")
    if format == 'BROWSE':
        # parse
        decoded = json.loads(entities)
        # I prepare a list of URIInstance of root so that I can check which I have subscribed to
        first_version_URIInstances = []
        for ei in decoded['content']['DataSets']:
            if 'first_version' in ei:
                first_version_URIInstances.append(ei['first_version']['URIInstance'])
            else:
                first_version_URIInstances.append(ei['URIInstance'])
        subscribed = SubscriptionToOther.objects.filter(first_version_URIInstance__in=first_version_URIInstances)
        subscribed_first_version_URIInstances = []
        for s in subscribed:
            subscribed_first_version_URIInstances.append(s.first_version_URIInstance)
        entities = []
        for ei in decoded['content']['DataSets']:
            entity = {}
            if 'ActualInstance' in ei.keys():
                actual_instance_class = list(ei['ActualInstance'].keys())[0]
                entity['actual_instance_name'] = ei['ActualInstance'][actual_instance_class]['name']
            else: #is a view
                entity['actual_instance_name'] = ei['description']
            entity['encodedURIInstance'] = urllib.parse.urlencode({'':ei['URIInstance']})[1:]
            entity['URIInstance'] = urllib.parse.quote(ei['URIInstance']).replace("/","%252F")
            subscribed_URIInstance = ei['first_version']['URIInstance'] if 'first_version' in ei else ei['URIInstance']
            if subscribed_URIInstance in subscribed_first_version_URIInstances:
                entity['subscribed'] = True
            entities.append(entity)
        cont = RequestContext(request, {'entities':entities, 'organization': organization, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True), 'external_ks': external_ks, 'es_info_json': es_info_json})
        return render_to_response('knowledge_server/datasets_of_type.html', context_instance=cont)
    
    
def home(request):
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
    return render(request, 'knowledge_server/home.html', context_instance=cont)


def api_ks_info(request, format):
    '''
        #80

        parameter:
        * format { 'XML' | 'JSON' }
        
        Implementation:
          it fetches this KS from the DB, takes its Organization and exports
          it with the structure "Organization-KS" 
    '''
    format = format.upper()
    this_ks = KnowledgeServer.this_knowledge_server()    
    es = DataSetStructure.objects.get(name = DataSetStructure.organization_DSN)
    ei = DataSet.objects.get(dataset_structure=es, root_instance_id=this_ks.organization.id)
    return api_dataset(request, ei.URIInstance, format)
    
    
def this_ks_unsubscribes_to(request, URIInstance):
    '''
    '''
    pass


def release_dataset(request, Dataset_URIInstance):
    '''
    '''
    try:
        Dataset_URIInstance = urllib.parse.unquote(Dataset_URIInstance)
        dataset = DataSet.objects.get(URIInstance = Dataset_URIInstance)
        dataset.set_released()
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, Dataset_URIInstance + " successfully released.").json()}, content_type="application/json")
    except Exception as ex:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, str(ex)).json()}, content_type="application/json")
        
        
def this_ks_subscribes_to(request, URIInstance):
    '''
    This ks is subscribing to a data set in another ks
    First I store the subscription locally
    Then I invoke remotely api_subscribe
    If it works I commit locally
    '''
    URIInstance = str(urllib.parse.unquote(URIInstance).replace("%2F","/"))
    other_ks_uri = KsUri(URIInstance).home()

    KnowledgeServer.get_remote_ks(other_ks_uri)
    
    try:
        with transaction.atomic():
            encoded_URIInstance = urllib.parse.urlencode({'':URIInstance})[1:]
            # invoke remote API to subscribe
            this_ks = KnowledgeServer.this_knowledge_server()
            url_to_invoke = urllib.parse.urlencode({'':this_ks.uri() + reverse('api_notify')})[1:]
            ar = ApiResponse()
            ar.invoke_oks_api(other_ks_uri, 'api_subscribe', args=(encoded_URIInstance,url_to_invoke,))
            if ar.status == ApiResponse.success:
                # save locally
                sto = SubscriptionToOther()
                sto.URI = URIInstance
                sto.first_version_URIInstance = ar.content # it contains the URIInstance of the first version
                sto.save()
                return render(request, 'knowledge_server/export.json', {'json': ar.response}, content_type="application/json")
            else:
                return render(request, 'knowledge_server/export.json', {'json': ar.response}, content_type="application/json")
    except Exception as ex:
        return HttpResponse(str(ex))
    
    
def api_subscribe(request, URIInstance, remote_url):
    '''
        #35 
        parameters:
        URIInstance is the one to which I want to subscribe
        remote_url the URL this KS has to invoke to notify
    '''
    # check the client KS has already subscribed; the check is done using the remote_ks (if any), remote URL otherwise
    URIInstance = urllib.parse.unquote(URIInstance)
    remote_url = urllib.parse.unquote(remote_url)

    # I want to check the request comes from the same domain as the remote_url
    # I do this checking that the IP address is the same
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')    

    ip_notification = socket.gethostbyname(KsUri(remote_url).netloc)
    if ip_notification != ip:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, "Trying to subscribe from a different IP address", "").json()}, content_type="application/json")
    
    # I try to get the remote ks info (if it is a ks) locally
    remote_ks = KnowledgeServer.get_remote_ks(remote_url)

    ei = DataSet.objects.get(URIInstance=URIInstance)
    first_version_URIInstance = ei.first_version.URIInstance
    if remote_ks:
        existing_subscriptions = SubscriptionToThis.objects.filter(first_version_URIInstance=first_version_URIInstance, remote_ks=remote_ks)
    else:
        existing_subscriptions = SubscriptionToThis.objects.filter(first_version_URIInstance=first_version_URIInstance, remote_url=remote_url)
    if len(existing_subscriptions) > 0:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, "Already subscribed").json()}, content_type="application/json")
    stt = SubscriptionToThis()
    stt.first_version_URIInstance=first_version_URIInstance
    stt.remote_url=remote_url
    stt.remote_ks = remote_ks
    stt.save()
    return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, "Subscribed sucessfully", first_version_URIInstance).json()}, content_type="application/json")
   
    
def api_unsubscribe(request, URIInstance, remote_URL):
    '''
        #123
        parameters:
        URIInstance is the one to which I want to subscribe
        remote_url the URL this KS has to invoke to notify
    '''
    
    
def api_dataset_structure_code(request, DataSetStructure_URIInstance):
    '''
    This API is needed just by another OKS and it is not meant to be public
    It's goal is to provide another OKS with the information needed to generate
    and migrate the models within a structure. TODO: Models that are external references
    are not included.
    The information is provided in the form of the code of the classes in a dictionary
    that groups them by APP/MODULE
    '''
    dss = DataSetStructure.retrieve(urllib.parse.unquote(DataSetStructure_URIInstance).replace("%2F","/"))
    try:
        classes_code = dss.classes_code()
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, "", classes_code).json()}, content_type="application/json")
    except Exception as ex:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, str(ex)).json()}, content_type="application/json")


@csrf_exempt
def api_notify(request):
    '''
        #35 it receives a notification; the verb is POST
        parameters:
        TODO: 
            first_version_URIInstance->first_version_URIInstance
            URL_dataset --> dataset_URIInstance
            URL_structure --> structure_URIInstance
        first_version_URIInstance: the URIInstance of the first version of the DataSet for which the event has happened
        event_type: the URInstance of the EventType
   '''
    first_version_URIInstance = request.POST.get("first_version_URIInstance", "")
    URL_dataset = request.POST.get("URL_dataset", "")
    URL_structure = request.POST.get("URL_structure", "")
    event_type = request.POST.get("type", "")
    # Did I subscribe to this?
    sto = SubscriptionToOther.objects.filter(first_version_URIInstance=first_version_URIInstance)
    ar = ApiResponse()
    if len(sto) > 0:
        nr = NotificationReceived()
        nr.URL_dataset = URL_dataset
        nr.URL_structure = URL_structure
        nr.save()
        ar.status = ApiResponse.success
    else:
        ar.status = ApiResponse.failure
        ar.message = "Not subscribed to this"
    return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")

        
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
    cont = RequestContext(request, {'received_notifications': received_notifications, 'notifications_to_be_sent': notifications_to_be_sent, 'events': events, 'subscriptions_to_other': subscriptions_to_other, 'subscriptions_to_this': subscriptions_to_this, 'this_ks': this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
    
    return render_to_response('knowledge_server/subscriptions.html', context_instance=cont)


def debug(request):
    '''
    created to debug code
    '''
    try:
        import importlib
        importlib.invalidate_caches()
        mmm = importlib.import_module("knowledge_server.models")
        print(mmm)
#         mmm = importlib.import_module("licenses.models")
#         reload(mmm)
        
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#         proc = Popen("python manage.py startapp deleteme", shell=True, cwd=BASE_DIR)
#         return_code = proc.wait()
#         the above commands create it correctly
        
        from django.core import management
        new_app_name = "delme2"

#         os.makedirs(BASE_DIR + "/" + new_app_name)
        management.call_command('startapp', new_app_name, 'oks/' + new_app_name, interactive=False)
        with open(BASE_DIR + "/" + new_app_name + "/models.py", "a") as myfile:
            myfile.write("from knowledge_server.models import ShareableModel\n\n\n\n")
        from django.apps.registry import apps as global_apps
        from collections import OrderedDict
        from django.conf import settings
        from django.db.migrations.state import ModelState, ProjectState

        print("11111111111111111111111111111111111111111111111111")
        mm = global_apps.get_models(include_swapped=True)
        ps = ProjectState.from_apps(global_apps)
        for m in mm:
            print(m)
        print(ps.models)

        with open(BASE_DIR + "/" + new_app_name + "/models.py", "a") as myfile:
#             myfile.write("class aa(models.Model):\n    legalcode = models.TextField(default = \"\")")
            myfile.write("class License(ShareableModel):\n    '''\n    Licenses from the list on http://opendefinition.org/licenses/\n    JUST THOSE WITH DOMAIN DATA\n    '''\n    name = models.CharField(max_length=200L)\n    short_name = models.CharField(max_length=50L)\n    # human_readable is a summary of the legal code;\n    human_readable = models.TextField(null = True, blank=True)\n    legalcode = models.TextField(default = \"\")\n    adaptation_shared = models.NullBooleanField(blank=True, null=True)\n    # requires to be shared with the attribution\n    attribution = models.NullBooleanField(blank=True, null=True)\n    # requires to be shared with the same license\n    share_alike = models.NullBooleanField(blank=True, null=True)\n    commercial_use = models.NullBooleanField(blank=True, null=True)\n    url_info = models.CharField(max_length=160L, null = True, blank=True)\n    reccomended_by_opendefinition = models.NullBooleanField(blank=True, null=True)\n    conformant_for_opendefinition = models.NullBooleanField(blank=True, null=True)\n    image = models.CharField(max_length=160L, null=True, blank=True)\n    image_small = models.CharField(max_length=160L, null=True, blank=True)\n")
        settings.INSTALLED_APPS += (new_app_name, )
        global_apps.app_configs = OrderedDict()
        global_apps.ready = False
        global_apps.populate(settings.INSTALLED_APPS)

        print("2222222222222222222222222222222222222222222222222222")
        mm = global_apps.get_models(include_swapped=True)
        ps = ProjectState.from_apps(global_apps)
        for m in mm:
            print(m)
        print(ps.models)
        
        
        management.call_command('makemigrations', new_app_name, interactive=False)
#         management.call_command('migrate', new_app_name, interactive=False)



#         import inspect
#         import types
#         l  = list({x: DataSetStructure.__dict__[x]} for x in DataSetStructure.__dict__.keys() if 
#                   ( inspect.isfunction(DataSetStructure.__dict__[x])
#                     or inspect.ismethod(DataSetStructure.__dict__[x])
#                     or inspect.ismethoddescriptor(DataSetStructure.__dict__[x]) )
#                   )
#         l  = list({x: DataSetStructure.__dict__[x]} for x in DataSetStructure.__dict__.keys() if 
#                   ( inspect.isroutine(DataSetStructure.__dict__[x]) )
#                   )
#         
#         sl = inspect.getsource(Notification)
#         print (sl)

#         import os
#         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# #         proc = Popen("python manage.py startapp deleteme", shell=True, cwd=BASE_DIR)
# #         return_code = proc.wait()
# #         the above commands create it correctly
#         
#         from django.core import management
#         new_app_name = "deleteme7"
# 
# #         os.makedirs(BASE_DIR + "/" + new_app_name)
# #         management.call_command('startapp', new_app_name, 'oks/' + new_app_name, interactive=False)
# #         the above 2 lines work fine
# 
# #         import os
# #         from subprocess import Popen, PIPE
# #         
# #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # #         proc = Popen("python manage.py startapp deleteme", shell=True, cwd=BASE_DIR)
# # #         return_code = proc.wait()
# # #         the above commands create it correctly
# #         
# #         from django.core import management
# #         new_app_name = "deleteme3"
# # 
#         os.makedirs(BASE_DIR + "/" + new_app_name)
#         management.call_command('startapp', new_app_name, 'oks/' + new_app_name, interactive=False)
# #         the above 2 lines work fine
#  
#         from django.apps import apps
#         from collections import OrderedDict
#         from django.conf import settings
# 
#         with open(BASE_DIR + "/" + new_app_name + "/models.py", "a") as myfile:
#             myfile.write("from knowledge_server.models import ShareableModel\n\n\n\n")
#             myfile.write("class aa(models.Model):\n    legalcode = models.TextField(default = \"\")")
#         
#     
#         settings.INSTALLED_APPS += (new_app_name, )
#         # I load the app
#         apps.app_configs = OrderedDict()
#         apps.ready = False
#         apps.populate(settings.INSTALLED_APPS)
#         
# 
#         management.call_command('makemigrations', new_app_name, interactive=False)
#         management.call_command('migrate', new_app_name, interactive=False)


    
        return HttpResponse("OK ")
    except Exception as ex:
        return HttpResponse(str(ex))

