# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import importlib
import urllib
import knowledge_server.models 
from datetime import datetime
from urlparse import urlparse

from django.conf import settings

class xmlMinidom():
    @staticmethod    
    def getString(xmldoc, tag):
        try:
            return xmldoc.getElementsByTagName(tag)[0].firstChild.data
        except:
            return ""

    @staticmethod    
    def getStringAttribute(xmldoc, tag):
        try:
            return xmldoc.attributes[tag].firstChild.data
        except:
            return "" 
        
    @staticmethod    
    def getNaturalAttribute(xmldoc, tag):
        '''
        a natural number; if it's not there -1 is returned
        '''
        try:
            return int(xmldoc.attributes[tag].firstChild.data)
        except:
            return -1

def load_class(module_name, class_name):
    """
    dynamically load a class from a string
    """
    module = importlib.import_module(module_name)
    # Finally, we retrieve the Class
    return getattr(module, class_name)

class poor_mans_logger():
        
    def log(self, message):
        logfile = open('/tmp/' + settings.LOG_FILE_NAME + '.log', "a")
        logfile.write(str(datetime.now()) + " " + message + "\n")
        logfile.close
        
    def debug(self, message):
        self.log("Debug: " + message)
        
    def info(self, message):
        self.log("Info: " + message)
        
    def warning(self, message):
        self.log("Warning: " + message)
        
    def error(self, message):
        self.log("Error: " + message)

    def critical(self, message):
        self.log("Critical: " + message)

class Choices():
    # in lower case as they are brought to lower before verification
    FORMAT = ['xml','json','html','browse']
    SCHEME = ['http','https']

class KsUri(object):
    '''
    This class is responsible for the good quality of all URIs generated bKnowledgeServery a KS
    in terms of syntax and for their coherent use throughout the whole application
    It helps also getting information on the instance behind this URI searching on the
    database; the dataset it belongs to
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
        # http://rootks.thekoa.org/entity/ModelMetadata/1/json/  --> http://rootks.thekoa.org/entity/ModelMetadata/1/
        self.clean_uri = uri
        # remove the trailing slash
        if self.clean_uri[-1:] == "/":
            self.clean_uri = self.clean_uri[:-1]
        # remove the format the slash before it and set self.format
        self.format = ""
        for format in Choices.FORMAT:
            if self.clean_uri[-(len(format) + 1):].lower() == "/" + format:
                self.clean_uri = self.clean_uri[:-(len(format) + 1)]
                self.format = format

        # I check whether it's structure i well formed according to the GenerateURIInstance method
        self.is_sintactically_correct = False
        # not it looks something like: http://rootks.thekoa.org/entity/ModelMetadata/1
        self.clean_parsed = urlparse(self.clean_uri)
        self.scheme = ""
        for scheme in Choices.SCHEME:
            if self.clean_parsed.scheme.lower() == scheme:
                self.scheme = self.clean_parsed.scheme.lower()
        self.netloc = self.clean_parsed.netloc.lower()
        self.path = self.clean_parsed.path
        if self.scheme and self.netloc and self.path:
            # the path should have the format: "/entity/ModelMetadata/1"
            # where "entity" is the module, "ModelMetadata" is the class name and "1" is the id or pk
            temp_path = self.path
            if temp_path[0] == "/":
                temp_path = temp_path[1:]
            # "entity/ModelMetadata/1"
            if temp_path.find('/'):
                self.namespace = temp_path[:temp_path.find('/')]
                temp_path = temp_path[temp_path.find('/') + 1:]
                # 'ModelMetadata/1'
                if temp_path.find('/'):
                    self.class_name = temp_path[:temp_path.find('/')]
                    temp_path = temp_path[temp_path.find('/') + 1:]
                    print(temp_path)
                    if temp_path.find('/') < 0:
                        self.pk_value = temp_path
                        self.is_sintactically_correct = True

    def encoded(self):
        return urllib.urlencode({'':self.uri})[1:]
        
    def home(self):
        return self.scheme + '://' + self.netloc 

    def __repr__(self):
        return self.scheme + '://' + self.netloc + '/' + self.namespace + '/' + self.class_name + '/' + str(self.pk_value)
    
    def search_on_db(self):
        '''
        Database check
        I do not put this in the __init__ so the class can be used only for syntactic check or functionalities
        '''
        self.actual_class = None
        self.actual_instance = None
        self.is_present = False
        if self.is_sintactically_correct:
            # I search the ks by netloc and scheme on materialized
            try:
                self.knowledge_server = knowledge_server.models.KnowledgeServer.objects.using('materialized').get(scheme=self.scheme, netloc=self.netloc)
                self.is_ks_known = True
            except:
                self.is_ks_known = False
            # TODO: I search for its module and class and set relevant flags
            try:
                self.actual_class = load_class(self.namespace, self.class_name)
            except:
                pass
            # I search on this database
            try:
                if self.actual_class:
                    self.actual_instance = self.actual_class.objects.retrieve(self.clean_uri)
            except:
                pass
                
            




