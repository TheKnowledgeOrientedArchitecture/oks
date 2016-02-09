# -*- coding: utf-8 -*-

from datetime import datetime
import json
import urllib, urllib2, urlparse
from xml.dom import minidom

from django.db import transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from knowledge_server.models import ModelMetadata, DataSetStructure, DataSet, KnowledgeServer
from knowledge_server.models import SubscriptionToOther, SubscriptionToThis, ApiResponse, NotificationReceived, KsUri, Notification, Event
import knowledge_server.utils as utils
import logging
import forms as myforms 

logger = logging.getLogger(__name__)

def api_dataset_view(request, DataSet_URIInstance, root_id, format):
    '''
    it returns the data of the istance with pk=root_id in the dataset (which is a view)
    if we are browsing a view there is not just one single root that we can explore
    but a list of instances that match the criteria; root_id tells us which one to browse
    '''
    format = format.upper()
    DataSet_URIInstance_decoded = urllib.unquote(DataSet_URIInstance)
    dataset = DataSet.retrieve(DataSet_URIInstance_decoded)
    actual_instance = ""
    actual_instance_json = ""
    # this dataset is a view; I shall use root_id to retrieve the actual instance
    module_name = dataset.dataset_structure.root_node.model_metadata.module
    actual_instance_class = utils.load_class(module_name + ".models", dataset.dataset_structure.root_node.model_metadata.name) 
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
    DataSet_URIInstance_decoded = urllib.unquote(DataSet_URIInstance)
    dataset = DataSet.retrieve(DataSet_URIInstance_decoded)
    actual_instance = ""
    actual_instance_json = ""
    #this dataset is not a view; if not dataset.dataset_structure.is_a_view:
    actual_instance = dataset.root
    
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
            actual_class = utils.load_class(module_name + ".models", simple_entity_name)
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
    DataSet_URIInstance = urllib.unquote(DataSet_URIInstance).replace("%2F","/")
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
    dss = DataSetStructure.retrieve(urllib.unquote(DataSetStructure_URIInstance).replace("%2F","/"))
    
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
        ks_url = urlparse.parse_qs('url=' + request.GET['ks_complete_url'])['url'][0]
    except:
        ks_url = request.POST['ks_complete_url']
    try:
        this_ks = KnowledgeServer.this_knowledge_server()
        # info on the remote ks
        local_url = reverse('api_ks_info', args=("JSON",))
        response = urllib2.urlopen(ks_url + local_url)
        ks_info_json_stream = response.read()
        # parsing json
        ks_info_json = json.loads(ks_info_json_stream)
        organization = ks_info_json['content']['DataSet']['ActualInstance']['Organization']
        for ks in organization['knowledgeserver_set']:
            if ks['this_ks']:
                explored_ks = ks
            
        # info about structures on the remote ks
        local_url = reverse('api_dataset_types', args=("JSON",))
        response = urllib2.urlopen(ks_url + local_url)
        entities_json = response.read()
        # parsing json
        decoded = json.loads(entities_json)
        owned_structures = []
        other_structures = []
        for ei in decoded['content']['DataSets']:
            entity = {}
            entity['actual_instance_name'] = ei['ActualInstance']['DataSetStructure']['name']
            entity['URIInstance'] = urllib.urlencode({'':ei['ActualInstance']['DataSetStructure']['URIInstance']})[1:]
            entity['oks_name'] = ei['owner_knowledge_server']['name']
            external_oks_url = KsUri(ei['owner_knowledge_server']['URIInstance']).home()
            entity['oks_home'] = urllib.urlencode({'':external_oks_url})[1:]
            if ei['owner_knowledge_server']['URIInstance'] == explored_ks['URIInstance']:
                owned_structures.append(entity)
            else:
                other_structures.append(entity)
    except Exception as ex:
        return HttpResponse(ex.message)
    cont = RequestContext(request, {'owned_structures':owned_structures, 'other_structures':other_structures, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True), 'organization': organization, 'explored_ks': explored_ks, 'ks_url':urllib.urlencode({'':ks_url})[1:]})
    return render_to_response('knowledge_server/ks_explorer_entities.html', context_instance=cont)

