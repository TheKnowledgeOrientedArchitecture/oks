# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import logging
import socket
import urllib

from datetime import datetime
from xml.dom import minidom

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt

from knowledge_server.models import ApiResponse, DataSetStructure, DataSet, KnowledgeServer, SubscriptionToThis
from knowledge_server.models import SubscriptionToOther, NotificationReceived
from knowledge_server.orm_wrapper import OrmWrapper
from knowledge_server.utils import KsUrl

logger = logging.getLogger(__name__)


@cache_page(60 * 600)
def api_ks_info(request):
    '''
        #80

        parameter:
        * response_format { 'XML' | 'JSON' }
        
        Implementation:
          it fetches this KS from the DB, takes its Organization and exports
          it with the structure "Organization-KS"
        CAN BE CACHED
    '''
    this_ks = KnowledgeServer.this_knowledge_server()
    dss = DataSetStructure.objects.get(name = DataSetStructure.organization_DSN)
    dataset = DataSet.objects.get(dataset_structure=dss, root_instance_id=this_ks.organization.id)
    return api_dataset(request, UKCL=dataset.UKCL)


@cache_page(60 * 600)
def api_dataset_view(request):
    '''
        it returns the data of the istance with pk=root_id in the dataset (which is a view)
        if we are browsing a view there is not just one single root that we can explore
        but a list of instances that match the criteria; root_id tells us which one to browse
        CAN BE CACHED
    '''
    DataSet_UKCL = request.GET[ 'UKCL' ]
    root_id = request.GET[ 'id' ]
    ar = ApiResponse( request=request )

    dataset = DataSet.retrieve_locally(DataSet_UKCL)
    actual_instance = ""
    actual_instance_json = ""
    # this dataset is a view; I shall use root_id to retrieve the actual instance
    module_name = dataset.dataset_structure.root_node.model_metadata.module
    dataset_uri = KsUrl(DataSet_UKCL)
    actual_instance_class = OrmWrapper.load_class(dataset_uri.netloc, module_name, dataset.dataset_structure.root_node.model_metadata.name) 
    actual_instance = actual_instance_class.objects.get(pk=root_id)
    
    if ar.response_format == 'HTML' or ar.response_format == 'BROWSE':
        actual_instance_json = '{' + actual_instance.serialize(dataset.dataset_structure.root_node, export_format='json', exported_instances = []) + '}'
    if ar.response_format == 'JSON':
        ar.content = { "DataSet": dataset.export(export_format = 'DICT') }
        ar.status = ApiResponse.success
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if ar.response_format == 'XML':
        ar.status = ApiResponse.success
        ar.content = dataset.export(export_format = ar.response_format)
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if ar.response_format == 'HTML' or ar.response_format == 'BROWSE':
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'dataset': dataset, 'actual_instance': actual_instance, 'actual_instance_json': actual_instance_json, 'sn': dataset.dataset_structure.root_node, 'DataSet_UKCL': DataSet_UKCL, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True)})
        return render_to_response('knowledge_server/browse_dataset.html', context_instance=cont)


# @cache_page(60 * 600)
def api_dataset(request, UKCL=None):
    '''
        #36
        It returns the data in the dataset with the UKCL in the parameter 
        
        parameter:
        * DataSet_UKCL: UKCL of the DataSet 
        
        Implementation:
        # it creates the ModelMetadata class, 
        # fetches from the DB the one with pk = DataSet.root_instance_id
        # it runs to_xml of the ModelMetadata using DataSet.dataset_structure.root_node
        CAN BE CACHED
    '''
    if UKCL:
        # invoked from ks_info
        DataSet_UKCL = UKCL
    else:
        DataSet_UKCL = request.GET['UKCL']
    ar = ApiResponse(request=request)

    url = KsUrl(DataSet_UKCL)
    # If it is not a DataSet we try to find the dataset it is in
    url.search_on_db()
    if url.actual_instance:
        if isinstance(url.actual_instance, DataSet):
            dataset = url.actual_instance
        else:
            dataset = url.actual_instance.dataset_I_belong_to
    if (not url.actual_instance) and (not dataset):
        ar.message = "Either the URL requested is not on this database or it is not part of a released dataset."
        if ar.response_format == 'JSON':
            return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
        if ar.response_format == 'XML':
            ar.status = ApiResponse.failure
            return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")

    actual_instance_json = ""
    #this dataset is not a view; if not dataset.dataset_structure.is_a_view:
    actual_instance = dataset.root

    if ar.response_format == 'JSON':
        ar.content = { "DataSet": dataset.export(export_format = 'DICT') }
        ar.status = ApiResponse.success
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if ar.response_format == 'XML':
        ar.status = ApiResponse.success
        ar.content = dataset.export(export_format = ar.response_format)
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if ar.response_format == 'HTML' or ar.response_format == 'BROWSE':
        actual_instance_json = '{' + actual_instance.serialize(dataset.dataset_structure.root_node, export_format='json', exported_instances = []) + '}'
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'dataset': dataset, 'actual_instance': actual_instance, 'actual_instance_json': actual_instance_json, 'sn': dataset.dataset_structure.root_node, 'DataSet_UKCL': DataSet_UKCL, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True)})
        return render_to_response('knowledge_server/browse_dataset.html', context_instance=cont)
        

