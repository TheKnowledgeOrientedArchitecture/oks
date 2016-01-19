# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import json
from urlparse import urlparse
import urllib
import urllib2

from django.db import models, transaction
from django.core.urlresolvers import reverse
from shareable.models import ShareableModel, DataSet, DataSetStructure
import utils

class Organization(ShareableModel):
    name = models.CharField(max_length=500L, blank=True)
    description = models.CharField(max_length=2000L, blank=True)
    website = models.CharField(max_length=500L, blank=True)

class KnowledgeServer(ShareableModel):
    name = models.CharField(max_length=500L, blank=True)
    description = models.CharField(max_length=2000L, blank=True)
    # ASSERT: only one KnowledgeServer in each KS has this_ks = True (in materialized db); I use it to know in which KS I am
    # this is handled when importing data about an external KS
    this_ks = models.BooleanField(default=False)
    # urlparse terminology https://docs.python.org/2/library/urlparse.html
#     scheme e.g. { "http" | "https" }
    scheme = models.CharField(max_length=50L)
#     netloc e.g. "ks.thekoa.org"
    netloc = models.CharField(max_length=200L)
#     html_home text that gets displayed at the home page
    html_home = models.CharField(max_length=4000L, default="")
#     html_disclaimer text that gets displayed at the disclaimer page
    html_disclaimer = models.CharField(max_length=4000L, default="")
    
    organization = models.ForeignKey(Organization)

    def uri(self, encode_base64=False):
        # "http://rootks.thekoa.org/"
        uri = self.scheme + "://" + self.netloc
        if encode_base64:
            uri = urllib.urlencode({'':uri})[1:]
        return uri
    
    def run_cron(self):
        '''
        This method processes notifications received, generate notifications to be sent
        if events have occurred, ...
        '''
        response = self.process_events()
        response += self.send_notifications()
        response += self.process_received_notifications()
        return response
        
    def process_events(self):
        '''
        Events are transformed in notifications to be sent
        "New version" is the only event so far
        
        Subscriptions to a released dataset generates a notification too, only once though
        '''
        message = "Processing events that could generate notifications<br>"
        # subscriptions
        subs_first_time = SubscriptionToThis.objects.filter(first_notification_prepared=False)
        message += "Found " + str(len(subs_first_time)) + " subscriptions to data in this OKS<br>"
        for sub in subs_first_time:
            try:
                with transaction.atomic():
                    # I get the DataSet from the subscription (it is the root)
                    root_ei = DataSet.objects.get(URIInstance=sub.first_version_URIInstance)
                    event = Event()
                    event.dataset = root_ei.get_latest(True)
                    event.type = "First notification"
                    event.processed = True
                    event.save()
                    n = Notification()
                    n.event = event
                    n.remote_url = sub.remote_url
                    n.save()
                    sub.first_notification_prepared = True
                    sub.save()
            except Exception as e:
                message += "process_events, subscriptions error: " + e.message
                print (str(e))
            
        # events
        events = Event.objects.filter(processed=False, type="New version")
        message += "Found " + str(len(events)) + " events<br>"
        for event in events:
            subs = SubscriptionToThis.objects.filter(first_version_URIInstance=event.dataset.root.URIInstance)
            try:
                with transaction.atomic():
                    for sub in subs:
                        # I do not want to send two notifications if "First notification" and "New version" happen at the same time
                        if not sub in subs_first_time:
                            n = Notification()
                            n.event = event
                            n.remote_url = sub.remote_url
                            n.save()
                    event.processed = True
                    event.save()
            except Exception as e:
                message += "process_events, events error: " + e.message
                print (str(e))
        return message + "<br>"
    
    def send_notifications(self):
        '''
        '''
        message = "Sending notifications<br>"
        try:
            this_ks = KnowledgeServer.this_knowledge_server()
            notifications = Notification.objects.filter(sent=False)
            message += "Found " + str(len(notifications)) + " notifications<br>"
            for notification in notifications:
                message += "send_notifications, found a notification for URIInstance " + notification.event.dataset.URIInstance + "<br>"
                message += "about to notify " + notification.remote_url + "<br>"
                m_es = DataSetStructure.objects.using('ksm').get(name=DataSetStructure.dataset_structure_name)
                es = DataSetStructure.objects.using('default').get(URIInstance=m_es.URIInstance)
                this_es = DataSetStructure.objects.get(URIInstance=notification.event.dataset.dataset_structure.URIInstance)
                ei_of_this_es = DataSet.objects.get(entry_point_instance_id=this_es.id, dataset_structure=es)
                values = { 'first_version_URIInstance' : notification.event.dataset.root.URIInstance,
                           'URL_dataset' : this_ks.uri() + reverse('api_dataset', args=(base64.encodestring(notification.event.dataset.URIInstance).replace('\n', ''), "XML",)),
                           'URL_structure' : this_ks.uri() + reverse('api_dataset', args=(base64.encodestring(ei_of_this_es.URIInstance).replace('\n', ''), "XML",)),
                           'type' : notification.event.type,
                           'timestamp' : notification.event.timestamp, }
                data = urllib.urlencode(values)
                req = urllib2.Request(notification.remote_url, data)
                response = urllib2.urlopen(req)
                ar = ApiReponse()
                ar.parse(response.read())
                if ar.status == "success":
                    notification.sent = True
                    notification.save()
                else:
                    message += "send_notifications " + notification.remote_url + " responded: " + ar.message + "<br>"
        except Exception as e:
            message += "send_notifications error: " + e.message
        return message + "<br>"
    
    def process_received_notifications(self):
        '''
        '''
        message = "Processing received notifications<br>"
        notifications = NotificationReceived.objects.filter(processed=False)
        message += "Found " + str(len(notifications)) + " notifications<br>"
        for notification in notifications:
            try:
                with transaction.atomic():
                    # We assume we have already all SimpleEntity
                    # Let's retrieve the structure
                    response = urllib2.urlopen(notification.URL_structure)
                    structure_xml_stream = response.read()
                    ei_structure = DataSet()
                    ei_structure = ei_structure.from_xml_with_actual_instance(structure_xml_stream)
                    ei_structure.dataset_structure = DataSetStructure.objects.get(name=DataSetStructure.dataset_structure_name)
                    ei_structure.materialize_dataset()
                    # the dataset is retrieved with api #36 api_dataset that serializes
                    # the DataSet and also the complete actual instance 
                    # from_xml_with_actual_instance will create the DataSet and the actual instance
                    response = urllib2.urlopen(notification.URL_dataset)
                    dataset_xml_stream = response.read()
                    ei = DataSet()
                    ei = ei.from_xml_with_actual_instance(dataset_xml_stream)
                    ei.dataset_structure = ei_structure.get_instance()
                    ei.materialize_dataset()
                    notification.processed = True
                    notification.save()
            except Exception as ex:
                message += "process_received_notifications error: " + ex.message
        return message + "<br>"
        
    @staticmethod
    def this_knowledge_server(db_alias='ksm'):
        '''
        *** method that works BY DEFAULT on the materialized database ***
        *** the reason being that only there "get(this_ks = True)" is ***
        *** guaranteed to return exactly one record                   ***
        when working on the default database we must first fetch it on the
        materialized; then, using the URIInstance we search it on the default
        because the URIInstance will be unique there
        '''
        materialized_ks = KnowledgeServer.objects.using('ksm').get(this_ks=True)
        if db_alias == 'default':
            return KnowledgeServer.objects.using('default').get(URIInstance=materialized_ks.URIInstance)
        else:
            return materialized_ks