def ks_explorer_form(request):
    form = myforms.ExploreOtherKSForm()
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'form':form, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.uri(True)})
    return render_to_response('knowledge_server/ks_explorer_form.html', context_instance=cont)

def datasets_of_type(request, ks_url, URIInstance, format):
    this_ks = KnowledgeServer.this_knowledge_server()
    format = format.upper()
    ks_url = urllib.unquote(ks_url)
    URIInstance = urllib.unquote(URIInstance)
    # info on the remote ks{{  }}
    local_url = reverse('api_ks_info', args=("JSON",))
    response = urllib2.urlopen(ks_url + local_url)
    ks_info_json_stream = response.read()
    # parsing json
    ks_info_json = json.loads(ks_info_json_stream)
    organization = ks_info_json['content']['DataSet']['ActualInstance']['Organization']
    for ks in organization['knowledgeserver_set']:
        if ks['this_ks']:
            external_ks_json = ks
    external_ks = KnowledgeServer()
    external_ks.name = external_ks_json['name']
    external_ks.scheme = external_ks_json['scheme']
    external_ks.netloc = external_ks_json['netloc']
    external_ks.description = external_ks_json['description']
    #info on the DataSetStructure
    response = urllib2.urlopen(URIInstance + "/json")
    es_info_json_stream = response.read()
    # parsing json
    es_info_json = json.loads(es_info_json_stream)
    
    
    if format == 'XML':
        local_url = reverse('api_datasets', args=(urllib.quote(URIInstance),format))
    if format == 'JSON' or format == 'BROWSE':
        local_url = reverse ('api_datasets', args=(urllib.quote(URIInstance).replace("/","%252F"),'JSON'))
    response = urllib2.urlopen(ks_url + local_url)
    entities = response.read()
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
            if ei.has_key('first_version'):
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
                actual_instance_class = ei['ActualInstance'].keys()[0]
                entity['actual_instance_name'] = ei['ActualInstance'][actual_instance_class]['name']
            else: #is a view
                entity['actual_instance_name'] = ei['description']
            entity['encodedURIInstance'] = urllib.urlencode({'':ei['URIInstance']})[1:]
            entity['URIInstance'] = urllib.quote(ei['URIInstance']).replace("/","%252F")
            subscribed_URIInstance = ei['first_version']['URIInstance'] if ei.has_key('first_version') else ei['URIInstance']
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
        Dataset_URIInstance = urllib.unquote(Dataset_URIInstance)
        dataset = DataSet.objects.get(URIInstance = Dataset_URIInstance)
        dataset.set_released()
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, Dataset_URIInstance + " successfully released.").json()}, content_type="application/json")
    except Exception as ex:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, ex.message).json()}, content_type="application/json")
        
def this_ks_subscribes_to(request, URIInstance):
    '''
    This ks is subscribing to a data set in another ks
    First I store the subscription locally
    Then I invoke remotely api_subscribe
    If it works I commit locally
    '''
    URIInstance = str(urllib.unquote(URIInstance).replace("%2F","/"))
    other_ks_uri = URIInstance[:str.find(URIInstance, '/', str.find(URIInstance, '/', str.find(URIInstance, '/')+1)+1)]
    # TODO: make the above a method of a helper class to find the URL of the KS from a URIInstance

    local_url = reverse('api_ks_info', args=("XML",))
    response = urllib2.urlopen(other_ks_uri + local_url)
    ks_info_xml_stream = response.read()
    # import_dataset creates the entity instance and the actual instance
    ei = DataSet()
    local_ei = ei.import_dataset(ks_info_xml_stream)
    # I have imported a KnowledgeServer with this_ks = True; must set it to False (see this_knowledge_server())
    external_org = local_ei.root
    for ks in external_org.knowledgeserver_set.all():
        ks.this_ks = False
        ks.save()
    # Now I can materialize it; I can use set released as I have certainly retrieved a released DataSet
    local_ei.set_released()
    
    try:
        with transaction.atomic():
            encoded_URIInstance = urllib.urlencode({'':URIInstance})[1:]
            # invoke remote API to subscribe
            this_ks = KnowledgeServer.this_knowledge_server()
            url_to_invoke = urllib.urlencode({'':this_ks.uri() + reverse('api_notify')})[1:]
            local_url = reverse('api_subscribe', args=(encoded_URIInstance,url_to_invoke,))
            response = urllib2.urlopen(other_ks_uri + local_url)
            response_text = response.read()
            ar = ApiResponse()
            ar.parse(response_text)
            if ar.status == ApiResponse.success:
                # save locally
                sto = SubscriptionToOther()
                sto.URI = URIInstance
                sto.first_version_URIInstance = ar.content # it contains the URIInstance of the first version
                sto.save()
                return render(request, 'knowledge_server/export.json', {'json': response_text}, content_type="application/json")
            else:
                return render(request, 'knowledge_server/export.json', {'json': response_text}, content_type="application/json")
    except Exception as ex:
        return HttpResponse(ex.message)
    