@cache_page(60 * 600)
def api_catch_all(request, uri_instance):
    '''
        parameters:
            url: http://root.beta.thekoa.org/knowledge_server/Attribute/1
            url: http://root.beta.thekoa.org/knowledge_server/Attribute/1/xml
            url: http://root.beta.thekoa.org/knowledge_server/Attribute/1/json
        
        Implementation:
            I do something only if it is a UKCL in my database; otherwise I return a not found message
            If there is a trailing string for the response_format I use it, otherwise I apply the default xml
            The trailing string can be "/xml", "/xml/", "/json", "/json/" where each character can 
            be either upper or lower case   
        CAN BE CACHED
    '''
    # I search for a response_format string, a UKCL has no trailing slash
    response_format = 'XML' #default
    if uri_instance[-1:] == "/":
        #I remove a trailing slash
        uri_instance = uri_instance[:-1]
    if uri_instance[-3:].lower() == "xml":
        uri_instance = uri_instance[:-4]
    if uri_instance[-4:].lower() == "json":
        response_format = 'JSON'
        uri_instance = uri_instance[:-5]
        
    try:
        split_path = uri_instance.split('/')
        if len(split_path) == 3:
            module_name = split_path[0]
            simple_entity_name = split_path[1]
            this_ks = KnowledgeServer.this_knowledge_server()
            actual_class = OrmWrapper.load_class(this_ks.netloc, module_name, simple_entity_name)
            instance = actual_class.retrieve_locally(this_ks.url() + "/" + uri_instance)
            if response_format == 'JSON':
                exported_json = '{ "Export" : { "ExportDateTime" : "' + str(datetime.now()) + '", ' + instance.serialize(export_format='JSON', exported_instances = []) + ' } }'
                return render(request, 'knowledge_server/export.json', {'json': exported_json}, content_type="application/json")
            if response_format == 'XML':
                exported_xml = "<Export ExportDateTime=\"" + str(datetime.now()) + "\">" + instance.serialize(export_format='XML', exported_instances = []) + "</Export>"
                xmldoc = minidom.parseString(exported_xml)
                exported_pretty_xml = xmldoc.toprettyxml(indent="    ")
                return render(request, 'knowledge_server/export.xml', {'xml': exported_pretty_xml}, content_type="application/xhtml+xml")
        else:
            raise(Exception("The url '" + uri_instance + "' does not match the UKCL format"))
    except Exception as es:
        if response_format == 'JSON':
            exported_json = '{ "Export" : { "ExportDateTime" : "' + str(datetime.now()) + '", "Error" : "' + str(es) + '" } }'
            return render(request, 'knowledge_server/export.json', {'json': exported_json}, content_type="application/json")
        if response_format == 'XML':
            exported_xml = "<Export ExportDateTime=\"" + str(datetime.now()) + "\" Error=\"" + str(es) + "\"/>"
            xmldoc = minidom.parseString(exported_xml)
            exported_pretty_xml = xmldoc.toprettyxml(indent="    ")
            return render(request, 'knowledge_server/export.xml', {'xml': exported_pretty_xml}, content_type="application/xhtml+xml")


@cache_page(60 * 600)
def api_dataset_types(request):
    '''
        parameters:
            None
        
        Implementation:
            Invoking api_datasets #64 with parameter "DataSetStructure"
            so that I get all the Structures in this_ks in a shallow export
        CAN BE CACHED
    '''
    ar = ApiResponse( request=request )
    dss = DataSetStructure.objects.using('materialized').get(name=DataSetStructure.dataset_structure_DSN)
    return api_datasets(request, DataSetStructure_UKCL = dss.UKCL, response_format=ar.response_format)