class Event(ShareableModel):
    '''
    Something that has happened to a specific instance and you want to get notified about; 
    so you can subscribe to a type of event for a specific data set / DataSet
    '''
    # The DataSet
    dataset = models.ForeignKey(DataSet)
    # the event type
    type = models.CharField(max_length=50, default="New version")
    # when it was fired
    timestamp = models.DateTimeField(auto_now_add=True)
    # if all notifications have been prepared e.g. relevant Notification instances are saved
    processed = models.BooleanField(default=False)

class SubscriptionToThis(ShareableModel):
    '''
    The subscriptions other systems do to my data
    '''
    first_version_URIInstance = models.CharField(max_length=2000L)
    # where to send the notification; remote_url, in the case of a KS, will be something like http://rootks.thekoa.org/notify
    # the actual notification will have the URIInstance of the DataSet and the URIInstance of the EventType
    remote_url = models.CharField(max_length=200L)
    # I send a first notification that can be used to get the data the first time
    first_notification_prepared = models.BooleanField(default=False)

class Notification(ShareableModel):
    '''
    When an event happens for an instance, for each corresponding subscription
    I create a  Notification; cron will send it and change its status to sent
    '''
    event = models.ForeignKey(Event)
    sent = models.BooleanField(default=False)
    remote_url = models.CharField(max_length=200L)

