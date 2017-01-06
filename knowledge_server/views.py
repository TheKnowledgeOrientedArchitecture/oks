# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from json import loads as json_loads 
from lxml import etree
from xml.dom import minidom

import importlib
import logging
import urllib

from urllib.request import urlopen

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from knowledge_server.forms import ExploreOtherKSForm, UploadFileForm, ImportChoice, ImportChoiceNothingOnDB
from knowledge_server.models import ApiResponse, DataSet, Event, KnowledgeServer, Notification, DataSetStructure
from knowledge_server.models import NotificationReceived, SubscriptionToOther, SubscriptionToThis, UploadedFile
from knowledge_server.utils import KsUrl

logger = logging.getLogger(__name__)


def ks_explorer(request):
    try:
        ks_url = urllib.parse.parse_qs('url=' + request.GET['ks_complete_url'])['url'][0]
    except:
        ks_url = request.POST['ks_complete_url']
    try:
        # use the KsUrl class to clean it up
        ks_url = KsUrl(ks_url).url
        this_ks = KnowledgeServer.this_knowledge_server()
        # info on the remote ks
        ar_ks_info = ApiResponse()
        ar_ks_info.invoke_oks_api(ks_url, 'api_ks_info') + "?format=JSON"
        if ar_ks_info.status == ApiResponse.success:
            organization = ar_ks_info.content['DataSet']['ActualInstance']['Organization']
            for ks in organization['knowledgeserver_set']:
                if ks['this_ks']:
                    explored_ks = ks
                
            # info about structures on the remote ks
            ar_ds_types = ApiResponse()
            ar_ds_types.invoke_oks_api(ks_url, 'api_dataset_types') + "?format=JSON"
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