@cache_page(60 * 600)
def api_dataset_info(request):
    '''
        #52 
        
        Parameters:
        * response_format { 'XML' | 'JSON' | 'HTML' = 'BROWSE' }
        * DataSet_UKCL: UKCL of the DataSet 
        
        Implementation:
        it fetches the DataSet, then the list of all that share the same root
        it returns DataSet.export(response_format) and for each on the above list:
            the UKCL of the DataSet
            the version status {working | released | obsolete}
            the version number (e.g. 0.1.0)
            the version date
            the version description
            other version metadata
        CAN BE CACHED
    '''
    DataSet_UKCL = request.GET['UKCL']
    ar = ApiResponse(request=request)
    DataSet_UKCL_unquoted = urllib.parse.unquote(DataSet_UKCL).replace("%2F","/")
    dataset = DataSet.retrieve_locally(DataSet_UKCL_unquoted)
    all_versions = DataSet.objects.filter(first_version = dataset.first_version)
    all_versions_serialized = ""
    all_versions_list = []
    if ar.response_format != 'HTML' and ar.response_format != 'BROWSE':
        for v in all_versions:
            if ar.response_format == 'JSON':
                # note I am using DICT as a response_format so that I can merge the dict (.update) and then convert it to json
                all_versions_list.append(v.export(export_format = 'DICT', force_external_reference=True))
            else:
                all_versions_serialized += v.export(export_format = ar.response_format, force_external_reference=True)
    if ar.response_format == 'XML':
        ar.status = ApiResponse.success
        ar.content = "<DataSet>" + dataset.export(export_format = ar.response_format, force_external_reference=True) + "</DataSet><Versions>" + all_versions_serialized + "</Versions>"
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if ar.response_format == 'JSON':
        ar.content = { "DataSet": dataset.export(export_format = "DICT", force_external_reference=True), "Versions": all_versions_list }
        ar.status = ApiResponse.success
        return HttpResponse(ar.json(), content_type = "application/json") 
#         return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")
    if ar.response_format == 'HTML' or ar.response_format == 'BROWSE':
        if dataset.dataset_structure.is_a_view:
            instances = dataset.get_instances()
        else:
            instances = []
            instances.append(dataset.root)
        all_versions_with_instances = []
        for v in all_versions:
            if v.UKCL != dataset.UKCL:
                version_with_instance = {}
                version_with_instance['dataset'] = v
                version_with_instance['root'] = []
                # views have no version by themselves; only their components have and they can be different
                # so if we are here we are not in a view hence there is just one instance: 
                #         I get root and not .get_instances()
                version_with_instance['root'].append(v.root)
                all_versions_with_instances.append(version_with_instance)
        this_ks = KnowledgeServer.this_knowledge_server()
        cont = RequestContext(request, {'DataSet_UKCL': DataSet_UKCL, 'dataset': dataset, 'all_versions_with_instances': all_versions_with_instances, 'ks': dataset.knowledge_server, 'instances': instances, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True) })
        return render_to_response('knowledge_server/api_dataset_info.html', context_instance=cont)
    
    
@cache_page(60 * 600)
def api_datasets(request, DataSetStructure_UKCL = None, response_format = None):
    '''
        http://redmine.davide.galletti.name/issues/64
        all the released datasets of a given structure/type
        
        parameter:
        * response_format { 'XML' | 'JSON' }
        * DataSetStructure_UKCL: UKCL of the DataSetStructure encoded
        
        Implementation:
        # it fetches the structure from the DB, looks for all the datasets
        # with that structure; if it is not a view only those that are released; 
        CAN BE CACHED
    '''
    if not DataSetStructure_UKCL:
        DataSetStructure_UKCL = request.GET['UKCL']
    if response_format:
        ar = ApiResponse(format=response_format)
    else:
        # if not specified I get it from the request object
        ar = ApiResponse(request=request)
    dss = DataSetStructure.retrieve_locally(urllib.parse.unquote(DataSetStructure_UKCL).replace("%2F","/"))
    
    # Now I need to get all the released DataSet of the DataSetStructure passed as a parameter
    if dss.is_a_view:
        # version_released is not relevant for views
        released_dataset = DataSet.objects.filter(dataset_structure = dss)
    else:
        released_dataset = DataSet.objects.filter(dataset_structure = dss, version_released=True)
    serialized = ""
    comma = ""
    dataset_list = []
    for dataset in released_dataset:
        if ar.response_format == 'JSON':
            dataset_list.append(dataset.export(export_format = "DICT", force_external_reference=True))
        else:
            serialized += dataset.export(export_format = ar.response_format, force_external_reference=True)
    if ar.response_format == 'XML':
        ar.status = ApiResponse.success
        ar.content = "<DataSets>" + serialized + "</DataSets>"
        return render(request, 'knowledge_server/export.xml', {'xml': ar.xml()}, content_type="application/xhtml+xml")
    if ar.response_format == 'JSON':
        ar.content = { "DataSets": dataset_list }
        ar.status = ApiResponse.success 
        return render(request, 'knowledge_server/export.json', {'json': ar.json()}, content_type="application/json")