class SubscriptionToOther(ShareableModel):
    '''
    The subscriptions I make to other systems' data
    '''
    # The URIInstance I am subscribing to 
    URI = models.CharField(max_length=200L)
    first_version_URIInstance = models.CharField(max_length=200L)

class NotificationReceived(ShareableModel):
    '''
    When I receive a notification it is stored here and processed asynchronously in cron 
    '''
    # URI to fetch the new data
    URL_dataset = models.CharField(max_length=200L)
    URL_structure = models.CharField(max_length=200L)
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
class ApiReponse():
    '''
    
    '''
    def __init__(self, status="", message=""):
        self.status = status
        self.message = message
        
    def json(self):
        ret_str = '{ "status" : "' + self.status + '", "message" : "' + self.message + '"}'
        return ret_str
    
    def parse(self, json_response):
        decoded = json.loads(json_response)
        self.status = decoded['status']
        self.message = decoded['message']
        
class KsUri(object):
    '''
    This class is responsible for the good quality of all URIs generated by a KS
    in terms of syntax and for their coherent use throughout the whole application
    '''

    def __init__(self, uri):
        '''
        only syntactic check
        uu= urlunparse([o.scheme, o.netloc, o.path, o.params, o.query, o.fragment])
        uu= urlunparse([o.scheme, o.netloc, o.path, o.params, o.query, ''])
        così possiamo rimuovere il fragment e params query in modo da ripulire l'url ed essere più forgiving sulle api; da valutare
        '''
        self.uri = uri
        self.parsed = urlparse(self.uri)
        # I remove format options if any, e.g.
        # http://rootks.thekoa.org/entity/SimpleEntity/1/json/  --> http://rootks.thekoa.org/entity/SimpleEntity/1/json/
        self.clean_uri = uri
        # remove the trailing slash
        if self.clean_uri[-1:] == "/":
            self.clean_uri = self.clean_uri[:-1]
        # remove the format the slash before it and set self.format
        self.format = ""
        for format in utils.Choices.FORMAT:
            if self.clean_uri[-(len(format) + 1):].lower() == "/" + format:
                self.clean_uri = self.clean_uri[:-(len(format) + 1)]
                self.format = format

        # I check whether it's structure i well formed according to the GenerateURIInstance method
        self.is_sintactically_correct = False
        # not it looks something like: http://rootks.thekoa.org/entity/SimpleEntity/1
        self.clean_parsed = urlparse(self.clean_uri)
        self.scheme = ""
        for scheme in utils.Choices.SCHEME:
            if self.clean_parsed.scheme.lower() == scheme:
                self.scheme = self.clean_parsed.scheme.lower()
        self.netloc = self.clean_parsed.netloc.lower()
        self.path = self.clean_parsed.path
        if self.scheme and self.netloc and self.path:
            # the path should have the format: "/entity/SimpleEntity/1"
            # where "entity" is the module, "SimpleEntity" is the class name and "1" is the id or pk
            temp_path = self.path
            if temp_path[0] == "/":
                temp_path = temp_path[1:]
            # "entity/SimpleEntity/1"
            if temp_path.find('/'):
                self.namespace = temp_path[:temp_path.find('/')]
                temp_path = temp_path[temp_path.find('/') + 1:]
                # 'SimpleEntity/1'
                if temp_path.find('/'):
                    self.class_name = temp_path[:temp_path.find('/')]
                    temp_path = temp_path[temp_path.find('/') + 1:]
                    print(temp_path)
                    if temp_path.find('/') < 0:
                        self.pk_value = temp_path
                        self.is_sintactically_correct = True

    def base64(self):
        return base64.encodestring(self.uri).replace('\n', '')
        
    def __repr__(self):
        return self.scheme + '://' + self.netloc + '/' + self.namespace + '/' + self.class_name + '/' + str(self.pk_value)
    
    def search_on_db(self):
        '''
        Database check
        I do not put this in the __init__ so the class can be used only for syntactic check or functionalities
        '''
        if self.is_sintactically_correct:
            # I search the ks by netloc and scheme on ksm
            try:
                self.knowledge_server = KnowledgeServer.objects.using('ksm').get(scheme=self.schem, netloc=self.netloc)
                self.is_ks_known = True
            except:
                self.is_ks_known = False
            if self.is_ks_known:
                # I search for its module and class and set relevant flags
                pass
        self.is_present = False
        # I search on this database
        #  on URIInstance
            
