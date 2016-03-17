#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import importlib
import logging

from collections import OrderedDict

import knowledge_server.models

from django.apps.registry import apps as global_apps
from django.conf import settings
from django.core import signals
import knowledge_server.utils

logger = logging.getLogger(__name__)


class OrmWrapper():
    def __init__(self):
        self.model_containers = global_apps
    
    @staticmethod
    def load_class(netloc, module_name, class_name):
        '''
        It returns a class that can be found in any <app_name>.models module
        Since some classes have been added dynamically, if not found it also 
        tries to reload the app/module 
        '''
        try:
            module_name = OrmWrapper.get_model_container_name(netloc, module_name)
            module = importlib.import_module(module_name + ".models")
            if not module_name in global_apps.app_configs.keys():
                if not hasattr(module, class_name):
                    OrmWrapper.load_module(module_name)
                    # I reload the module
                    # and reload the module
                    importlib.invalidate_caches()
                    module = importlib.reload(module)
            return getattr(module, class_name)        
        except Exception as ex:
            logger.warning("OrmWrapper.load_class not found netloc %s, module_name %s, class_name %s: _%s" % (netloc, module_name, class_name, str(ex)))
            raise(ex)
    
    @staticmethod
    def load_classes(module_name, class_name):
        '''
        NOT USED
        It returns a list of classes that have the same module and class name.
        There can be more than one because they can live in different namespaces
        e.g. coming from different OKSs. I procede as follows:
        - I search on ModelMetadata
        - from it's uri I get the netloc
        - I invoke OrmWrapper.load_class and build the list
        '''
        try:
            classes = []
            mms = knowledge_server.models.ModelMetadata.filter(module=module_name, name=class_name)
            for mm in mms:
                classes.append(OrmWrapper.load_class(knowledge_server.utils.KsUrl(mm.UKCL).netloc,module_name, class_name))
            
            return classes        
        except Exception as ex:
            logger.warning("OrmWrapper.load_classes not found module_name %s, class_name %s: _%s" % (module_name, class_name, str(ex)))
            raise(ex)
    
    @staticmethod
    def get_model_container_name(netloc, name):
        '''
        netloc is the netloc of the ks publisher of the ModelMetadata
        name is the name of the module of the ModelMetadata
        container == APP in Django terminology
        If I am in the KS that created this model (I created the actual code for the ORM
        and the corresponding record (and dataset) for the ModelMetadata then the 
        container name doesn't need to include the reversed url of the OKS.
        E.g. the app licenses in the OKS where it's been created, license.beta.thekoa.org
        has the name licenses. The same app in anotheroks.example.com would be called
        org_thekoa_beta_license__licenses so that we are sure there are no collisions.
        The domain (license.beta.thekoa.org) acts as a namespace for the app name (licenses) 
        so that example can have another app licenses without any collision.
        To keep the container name short, when possible, we will ad to the name the minimum 
        part of the domain (e.g. namespace) necessary. E.g.
        App licenses from license.beta.thekoa.org is called
            org_thekoa_beta_license__licenses on anotheroks.example.com
        but more concisely
            ___license__licenses on root.beta.thekoa.org
        Basically the parts of the url that are shared are not included in the name. 
        That still guarantees the independence of all namespaces.
        See comments on get_model_metadata to see why we leave underscores in place in the concise form
        PLEASE NOTE that the root OKS is an exception as its modules "knowledge_server" and "serializable"
                    have the same name in any OKS
        '''
        try:
            if netloc == "root.beta.thekoa.org":
                return name
            if name in knowledge_server.models.KnowledgeServer.root_apps:
                return name
            this_ks = knowledge_server.models.KnowledgeServer.this_knowledge_server()
            that = netloc.split('.')
            this = this_ks.netloc.split('.')
            leading_underscores = ""
            while len(this) > 0 and len(that) > 0 and this[-1] == that[-1]:
                leading_underscores += "_"
                this.pop()
                that.pop()
            
            if len(that) == 0:
                return name
            else:
                that.reverse()
                return leading_underscores + "_".join(that) + "__" + name
            
        except Exception as ex:
            logger.error("OrmWrapper.get_model_container_name: " + str(ex))
            raise ex
        
    @staticmethod
    def get_model_metadata_module(app_label):
        position = app_label.rfind("__")
        if position >= 0:
            return app_label[position+2:]
        else:
            return app_label
        
    @staticmethod
    def get_model_metadata_netloc(app_label):
        # the apps in the root OKS are an exception because they have always the same label
        # even in other OKSs
        if app_label in knowledge_server.models.KnowledgeServer.root_apps:
            return "root.beta.thekoa.org"
        this_ks = knowledge_server.models.KnowledgeServer.this_knowledge_server()
        position = app_label.rfind("__")
        if position < 0:
            return this_ks.netloc
        else:
            split_this_ks_netloc = this_ks.netloc.split(".")
            split_this_ks_netloc.reverse()
            # app_label is something like org_thekoa_beta...
            # 
            split_app_label = app_label[:position].split("_")
            for index, item in enumerate(split_app_label):
                if item == "":
                    split_app_label[index] = split_this_ks_netloc[index]
                else:
                    break
            split_app_label.reverse()
            return ".".join(split_app_label)

    @staticmethod
    def load_dynamic_apps():
        dmcs = knowledge_server.models.DynamicModelContainer.objects.all()
        for dmc in dmcs:
            OrmWrapper.load_module(dmc.name)
        
    @staticmethod
    def load_module(module_name, just_do_it=False):
        if just_do_it or (not module_name in settings.INSTALLED_APPS):
            settings.INSTALLED_APPS += (module_name, )
            # I load the app
            global_apps.app_configs = OrderedDict()
            global_apps.ready = False
            global_apps.populate(settings.INSTALLED_APPS)
    
class ModelContainer():
    '''
    A wrapper to the "App" concept of Django; an App is more general but we are interested in it
    only as it contains django.db.models.Model 
    '''
    @staticmethod
    def create():
        '''
        startapp
        '''

def signal_request_started(sender, environ, **kwargs):
    path_info_ext = ""
    if environ['PATH_INFO'].rfind(".") >=0:
        path_info_ext = environ['PATH_INFO'][environ['PATH_INFO'].rfind("."):]
    if path_info_ext != ".css" and path_info_ext != ".js":
        print(str(global_apps.app_configs.keys()))
        OrmWrapper.load_dynamic_apps()
        print(str(global_apps.app_configs.keys()))
    
orm_wrapper = OrmWrapper()

signals.request_started.connect(signal_request_started)        
        