def api_subscribe(request, URIInstance, remote_url):
    '''
        #35 
        parameters:
        URIInstance is the one to which I want to subscribe
        remote_url the URL this KS has to invoke to notify
    '''
    # check the client KS has already subscribed
    URIInstance = urllib.unquote(URIInstance)
    remote_url = urllib.unquote(remote_url)
    ei = DataSet.objects.get(URIInstance=URIInstance)
    first_version_URIInstance = ei.first_version.URIInstance
    existing_subscriptions = SubscriptionToThis.objects.filter(first_version_URIInstance=first_version_URIInstance, remote_url=remote_url)
    if len(existing_subscriptions) > 0:
        return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.failure, "Already subscribed").json()}, content_type="application/json")
    stt = SubscriptionToThis()
    stt.first_version_URIInstance=first_version_URIInstance
    stt.remote_url=remote_url
    stt.save()
    return render(request, 'knowledge_server/export.json', {'json': ApiResponse(ApiResponse.success, "Subscribed sucessfully", first_version_URIInstance).json()}, content_type="application/json")
    
def api_unsubscribe(request, URIInstance, remote_URL):
    '''
        #123
        parameters:
        URIInstance is the one to which I want to subscribe
        remote_url the URL this KS has to invoke to notify
    '''
    
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
        from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure, StructureNode
        from licenses.models import License
        with transaction.atomic():
            test_license_org = Organization();test_license_org.name = "A test Organization hosting license information";test_license_org.website = 'http://license_org.example.com';test_license_org.description = "This is just a test Organization.";
            test_license_org.save(using='default')
            id_on_default_db = test_license_org.id
            test_license_org.id = None
            test_license_org.save(using='materialized')
            m_test_license_org = test_license_org
            test_license_org = Organization.objects.get(pk=id_on_default_db)
            
            root_ks = KnowledgeServer.this_knowledge_server('default')
            root_ks.this_ks = False
            root_ks.save()
            root_ks = KnowledgeServer.this_knowledge_server()
            root_ks.this_ks = False
            root_ks.save()
            
            m_test_license_org_ks = KnowledgeServer(name="A test Open Knowledge Server using some data from opendefinition.org.", scheme="http", netloc="licenses.thekoa.org", description="Please not that this site not affiliated with opendefinition.org. It is just a test some opendefinition.org data.", organization=test_license_org, this_ks=True, html_home="licenses html_home", html_disclaimer="This web site is solely for test purposes; information provided is taken from sources that make it available with opendefinition.org conformant licenses. If you think that part of this information should not be provided here or that any information is somehow misleading please contact us.")
            m_test_license_org_ks.save(using='materialized')
            test_license_org_ks = m_test_license_org_ks
            test_license_org_ks.id = None
            test_license_org_ks.URIInstance = ""
            test_license_org_ks.save(using='default')
            
            # m_test_license_org and test_license_org have the wrong URIInstance because they where created before their Knowledge Server
            # I fix this:
            m_test_license_org.URIInstance = ""
            m_test_license_org.save()
            test_license_org.URIInstance = ""
            test_license_org.save()
            
            
            this_ks = KnowledgeServer.this_knowledge_server('default')
            seLicense = ModelMetadata.objects.using('default').get(name="License")
            
            en1 = StructureNode();en1.model_metadata = seLicense;en1.save(using='default')
            esLicense = DataSetStructure();esLicense.multiple_releases = True;esLicense.is_shallow = True;
            esLicense.root_node = en1;esLicense.name = "License";esLicense.description = "License information";esLicense.namespace = "license";
            esLicense.save(using='default')
            m_es = DataSetStructure.objects.using('materialized').get(name=DataSetStructure.dataset_structure_DSN)
            es = DataSetStructure.objects.using('default').get(URIInstance=m_es.URIInstance)
            ei = DataSet(description='-License- data set structure', owner_knowledge_server=this_ks, dataset_structure=es, 
                         root=esLicense, version_major=0, version_minor=1, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
            
            seLicense.dataset_structure = esLicense; seLicense.save(using='default')
            
            # DataSetStructure di tipo view per la lista di licenze;  
            en1 = StructureNode();en1.model_metadata = seLicense;en1.save(using='default')
            esLicenseList = DataSetStructure();esLicenseList.is_a_view = True;
            esLicenseList.root_node = en1;esLicenseList.name = "List of licenses";esLicenseList.description = "List of all released licenses";esLicenseList.namespace = "license";
            esLicenseList.save(using='default')
            # DataSet of the above DataSetStructure
            ei = DataSet(description='-List of licenses- data set structure', owner_knowledge_server=this_ks, dataset_structure=es, 
                         root=esLicenseList, version_major=0, version_minor=1, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
            
            
            
            m_es = DataSetStructure.objects.using('materialized').get(name=DataSetStructure.organization_DSN)
            es = DataSetStructure.objects.get(URIInstance=m_es.URIInstance)
            ei = DataSet(owner_knowledge_server=test_license_org_ks, root=test_license_org, dataset_structure=es, description="A test Organization and their KSs", version_major=0, version_minor=1, version_patch=0)
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            # let's materialize the ei; I cannot release it as I saved manually the ks in materialized (I cannot do otherwise as it 
            # is needed to generateURIInstance every time something is saved)
            ei.materialize(ei.shallow_structure().root_node, processed_instances=[])
            
            esLicense = DataSetStructure.objects.get(name="License") 
            
            ######## BEGIN LICENSES DATA
            
            # Against DRM 
            adrm = License()
            adrm.name = "Against DRM"
            adrm.short_name = ""
            adrm.attribution = True
            adrm.share_alike = True
            adrm.url_info = "http://opendefinition.org/licenses/against-drm"
            adrm.reccomended_by_opendefinition = False
            adrm.conformant_for_opendefinition = True
            adrm.legalcode = ''
            adrm.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=adrm, version_major=2, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            # Creative Commons Attribution 1.0
            ccby10 = License()
            ccby10.name = "Creative Commons Attribution 1.0"
            ccby10.short_name = "CC-BY-1.0"
            ccby10.attribution = True
            ccby10.share_alike = False
            ccby10.url_info = "http://creativecommons.org/licenses/by/1.0"
            ccby10.reccomended_by_opendefinition = False
            ccby10.conformant_for_opendefinition = True
            ccby10.legalcode = ''
            ccby10.save(using='default')
            ei_ccby10 = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                                root=ccby10, version_major=1, version_minor=0, version_patch=0, version_description="")
            ei_ccby10.save(using='default');ei_ccby10.first_version_id = ei_ccby10.id;ei_ccby10.save(using='default')
            ei_ccby10.set_released()  # here materialization happens
        
            # above reccomended; below other conformant
            
            # Creative Commons CCZero
            cczero = License()
            cczero.name = "Creative Commons CCZero"
            cczero.short_name = "CC0"
            cczero.attribution = False
            cczero.share_alike = False
            cczero.url_info = "http://opendefinition.org/licenses/cc-zero"
            cczero.reccomended_by_opendefinition = True
            cczero.conformant_for_opendefinition = True
            cczero.legalcode = ''
            cczero.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=cczero, version_major=1, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            # Open Data Commons Public Domain Dedication and Licence
            pddl = License()
            pddl.name = "Open Data Commons Public Domain Dedication and Licence"
            pddl.short_name = "PDDL"
            pddl.attribution = False
            pddl.share_alike = False
            pddl.url_info = "http://opendefinition.org/licenses/odc-pddl"
            pddl.reccomended_by_opendefinition = True
            pddl.conformant_for_opendefinition = True
            pddl.legalcode = ''
            pddl.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=pddl, version_major=1, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            # Creative Commons Attribution 4.0
            ccby40 = License()
            ccby40.name = "Creative Commons Attribution 4.0"
            ccby40.short_name = "CC-BY-4.0"
            ccby40.attribution = True
            ccby40.share_alike = False
            ccby40.url_info = "http://creativecommons.org/licenses/by/4.0"
            ccby40.reccomended_by_opendefinition = True
            ccby40.conformant_for_opendefinition = True
            ccby40.legalcode = ''
            ccby40.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, first_version_id=ei_ccby10.id, dataset_structure=esLicense, 
                         root=ccby40, version_major=4, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default')
            # I do not set it as released; it will be done to demonstrate the notification and update process
        #     ei.set_released() #here materialization happens
        
            # Open Data Commons Attribution License 
            odcby = License()
            odcby.name = "Open Data Commons Attribution License"
            odcby.short_name = "ODC-BY"
            odcby.attribution = True
            odcby.share_alike = False
            odcby.url_info = "http://opendefinition.org/licenses/odc-by"
            odcby.reccomended_by_opendefinition = True
            odcby.conformant_for_opendefinition = True
            odcby.legalcode = ''
            odcby.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=odcby, version_major=1, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            # Creative Commons Attribution Share-Alike 4.0  
            ccbysa40 = License()
            ccbysa40.name = "Creative Commons Attribution Share-Alike 4.0"
            ccbysa40.short_name = "CC-BY-SA-4.0"
            ccbysa40.attribution = True
            ccbysa40.share_alike = True
            ccbysa40.url_info = "http://opendefinition.org/licenses/cc-by-sa"
            ccbysa40.reccomended_by_opendefinition = True
            ccbysa40.conformant_for_opendefinition = True
            ccbysa40.legalcode = ''
            ccbysa40.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=ccbysa40, version_major=4, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            # Open Data Commons Open Database License 
            odbl = License()
            odbl.name = "Open Data Commons Open Database License"
            odbl.short_name = "ODbL"
            odbl.attribution = True
            odbl.share_alike = False
            odbl.url_info = "http://opendefinition.org/licenses/odc-odbl"
            odbl.reccomended_by_opendefinition = True
            odbl.conformant_for_opendefinition = True
            odbl.legalcode = ''
            odbl.save(using='default')
            ei = DataSet(owner_knowledge_server=test_license_org_ks, dataset_structure=esLicense, 
                         root=odbl, version_major=1, version_minor=0, version_patch=0, version_description="")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            ei.set_released()  # here materialization happens
        
            ######## END LICENSES DATA
        
            esLicenseList = DataSetStructure.objects.get(name="List of licenses")
            
            # 2 DataSet with the above DataSetStructure
            # opendefinition.org conformant
            ei = DataSet(owner_knowledge_server=test_license_org_ks, filter_text="conformant_for_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant licenses.")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            # let's materialize the ei that is a view so it doesn't need to be set to released
            ei.materialize(ei.shallow_structure().root_node, processed_instances=[])
            # opendefinition.org conformant and reccomended
            ei = DataSet(owner_knowledge_server=test_license_org_ks, filter_text="reccomended_by_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant and reccomended licenses.")
            ei.save(using='default');ei.first_version_id = ei.id;ei.save(using='default')
            # let's materialize the ei that is a view so it doesn't need to be set to released
            ei.materialize(ei.shallow_structure().root_node, processed_instances=[])

        return HttpResponse("OK ")
    except Exception as ex:
        return HttpResponse(ex.message)

