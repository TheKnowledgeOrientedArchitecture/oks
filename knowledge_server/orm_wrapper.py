#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import importlib

from collections import OrderedDict

from django.apps.registry import apps as global_apps
from django.conf import settings



class OrmWrapper():
    def __init__(self):
        self.model_containers = global_apps
    
    @staticmethod
    def load_class(module_name, class_name):
        '''
        It returns a class that can be found in any <app_name>.models module
        Since some classes have been added dynamically, if not found it also 
        tries to reload the app/module 
        '''
        try:
            module = importlib.import_module(module_name + ".models")
            if not module_name in global_apps.app_configs.keys():
                if not hasattr(module, class_name):
                    OrmWrapper.load_module(module_name)
                    # I reload the module
                    # and reload the module
                    importlib.invalidate_caches()
                    module = importlib.reload(module)
            return getattr(module, class_name)        
        except:
            return None
            
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
    
    
orm_wrapper = OrmWrapper()