@never_cache
def api_subscribe(request):
    '''
        #35 
        parameters:
        UKCL is the one to which I want to subscribe
        remote_url the URL this KS has to invoke to notify
        NEVER CACHED
    '''
    UKCL = request.GET[ 'UKCL' ]
    remote_url = request.GET[ 'remote_url' ]

    # I want to check the request comes from the same domain as the remote_url
    # I do this checking that the IP address is the same
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')    

    ip_notification = socket.gethostbyname(KsUrl(remote_url).netloc)
    if ip_notification != ip:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, "Trying to subscribe from a different IP address", "").json()}, content_type="application/json")

    ar = ApiResponse( request = request )

    # I try to get the remote ks info (if it is a ks) locally
    remote_ks = KnowledgeServer.get_remote_ks(remote_url)

    dataset = DataSet.objects.get(UKCL=UKCL)
    first_version_UKCL = dataset.first_version.UKCL
    # check the client KS has already subscribed; the check is done using the remote_ks (if any), remote URL otherwise
    if remote_ks:
        existing_subscriptions = SubscriptionToThis.objects.filter(first_version_UKCL=first_version_UKCL,
                                                                   remote_ks=remote_ks)
    else:
        existing_subscriptions = SubscriptionToThis.objects.filter(first_version_UKCL=first_version_UKCL,
                                                                   remote_url=remote_url)
    if len(existing_subscriptions) > 0:
        return render(request, 'knowledge_server/export.json',
                      {'json': ApiResponse(ApiResponse.failure, "Already subscribed").json()},
                      content_type="application/json")
    stt = SubscriptionToThis()
    stt.first_version_UKCL=first_version_UKCL
    stt.remote_url = remote_url
    stt.remote_ks = remote_ks
    stt.save()
    return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, "Subscribed sucessfully", first_version_UKCL).json()}, content_type="application/json")
   
    
@never_cache
def api_unsubscribe(request):
    '''
        #123
        parameters:
        UKCL is the one I want to unsubscribe from
        NEVER CACHED
    '''
    ar = ApiResponse( request = request )
    UKCL = request.GET[ 'UKCL' ]
    # remote_url has to be a parameter because without it I would have to guess the remote
    # server who has subscribed from the IP and/or the domain name in the request: unreliable
    remote_url = request.GET[ 'remote_url' ]
    # I want to check the request comes from the same domain as the remote_url
    # I do this checking that the IP address is the same
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    ip_notification = socket.gethostbyname(KsUrl(remote_url).netloc)
    if ip_notification != ip:
        return render(request, 'knowledge_server/export.json',
                      {'json': ApiResponse(ApiResponse.failure, "Apparently this is a malicious attempt to unsubscribe.",
                                           "").json()}, content_type="application/json")

    dataset = DataSet.objects.get( UKCL=UKCL )
    first_version_UKCL = dataset.first_version.UKCL
    if SubscriptionToThis.objects.filter(first_version_UKCL = first_version_UKCL, remote_url=remote_url).exists():
        stt = SubscriptionToThis.objects.get(first_version_UKCL = first_version_UKCL, remote_url=remote_url)
        stt.delete()
    else:
        logger.warning( "Unsubscribe requested for a non existing subscription: %s from %s" % (UKCL, remote_url) )
    return render(request, 'knowledge_server/export.json',
                  {'json': ApiResponse(ApiResponse.failure, "Your request has been processed").json()},
                  content_type="application/json")

    
@cache_page(60 * 600)
def api_dataset_structure_code(request):
    '''
        This API is needed just by another OKS and it is not meant to be public
        It's goal is to provide another OKS with the information needed to generate
        and migrate the models within a structure. TODO: Models that are external references
        are not included.
        The information is provided in the form of the code of the classes in a dictionary
        that groups them by APP/MODULE
        CAN BE CACHED
    '''
    DataSetStructure_UKCL = request.GET['UKCL']
    dss = DataSetStructure.retrieve_locally(urllib.parse.unquote(DataSetStructure_UKCL).replace("%2F","/"))
    try:
        classes_code = dss.classes_code()
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, "", classes_code).json()}, content_type="application/json")
    except Exception as ex:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, str(ex)).json()}, content_type="application/json")

@never_cache
@csrf_exempt
def api_notify(request):
    '''
        #35 it receives a notification; the verb is POST
        parameters:
        TODO: 
            first_version_UKCL->first_version_UKCL
            URL_dataset --> dataset_UKCL
            URL_structure --> structure_UKCL
        first_version_UKCL: the UKCL of the first version of the DataSet for which the event has happened
        event_type: the URInstance of the EventType
        NEVER CACHED
   '''
    first_version_UKCL = request.POST.get("first_version_UKCL", "")
    URL_dataset = request.POST.get("URL_dataset", "")
    URL_structure = request.POST.get("URL_structure", "")
    event_type = request.POST.get("type", "")
    # Did I subscribe to this?
    sto = SubscriptionToOther.objects.filter(first_version_UKCL=first_version_UKCL)
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

        