@login_required
def ks_explorer_form(request):
    form = ExploreOtherKSForm()
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
    tmp_ks_url = KsUrl(ks_url)
    
    q_UKCL = UKCL
    UKCL = urllib.parse.unquote(UKCL)
    if this_ks.scheme != tmp_ks_url.scheme or this_ks.netloc != tmp_ks_url.netloc:
        # info on the remote ks
        ar_ks_info = ApiResponse()
        ar_ks_info.invoke_oks_api(ks_url, 'api_ks_info') + "?format=JSON"
        organization = ar_ks_info.content['DataSet']['ActualInstance']['Organization']
        for ks in organization['knowledgeserver_set']:
            if ks['this_ks']:
                external_ks_json = ks
        external_ks = KnowledgeServer()
        external_ks.name = external_ks_json['name']
        external_ks.scheme = external_ks_json['scheme']
        external_ks.netloc = external_ks_json['netloc']
        external_ks.description = external_ks_json['description']
        browsing_this = False
    else:
        external_ks = this_ks
        organization = this_ks.organization
        browsing_this = True
    # info on the DataSetStructure
    # TODO: the following call relies on api_catch_all; use dataset_info instead
    response = urlopen(UKCL + "/json")
    es_info_json = json_loads(response.read().decode("utf-8"))
    
    if response_format == 'XML':
        local_url = reverse('api_datasets') + ("?UKCL=%s&format=%s" % (q_UKCL,response_format))
    if response_format == 'JSON' or response_format == 'BROWSE':
        local_url = reverse('api_datasets') + ("?UKCL=%s&format=JSON" % q_UKCL)
    response = urlopen(ks_url + local_url)
    datasets = response.read().decode("utf-8")
    if response_format == 'XML':
        return render(request, 'knowledge_server/export.xml', {'xml': datasets}, content_type="application/xhtml+xml")
    if response_format == 'JSON':
        return render(request, 'knowledge_server/export.json', {'json': datasets}, content_type="application/json")
    if response_format == 'BROWSE':
        # parse
        decoded = json_loads(datasets)
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
        datasets = []
        for ei in decoded['content']['DataSets']:
            dataset = {}
            if 'ActualInstance' in ei.keys():
                actual_instance_class = list(ei['ActualInstance'].keys())[0]
                dataset['actual_instance_name'] = ei['ActualInstance'][actual_instance_class]['name']
            else: #is a view
                dataset['actual_instance_name'] = ei['description']
            dataset['encodedUKCL'] = urllib.parse.urlencode({'':ei['UKCL']})[1:]
            dataset['UKCL'] = urllib.parse.quote(ei['UKCL']).replace("/","%2F")
            subscribed_UKCL = ei['first_version']['UKCL'] if 'first_version' in ei else ei['UKCL']
            dataset['subscribed'] = subscribed_UKCL in subscribed_first_version_UKCLs
            datasets.append(dataset)
        cont = RequestContext(request, {'browsing_this':browsing_this, 'datasets':datasets, 'organization': organization, 'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True), 'external_ks': external_ks, 'es_info_json': es_info_json})
        return render_to_response('knowledge_server/datasets_of_type.html', context_instance=cont)
    

def home(request):
    this_ks = KnowledgeServer.this_knowledge_server()
    cont = RequestContext(request, {'this_ks':this_ks, 'this_ks_encoded_url':this_ks.url(True)})
    return render(request, 'knowledge_server/home.html', context_instance=cont)


@login_required
def this_ks_unsubscribes_to(request, UKCL):
    '''
    '''
    pass


@login_required
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
        
        
@login_required
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
            ar.invoke_oks_api(other_ks_uri, 'api_subscribe') + ("?UKCL=%s&remote_url=%s" % ((encoded_UKCL,url_to_invoke)))
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

    
@login_required
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


@login_required
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


@login_required
def upload_page(request):
    message = ''
    if request.method == 'POST':
        form = UploadFileForm( request.POST, request.FILES )
        if form.is_valid( ):
            xml_uploaded = request.FILES[ 'file' ].read( )
            # http://stackoverflow.com/questions/3310614/remove-whitespaces-in-xml-string
            p = etree.XMLParser( remove_blank_text=True )
            elem = etree.XML( xml_uploaded, parser=p )
            xml_uploaded = etree.tostring( elem )

            new_uploaded_file = UploadedFile( docfile=request.FILES[ 'file' ] )
            # we save it on disk so that we can process it after the user has told us which part to import and how to import it
            new_uploaded_file.save( )
            # we parse it so that we check what is on the file against what is on the database and we show this info to the user
            try:
                # I extract the information I want to show to the user before I actually perform the import
                # The info allows the user to compare what is in the file and what is in the database
                # so that they can decide whether to update or insert
                initial_data = {}
                initial_data[ 'uploaded_file_id' ] = new_uploaded_file.id
                initial_data[ 'new_uploaded_file_relpath' ] = new_uploaded_file.docfile.url
                xmldoc = minidom.parseString( xml_uploaded )
                URI = xmldoc.childNodes[ 0 ].attributes[ "DataSetStructureURI" ].firstChild.data
                e = DataSetStructure.objects.get( URIInstance=URI )
                # I check that the first SimpleEntity is the same simple_entity of the DataSetStructure's entry_point
                if e.entry_point.simple_entity.name != xmldoc.childNodes[ 0 ].childNodes[ 0 ].tagName:
                    message = "The DataSetStructure structure tells that the first SimpleEntity should be " + e.entry_point.simple_entity.name + " but the first TAG in the file is " + \
                              xmldoc.childNodes[ 0 ].childNodes[ 0 ].tagName
                    raise Exception( message )
                else:
                    # Is there a URIInstance of the first SimpleEntity;
                    try:
                        simple_entity_uri_instance = xmldoc.childNodes[ 0 ].childNodes[ 0 ].attributes[
                            "URIInstance" ].firstChild.data
                    except Exception as ex:
                        # if it's not in the file it means that the data in the file does not come from a KS
                        simple_entity_uri_instance = None
                    initial_data[ 'simple_entity_uri_instance' ] = simple_entity_uri_instance
                    try:
                        initial_data[ 'simple_entity_name' ] = xmldoc.childNodes[ 0 ].childNodes[ 0 ].attributes[
                            e.entry_point.simple_entity.name_field ].firstChild.data
                    except:
                        initial_data[ 'simple_entity_name' ] = None
                    try:
                        initial_data[ 'simple_entity_description' ] = xmldoc.childNodes[ 0 ].childNodes[ 0 ].attributes[
                            e.entry_point.simple_entity.description_field ].firstChild.data
                    except:
                        initial_data[ 'simple_entity_description' ] = None
                    module_name = e.entry_point.simple_entity.module
                    child_node = xmldoc.childNodes[ 0 ].childNodes[ 0 ]
                    actual_class_name = module_name + ".models " + child_node.tagName
                    initial_data[ 'actual_class_name' ] = actual_class_name
                    module = importlib.import_module( module_name + ".models" )
                    actual_class = getattr( module, child_node.tagName )
#                    actual_class = utils.load_class( module_name + ".models", child_node.tagName )
                    try:
                        '''
                        ?How does the import work wrt URIInstance? A SerializableSimpleEntity has
                            URIInstance
                            URI_imported_instance
                        attributes; the second comes from the imported record (if any); the first is generated
                        upon record creation; so the first always refer to local KS; the second, if present,
                        will tell you where the record comes from via import or fetch (fetch not implemented yet)
                        '''
                        if not simple_entity_uri_instance is None:
                            simple_entity_on_db = actual_class.retrieve( simple_entity_uri_instance )
                            initial_data[ 'simple_entity_on_db' ] = simple_entity_on_db
                            initial_data[ 'simple_entity_on_db_name' ] = getattr( simple_entity_on_db,
                                                                                  e.entry_point.simple_entity.name_field ) if e.entry_point.simple_entity.name_field else ""
                            initial_data[ 'simple_entity_on_db_description' ] = getattr( simple_entity_on_db,
                                                                                         e.entry_point.simple_entity.description_field ) if e.entry_point.simple_entity.description_field else ""
                            initial_data[ 'simple_entity_on_db_URIInstance' ] = getattr( simple_entity_on_db,
                                                                                         "URIInstance" )
                        else:
                            initial_data[ 'simple_entity_on_db' ] = None
                    except:
                        # .get returning more than one record would be a logical error (CHECK: ?and should be raised here?)
                        # it could actually happen if I use an export from this ks to import again into new records
                        # then I modify the file and import again; instead of modifying the file the preferred behavior
                        # should be to export, modify the newly exported file and import again; this last method would work
                        # the first wouldn't yield initial_data['simple_entity_on_db'] = None
                        initial_data[ 'simple_entity_on_db' ] = None
                    initial_data[ 'prettyxml' ] = xmldoc.toprettyxml( indent="    " )
                    initial_data[ 'file' ] = request.FILES[ 'file' ]
                    initial_data[ 'new_uploaded_file' ] = new_uploaded_file
                    if initial_data[ 'simple_entity_on_db' ] is None:
                        import_choice_form = ImportChoiceNothingOnDB( initial={'uploaded_file_id': new_uploaded_file.id,
                                                                               'new_uploaded_file_relpath': new_uploaded_file.docfile.url,
                                                                               'how_to_import': 1} )
                    else:
                        import_choice_form = ImportChoice( initial={'uploaded_file_id': new_uploaded_file.id,
                                                                    'new_uploaded_file_relpath': new_uploaded_file.docfile.url,
                                                                    'how_to_import': 0} )
                    initial_data[ 'import_choice_form' ] = import_choice_form
                    return render( request, 'entity/import_file.html', initial_data )
            except Exception as ex:
                message = 'Error parsing uploaded file: ' + str( ex )
    else:
        form = UploadFileForm( )
    return render_to_response( 'entity/upload_page.html', {'form': form, 'message': message},
                               context_instance=RequestContext( request ) )


@login_required
def perform_import(request):
    '''
    Import is performed according to an DataSetStructure a structure of instances of ShareableModel
    The structure allows to have external references to a instances; use an external reference
    when you need to relate to that instance but do not want to import/export it.
    When an instance is an external reference its ID does not matter; its UKCL is
    relevant. The import behavior for external reference is:
    it looks for an instance with the same UKCL, if it does exist it takes it's ID and
    uses it for the relationships; otherwise it creates it (which of course happens only once)
    The import behavior when not reference is .................................
    '''
    new_uploaded_file_relpath = request.POST[ "new_uploaded_file_relpath" ]
    #     request.POST['how_to_import']
    #     0   Update if ID exists, create if ID is empty or non existent
    #     1   Always create new records

    # how_to_import = true  ==> always_insert = always create
    # how_to_import = false ==> Update if ID exists, create if ID is empty or non existent
    always_insert = (int( request.POST.get( "how_to_import", "" ) ) == 1)
    with open( settings.BASE_DIR + "/" + new_uploaded_file_relpath, 'r' ) as content_file:
        xml_uploaded = content_file.read( )
    # http://stackoverflow.com/questions/3310614/remove-whitespaces-in-xml-string
    p = etree.XMLParser( remove_blank_text=True )
    elem = etree.XML( xml_uploaded, parser=p )
    xml_uploaded = etree.tostring( elem )
    xmldoc = minidom.parseString( xml_uploaded )
    try:
        URIInstance = xmldoc.childNodes[ 0 ].attributes[ "DataSetStructureURI" ].firstChild.data
        et = DataSetStructure.objects.get( URIInstance=URIInstance )
    except Exception as ex:
        raise Exception(
            "I cannot find the DataSetStructure in my database or it's DataSetStructureURI in the file you submitted: " + str(
                ex ) )
    child_node = xmldoc.childNodes[ 0 ].childNodes[ 0 ]

    try:
        se = SimpleEntity.objects.get( URIInstance=child_node.attributes[ "URISimpleEntity" ].firstChild.data )
    except Exception as ex:
        raise Exception( "I cannot find the SimpleEntity " + child_node.attributes[
            "URISimpleEntity" ].firstChild.data + " Error: " + str( ex ) )
    assert (
    et.entry_point.simple_entity.name == child_node.tagName == se.name), "child_node.simple_entity.name - child_node.tagName - se.name: " + child_node.simple_entity.name + ' - ' + child_node.tagName + ' - ' + se.name

    module_name = et.entry_point.simple_entity.module
#    actual_class = utils.load_class( module_name + ".models", child_node.tagName )
    module = importlib.import_module( module_name + ".models" )
    actual_class = getattr( module, child_node.tagName )

    try:
        simple_entity_uri_instance = xmldoc.childNodes[ 0 ].childNodes[ 0 ].attributes[ "URIInstance" ].firstChild.data
    except Exception as ex:
        # if it's not in the file it means that the data in the file does not come from a KS
        simple_entity_uri_instance = None
    if always_insert or (simple_entity_uri_instance is None):
        instance = actual_class( )
    else:
        instance = actual_class.retrieve( simple_entity_uri_instance )
    # At least the first node has full export = True otherwise I would not import anything but just load something from the db
    instance.from_xml( child_node, et.entry_point, always_insert )
    return HttpResponse( "OK" )


def json(request):
    '''
    micro test for json
    '''
    try:
        ar = ApiResponse()
        ar.content = { "DataSet": "Versions"}
        ar.status = ApiResponse.success
        return HttpResponse(ar.json(), content_type = "application/json") 
    except Exception as ex:
        logger.error("views.debug: " + str(ex))
        return HttpResponse(str(ex))


def debug(request):
    '''
    created to debug code

    Args:
        request: 
    '''
    UKCL = request.GET["UKCL"]
    return HttpResponse( "OK: " + UKCL )
    try:
        from django.core import management
#         management.call_command('migrate', "--database=materialized", interactive=False)
#         management.call_command('migrate', 'ap', interactive=False)
#         management.call_command('migrate', interactive=False)
        management.call_command('migrate', 'ap', interactive=False)
# funziona?        management.call_command('migrate', "knowledge_server 0003_initial_data --database=materialized", interactive=False)
        return HttpResponse("OK")

        import scrapy

        class DmozItem(scrapy.Item):
            title = scrapy.Field()
            link = scrapy.Field()
            desc = scrapy.Field()
        
        class DmozSpider(scrapy.Spider):
            name = "dmoz"
            allowed_domains = ["dmoz.org"]
            start_urls = [
                "http://www.dmoz.org/Computers/Programming/Languages/Python/",
            ]
        
            def parse(self, response):
                for href in response.css("ul.directory.dir-col > li > a::attr('href')"):
                    url = response.urljoin(href.extract())
                    yield scrapy.Request(url, callback=self.parse_dir_contents)
        
            def parse_dir_contents(self, response):
                for sel in response.xpath('//ul/li'):
                    item = DmozItem()
                    item['title'] = sel.xpath('a/text()').extract()
                    item['link'] = sel.xpath('a/@href').extract()
                    item['desc'] = sel.xpath('text()').extract()
                    yield item

        return HttpResponse('OK')

    
        ar = ApiResponse()
        ar.content = { "DataSet": "Versions"}
        ar.status = ApiResponse.success
        return HttpResponse(ar.json(), content_type = "application/json")
     
        # TODO: AGGIORNARE SU STACKOVERFLOW: http://stackoverflow.com/questions/8784400/clearing-specific-cache-in-django
        
        from licenses.models import License
        db_alias = 'default'
        ccbysa40 = License.objects.using(db_alias).get(short_name = "CC-BY-SA-4.0")
        dssModelMetadataFields = DataSetStructure.get_from_name(DataSetStructure.model_metadata_DSN, db_alias)
        dssDataSetStructureStructureNode = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN, db_alias)
        dssOrganizationKS = DataSetStructure.get_from_name(DataSetStructure.organization_DSN, db_alias)
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssModelMetadataFields):
            ds.licenses.add(ccbysa40)
            ds.save()
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssDataSetStructureStructureNode):
            ds.licenses.add(ccbysa40)
            ds.save()
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssOrganizationKS):
            ds.licenses.add(ccbysa40)
            ds.save()
        db_alias = 'materialized'
        ccbysa40 = License.objects.using(db_alias).get(short_name = "CC-BY-SA-4.0")
        dssModelMetadataFields = DataSetStructure.get_from_name(DataSetStructure.model_metadata_DSN, db_alias)
        dssDataSetStructureStructureNode = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN, db_alias)
        dssOrganizationKS = DataSetStructure.get_from_name(DataSetStructure.organization_DSN, db_alias)
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssModelMetadataFields):
            ds.licenses.add(ccbysa40)
            ds.save()
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssDataSetStructureStructureNode):
            ds.licenses.add(ccbysa40)
            ds.save()
        for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssOrganizationKS):
            ds.licenses.add(ccbysa40)
            ds.save()
        return HttpResponse("OK ")

        from django.core.cache import cache
        from django.utils.cache import get_cache_key, _generate_cache_header_key
        from django.utils.encoding import escape_uri_path
        from django.http import HttpRequest
        
        new_request = HttpRequest()
        new_request.path = 'root.beta.thekoa.org/oks/api/ks_info/JSON/' ##this path works
        new_request.META['SERVER_PORT'] = request.META['SERVER_PORT']
        new_request.META['SERVER_NAME'] = request.META['SERVER_NAME']

        key = _generate_cache_header_key("", new_request)
        if cache.has_key(key):   
            cache.delete(key)
        
        full_path = 'http://root.beta.thekoa.org/oks/api/datasets/http%253A%252F%252Froot.beta.thekoa.org%252Fknowledge_server%252FDataSetStructure%252F4/JSON/'
        import hashlib
        from django.utils.encoding import force_bytes, iri_to_uri
        from django.utils.cache import _i18n_cache_key_suffix
        # code from _generate_cache_header_key
        url = hashlib.md5(force_bytes(iri_to_uri(full_path)))
        cache_key = 'views.decorators.cache.cache_header.%s.%s' % ("", url.hexdigest())
        key = _i18n_cache_key_suffix(request, cache_key)
        if cache.has_key(key):   
            cache.delete(key)
        
        return HttpResponse("OK ")
#         d = DataSet.objects.get(pk=1)
#         s = d.shallow_structure()
#         rct = d.root_content_type
# 
#         
#         for structure_child_node in s.root_node.child_nodes.all():
#             mm = structure_child_node.sn_model_metadata(d)
#             print(mm.name)
        
        dssContinentState=DataSetStructure()
        dssContinentState.name="Test Continent-SubContinent-State";
        dssContinentState.SetNotNullFields()
        dssContinentState.save()

        return HttpResponse("OK ")
    except Exception as ex:
        logger.error("views.debug: " + str(ex))
        return HttpResponse(str(ex))

