# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

'''
These models should be made thinner in order to represent only the 
Data Access or Persistence Layer
Whatever is not related to persistence should be moved to the Domain or
Business Layer
'''


import importlib
import inspect
import json
import logging
import os
import urllib
from urllib.request import urlopen, Request

from collections import OrderedDict
from datetime import datetime
from lxml import etree
from xml.dom import minidom

from django.apps.registry import apps as global_apps
from django.conf import settings
from django.core import management
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.state import ModelState, ProjectState
from django.db.models import Max, Q
from django.db.models.manager import ManagerDescriptor

from knowledge_server.utils import KsUrl
from knowledge_server.orm_wrapper import OrmWrapper
from serializable.models import SerializableModel

logger = logging.getLogger(__name__)


class CustomModelManager(models.Manager):
    '''
    Created to be used by ShareableModel so that all classes that inherit 
    will get the post_save signal bound to model_post_save. The following decorator

    @receiver(post_save, sender=ShareableModel)
    def model_post_save(sender, **kwargs):

    wouldn't work at all while it would work specifying the class name that inherits e.g. Workflow

    @receiver(post_save, sender=Workflow)
    def model_post_save(sender, **kwargs):

    '''
    def contribute_to_class(self, model, name):
        super(CustomModelManager, self).contribute_to_class(model, name)
        self._bind_post_save_signal(model)

    def _bind_post_save_signal(self, model):
        models.signals.post_save.connect(model_post_save, model)


def model_post_save(sender, **kwargs):
    if kwargs['instance'].UKCL == "":
        try:
            kwargs['instance'].UKCL = kwargs['instance'].generate_UKCL()
            if kwargs['instance'].UKCL != "":
                kwargs['instance'].save()
        except Exception as e:
            logger.error("model_post_save kwargs['instance'].UKCL: " + kwargs['instance'].UKCL + "  -  " + str(e))
    if isinstance(kwargs['instance'], DataSet):
        if kwargs['instance'].first_version_id == None:
            kwargs['instance'].first_version_id = kwargs['instance'].pk
            kwargs['instance'].save()



class ShareableModel(SerializableModel):
    '''
    ShareableModel is the superclass of all classes, including the ones you define in your apps, that
    can be shared via a KnowledgeServer 
    UKCL Uniform Knowledge Chunk Locator
    UKCL is the unique identifier of this ShareableModel in this KS
    When a new instance of a ShareableModel is created within a dataset with the 
    new_version method, a new UKCL is generated using generate_UKCL
    '''
    UKCL = models.CharField(max_length=750, default='', blank=True, db_index=True)
    '''
    UKCL_previous_version is the UKCL of the previous version if 
    this record has been created with the new_version method.
    It is used when materializing to update the relationships from old to new records
    '''
    UKCL_previous_version = models.CharField(max_length=750, null=True, blank=True, db_index=True)
    objects = CustomModelManager()
    '''
    Each instance of a ShareableModel should, sooner or later, be part of a dataset that is not a view neither shallow
    e.g. has version information. DataSet.set_released sets this attribute for each instance in the dataset
    '''
    dataset_I_belong_to = models.ForeignKey("DataSet", null=True, blank=True, related_name='+')

    @property
    def q_UKCL(self):
        # Quoted UKCL
        return urllib.parse.quote(self.UKCL).replace("/","%2F")
        
    @property
    def p_name(self):
        mm = self.get_model_metadata()
        return getattr(self, mm.name_field)

    def generate_UKCL(self):
        '''
        *** method that works on the same database where self is saved ***
        UKCL is generated on records owned by this_ks
        '''
        try:
            # http://stackoverflow.com/questions/10375019/get-database-django-model-object-was-queried-from
            db_alias = self._state.db
            this_ks = KnowledgeServer.this_knowledge_server()

            mm = self.get_model_metadata(db_alias=db_alias)
            name = mm.name
            id_field = mm.id_field
            namespace = OrmWrapper.get_model_container_name(this_ks.netloc, mm.module)
            return this_ks.url() + "/" + namespace + "/" + name + "/" + str(getattr(self, id_field))
        except Exception as es:
            logger.error("Exception 'generate_UKCL' " + self.__class__.__name__ + "." + str(self.pk) + ":" + str(es))
            return ""
    
    def regenerate_UKCL(self):
        '''
        Creating initial data like current knowledge server can leave some record with the wrong 
        UKCL based on old KnowledgeServer.netloc
        This method fixes UKCL on both materialized and default db
        '''
        m_self = self.__class__.objects.using('materialized').get(UKCL=self.UKCL)
        d_self = self.__class__.objects.using('default').get(UKCL=self.UKCL)
        m_self.UKCL = ""
        m_self.save()
        d_self.UKCL = ""
        d_self.save()
        self.UKCL = d_self.UKCL
        
    def get_model_metadata (self, class_name="", db_alias='materialized'):
        '''
        *** method that works BY DEFAULT on the materialized database ***
        There can be more than one class with the same name in different apps e.g. coming from different
        OKSs; we need to find the app name as well so that we check if it matches the model metadata UKCL
        finds the instance of class ModelMetadata where the name corresponds to the name of the class of self
        TODO: should we make it work by default on db_alias=self._state.db ?
        '''
        try:
            # self might as well not have a UKCL yet as this method is also invoked by generate_UKCL
            if class_name == "":
                # I reverse engineer the netloc of the model_metadata from the app_label/model_container
                # example: this_ks is http://client.thekoa.org and self has "__license__licenses" as app_label
                # then the ModelMetadata is from  http://license.thekoa.org
                mm_netloc = OrmWrapper.get_model_metadata_netloc(self.__class__._meta.app_label)
                # I reverse engineer the bare module of the model_metadata from the app_label/model_container
                # example: self has "__license__licenses" as app_label, the module is "licenses"
                mm_module = OrmWrapper.get_model_metadata_module(self.__class__._meta.app_label)
                mms = ModelMetadata.objects.using(db_alias).filter(name=self.__class__.__name__, module=mm_module)
                # there could be many ModelMetadata with same class name and module name
                # example I have License in app/container licenses on servers:
                # http://license.thekoa.org
                # http://license.beta.thekoa.org
                # http://oks.creativecommons.org
                # The app labels (that will help me calculate the model_metadata netloc) will be respectively:
                # if this_ks is http://client.thekoa.org
                # __license__licenses
                # __beta_license__licenses
                # _creativecommons_oks__licenses
                # if this_ks is http://client.beta.thekoa.org
                # __license__licenses
                # ___license__licenses
                # _creativecommons_oks__licenses
                for mm in mms.all():
                    tmp_url = KsUrl(mm.UKCL)
                    if mm_netloc == tmp_url.netloc:
                        return mm
                raise("ModelMetadata not found. content_type.app_label="+self.__class__._meta.app_label)
            else:
                # TBC we don't have a way to check the app yet so THIS COULD RAISE AN EXCEPTION
                return ModelMetadata.objects.using(db_alias).get(name=class_name)
        except Exception as ex:
            logger.error('get_model_metadata - db_alias = ' + db_alias + ' - class_name self.__class__.__name__= ' + class_name + " " + self.__class__.__name__ + " -- " + str(ex))
            
    def structures(self):
        '''
        Lists the structures whose root is of the same class of self
        '''
        return DataSetStructure.objects.filter(root_node__model_metadata=self.get_model_metadata())

    def serialized_URI_MM(self, export_format='XML'):
        if export_format == 'XML':
            return ' URIModelMetadata="' + self.get_model_metadata().UKCL + '" '  
        if export_format == 'JSON':
            return ' "URIModelMetadata" : "' + self.get_model_metadata().UKCL + '" '
        if export_format == 'DICT':
            return { "URIModelMetadata": self.get_model_metadata().UKCL }
        
    def shallow_structure(self, db_alias='default'):
        '''
        It creates a DataSetStructure, saves it on the database and returns it.
        The structure created is shallow e.g. it has no depth but just one node
        THE NEED: if a user wants to serialize something without passing an DataSetStructure
        I search for a DataSetStructure with is_shallow=True; if I can't find it I create it and save it
        for future use and I use it for serialization
        '''
        try:
            dss = DataSetStructure.objects.using(db_alias).get(root_node__model_metadata=self.get_model_metadata(), is_shallow=True)
        except:
            dss = DataSetStructure()
            dss.is_shallow = True
            dss.name = self.__class__.__name__ + " (shallow)"
            dss.model_metadata = self.get_model_metadata()
            dss.root_node = self.shallow_structure_node(db_alias)
            dss.save()
            dss.save(using=db_alias)
            # I need to materialize them because I might have DanglingReferences on materialized.
            # To create them I need the StructureNode in materialized db too.
            dss_dss = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN)
            dss.materialize(dss_dss.root_node, processed_instances=[])
        return dss 
        
    def shallow_structure_node(self, db_alias='default'):
        '''
        it creates a StructureNode used to serialize (to_xml) self. It has the ModelMetadata 
        and references to ForeignKeys and ManyToMany
        '''
        structure_node = StructureNode()
        structure_node.model_metadata = self.get_model_metadata() 
        structure_node.external_reference = False
        structure_node.is_many = False
        structure_node.save(using=db_alias)
        structure_node.child_nodes = []
        for rel in self.foreign_key_attributes() + self.many_to_many_attributes():
            rel_structure_node = StructureNode()
            
            class_name = self._meta.get_field(rel).rel.model.__name__
            # from the module name I remove the final ".models"
            # TODO: usare queste righe seguenti per creare una nuova implementazione di get_model_metadata
            module_name = self._meta.get_field(rel).rel.model.__module__[:-7]
            try:
                rel_structure_node.model_metadata = ModelMetadata.objects.using(db_alias).get(name=class_name, module=module_name)
            except Exception as ex:
                raise Exception("shallow_structure_node class_name = %s -- module_name = %s --- %s" %  (class_name, module_name, str(ex)))
            rel_structure_node.external_reference = True
            rel_structure_node.attribute = rel
            rel_structure_node.is_many = (rel in self.many_to_many_attributes())
            rel_structure_node.save(using=db_alias)
            structure_node.child_nodes.add(rel_structure_node)
        for rel, ct_field, fk_field in self.generic_foreign_key_attributes():
            rel_structure_node = StructureNode()
            
            # It's a GenericForeignKey
            # https://docs.djangoproject.com/en/1.9/ref/contrib/contenttypes/#django.contrib.contenttypes.fields.GenericForeignKey
            # ct = Content Type    fk = Foreign Key
            rel_structure_node.ct_field = ct_field
            rel_structure_node.fk_field = fk_field

            rel_structure_node.external_reference = True
            rel_structure_node.attribute = rel
            rel_structure_node.is_many = False
            rel_structure_node.save(using=db_alias)
            structure_node.child_nodes.add(rel_structure_node)
        structure_node.save(using=db_alias)
        return structure_node

    def serialize(self, structure_node=None, exported_instances=[], export_format='XML', parent=None):
        '''
        formats so far: {'XML' | 'JSON' | 'DICT'}
            dict is a python dictionary that can be easily inserted in other dictionaries and serialized at a later stage
            If within a structure I have already exported this instance I don't want to duplicate all details hence I just export it's 
            UKCL, name and ModelMetadata URL. Then I need to add an attribute so that when importing it I will recognize that 
            its details are somewhere else in the file
            <..... URIModelMetadata="....." UKCL="...." attribute="...." REFERENCE_IN_THIS_FILE=""
            the TAG "REFERENCE_IN_THIS_FILE" is used to mark the fact that attributes values are somewhere else in the file
        '''
        export_format = export_format.upper()
        serialized = ""
        tmp_dict = {}
        export_dict = {}
        # if there is no structure_node I export just this object creating a shallow DataSetStructure 
        if structure_node is None:
            structure_node = self.shallow_structure().root_node
        if structure_node.is_many:
            # the attribute corresponds to a list of instances of the model_metadata 
            tag_name = structure_node.sn_model_metadata(parent).name
        else:
            tag_name = self.__class__.__name__ if structure_node.attribute == "" else structure_node.attribute
        # already exported, I just export a short reference with the UKCL
        if self.UKCL and self.UKCL in exported_instances and structure_node.sn_model_metadata(parent).name_field:
            if export_format == 'XML':
                xml_name = " " + structure_node.sn_model_metadata(parent).name_field + "=\"" + getattr(self, structure_node.sn_model_metadata(parent).name_field) + "\""
                return '<' + tag_name + ' REFERENCE_IN_THIS_FILE=\"\"' + self.serialized_URI_MM(export_format) + xml_name + ' UKCL="' + self.UKCL + '"/>'  
            if export_format == 'JSON':
                json_name = ' "' + structure_node.sn_model_metadata(parent).name_field + '" : "' + getattr(self, structure_node.sn_model_metadata(parent).name_field) + '"'
                if structure_node.is_many:
                    return ' { "REFERENCE_IN_THIS_FILE" : \"\", ' + self.serialized_URI_MM(export_format) + ", " + json_name + ', "UKCL": "' + self.UKCL + '"} '
                else:
                    return '"' + tag_name + '" : { "REFERENCE_IN_THIS_FILE" : \"\", ' + self.serialized_URI_MM(export_format) + ", " + json_name + ', "UKCL": "' + self.UKCL + '"}'  
            if export_format == 'DICT':
                tmp_dict[structure_node.sn_model_metadata(parent).name_field] = getattr(self, structure_node.sn_model_metadata(parent).name_field)
                tmp_dict["REFERENCE_IN_THIS_FILE"] = ""
                tmp_dict.update(self.serialized_URI_MM(export_format))
                tmp_dict["UKCL"] = self.UKCL
                if structure_node.is_many:
                    export_dict = tmp_dict
                else:
                    export_dict[tag_name] = tmp_dict
                return export_dict
        exported_instances.append(self.UKCL) 
        if not structure_node.external_reference:
            try:
                outer_comma = ""
                for child_structure_node in structure_node.child_nodes.all():
                    if child_structure_node.method_to_retrieve:
                        # there is no attribute but a method to access the child(ren)
                        method_to_retrieve = getattr(self, child_structure_node.method_to_retrieve)
                        o = method_to_retrieve(export_format)
                        if export_format == 'XML':
                            serialized += o
                        if export_format == 'JSON':
                            serialized += o
                        if export_format == 'DICT':
                            tmp_dict.update(o)
#                         source_code = inspect.getsource(self)
                        outer_comma = ", "
                    else:
                        if child_structure_node.is_many:
                            child_instances = eval("self." + child_structure_node.attribute + ".all()")
                            if export_format == 'XML':
                                serialized += "<" + child_structure_node.attribute + ">"
                            if export_format == 'JSON':
                                serialized += outer_comma + ' "' + child_structure_node.attribute + '" : ['
                            innner_comma = ''
                            children_list = []
                            for child_instance in child_instances:
                                # let's prevent infinite loops if self relationships
                                if (child_instance.__class__.__name__ != self.__class__.__name__) or (self.pk != child_structure_node.pk):
                                    if export_format == 'JSON':
                                        serialized += innner_comma
                                    if export_format == 'DICT':
                                        children_list.append(child_instance.serialize(child_structure_node, exported_instances=exported_instances, export_format=export_format, parent=self))
                                    else:
                                        serialized += child_instance.serialize(child_structure_node, exported_instances=exported_instances, export_format=export_format, parent=self)
                                innner_comma = ", "
                            if export_format == 'XML':
                                serialized += "</" + child_structure_node.attribute + ">"
                            if export_format == 'JSON':
                                serialized += "]"
                            if export_format == 'DICT':
                                tmp_dict[child_structure_node.attribute] = children_list

                            outer_comma = ", "
                        else:
                            child_instance = eval("self." + child_structure_node.attribute)
                            if not child_instance is None:
                                child_serialized = ""
                                if export_format == 'JSON':
                                    child_serialized = outer_comma
                                if export_format == 'DICT':
                                    tmp_dict.update(child_instance.serialize(child_structure_node, export_format=export_format, exported_instances=exported_instances, parent=self))
                                else:
                                    child_serialized += child_instance.serialize(child_structure_node, export_format=export_format, exported_instances=exported_instances, parent=self)
                                serialized += child_serialized
                                outer_comma = ", "
            except Exception as ex:
                logger.error("ShareableModel.serialize: " + str(ex))
            if export_format == 'XML':
                return '<' + tag_name + self.serialized_URI_MM(export_format) + self.serialized_attributes(parent_class=ShareableModel, format=export_format) + '>' + self.serialized_tags(parent_class=ShareableModel) + serialized + '</' + tag_name + '>'
            if export_format == 'JSON':
                if structure_node.is_many:
                    return ' { ' + self.serialized_URI_MM(export_format) + ', ' + self.serialized_attributes(format=export_format) + outer_comma + serialized + ' }'
                else:
                    return '"' + tag_name + '" : { ' + self.serialized_URI_MM(export_format) + ', ' + self.serialized_attributes(format=export_format) + outer_comma + serialized + ' }'
            if export_format == 'DICT':
                tmp_dict.update(self.serialized_URI_MM(export_format))
                tmp_dict.update(self.serialized_attributes(format=export_format))
                if structure_node.is_many:
                    export_dict = tmp_dict
                else:
                    export_dict[tag_name] = tmp_dict
                return export_dict
        else:
            # structure_node.external_reference = True
            xml_name = ''
            json_name = ''
            if structure_node.sn_model_metadata(parent).name_field != "":
                if export_format == 'XML':
                    xml_name = " " + structure_node.sn_model_metadata(parent).name_field + "=\"" + getattr(self, structure_node.sn_model_metadata(parent).name_field) + "\""
                if export_format == 'JSON':
                    json_name = ', "' + structure_node.sn_model_metadata(parent).name_field + '": "' + getattr(self, structure_node.sn_model_metadata(parent).name_field) + '"'
                if export_format == 'DICT':
                    tmp_dict[structure_node.sn_model_metadata(parent).name_field] = getattr(self, structure_node.sn_model_metadata(parent).name_field)
            if export_format == 'XML':
                return '<' + tag_name + self.serialized_URI_MM() + 'UKCL="' + self.UKCL + '" ' + self._meta.pk.attname + '="' + str(self.pk) + '"' + xml_name + '/>'
            if export_format == 'JSON':
                if structure_node.is_many:
                    return '{ ' + self.serialized_URI_MM(export_format) + ', "UKCL" : "' + self.UKCL + '", "' + self._meta.pk.attname + '" : "' + str(self.pk) + '"' + json_name + ' }'
                else:
                    return '"' + tag_name + '" :  { ' + self.serialized_URI_MM(export_format) + ', "UKCL" : "' + self.UKCL + '", "' + self._meta.pk.attname + '" : "' + str(self.pk) + '"' + json_name + ' }'
            if export_format == 'DICT':
                tmp_dict.update(self.serialized_URI_MM(export_format))
                tmp_dict["UKCL"] = self.UKCL
                tmp_dict[self._meta.pk.attname] = self.pk
                if structure_node.is_many:
                    export_dict = tmp_dict
                else:
                    export_dict[tag_name] = tmp_dict
                return export_dict
            
    def save_from_xml(self, structure_netloc, xmldoc, structure_node, parent=None):
        '''
        save_from_xml gets from xmldoc the attributes of self and saves it; it searches for child nodes according
        to structure_node.child_nodes, creates instances of child objects and calls itself recursively
        Every tag corresponds to a MetatadaModel, hence it
            contains a tag URIMetadataModel which points to the KS managing the MetadataModel
        
        Each ShareableModel(SerializableModel) has UKCL and UKCL_previous_version attributes. 
        
        external_reference
            the first ShareableModel in the XML cannot be marked as an external_reference in the structure_node
            save_from_xml doesn't get called recursively for external_references which are to be found in the database
            or to remain dangling references
        '''
        field_name = ""
        if parent:
#           I have a parent; let's set it
            field_name = ShareableModel.get_parent_field_name(parent, structure_node.attribute)
            if field_name:
                setattr(self, field_name, parent)
        '''
        Some TAGS have no data (attribute REFERENCE_IN_THIS_FILE is present) because the instance they describe
        is present more than once in the XML file and the export doesn't replicate data; hence either
           I have it already in the database so I can load it
        or
           I have to save this instance but I will find its attribute later in the imported file
        '''
        try:
            xmldoc.attributes["REFERENCE_IN_THIS_FILE"]
            # if the TAG is not there an exception will be raised and the method will continue and expect to find all data
            module_name = structure_node.sn_model_metadata(parent).module
            
            actual_class = OrmWrapper.load_class(structure_netloc, module_name, structure_node.sn_model_metadata(parent).name) 
            try:
                instance = actual_class.retrieve_locally(xmldoc.attributes["UKCL"].firstChild.data)
                # It's in the database; I just need to set its parent; data is either already there or it will be updated later on
                if parent:
                    field_name = ShareableModel.get_parent_field_name(parent, structure_node.attribute)
                    if field_name:
                        setattr(instance, field_name, parent)
                    instance.save()
            except:
                # I haven't found it in the database; I need to do something only if I have to set the parent
                if parent: 
                    try:
                        setattr(self, "UKCL", xmldoc.attributes["UKCL"].firstChild.data)
                        self.SetNotNullFields()
                        self.save()
                    except:
                        logger.error("Error in REFERENCE_IN_THIS_FILE TAG setting attribute UKCL for instance of class " + self.__class__.__name__)
            # let's exit, nothing else to do, it's a REFERENCE_IN_THIS_FILE
            return
        except:
            # nothing to do, there is no REFERENCE_IN_THIS_FILE attribute
            pass
        for key in self._meta.fields:
            '''
              let's setattr the other attributes
              that are not ForeignKey as those are treated separately
              and is not the field_name pointing at the parent as it has been already set
            '''
            if key.__class__.__name__ != "ForeignKey" and (not parent or key.name != field_name):
                try:
                    if key.__class__.__name__ in SerializableModel.types_serialized_as_tags and (not key.name in list(key.name for key in ShareableModel._meta.fields)):
                        child_tag = xmldoc.getElementsByTagName(key.name)[0]
                        setattr(self, key.name, child_tag.firstChild.data)
                    elif key.__class__.__name__ == "BooleanField":
                        setattr(self, key.name, xmldoc.attributes[key.name].firstChild.data.lower() == "true") 
                    elif key.__class__.__name__ == "IntegerField":
                        setattr(self, key.name, int(xmldoc.attributes[key.name].firstChild.data))
                    else:
                        setattr(self, key.name, xmldoc.attributes[key.name].firstChild.data)
                except Exception as ex:
                    logger.debug("Extracting from xml \"" + key.name + "\" for object of class \"" + self.__class__.__name__ + "\" with PK " + str(self.pk) + ". Exception: " + str(ex))
        # in the previous loop I have set the pk too; I must set it to None before saving
        self.pk = None

        # I must set foreign_key child nodes BEFORE SAVING self otherwise I get an error for ForeignKeys not being set
        for child_structure_node in structure_node.child_nodes.all():
            if child_structure_node.attribute == 'first_version':
                pass
            # I must skip the import if self is a DataSet and the GenericForeignKey is 'root'
            # this is because the export of a DataSet is done differently from any other; it
            # starts from the root with the DataSet.dataset_structure.root_node
            elif child_structure_node.attribute in self.virtual_field_attributes() and isinstance(self, DataSet) and child_structure_node.attribute=='root':
                pass
            elif child_structure_node.attribute in (self.foreign_key_attributes() + self.virtual_field_attributes()):
                try:
                    # ASSERT: in the XML there is exactly at most one child tag
                    child_tag = [t for t in xmldoc.getElementsByTagName(child_structure_node.attribute) if t in xmldoc.childNodes]
                    if len(child_tag) == 1:
                        xml_child_node = child_tag[0] 
                        # I search for the corresponding ModelMetadata
                         
                        se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                        assert (child_structure_node.sn_model_metadata(self).name == se.name), "child_structure_node.sn_model_metadata(self).name - se.name: " + child_structure_node.sn_model_metadata(self).name + ' - ' + se.name
                        module_name = child_structure_node.sn_model_metadata(self).module
                        actual_class = OrmWrapper.load_class(structure_netloc, module_name, child_structure_node.sn_model_metadata(self).name)
                        instance = None
                        if child_structure_node.external_reference:
                            '''
                            If it is an external reference I must search for it in the database first;  
                            if it is not there I fetch it using it's URL and then create it in the database
                            '''
                            # it can be a self relation; if so instance is self
                            if self.UKCL == xml_child_node.attributes["UKCL"].firstChild.data:
                                instance = self 
                            else:
                                try:
                                    # let's search it in the database
                                    instance = actual_class.retrieve_locally(xml_child_node.attributes["UKCL"].firstChild.data)
                                except ObjectDoesNotExist:
                                    # TODO: if it is not there it is a dangling reference
                                    logger.warning("\"" + module_name + ".models " + se.name + "\" TODO: dangling reference for UKCL \"" + xml_child_node.attributes["UKCL"].firstChild.data)
                                except Exception as ex:
                                    logger.error("\"" + module_name + ".models " + se.name + "\" has no instance with UKCL \"" + xml_child_node.attributes["UKCL"].firstChild.data + " " + str(ex))
                                    raise Exception("\"" + module_name + ".models " + se.name + "\" has no instance with UKCL \"" + xml_child_node.attributes["UKCL"].firstChild.data + " " + str(ex))
                        else:
                            instance = actual_class()
                            # save_from_xml takes care of saving instance with a self.save() at the end
                            instance.save_from_xml(structure_netloc, xml_child_node, child_structure_node)  # the fourth parameter, "parent" shouldn't be necessary in this case as this is a ForeignKey
                        if not instance is None:
                            setattr(self, child_structure_node.attribute, instance)
                except Exception as ex:
                    logger.error("save_from_xml self=%s child_structure_node.attribute='%s' in (foreign_key + virtual_field):  -- %s" % (self.UKCL, child_structure_node.attribute, str(ex)))
                    raise Exception("save_from_xml: " + str(ex))
                 
        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        # TODO: UGLY PATCH: see #143
        if self.__class__.__name__ == 'DataSet':
            self.first_version = None
            # if it is a view root_instance_id could be set to "" but it should be None
            if self.root_instance_id == "": 
                self.root_instance_id = None
        # I can save now
        self.save()
        # TODO: UGLY PATCH: see #143
        if self.__class__.__name__ == 'DataSet':
            '''
            if the first_version has been imported here then I use it, otherwise self
            '''
            self.first_version = self
            try:
                first_version_tag = [t for t in xmldoc.getElementsByTagName('first_version') if t in xmldoc.childNodes]
                if len(first_version_tag) == 1:
                    first_version_UKCL = first_version_tag[0].attributes["UKCL"].firstChild.data
                    instance = DataSet.retrieve_locally(first_version_UKCL)
                    self.first_version = instance
            except:
                pass
            self.save()
        # TODO: CHECK maybe the following comment is wrong and  UKCL is always set 
        # save_from_xml can be invoked on an instance retrieved from the database (where UKCL is set)
        # or created on the fly (and UKCL is not set); in the latter case, only now I can generate UKCL
        # as I have just saved it and I have a local ID
        
        for child_structure_node in structure_node.child_nodes.all():
            # I have already processed foreign keys and virtual_field (=GenericForeignKey), I skip them now
            if child_structure_node.attribute and (not child_structure_node.attribute in (self.foreign_key_attributes() + self.virtual_field_attributes())):
                # ASSERT: in the XML there is exactly one child tag
                xml_attribute_nodes = [t for t in xmldoc.getElementsByTagName(child_structure_node.attribute) if t in xmldoc.childNodes]
                xml_attribute_node = xml_attribute_nodes[0]
                if child_structure_node.is_many:
                    for xml_child_node in xml_attribute_node.childNodes:
                        se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                        module_name = child_structure_node.sn_model_metadata(self).module
                        assert (child_structure_node.sn_model_metadata(self).name == se.name), "child_structure_node.name - se.name: " + child_structure_node.sn_model_metadata(self).name + ' - ' + se.name
                        actual_class = OrmWrapper.load_class(structure_netloc, module_name, child_structure_node.sn_model_metadata(self).name)
                        if child_structure_node.external_reference:
                            instance = actual_class.retrieve_locally(xml_child_node.attributes["UKCL"].firstChild.data)
                            # TODO: il test successivo forse si fa meglio guardando il concrete_model - capire questo test e mettere un commento
                            if child_structure_node.attribute in self._meta.fields:
                                setattr(instance, child_structure_node.attribute, self)
                                instance.save()
                            else:  
                                setattr(self, child_structure_node.attribute, instance)
                                self.save()
                        else:
                            instance = actual_class()
                            # is_many = True, I need to add this instance to self
                            
                            tmp_log = getattr(self._meta.concrete_model, child_structure_node.attribute)
                            logger.debug("getattr(self._meta.concrete_model, child_structure_node.attribute) %s" % tmp_log.__class__.__name__)
                            logger.debug("self.UKCL=%s - child_structure_node.attribute='%s'" % (self.UKCL, child_structure_node.attribute))
                            instance.save_from_xml(structure_netloc, xml_child_node, child_structure_node, self)
                            related_parent = getattr(self._meta.concrete_model, child_structure_node.attribute)
                            related_list = getattr(self, child_structure_node.attribute)
                            # if it is a manytomany it is not there yet ... 
                            if ShareableModel.get_parent_field_name(self, child_structure_node.attribute) == "":
#                             if instance.id not in [i.id for i in related_list.all()]:
                                # I add it
                                related_list.add(instance)
                                self.save()
                else:
                    # is_many == False
                    xml_child_node = xml_attribute_node
                    se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                    module_name = child_structure_node.sn_model_metadata(self).module
                    assert (child_structure_node.sn_model_metadata(self).name == se.name), "child_structure_node.name - se.name: " + child_structure_node.sn_model_metadata(self).name + ' - ' + se.name
                    actual_class = OrmWrapper.load_class(structure_netloc, module_name, child_structure_node.sn_model_metadata(self).name)
                    if child_structure_node.external_reference:
                        instance = actual_class.retrieve_locally(xml_child_node.attributes["UKCL"].firstChild.data)
                        # TODO: il test successivo forse si fa meglio guardando il concrete_model - capire questo test e mettere un commento
                        if child_structure_node.attribute in self._meta.fields:
                            setattr(instance, child_structure_node.attribute, self)
                            instance.save()
                        else:  
                            setattr(self, child_structure_node.attribute, instance)
                            self.save()
                    else:
                        instance = actual_class()
                        instance.save_from_xml(structure_netloc, xml_child_node, child_structure_node, self)
        
    def new_version(self, structure_node, processed_instances, parent=None):
        '''
        invoked by DataSet.new_version that wraps it in a transaction
        it recursively invokes itself to create a new version of the full structure
        
        processed_instances is a dictionary where the key is the old UKCL and 
        the data is the new one
        
        returns the newly created instance
        '''

        if structure_node.external_reference:
            # if it is an external reference I do not need to create a new instance
            return self

        if self.UKCL and str(self.UKCL) in processed_instances.keys():
            # already created, I get it and return it
            return self.__class__.objects.get(UKCL=processed_instances[str(self.UKCL)])
        
        new_instance = self.__class__()
        if parent:
#           I have a parent; let's set it
            field_name = ShareableModel.get_parent_field_name(parent, structure_node.attribute)
            if field_name:
                setattr(new_instance, field_name, parent)
                
        for child_structure_node in structure_node.child_nodes.all():
            if child_structure_node.attribute in self.foreign_key_attributes():
                # not is_many
                child_instance = eval("self." + child_structure_node.attribute)
                new_child_instance = child_instance.new_version(child_structure_node, processed_instances)
                setattr(new_instance, child_structure_node.attribute, new_child_instance)  # the parameter "parent" shouldn't be necessary in this case as this is a ForeignKey
                
        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        new_instance.save()
                
        for child_structure_node in structure_node.child_nodes.all():
            if child_structure_node.is_many:
                child_instances = eval("self." + child_structure_node.attribute + ".all()")
                for child_instance in child_instances:
                    # let's prevent infinite loops if self relationships
                    if (child_instance.__class__.__name__ == self.__class__.__name__) and (self.pk == child_structure_node.pk):
                        eval("new_instance." + child_structure_node.attribute + ".add(new_instance)")
                    else:
                        new_child_instance = child_instance.new_version(child_structure_node, processed_instances, new_instance)
            else:
                # not is_many
                child_instance = eval("self." + child_structure_node.attribute)
                new_child_instance = child_instance.new_version(child_structure_node, processed_instances, self)
                setattr(new_instance, child_structure_node.attribute, new_child_instance)
        
        for key in self._meta.fields:
            if key.__class__.__name__ != "ForeignKey" and self._meta.pk != key:
                setattr(new_instance, key.name, eval("self." + key.name))
        new_instance.UKCL_previous_version = new_instance.UKCL
        new_instance.UKCL = ""
        new_instance.save()
        # after saving
        processed_instances[str(self.UKCL)] = new_instance.UKCL
        return new_instance

    def materialize(self, structure_node, processed_instances, parent=None):
        '''
        invoked by DataSet.set_released that wraps it in a transaction
        it recursively invokes itself to copy the full structure to the materialized DB
        
        ASSERTION: UKCL remains the same on the materialized database
        
        processed_instances is a list of processed UKCL 
        
        TODO: before invoking this method a check is done to see whether it is already materialized; is it done always? 
        If so shall we move it inside this method?
        '''

        if structure_node.external_reference:
            try:
                return self.__class__.objects.using('materialized').get(UKCL=self.UKCL)
            except Exception as ex:
                logger.info("ShareableModel.materialize: external_reference to UKCL: " + self.UKCL + " searching it on materialized: " + str(ex) + " Adding it to DanglingReferences")
                raise ExternalReferenceNotFoundOnMaterialized("")

        if self.UKCL and str(self.UKCL) in processed_instances:
            # already materialized it, I return that one 
            return self.__class__.objects.using('materialized').get(UKCL=self.UKCL)
        
        new_instance = self.__class__()
        if parent:
#           I have a parent; let's set it
            field_name = ShareableModel.get_parent_field_name(parent, structure_node.attribute)
            if field_name:
                setattr(new_instance, field_name, parent)

        dangling_references = []  
        list_of_self_relationships_pointing_to_self = []      
        for child_structure_node in structure_node.child_nodes.all():
            if child_structure_node.attribute in (self.foreign_key_attributes() + self.virtual_field_attributes()):
                # not is_many
                # if they are nullable I do nothing
                try:
                    child_instance = getattr(self, child_structure_node.attribute)
                    if not child_instance is None:
                        # e.g. DataSet.root is a self relationship often set to self; I am materializing self
                        # so I don't have it; I return self; I could probably do the same also in the other case
                        # because what actually counts for Django is the pk
                        if self == child_instance:
                            # In Django ORM it seems not possible to have not nullable self relationships pointing to self
                            # I make not nullable in the model (this becomes a general constraint!); 
                            # put them in a list and save them after saving new_instance
                            list_of_self_relationships_pointing_to_self.append(child_structure_node.attribute)
                        else:
                            try:
                                new_child_instance = child_instance.materialize(child_structure_node, processed_instances)
                                # the parameter "parent" shouldn't be necessary in this case as this is a ForeignKey
                                setattr(new_instance, child_structure_node.attribute, new_child_instance)  
                            except ExternalReferenceNotFoundOnMaterialized:
                                # The reference exists in default, so we store the DanglingReference on the materialized
                                dr = DanglingReference()
                                dr.UKCL_actual_instance = child_instance.UKCL
                                # child_structure_node is from default; we can't have a rel with dr on materialized
                                dr.structure_node = StructureNode.objects.using('materialized').get(UKCL=child_structure_node.UKCL)
                                dangling_references.append(dr)
                                # I need to set a placeholder otherwise saving new_instance will fail if the attribute can't be null
                                setattr(new_instance, child_structure_node.attribute, child_instance.__class__.placeholder('materialized'))
                            except Exception as ex:
                                logger.error("Error materializing " + child_instance.UKCL + " - " + str(ex))
                                raise ex
                except Exception as ex:
                    logger.error("ShareableModel.materialize: " + self.__class__.__name__ + " " + str(self.pk) + " attribute \"" + child_structure_node.attribute + "\" " + str(ex))
                    raise ex
        for key in self._meta.fields:
            if key.__class__.__name__ != "ForeignKey" and self._meta.pk != key:
                setattr(new_instance, key.name, eval("self." + key.name))

        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        try:
            new_instance.save(using='materialized')
        except Exception as ex:
            logger.error("ShareableModel.materialize, errore saving new_instance of " + self.__class__.__name__ + " " + str(self.pk) + + str(ex))
        # now I can link the dangling_references to new_instance
        for dr in dangling_references:
            dr.object_with_dangling=new_instance
            dr.save(using='materialized')
        if len(list_of_self_relationships_pointing_to_self) > 0:
            for attribute in list_of_self_relationships_pointing_to_self:
                setattr(new_instance, attribute, new_instance)
            new_instance.save(using='materialized')
        
        for child_structure_node in structure_node.child_nodes.all():
            if not (child_structure_node.attribute in (self.foreign_key_attributes() + self.virtual_field_attributes())):
                if child_structure_node.is_many:
                    # if we have a method to retrieve the children there is nothing to be materialized
                    if not child_structure_node.method_to_retrieve:
                        child_instances = eval("self." + child_structure_node.attribute + ".all()")
                        for child_instance in child_instances:
                            # let's prevent infinite loops if self relationships
                            if (child_instance.__class__.__name__ == self.__class__.__name__) and (self.pk == child_structure_node.pk):
                                eval("new_instance." + child_structure_node.attribute + ".add(new_instance)")
                            else:
                                if child_structure_node.attribute in self.many_to_many_attributes():
                                    new_child_instance = child_instance.materialize(child_structure_node, processed_instances)
                                    eval("new_instance." + child_structure_node.attribute + ".add(new_child_instance)")
                                else:
                                    new_child_instance = child_instance.materialize(child_structure_node, processed_instances, new_instance)
                else:
                    # not is_many ###############################################################################
                    child_instance = eval("self." + child_structure_node.attribute)
                    new_child_instance = child_instance.materialize(child_structure_node, processed_instances, self)
                    # The child_instance could be a reference so we expect to find it already there
                    setattr(new_instance, child_structure_node.attribute, new_child_instance)
        
        new_instance.save(using='materialized')
        # after saving
        processed_instances.append(new_instance.UKCL)
        # resolve dangling
        drs = DanglingReference.objects.using('materialized').filter(UKCL_actual_instance=new_instance.UKCL)
        for dr in drs:
            try:
                if dr.structure_node.is_many:
                    eval("dr.object_with_dangling." + child_structure_node.attribute + ".add(new_instance)")
                else:
                    setattr(dr.object_with_dangling, dr.structure_node.attribute, new_instance)
                dr.object_with_dangling.save(using='materialized')
                dr.delete()
            except:
                logger.warn("Couldn't resolve a dangling reference from " + dr.UKCL_actual_instance + " to " + dr.object_with_dangling.UKCL)
        return new_instance

    def delete_children(self, structure_node, parent=None):
        '''
        invoked by DataSet.delete_entire_dataset that wraps it in a transaction
        it recursively invokes itself to delete children's children; self is in the 
        materialized database
        
        It is invoked only if DataSet.dataset_structure.multiple_releases = False
        Then I also have to remap foreign keys pointing to it in the materialized DB and
        in default DB
        '''

        # I delete the children; must do it before remapping foreignkeys otherwise some will escape deletion
        for child_structure_node in structure_node.child_nodes.all():
            if not child_structure_node.external_reference:
                if child_structure_node.is_many:
                    child_instances = eval("self." + child_structure_node.attribute + ".all()")
                    for child_instance in child_instances:
                        # let's prevent deleting self; self will be deleted by who has invoked this method 
                        if (child_instance.__class__.__name__ != self.__class__.__name__) or (self.pk != child_structure_node.pk):
                            child_instance.delete_children(child_structure_node, self)
                            child_instance.delete()
                else:
                    # not is_many
                    child_instance = eval("self." + child_structure_node.attribute)
                    child_instance.delete_children(child_structure_node, self)
                    child_instance.delete()
        
        try:
            # before deleting self I must remap foreignkeys pointing at it to the new instances
            # let's get the instance it should point to
            '''
            There could be more than one; imagine the case of an Italian Province split into two of them (Region Sardinia
            had four provinces and then they become 4) then there will be two new instances with the same UKCL_previous_version.
            TODO: we should also take into account the case when a new_materialized_instance can have more than UKCL_previous_version; this
            situation requires redesign of the model and db
            '''
            new_materialized_instances = self.__class__.objects.using('materialized').filter(UKCL_previous_version=self.UKCL)
            new_instances = self.__class__.objects.filter(UKCL_previous_version=self.UKCL)
            self_on_default_db = self.__class__.objects.filter(UKCL=self.UKCL)
            
            assert (len(new_materialized_instances) == len(new_instances)), 'ShareableModel.delete_children self.UKCL="' + self.UKCL + '": "(len(new_materialized_instances ' + str(new_materialized_instances) + ') != len(new_instances' + str(new_instances) + '))"'
            if len(new_materialized_instances) == 1:
                new_materialized_instance = new_materialized_instances[0]
                new_instance = new_instances[0]
                # I NEED TO LIST TODO:ALL THE RELATIONSHIPS POINTING AT THIS MODEL
                for rel_key in self._meta.fields_map.keys():
                    rel = self._meta.fields_map[rel_key]
                    if rel.__class__.__name__ == 'ManyToOneRel':
                        related_name = rel.related_name
                        if related_name is None:
                            related_name = rel_key + "_set"
                        related_materialized_instances_manager = getattr(self, related_name)
                        related_instances_manager = getattr(self_on_default_db, related_name)  #TODO: CHECK self_on_default_db is a QuerySet returned by a .filter !!!!
                        # running      related_materialized_instances_manager.update(rel.field.name=new_materialized_instance)
                        # raises       SyntaxError: keyword can't be an expression
                        # update relationship on the materialized DB
                        eval('related_materialized_instances_manager.update(' + rel.field.name + '=new_materialized_instance)')
                        # update relationship on default DB
                        eval('related_instances_manager.update(' + rel.field.name + '=new_instance)')
            else:
                raise Exception('NOT IMPLEMENTED in ShareableModel.delete_children: mapping between different versions: UKCL "' + self.UKCL + '" has ' + str(len(new_instances)) + ' materialized records that have this as UKCL_previous_version.') 
        except Exception as e:
            logger.error(str(e))

    def navigate_helper_set_dataset(self, instance, status):
        if not 'output' in status.keys():
            status['output'] = {}
        instance.dataset_I_belong_to = status['dataset']
        instance.save()

    @staticmethod
    def model_metadata_from_xml_tag(xml_child_node):
        UKCL = xml_child_node.attributes["URIModelMetadata"].firstChild.data
        try:
            se = ModelMetadata.objects.get(UKCL=UKCL)
        except:
            raise Exception("ERROR model_metadata_from_xml_tag: there is no ModelMetadata corresponding to this URL: " + UKCL)
        return se

    @classmethod
    def retrieve_locally(cls, UKCL):
        '''
        It returns an instance of a ShareableModel stored in this KS
        It searches on the UKCL field
        The caller must catch and handle the exception when it's not found
        '''
        actual_instance = cls.objects.get(UKCL=UKCL)
        return actual_instance

    @staticmethod
    def intersect_list(first, second):
        first_UKCLs = list(i.UKCL for i in first)
        return [item for item in second if item.UKCL in first_UKCLs]
            
    @classmethod
    def create_with_dataset(cls, dss, data_dict, db_alias='default', release=False, ks=None):
        new_instance = cls()
        for key in data_dict.keys():
            setattr(new_instance, key, data_dict[key])
        new_instance.save(using=db_alias)
            
        if not ks:
            ks = KnowledgeServer.this_knowledge_server(db_alias)
        new_dataset = DataSet(description='', knowledge_server=ks, dataset_structure=dss, 
                     root=new_instance, version_major=0, version_minor=1, version_patch=0, version_description="")
        new_dataset.save(using=db_alias)
        if release:
            new_dataset.set_released()
        
        return new_instance

        
        
    class Meta:
        abstract = True



class DanglingReference(ShareableModel):
    '''
    Moving data chunks across OKSs means ending up having external_reference to data that is not available in the same db
    Such references or FK will point to an instance of this class which holds all the info neeeded to resolve the 
    dangling reference; an OKS' admin will be able to instruct the OKS to resolve some reference e.g. all those coming from
    an OKS, all those of a specific type/structure, all those depending on a specific dataset ...
    Importing new data structures will attempt the resolution of existing dangling references
    '''
    UKCL_actual_instance = models.CharField(max_length=750, default='', db_index=True)
    '''
    the structure_node tells us the attribute and whether is_many or not
    '''
    structure_node = models.ForeignKey("StructureNode")
    '''
    We want to group DRs so that we can try to resolve them with not so many API calls to external OKSs
    the only info we have is the UKCL from which we determin the oks_home; we save on a separate column
    to TODO: make an index an more efficient queries
    '''
    oks_home = models.CharField(max_length=255, blank=True)
    object_with_dangling_content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_with_dangling_instance_id = models.PositiveIntegerField(null=True, blank=True)
    object_with_dangling = GenericForeignKey('object_with_dangling_content_type', 'object_with_dangling_instance_id')



class ModelMetadata(ShareableModel):
    '''
    A ModelMetadata roughly contains the meta-data describing a table in a database or a class if we have an ORM
    '''
    # this name corresponds to the class name
    name = models.CharField(max_length=100, db_index=True)
    '''
    The module determines the app/module name containing the class
    describing the model (e.g. the object-relational mapping). A module acts as 
    a namespace that belongs to the organization that created the model (and the 
    ModelMetadata record). Within that namespace the model names are unique. A model 
    License che be in the "licenses" namespace of an OKS but also on the "software"
    namespace of the OKS or on another namespace of another OKS.
    Along with the Organization URL netloc, it is used to create a unique
    name for the app/module so that there can be no collisions. See OrmWrapper
    for more details.
    '''
    '''
    module is Python terminology; app is Django. More generally the module is a group of models,
    shareable models in our case. It is part of the name of the namespace where each model lives.
    It is used to build the UKCL.
    For its use, it is not supposed to change over time.
    '''
    module = models.CharField(max_length=500, db_index=True)
    description = models.CharField(max_length=2000, default="")
    table_name = models.CharField(max_length=255, db_column='tableName', default="")
    id_field = models.CharField(max_length=255, db_column='idField', default="id")
    name_field = models.CharField(max_length=255, db_column='nameField', default="name")
    description_field = models.CharField(max_length=255, db_column='descriptionField', default="description")
    '''
    dataset_structure attribute is not in NORMAL FORM! When not null it tells in which DataSetStructure is this 
    ModelMetadata; a ModelMetadata must be in only one DataSetStructure for version/state purposes! 
    It can be in as many DataSetStructure-views as needed.
    '''
    dataset_structure = models.ForeignKey("DataSetStructure", null=True, blank=True)
    
    def dataset_structures(self, is_shallow=False, is_a_view=False, external_reference=False):
        '''
        returns the list of the structures in which self is present as a node's ModelMetadata
        if only_versioned: skips views and shallow ones and returns at most one 
        '''
        types = []
        nodes = StructureNode.objects.using('materialized').filter(model_metadata=self, external_reference=external_reference)
        try:
            for structure_node in nodes:
                entry_node = structure_node
                visited_nodes_ids = []
                visited_nodes_ids.append(entry_node.id)
                while len(entry_node.parent.all()) > 0:
                    for parent in entry_node.parent.all():
                        if parent.id not in visited_nodes_ids:
                            entry_node = parent
                            visited_nodes_ids.append(entry_node.id)
                            break
                dataset_type = entry_node.dataset_type.all()[0]
                if (not dataset_type in types) and dataset_type.is_shallow == is_shallow and dataset_type.is_a_view == is_a_view:
                    types.append(dataset_type)
        except Exception as ex:
            logger.error("dataset_structures type(self): " + str(type(self)) + " self.id " + str(self.id) + str(ex) + "\ndataset_structures visited_nodes_ids : " + str(visited_nodes_ids))
        return types

    def get_class(self, netloc=""):
        '''
        when creating a dataset structure with root_node.children_for
        the dataset_structure has not a UKCL yet, so it comes as a parameter from this_ks
        '''
        if netloc == "":
            netloc = KsUrl(self.dataset_structure.UKCL).netloc
        return OrmWrapper.load_class(netloc, self.module, self.name)



class StructureNode(ShareableModel):
    model_metadata = models.ForeignKey('ModelMetadata', null=True, blank=True)
    # attribute is blank for the entry point as it is available as dataset.root
    attribute = models.CharField(max_length=255, blank=True)
    # if ct and fk are not '' then it is a GenericForeignKey e.g. I do not 
    # now to which ContentType the fk points to; ct_field tells me which ContentType; 
    # fk tells me the pk value
    # model_metadata is None if it is a GenericForeignKey
    ct_field = models.CharField(max_length=255, default='')
    fk_field = models.CharField(max_length=255, default='')
    '''
       method_to_retrieve is a method that can be invoked to retrieve
       the value of the instance or instances corresponding to this 
       node of the structure. It is an alternative to the attribute,
       they can't be both present.
       Use case: the structure of a SerializableModel(models.Model) <<==>> ModelMetadata
       has a list of fields; there is no need to store them in the database as
       they are *somehow* available using reflection; when we serialize an instance
       of ModelMetadata we use a method of the instance (inherited from SerializableModel) 
       to retrieve the list of fields of the class corresponding to that instance.
    '''
    method_to_retrieve = models.CharField(max_length=255, null=True, blank=True)
    
    # there is only one parent so we should change to 
    child_nodes = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="parent")
    # if not external_reference all attributes are exported, otherwise only the id
    external_reference = models.BooleanField(default=False, db_column='externalReference', db_index=True)
    # is_many is true if the attribute correspond to a list of instances of the ModelMetadata
    is_many = models.BooleanField(default=False, db_column='isMany')

    def navigate(self, instance, instance_method_name, node_method_name, status, children_before):
        # I invoke the method on the instance and recursively on each children
        if instance_method_name:
            instance_method = getattr(instance, instance_method_name)
        if node_method_name:
            node_method = getattr(self, node_method_name)
        if not children_before and instance_method_name:
            instance_method(instance, status)
        if not children_before and node_method_name:
            node_method(self, status)
        # loop on children

        for child_structure_node in self.child_nodes.all():
            # I don't do it to external references, they don't belong to this dataset
            # at the moment I don't do it when attribute is '' as I should use method_to_retrieve
            # to get the child instances and I can't guarantee that they are instances of ShareableModel
            if (not child_structure_node.external_reference) and child_structure_node.attribute:
                if child_structure_node.is_many:
                    child_instances = eval("instance." + child_structure_node.attribute + ".all()")
                    for child_instance in child_instances:
                        # let's prevent infinite loops if self relationships
                        if (child_instance.__class__.__name__ != instance.__class__.__name__) or (instance.pk != child_structure_node.pk):
                            child_structure_node.navigate(child_instance, instance_method_name, node_method_name, status, children_before)
                else:
                    child_instance = eval("instance." + child_structure_node.attribute)
                    if not child_instance is None:
                        child_structure_node.navigate(child_instance, instance_method_name, node_method_name, status, children_before)
            # else there's a method extracting information from other sources (e.g. Fields information from ORM model)
        if children_before and instance_method_name:
            instance_method(instance, status)
        if children_before and node_method_name:
            node_method(self, status)
        
    def navigate_helper_set_datasetstructure(self, instance, status):
        '''
        instance is a StructureNode, I must set its model_metadata.dataset_structure
        on both default and materialized database
        '''
        if not 'output' in status.keys():
            status['output'] = ""
        instance.model_metadata.dataset_structure = status['dataset'].dataset_structure
        instance.model_metadata.save()
        try:
            mm_model_metadata = ModelMetadata.objects.using('materialized').get(UKCL=instance.model_metadata.UKCL)
            # TODO: next query do it just once
            mm_dataset_structure = DataSetStructure.objects.using('materialized').get(UKCL=status['dataset'].dataset_structure.UKCL)
            mm_model_metadata.dataset_structure = mm_dataset_structure
            mm_model_metadata.save()
        except ObjectDoesNotExist:
            # navigate_helper_set_datasetstructure materialized doesn't exist yet; dataset_structure will be set when materializing
            logger.debug("navigate_helper_set_datasetstructure materialized doesn't exist yet; dataset_structure will be set when materializing")
        except Exception as ex:
            logger.error('''            navigate_helper_set_datasetstructure 
                self=%s 
                instance=%s 
                status['dataset']=%s''' % (self.UKCL, instance.UKCL, status['dataset'].UKCL))
            raise ex
    
    def navigate_helper_list_by_type(self, instance, status):
        # if status['output'] is None I create a dictionary whose keys will be 
        # different ModelMetadata and whose values will be list without repetition
        # of instances of the classes corresponding to that ModelMetadata
        if not 'output' in status.keys():
            status['output'] = {}
        if not self.model_metadata in status['output'].keys():
            status['output'][self.model_metadata] = []
        if not instance in status['output'][self.model_metadata]:
            status['output'][self.model_metadata].append(instance)

    def app_models(self, processed_instances={}, ):
        if self in processed_instances.keys():
            return None
        processed_instances[self] = ""
        l = []
        if self.method_to_retrieve == None:
            l = [{"app": self.model_metadata.module, "model": self.model_metadata.name}]
        for child_structure_node in self.child_nodes.all():
            child_app_models = child_structure_node.app_models(processed_instances)
            if child_app_models:
                l += child_app_models
        if len(l) == 0:
            return None
        else:
            return l

    def sn_model_metadata(self, parent = None):
        '''
        A structure node now can handle a GenericForeignKey that means that self.model_metadata
        sometimes is None; when it is a GenericForeignKey then it is always an external reference;
        if it is a GenericForeignKey I can determine the model metadata only when navigating
        an actual DataSet that has this structure; I do it with the parent, the attribute (which 
        can't be None either as the root_node can't be external_reference and can't be a GenericForeignKey)
        
        SE E' UN GENERIC NON POSSO TROVARE IL MODELMETADATA SE NON HO L'ISTANZA  
        '''
        if self.model_metadata is None:
            child = getattr(parent, self.attribute)
            return child.get_model_metadata()
        else:
            return self.model_metadata

    def children_nodes_for( self, attributes, netloc ):
        '''
        '''
        cl = self.model_metadata.get_class(netloc)
        for attribute in attributes:
            attr_field = getattr(cl._meta.model, attribute).field
            class_name = attr_field.opts.object_name
            app_label = attr_field.opts.app_label
            mm = ModelMetadata.objects.get(name=class_name, module=app_label)
            sn = StructureNode()
            sn.model_metadata = mm
            sn.attribute = attribute
            sn.is_many = attr_field.many_to_one or attr_field.many_to_many
            sn.save()
            self.child_nodes.add(sn)
        self.save()


    def children_external_references_nodes_for ( self, attributes, netloc ):
        '''
        '''
        cl = self.model_metadata.get_class(netloc)
        for attribute in attributes:
            attr_field = getattr(cl._meta.model, attribute).field
            class_name = attr_field.related_model().__class__.__name__    #attr_field.opts.object_name
            app_label = attr_field.related_model()._meta.app_label        #attr_field.opts.app_label
            mm = ModelMetadata.objects.get(name=class_name, module=app_label)
            sn = StructureNode()
            sn.model_metadata = mm
            sn.attribute = attribute
            sn.external_reference = True
            sn.is_many = attr_field.many_to_one or attr_field.many_to_many
            sn.save()
            self.child_nodes.add(sn)
        self.save()


class DataSetStructure(ShareableModel):
    # DSN = DataSet Structure Name
    dataset_structure_DSN = "Dataset structure"
    model_metadata_DSN = "Model meta-data"
    organization_DSN = "Organization and Open Knowledge Servers"
    license_DSN = "License"
    '''
    Main idea behind the model: a chunk of knowledge that needs to be shared is not represented 
    with a single class or a single table in a database but it is usually represented using a 
    collection of them related to each other. An Issue in a tracking system has a 
    DataSetStructure with a list of notes that can be appended to it, a user who has created
    it, and many other attributes. The user does not belong just to this DataSetStructure, hence it
    is a reference; the notes do belong to the issue. The idea is to map the set of tables
    in a (relational) database into structures so that a generic operation can work on a 
    generic DataSetStructure, composed with more than one ModelMetadata (that is in 
    more direct correspondence with a database table). A ModelMetadata
    can be in more than one DataSetStructure; because, for instance, we might like to render/...
    .../export/... a subset of the ModelMetadata of a complex entity or filter only those
    that match a specific condition.
    A DataSet has a DataSetStructure; a DataSet has a version (if it is not a view - see DataSet class);
    we want a unique way to know the version and the status of a instance of ModelMetadata. 
    A ModelMetadata must not be in more than DataSetStructure that has a version (not counting
    when it is an external reference). In other words the ModelMetadata used by DataSets with 
    version must partition the E/R diagram of our database in graphs without any intersection. 
     
    Types of DataSetStructures
    versionable  : they are the default, used to define the structure of an DataSet
                   CONSTRAINT: if a ModelMetadata is in one of them it cannot be in another one of them
                   it has version information
    shallow      : created automatically to export a ModelMetadata
                   CONSTRAINT: only one shallow per ModelMetadata 
                   it has NO version information
    view         : used for example to export a structure different from one of the above; 
                   it has NO version information
    
    CHECK: Only versionable and view are listed on the OKS and other systems can subscribe to.
    '''
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000, default='')
    '''
    It is shallow when automatically created to export a ModelMetadata without following any relationship; 
    is_shallow = True means that all foreignKeys and related attributes are external references
    '''
    is_shallow = models.BooleanField(default=False)
    '''
    It is a view if it is not used to determine the structure of a DataSet
    hence it is used for example just to export some data;
    '''
    is_a_view = models.BooleanField(default=False)
    '''
    the entry point of the structure; the class StructureNode has then child_nodes of the same class 
    hence it defines the structure/graph
    assert: the root_node is the entry point for only one structure 
    '''
    root_node = models.ForeignKey('StructureNode', related_name='dataset_type')
    '''
    when multiple_releases is true more than one instance get materialized
    otherwise just one; it defaults to False just not to make it nullable;
    a default is indicated as shallow structures are created without specifying it
    makes no sense when is_a_view
    '''
    multiple_releases = models.BooleanField(default=False)
    
    
    def navigate(self, dataset, instance_method_name, node_method_name, children_before = True):
        '''
        Many methods do things on each node navigating in the structure
        This is a generic method that takes a method as a parameter
        and executes it on the actual instance of each node; the signature of such method must be:
            def generic_structure_node_method(self, instance, status)
        each method can add whatever it wants to the status and set its output to status.output
        the instance_method_name must be a method of ModelMetadata so that it is implemented
        by any instance of any node.
        If children_before the method is invoked on the children first
        '''
        status = {"dataset": dataset}
        if self.is_a_view:
            # I have to do it on all instances that match the dataset criteria
            for instance in dataset.get_instances():
                self.root_node.navigate(instance, instance_method_name, node_method_name, status, children_before)
        else:
            instance = dataset.root
            self.root_node.navigate(instance, instance_method_name, node_method_name, status, children_before)
        return status['output']


    def classes_code(self):
        '''
        '''
        app_models = self.root_node.app_models(processed_instances={})
        code_per_app = {}
        for app_model in app_models:
            netloc = KsUrl(self.UKCL).netloc
            c = OrmWrapper.load_class(netloc, app_model['app'], app_model['model'])
            # I need the list of methods to guarantee I am not injecting code into another OKS
            c_methods  = list({x: c.__dict__[x]} for x in c.__dict__.keys() if inspect.isroutine(c.__dict__[x]))
            # let's exclude instances of ManagerDescriptor from the list
            c_methods  = list(m for m in c_methods if not isinstance(list(m.values())[0], ManagerDescriptor))
            if len(c_methods) > 0:
                raise Exception("Methods found in " + str(app_model) + ": " + str(str(list(m.keys([0] for m in c_methods))) + ". It is unsafe to export class' code to another OKS."))
            if not app_model['app'] in code_per_app.keys():
                code_per_app[app_model['app']] = {}
            if not app_model['model'] in code_per_app[app_model['app']].keys():
                code_per_app[app_model['app']][app_model['model']] = inspect.getsource(c)
        return code_per_app


    def make_persistable(self):
        # If the owner of this structure is not this OKS I must check that I can persist each instance on each node.
        # I loop through all classes and check if they are present locally; if at least 
        # one is not I fetch classes_code via api_dataset_structure_code remotely, then I:
        #  - create the APP/MODULE if needed
        #  - create the needed data-layer classes present in the structure (if not already present here)
        #  - create the migrations
        #  - run the migrations which create the tables on the database
        #  - #########
        # At the moment it works if the model is in a single file as it doesn't manage the imports
        app_models = self.root_node.app_models(processed_instances={})
        persistable = True
        for app_model in app_models:
            try:
                netloc = KsUrl(self.UKCL).netloc
                OrmWrapper.load_class(netloc, app_model['app'], app_model['model'])
            except:
                persistable = False
        if not persistable:
            # I must go to the knowledge_server of the DataSet
            # I wanted to do "DataSet.objects.get(root=self)" but it doesn't work so I had to make it more verbose:
            ds = DataSet.objects.get(root_instance_id=self.id, root_content_type_id=ContentType.objects.get(model='DataSetStructure').id)
            #            ds = DataSet.objects.get(root_instance_id=self.id, root_content_type=ContentType.objects.get_for_model(DataSetStructure._meta.model))
            ar = ApiResponse()
            ar.invoke_oks_api(ds.knowledge_server.url(), 'api_dataset_structure_code', args=(urllib.parse.urlencode({'':self.UKCL})[1:],))
            if ar.status == ApiResponse.success:
                apps_code = ar.content
                for app in apps_code:
                    app_name = OrmWrapper.get_model_container_name(netloc, app)
                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    # is the app missing?
                    logger.debug("make_persistable: is %s in app_config.keys=" % app_name)
                    if not app_name in global_apps.app_configs.keys():
                        logger.debug("make_persistable: %s NOT in app_config.keys=" % app_name)
                        # must add it
                        dmc = DynamicModelContainer(name=app_name)
                        dmc.save()
                        management.call_command('startapp', app_name, 'oks/' + app_name, interactive=False)
                        with open(BASE_DIR + "/" + app_name + "/models.py", "a") as myfile:
                            myfile.write("from knowledge_server.models import ShareableModel\n\n\n\n")
                        settings.INSTALLED_APPS += (app_name, )
                    module = importlib.import_module(app_name + ".models")
                    for model_class in apps_code[app]:
                        # is the class missing?
                        if not hasattr(module, model_class):
                            # must add it
                            with open(BASE_DIR + "/" + app_name + "/models.py", "a") as myfile:
                                myfile.write(apps_code[app][model_class] + "\n\n")
                    # I need to reload the apps as I modified the files
                    global_apps.app_configs = OrderedDict()
                    global_apps.ready = False
                    global_apps.populate(settings.INSTALLED_APPS)
                    # and reload the module
                    importlib.invalidate_caches()
                    module = importlib.reload(module)

                    logger.debug("make_persistable: makemigrations %s " % app_name)
                    # eventually I can generate the migrations for the new app
                    management.call_command('makemigrations', app_name, interactive=False)
                    # and migrate it
                    logger.debug("make_persistable: migrate %s " % app_name)
                    management.call_command('migrate', app_name, interactive=False)                
                    logger.debug("make_persistable: migrate --database=materialized %s " % app_name)
                    management.call_command('migrate', "--database=materialized", app_name, interactive=False)
                persistable = True
            
        return persistable


    def models_and_migration(self):
        '''
        '''
        # Create a list of (app, model) that are in the structure not including external references
        # 
        # navigate structure to populate app_models
        app_models = self.root_node.app_models()
        
        project_state = ProjectState()
        for app_model in app_models:
            model = global_apps.get_model(app_model['app'], app_model['model'])
            model_state = ModelState.from_model(model)
            project_state.add_model(model_state)
            
        autodetector = MigrationAutodetector(ProjectState(), project_state)
        autodetector.generated_operations = {}
        graph = MigrationGraph()
        keep_going = True
        while keep_going:
            try:
                changes = autodetector.changes(graph)
                keep_going = False
            except ValueError as ve:
                pass
  
  
    def root_model_metadata(self, model_metadata):
        '''
        '''
        sn = StructureNode()
        sn.model_metadata = model_metadata
        sn.save()
        self.root_node = sn
        self.save()
    
    
    def create_model_metadata(self, name, module, name_field="", description_field=""):
        """

        Returns:
            ModelMetadata:
        """
        mm=ModelMetadata();
        mm.dataset_structure = self
        mm.name = name
        mm.module = module
        mm.name_field = name_field
        mm.description_field = description_field
        mm.save()
        return mm
        
    @staticmethod
    def get_from_name(model_metadata_name, db_alias='default'):
        materialized = DataSetStructure.objects.using('materialized').get(name=model_metadata_name)
        if db_alias=='default':
            return DataSetStructure.objects.using('default').get(UKCL=materialized.UKCL)
        else:
            return materialized



class DataSet(ShareableModel):
    '''
    A data set / chunk of knowledge; its data structure is described by self.dataset_structure
    The only Versionable object so far
    Serializable like many others 
    It has an owner KS which can be inferred by the UKCL but it is explicitly linked 

    A DataSet is Versionable (if its structure is neither shallow nor a view) so there are many datasets
    that are basically different versions of the same thing; they share the same "first_version" attribute
    
    Relevant methods:
        new version:  create a copy of all instances starting from the root, following the nodes in the   
                      structure, all but those with external_reference=True
        set_released: it sets version_released True and it sets it to False for all the other instances 
                      of the same set; it materializes the dataset
    '''

    '''
    The knowledge server that is making this dataset available; not necessarily the
    organization that owns this knowledge server is the author of the data in the set.
    The Organization that has published the information in this dataset is 
    knowledge_server.organization.
    '''
    knowledge_server = models.ForeignKey("knowledge_server.KnowledgeServer")

    # if the dataset structure is intended to be a view there won't be any version information
    # assert dataset_structure.is_a_view ===> root, version, ... == None
    dataset_structure = models.ForeignKey(DataSetStructure)

    # if it is a view a description might be useful
    description = models.CharField(max_length=2000, default="")
    
    root_content_type = models.ForeignKey(ContentType, null=True, blank=True)
    root_instance_id = models.PositiveIntegerField(null=True, blank=True)
    root = GenericForeignKey('root_content_type', 'root_instance_id')

    # An alternative to the root_node_id is to have a filter to apply to the all the objects 
    # of type root_content_type. Assert:
    #     filter_text != None ===> root == None
    #     root != None ===> filter_text == None
    # If root_node == None filter_text can be "" meaning that you have to take all of the 
    # entries without filtering them
    filter_text = models.CharField(max_length=200, null=True, blank=True)

    # When root is None (hence the structure is a view) I still might want to refer to a version for the 
    # data that will be in my view; there might be data belonging to different versions matching the 
    # criteria in the filter text; to prevent this I specify a DataSet (that has its own version) so 
    # that I will put in the view only those belonging to that version
    filter_dataset = models.ForeignKey('self', null=True, blank=True, related_name="+")
    # NOT USED YET: TODO: it should be used in get_instances

    # a dataset has one or more licenses; the organization that can assign licenses
    # to this dataset is owner_organization; in case of attribution it is the one to be credited
    owner_organization = models.ForeignKey("Organization", null=True, blank=True)
    # creation_date when the owner organization has published the data 
    creation_date = models.DateTimeField(null=True, blank=True)
    # following attributes used to be in a separate class VersionableDataSet
    '''
    An Instance belongs to a set of instances which are basically the same but with a different version.
    first_version is the first instance of this set; first_version has first_version=self so that if I filter 
    for first_version=smthng I get all of them including the first_version
    WE REFER TO SUCH SET AS THE "version set"
    '''
    first_version = models.ForeignKey('self', related_name='versions', null=True, blank=True)
    # http://semver.org/
    version_major = models.IntegerField(null=True, blank=True, db_index=True)
    version_minor = models.IntegerField(null=True, blank=True, db_index=True)
    version_patch = models.IntegerField(null=True, blank=True, db_index=True)
    version_description = models.CharField(max_length=2000, default="")
    # release_date is the date of the release of the dataset; e.g. the date the Creative 
    # Commons Attribution 1.0 license was released
    release_date = models.DateTimeField(auto_now_add=True)
    # version_date is the date this version has been released in the OKS
    version_date = models.DateTimeField(auto_now_add=True)
    '''
    Assert: If self.dataset_structure.multiple_releases==False: at most one instance in the VERSION SET
            has version_released = True
    '''
    version_released = models.BooleanField(default=False, db_index=True)
    '''
        http://www.dcc.ac.uk/resources/how-guides/license-research-data 
        "The option to multiply license a dataset is certainly available to you if you hold all the rights 
        that pertain to the dataset"
    '''
    licenses = models.ManyToManyField("licenses.License")

    @property
    def p_release_date(self):
        return self.release_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    @property
    def p_distributions(self):
        '''
<div property='dcat:distribution' typeof='dcat:Distribution'>
    <span property="dct:title">JSON</span><span content='application/json' property='dcat:mediaType'/> <a href='{link to data}' property='dcat:accessURL'>Download</a>
</div>
        '''
        dist_html = "<ul><li property='dcat:distribution' typeof='dcat:Distribution'>"
        dist_html += "<span content='application/json' property='dcat:mediaType'/> "
        dist_html += "<a href='" + reverse('api_dataset_view', args=(self.q_UKCL,self.root.pk,"JSON")) + "' property='dcat:accessURL'><span property='dct:title'>JSON</span></a>"
        dist_html += "</li>"
        dist_html += "<li property='dcat:distribution' typeof='dcat:Distribution'>"
        dist_html += "<span content='application/xml' property='dcat:mediaType'/> "
        dist_html += "<a href='" + reverse('api_dataset_view', args=(self.q_UKCL,self.root.pk,"XML")) + "' property='dcat:accessURL'><span property='dct:title'>XML</span></a>"
        dist_html += "</li>"
        dist_html += "<li property='dcat:distribution' typeof='dcat:Distribution'>"
        dist_html += "<span content='application/html' property='dcat:mediaType'/> "
        dist_html += "<a href='" + reverse('api_dataset_view', args=(self.q_UKCL,self.root.pk,"HTML")) + "' property='dcat:accessURL'><span property='dct:title'>View it in the browser</span></a>"
        dist_html += "</li></ul>"
        return dist_html
    

    def export(self, export_format='XML', force_external_reference=False):
        '''
        it exports, serializing it, a dataset; starting from the root the serialization is based on the dataset structure
        parameters:
        force_external_reference: if True if will force the root to be serialized like an external reference e.g. only the pk
        '''
        export_format = export_format.upper()
        export_dict = {}
        serialized_head = ''
        comma = ""    

        if export_format == 'XML':
            serialized_head = "<DataSet " + self.serialized_attributes(parent_class=ShareableModel, format=export_format) + " >" + self.serialized_tags(parent_class=ShareableModel)
        if export_format == 'JSON':
            serialized_head = ' { ' + self.serialized_attributes(format=export_format)
            comma = ", "
        if export_format == 'DICT':
            export_dict.update(self.serialized_attributes(format=export_format))

        e_model_metadata = ModelMetadata.objects.get(name="DataSetStructure")
        temp_structure_node = StructureNode(model_metadata=e_model_metadata, external_reference=True, is_many=False, attribute="dataset_structure")
        tmp = self.dataset_structure.serialize(temp_structure_node, exported_instances=[], export_format=export_format)
        if export_format == 'DICT':
            export_dict.update(tmp)
        else:
            serialized_head += comma + tmp
        
        ks_model_metadata = ModelMetadata.objects.get(name="KnowledgeServer")
        temp_structure_node = StructureNode(model_metadata=ks_model_metadata, external_reference=True, is_many=False, attribute="knowledge_server")
        tmp = self.knowledge_server.serialize(temp_structure_node, exported_instances=[], export_format=export_format)
        if export_format == 'DICT':
            export_dict.update(tmp)
        else:
            serialized_head += comma + tmp
        
        
        # UGLY PATCH: I have to add licenses
        # quick and dirty, I export using the shallow and take the licenses from there
        q_and_d = self.serialize(self.shallow_structure().root_node, exported_instances=[], export_format=export_format)
        if export_format == 'DICT':
            export_dict.update({'licenses': q_and_d['DataSet']['licenses']})
        else:
            end_tag="</licenses>"
            serialized_head += comma +q_and_d[q_and_d.find("<licenses>"):q_and_d.find(end_tag)+len(end_tag)] 
        
        if not self.dataset_structure.is_a_view:
            #if it is a view there is no first_version
            ei_model_metadata = ModelMetadata.objects.get(name="DataSet")
            temp_structure_node = StructureNode(model_metadata=ei_model_metadata, external_reference=True, is_many=False, attribute="first_version")
            tmp = self.first_version.serialize(temp_structure_node, exported_instances=[], export_format=export_format)
            if export_format == 'DICT':
                export_dict.update(tmp)
            else:
                serialized_head += comma + tmp

        if force_external_reference:
            self.dataset_structure.root_node.external_reference = True

#         if self.root_instance_id:
        if not self.dataset_structure.is_a_view:
            instance = self.root
            tmp = instance.serialize(self.dataset_structure.root_node, exported_instances=[], export_format=export_format)
            if export_format == 'XML':
                serialized_head += "<ActualInstance>" + tmp + "</ActualInstance>"
            if export_format == 'JSON':
                serialized_head += ', "ActualInstance" : { ' + tmp + " } "
            if export_format == 'DICT':
                export_dict["ActualInstance"] = tmp
        elif self.filter_text:
            instances = self.get_instances()
            if export_format == 'XML':
                serialized_head += "<ActualInstances>"
            if export_format == 'JSON':
                serialized_head += ', "ActualInstances" : [ '
            comma = ""
            instance_list = []
            for instance in instances:
                tmp = instance.serialize(self.dataset_structure.root_node, exported_instances=[], export_format=export_format)
                if export_format == 'XML':
                    serialized_head += "<ActualInstance>" + tmp + "</ActualInstance>"
                if export_format == 'JSON':
                    serialized_head += comma + ' { ' + tmp + " } "
                    comma = ', '
                if export_format == 'DICT':
                    instance_list.append(tmp)
            if export_format == 'XML':
                serialized_head += "</ActualInstances>"
            if export_format == 'JSON':
                serialized_head += ' ] '
            if export_format == 'DICT':
                export_dict["ActualInstances"] = instance_list
        if export_format == 'XML':
            serialized_tail = "</DataSet>"
        if export_format == 'JSON':
            serialized_tail = " }"
        if export_format == 'DICT':
            return export_dict
        else:
            return serialized_head + serialized_tail


    def import_dataset(self, dataset_xml_stream):
        '''
        '''
        # http://stackoverflow.com/questions/3310614/remove-whitespaces-in-xml-string 
        p = etree.XMLParser(remove_blank_text=True)
        elem = etree.XML(dataset_xml_stream, parser=p)
        dataset_xml_stream = etree.tostring(elem)
        xmldoc = minidom.parseString(dataset_xml_stream)
        
        dataset_xml = xmldoc.childNodes[0].childNodes[0]
        tags = [t for t in dataset_xml.getElementsByTagName("dataset_structure") if t in dataset_xml.childNodes]
        DataSetStructureURI = tags[0].attributes["UKCL"].firstChild.data
        # The structure netloc tells me the OKS that created the structure and the models for the nodes
        # so I will pass it to load_class in this method and in from_xml too
        dss_url = KsUrl(DataSetStructureURI)
        structure_netloc = dss_url.netloc

        # the structure is present locally because when I receive a dataset I import the structure before importing the dataset itself
        es = DataSetStructure.retrieve_locally(DataSetStructureURI)
        es.make_persistable()
        self.dataset_structure = es
        
        try:
            with transaction.atomic():
                actual_instances_xml = []
                if es.is_a_view:
                    # I have a list of actual instances
                    tags = [t for t in dataset_xml.getElementsByTagName("ActualInstances") if t in dataset_xml.childNodes]
                    for instance_xml in tags[0].childNodes:
                        actual_instances_xml.append(instance_xml.childNodes[0])
                else:
                    # I create the actual instance
                    tags = [t for t in dataset_xml.getElementsByTagName("ActualInstance") if t in dataset_xml.childNodes]
                    actual_instances_xml.append(tags[0].childNodes[0])
                actual_class = OrmWrapper.load_class(structure_netloc, es.root_node.model_metadata.module, es.root_node.model_metadata.name)
                for actual_instance_xml in actual_instances_xml:
                    # already imported ?
                    actual_instance_UKCL = actual_instance_xml.attributes["UKCL"].firstChild.data
                    try:
                        actual_instance = actual_class.retrieve_locally(actual_instance_UKCL)
                        # it is already in this database; no need to import it again; UKCL is a persistent unique  
                        # identifier so changing the data it identifies would be an error
                    except:  # I didn't find it on this db, no problem
                        actual_instance = actual_class()
                        actual_instance.save_from_xml(structure_netloc, actual_instance_xml, es.root_node)
                        # save_from_xml saves actual_instance on the database
                
                # finished importing the data contained in the dataset
                # let's create the record for the DataSet if not already imported
                dataset_UKCL = dataset_xml.attributes["UKCL"].firstChild.data
                try:
                    dataset_on_db = DataSet.retrieve_locally(dataset_UKCL)
                    logger.warning("DataSet.import_dataset - I am importing a DataSet that is already in this database; it seems it doesn't not make sense; take a look at it: " + dataset_UKCL)
                    if not es.is_a_view:
                        dataset_on_db.root = actual_instance
                        dataset_on_db.save()
                    return dataset_on_db
                except:  # I didn't find it on this db, no problem
                    # In the next call the KnowledgeServer owner of this DataSet must exist
                    # because it was imported while subscribing; it is imported by this very same method
                    # since it is in the actual instance the next method will find it
                    # netloc is "root.beta.thekoa.org" as I am importing a dataset (whose structure is 
                    # owned by root)
                    self.save_from_xml("root.beta.thekoa.org", dataset_xml, self.shallow_structure().root_node)
                    if not es.is_a_view:
                        self.root = actual_instance
                        self.save()
        except Exception as ex:
            logger.error("import_dataset: " + str(ex))
            raise ex
        return self


    def get_instances(self, db_alias='materialized'):
        '''
        Used for views only
        It returns the list of instances matching the filter criteria
        CHECK: default materialized? E' una view e quindi che senso ha andare su default dove ci sono anche le versioni vecchie?
        '''
        mm_model_metadata = self.dataset_structure.root_node.model_metadata
        # The structure netloc tells me the OKS that created the structure and the models for the nodes
        # so I will pass it to load_class in this method and in from_xml too
        dss_url = KsUrl(self.dataset_structure.UKCL)
        structure_netloc = dss_url.netloc
        actual_class = OrmWrapper.load_class(structure_netloc, mm_model_metadata.module, mm_model_metadata.name)
        q = eval("Q(" + self.filter_text + ")")
        return actual_class.objects.using(db_alias).filter(q)

    
    def get_instances_of_a_type(self, se, db_alias='materialized'):
        '''
        starting from the instances matching the filter criteria it returns the list of instances of the se type
        anywhere in the structure 
        '''
        t = self.dataset_structure.navigate(self, "", "navigate_helper_list_by_type")
        if se in t.keys():
            return t[se]
        else:
            return None


    def get_state(self):
        '''
        Three implicit states: working, released, obsolete  
         -  working: the latest version where version_released = False
         -  released: the one with version_released = True
         -  obsolete: all the others
        '''
        if self.version_released:
            return "released"
        version_major__max = self.__class__.objects.all().aggregate(Max('version_major'))['version_major__max']
        if self.version_major == version_major__max:
            version_minor__max = self.__class__.objects.filter(version_major=version_major__max).aggregate(Max('version_minor'))['version_minor__max']
            if self.version_minor == version_minor__max:
                version_patch__max = self.__class__.objects.filter(version_major=version_major__max, version_minor=version_minor__max).aggregate(Max('version_patch'))['version_patch__max']
                if self.version_patch == version_patch__max:
                    return "working"
        return "obsolete"

        
    def set_version(self, version_major=0, version_minor=1, version_patch=0):
        self.version_major = version_major
        self.version_minor = version_minor
        self.version_patch = version_patch


    def new_version(self, version_major=None, version_minor=None, version_patch=None, version_description="", version_date=None):
        '''
        DATABASE: it works only on default database as record go to the materialized one only
                  via the set_released method
        It creates new records for each record in the whole structure excluding external references
        version_released is set to False
        It creates a new DataSet and returns it
        '''

        if version_major == None or version_minor == None or version_patch == None:
            # if the version is not fully specified just version_patch is increased by 1
            version_major = self.version_major
            version_minor = self.version_minor
            version_patch = self.version_patch + 1
        else:
            # it needs to be a greater version number
            message = "Trying to create a new version with an older version number."
            if version_major < self.version_major:
                raise Exception(message)
            else:
                if version_major == self.version_major and version_minor < self.version_minor:
                    raise Exception(message)
                else:
                    if version_major == self.version_major and version_minor == self.version_minor and version_patch < self.version_patch:
                        raise Exception(message)
        try:
            with transaction.atomic():
                instance = self.root.new_version(self.dataset_structure.root_node, processed_instances={})
                new_ds = DataSet()
                new_ds.version_major = version_major
                new_ds.version_minor = version_minor
                new_ds.version_patch = version_patch
                # I am making a new version of a DataSet so I take the ownership
                # If we are not the publishers, we must have checked that derivative works are possible before doing so!
                new_ds.knowledge_server = KnowledgeServer.this_knowledge_server('default')
                # I link the new one with the previous version
                new_ds.UKCL_previous_version = self.UKCL
                new_ds.dataset_structure = self.dataset_structure
                new_ds.first_version = self.first_version
                new_ds.version_description = version_description
                new_ds.root = instance
                if version_date:
                    new_ds.version_date = version_date
                new_ds.save()
                new_ds.set_dataset_on_instances()
        except Exception as e:
            logger.error("new_version: " + str(e))
        return new_ds


    def materialize_dataset(self):
        '''
        if this dataset is a view then I have imported it and need to materialize it with all its instances
        if it is not a view it will have just one instance
        '''
        try:
            if self.dataset_structure.is_a_view:
                instances = self.get_instances(db_alias='default')
            else:
                instances = []
                instances.append(self.root)
            for instance in instances:
                m_existing = instance.__class__.objects.using('materialized').filter(UKCL=instance.UKCL)
                if len(m_existing) == 0:
                    instance.materialize(self.dataset_structure.root_node, processed_instances=[])
            m_existing = DataSet.objects.using('materialized').filter(UKCL=self.UKCL)
            if len(m_existing) == 0:
                self.materialize(self.shallow_structure().root_node, processed_instances=[])
            # end of transaction
        except Exception as ex:
            logger.error("materialize_dataset (" + self.description + "): " + str(ex))
            raise ex


    def set_dataset_on_instances(self):
        self.dataset_structure.navigate(self, "navigate_helper_set_dataset", "")
        

    def set_released(self):
        '''
        Sets this version as the (only) released (one)
        It materializes data and the DataSet itself
        It triggers the generation of events so that subscribers to relevant datasets can get the notification
        '''
        try:
            with transaction.atomic():
                # I set for each instance the "dataset" attribute to this dataset
                # doing so it will be easy to retrieve the dataset in which an instance
                # is contained; useful to retrieve its version, to make the API forgiving, ...
                self.set_dataset_on_instances()
                
                currently_released = None
                previously_released = None
                if not self.dataset_structure.multiple_releases:
                    # There cannot be more than one released? I set the other one to False
                    try:
                        currently_released = self.first_version.versions.get(version_released=True)
                        if currently_released.pk != self.pk:
                            currently_released.version_released = False
                            currently_released.save()
                        previously_released = currently_released
                    except Exception as ex:
                        # there's no other version released
                        pass
                    if previously_released and previously_released.pk == self.pk:
                        # version_released was erroneously set to True before the set_released (TODO: it should be encapsulated in a property)
                        previously_released = None
                # this one is released now
                self.version_released = True
                self.save()
                # MATERIALIZATION Now we must copy newly released self to the materialized database
                # I must check whether it is already materialized so that I don't do it twice
                m_existing = DataSet.objects.using('materialized').filter(UKCL=self.UKCL)
                if len(m_existing) == 0:
                    instance = self.root
                    materialized_instance = instance.materialize(self.dataset_structure.root_node, processed_instances=[])
                    materialized_self = self.materialize(self.shallow_structure().root_node, processed_instances=[])
                    materialized_self.root = materialized_instance
                    materialized_self.save()
                    if not self.dataset_structure.multiple_releases:
                        # if there is only a materialized release I must set first_version to self otherwise deleting the 
                        # previous version will delete this as well
                        materialized_self.first_version = materialized_self
                        materialized_self.save()
                        # now I can delete the old dataset (if any) as I want just one release (multiple_releases == false)
                        if previously_released:
                            materialized_previously_released = DataSet.objects.using('materialized').get(UKCL=previously_released.UKCL)
                            materialized_previously_released.delete_entire_dataset()
                    # materialization is complete; I need to set the dataset on instances
                    # it could not be done before because the materialization of the instances happens before
                    # the materialization of the dataset; if would have generated a dangling reference
                    materialized_self.set_dataset_on_instances()
                    
                    # If I own this DataSet then I create the event for notifications
                    # releasing a dataset that I do not own makes no sense; in fact when I create a new version of
                    # a dataset that has a different owner, the owner is set to this oks
                    this_ks = KnowledgeServer.this_knowledge_server()
                    if self.knowledge_server.UKCL == this_ks.UKCL:
                        # TODO: in the future this task must be run asynchronously
                        e = Event()
                        e.dataset = self
                        e.type = "New version"
                        e.save()
                        '''#157 now I need to generate events for views
                        I shall navigate the release structure
                        Creating a set of lists, one list per each kind of ModelMetadata I encounter
                        Each list contains the instances without repetitions
                        Then for each list I find each DataSetStructure that contains a node of the ModelMetadata
                        For each DataSet with that structure that is a view I test whether at least one of the
                        instances on the list is also in the dataset (also I must check if any is no longer there!)
                        If so I generate the event for that dataset.
                        To check if one is no longer there I must generate the same lists also for previously_released
                        and then compare the lists after applying the criteria of the view

                        '''
                        released_instances_list = self.dataset_structure.navigate(self, "", "navigate_helper_list_by_type")
                        if not self.dataset_structure.multiple_releases:
                            previously_released_instances_list = []
                            if previously_released:
                                previously_released_instances_list = previously_released.dataset_structure.navigate(self, "", "navigate_helper_list_by_type")
                        # I assume the list of keys of the above lists is the same, e.g. the dataset_structure has not changed
                        # keys are ModelMetadata
                        for se in released_instances_list.keys():
                            '''
                            '   if multiple_releases all the newly released instances can affect a view
                            '   else we must compare currently and previously released
                            '   I must create a list of
                            '    - all those that are in current but not in previous
                            '    - all those that are in previous but not in current
                            '    - all those that are in both but have changed 
                                        changed means attribute but TODO:also their relationships!!!
                            '''
                            if not self.dataset_structure.multiple_releases:
                                if previously_released:
                                    #     - all those that are in current but not in previous
                                    current_not_previous = list(i for i in released_instances_list[se] if i.UKCL_previous_version not in list(i.UKCL for i in previously_released_instances_list[se]))
                                    #    - all those that are in previous but not in current
                                    previous_not_current = list(i for i in previously_released_instances_list[se] if i.UKCL not in list(i.UKCL_previous_version for i in released_instances_list[se]))
                                else:
                                    # previously_released is None
                                    #     - all those that are in current but not in previous
                                    current_not_previous = list(i for i in released_instances_list[se])
                                    previous_not_current = []
                                #    - all those that are in both but have changed 
                                current_changed = []
                                previous_changed = []
                                if previously_released:
                                    previous_and_current = list(i for i in previously_released_instances_list[se] if i.UKCL in list(i.UKCL_previous_version for i in released_instances_list[se]))
                                else: # previously_released is None
                                    previous_and_current = []
                                for previous_instance in previous_and_current:
                                    current_instance = list(i for i in released_instances_list[se] if i.UKCL_previous_version == previous_instance.UKCL)[0]
                                    if not ModelMetadata.compare(current_instance, previous_instance):
                                        current_changed.append(current_instance)
                                        previous_changed.append(previous_instance)
                            else:
                                current = released_instances_list[se]
                            # for each simple entity I must find the list of all structures of type view the contain
                            # at least a node of that type;
                            structure_views = se.dataset_structures(is_shallow=False, is_a_view=True, external_reference=False)
                            for sv in structure_views:
                                # for each of them I find all the actual datasets
                                dataset_views = DataSet.objects.filter(dataset_structure = sv)
                                for dv in dataset_views:
                                    # instances of type se within the structure of the dataset
                                    t = dv.get_instances_of_a_type(se)
                                    generate_event = False
                                    if self.dataset_structure.multiple_releases:
                                        generate_event = (len(ModelMetadata.intersect_list(t, current)) > 0)
                                    else:
                                        generate_event = (len(ModelMetadata.intersect_list(t, (current_not_previous + previous_not_current + current_changed + previous_changed))) > 0)
                                    if generate_event:
                                        e = Event()
                                        e.dataset = dv
                                        e.type = "New version"
                                        e.save()
                    # end of transaction
                if isinstance(self.root, DataSetStructure):
                    # now that the DataSetStructure is released we can set each ModelMetadata.dataset_structure
                    # attribute; the method takes care of both default and materialized instances.
                    self.dataset_structure.navigate(self, "", "navigate_helper_set_datasetstructure")
        except Exception as ex:
            logger.error("set_released DataSet " + str(self.pk) + " '" + self.description + "': " + str(ex))
            raise(ex)
    

    def delete_entire_dataset(self):
        '''
        Navigating the structure deletes each record in the entire dataset obviously excluding external references
        Then it deletes self
        '''
        with transaction.atomic():
            self.root.delete_children(self.dataset_structure.root_node)
            self.root.delete()
            self.delete()

        
    def get_latest(self, released=None):
        '''
        gets the latest version starting from any DataSet in the version set
        it can be either released or not if released is None:
        if released == True: the latest released one
        if released == False: the latest unreleased one
        '''
        if released is None:  # I take the latest regardless of the fact that it is released or not
            version_major__max = DataSet.objects.filter(first_version=self.first_version).aggregate(Max('version_major'))['version_major__max']
            version_minor__max = DataSet.objects.filter(first_version=self.first_version, version_major=version_major__max).aggregate(Max('version_minor'))['version_minor__max']
            version_patch__max = DataSet.objects.filter(first_version=self.first_version, version_major=version_major__max, version_minor=version_minor__max).aggregate(Max('version_patch'))['version_patch__max']
        else:  # I filter according to released
            version_major__max = DataSet.objects.filter(version_released=released, first_version=self.first_version).aggregate(Max('version_major'))['version_major__max']
            version_minor__max = DataSet.objects.filter(version_released=released, first_version=self.first_version, version_major=version_major__max).aggregate(Max('version_minor'))['version_minor__max']
            version_patch__max = DataSet.objects.filter(version_released=released, first_version=self.first_version, version_major=version_major__max, version_minor=version_minor__max).aggregate(Max('version_patch'))['version_patch__max']
        return DataSet.objects.get(first_version=self.first_version, version_major=version_major__max, version_minor=version_minor__max, version_patch=version_patch__max)
  
   

class Organization(ShareableModel):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=2000, blank=True)
    website = models.CharField(max_length=500, blank=True)
    logo = models.CharField(max_length=500, blank=True)



class KnowledgeServer(ShareableModel):
    root_apps = ['knowledge_server', 'licenses', 'serializable']
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=2000, blank=True)
    # ASSERT: only one KnowledgeServer in each KS has this_ks = True (in materialized db); I use it to know in which KS I am
    # this is handled when importing data about an external KS
    this_ks = models.BooleanField(default=False)
    # urlparse terminology https://docs.python.org/2/library/urlparse.html
    # scheme e.g. { "http" | "https" }
    scheme = models.CharField(max_length=50, default="http")
    # netloc e.g. "root.thekoa.org"
    netloc = models.CharField(max_length=200)
    #  html_home text that gets displayed at the home page
    html_home = models.CharField(max_length=4000, default="")
    #  html_disclaimer text that gets displayed at the disclaimer page
    html_disclaimer = models.CharField(max_length=4000, default="")
    #  html_* can include html tags
    organization = models.ForeignKey(Organization)

    def url(self, encode=False):
        # "http://root.beta.thekoa.org/"
        tmp_url = self.scheme + "://" + self.netloc
        if encode:
            tmp_url = urllib.parse.urlencode({'':tmp_url})[1:]
        return tmp_url
    
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
                    root_ei = DataSet.objects.get(UKCL=sub.first_version_UKCL)
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
                message += "process_events, subscriptions error: " + str(e)
                logger.error("process_events, subscriptions error: " + str(e))
            
        # events
        events = Event.objects.filter(processed=False, type="New version")
        message += "Found " + str(len(events)) + " events<br>"
        for event in events:
            subs = SubscriptionToThis.objects.filter(first_version_UKCL=event.dataset.first_version.UKCL)
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
                message += "process_events, events error: " + str(e)
                logger.error("process_events, events error: " + str(e))
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
                message += "send_notifications, found a notification for UKCL " + notification.event.dataset.UKCL + "<br>"
                message += "about to notify " + notification.remote_url + "<br>"
                m_es = DataSetStructure.objects.using('materialized').get(name=DataSetStructure.dataset_structure_DSN)
                es = DataSetStructure.objects.using('default').get(UKCL=m_es.UKCL)
                this_es = DataSetStructure.objects.get(UKCL=notification.event.dataset.dataset_structure.UKCL)
                ei_of_this_es = DataSet.objects.get(root_instance_id=this_es.id, dataset_structure=es)
                values = { 'first_version_UKCL' : notification.event.dataset.first_version.UKCL,
                           'URL_dataset' : this_ks.url() + reverse('api_dataset', args=(urllib.parse.urlencode({'':notification.event.dataset.UKCL})[1:], "XML",)),
                           'URL_structure' : this_ks.url() + reverse('api_dataset', args=(urllib.parse.urlencode({'':ei_of_this_es.UKCL})[1:], "XML",)),
                           'type' : notification.event.type,
                           'timestamp' : notification.event.timestamp, }
                data = urllib.parse.urlencode(values)
                binary_data = data.encode('utf-8')
                req = Request(notification.remote_url, binary_data)
                response = urlopen(req)
                ar = ApiResponse()
                ar.parse(response.read().decode("utf-8"))
                if ar.status == ApiResponse.success:
                    notification.sent = True
                    notification.save()
                else:
                    # TODO: set some numeric error codes in APIResponse and if not subscribed delete subscription
                    message += "send_notifications " + notification.remote_url + " responded: " + ar.message + "<br>"
        except Exception as e:
            message += "send_notifications error: " + str(e)
            logger.error("send_notifications error: " + str(e))
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
                    '''
                    **********************************************************************************
                    **************************DATASET*STRUCTURE***************************************
                    **********************************************************************************
                    '''
                    # Let's retrieve the structure
                    response = urlopen(notification.URL_structure)
                    structure_xml_stream = response.read()
                    
                    # Before importing the DataSet of the structure we must import all
                    # the datasets of the ModelMetadata within the structure
                    # otherwise we might get Dangling references
                    
                    # so we parse structure_xml_stream searching for all tags <model_metadata
                    # http://stackoverflow.com/questions/3310614/remove-whitespaces-in-xml-string 
                    p = etree.XMLParser(remove_blank_text=True)
                    elem = etree.XML(structure_xml_stream, parser=p)
                    dataset_xml_stream = etree.tostring(elem)
                    xmldoc = minidom.parseString(dataset_xml_stream)
                    model_metadata_tags = xmldoc.getElementsByTagName("model_metadata")
                    model_metadata_URIs = []
                    for mmt in model_metadata_tags:
                        model_metadata_URIs.append(mmt.attributes["UKCL"].firstChild.data)
                    # let's make it unique
                    model_metadata_URIs = list(set(model_metadata_URIs))
                    # and we loop through the ModelMetadata
                    for mmu in model_metadata_URIs:
                        try:
                            ModelMetadata.retrieve_locally(mmu)
                        except:
                            # if it is not in local db we import it; I rely on the forgiveness of api_dataset
                            url_to_invoke = KsUrl(mmu).home() + reverse('api_dataset', args=(urllib.parse.urlencode({'':mmu})[1:], "XML",))
                            response = urlopen(url_to_invoke)
                            mm_xml_stream = response.read()
                            mm_dataset = DataSet()
                            mm_dataset = mm_dataset.import_dataset(mm_xml_stream)
                            mm_dataset.materialize_dataset()
                    ds_structure = DataSet()
                    ds_structure = ds_structure.import_dataset(structure_xml_stream)
                    ds_structure.dataset_structure = DataSetStructure.objects.get(name=DataSetStructure.dataset_structure_DSN)
                    ds_structure.materialize_dataset()

                    '''
                    **********************************************************************************
                    **************************DATASET*************************************************
                    **********************************************************************************
                    '''
                    # the dataset is retrieved with api #36 api_dataset that serializes
                    # the DataSet and also the complete actual instance 
                    # import_dataset will create the DataSet and the actual instance
                    response = urlopen(notification.URL_dataset)
                    dataset_xml_stream = response.read()
                    actual_dataset = DataSet()
                    actual_dataset = actual_dataset.import_dataset(dataset_xml_stream)
                    actual_dataset.dataset_structure = ds_structure.root
                    actual_dataset.materialize_dataset()
                    notification.processed = True
                    notification.save()
            except Exception as ex:
                message += "process_received_notifications error: " + str(ex)
                logger.error("process_received_notifications error: " + str(ex))
        return message + "<br>"
        
    def set_as_this_ks(self):
        '''
        Invoked on a KnowledgeServer with this_ks set to False
        It sets it to True on both default and materialized and set it to False to the one that had it set to True
        '''
        try:
            m_this_ks = KnowledgeServer.this_knowledge_server('materialized')
            d_this_ks = KnowledgeServer.this_knowledge_server('default')
            m_this_ks.this_ks = False
            m_this_ks.save()
            d_this_ks.this_ks = False
            d_this_ks.save()
        except Exception as ex:
            '''
            When creating a new dataset for the organization that contains this_ks
            I have to set this_ks to False right after new_version; when releasing
            the new version is copied to the materialized database and the old version
            is deleted; we are left without this_ks in the materialized for (hopefully)
            a short while e.g. until this method is executed. Hence if I don't find
            this_ks on the db it is no problem; I will have it again in a minute.
            '''
            logger.info("set_as_this_ks: " + str(ex))
        
        m_self = KnowledgeServer.objects.using('materialized').get(UKCL=self.UKCL)
        d_self = KnowledgeServer.objects.using('default').get(UKCL=self.UKCL)
        m_self.this_ks = True
        m_self.save()
        # now I am ready to generate UKCL with the new KS scheme and netloc
        # so I trigger the regeneration on the existing record
        m_self.UKCL = ""
        m_self.save()
        d_self.this_ks = True
        d_self.UKCL = ""
        d_self.save()
      
    @staticmethod
    def this_knowledge_server(db_alias='materialized'):
        '''
        *** method that works BY DEFAULT on the materialized database ***
        *** the reason being that only there "get(this_ks = True)" is ***
        *** guaranteed to return exactly one record                   ***
        when working on the default database we must first fetch it on the
        materialized; then, using the UKCL we search it on the default
        because the UKCL will be unique there
        '''
        materialized_ks = KnowledgeServer.objects.using('materialized').get(this_ks=True)
        if db_alias == 'default':
            return KnowledgeServer.objects.using('default').get(UKCL=materialized_ks.UKCL)
        else:
            return materialized_ks

    @staticmethod
    def get_remote_ks(remote_url):
        '''
        I get the domain from the remote_url which can be anything like 
            http://lisences.thekoa.org
        or
            http://lisences.thekoa.org/knowledge_server/DataSet/17
        it tries to invoke api_ks_info from the remote_ks 
        if it gets the info it imports the dataset locally and returns the corresponding KnowledgeServer object
        otherwise it might be a different system and it returns None
        '''
        remote_ks = None
        try:
            local_url = reverse('api_ks_info', args=("XML",))
            response = urlopen(KsUrl(remote_url).home() + local_url)
            ks_info_xml_stream = response.read()
            # import_dataset creates the entity instance and the actual instance
            ei = DataSet()
            local_ei = ei.import_dataset(ks_info_xml_stream)
            # I have imported a KnowledgeServer with this_ks = True; must set it to False (see this_knowledge_server())
            external_org = local_ei.root
            for ks in external_org.knowledgeserver_set.all():
                if ks.this_ks:
                    remote_ks = ks
                    ks.this_ks = False
                    ks.save()
            # Now I can materialize it; I can use set released as I have certainly retrieved a released DataSet
            local_ei.set_released()
        except Exception as ex:
            logger.error("get_remote_ks: " + str(ex))
            raise ex
        
        return remote_ks

    @staticmethod
    def create_this_ks(org_ks):
        '''
        org_ks is a dictionary with main fields for Organization and KnowledgeServer
        It is intended to make it easy to initialize a new KS juts providing the dictionary
        This method is better invoked in a migration which is processed before any new dataset or 
        any new instance of any class that inherits from ShareableModel is created.
        
        create_this_ks takes care of creating the Organization and the KnowledgeServer,
        the relevant DataSet which is then released. After this method data and dataset
        can be safely created and released. The Organization and the KnowledgeServer
        hereby created will own all newly created data. Invoking this method more than
        once in the lifetime of an instance of OKS does not make sense.
        If Organization is not in the dictionary, the existing one of current OKS is 
        used (e.g. TheKoa.org)  
        '''
        if "Organization" in org_ks.keys():
            new_org = Organization()
            new_org.name = org_ks["Organization"]["name"]
            new_org.website = org_ks["Organization"]["website"]
            new_org.description = org_ks["Organization"]["description"]
            new_org.save()
        else:
            this_ks = KnowledgeServer.this_knowledge_server('default')
            ds = this_ks.dataset_I_belong_to.new_version()
            ''' This is a very special dataset as it includes this_knowledge_server
                now we have two KnowledgeServer instances with this_ks = True
                before materializing it (via set_released) I must set the flag
                to False; I do it now
            ''' 
            old_this_ks = ds.root.knowledgeserver_set.filter(this_ks = True)[0]
            old_this_ks.this_ks = False
            old_this_ks.save()
            new_org = ds.root
        new_ks = KnowledgeServer()
        new_ks.name = org_ks["KnowledgeServer"]["name"]
        if "scheme" in org_ks["KnowledgeServer"].keys():
            new_ks.scheme = org_ks["KnowledgeServer"]["scheme"]
        new_ks.netloc = org_ks["KnowledgeServer"]["netloc"]
        new_ks.description = org_ks["KnowledgeServer"]["description"]
        new_ks.organization = new_org
        new_ks.save()
        
        if "Organization" in org_ks.keys():
            dss_org = DataSetStructure.get_from_name(DataSetStructure.organization_DSN)
            ds = DataSet(description='', knowledge_server=new_ks, dataset_structure=dss_org, 
                         root=new_org, version_major=0, version_minor=1, version_patch=0, version_description="")
            ds.save()
        ds.set_released()
        
        new_ks.set_as_this_ks()
        if "Organization" in org_ks.keys():
            new_org.regenerate_UKCL()
        new_ks = KnowledgeServer.this_knowledge_server('default')
        ds.regenerate_UKCL()
        return KnowledgeServer.this_knowledge_server()
        
    @staticmethod
    def register_models(model_metadata_list):
        '''
        It registers models for this_ks
        '''
        this_ks = KnowledgeServer.this_knowledge_server('default')
        dssModelMetadataFields=DataSetStructure.get_from_name(DataSetStructure.model_metadata_DSN)
        for mm in model_metadata_list:
            ds = DataSet(knowledge_server=this_ks,dataset_structure=dssModelMetadataFields,root = mm,
                         description=mm.name + " ModelMetadata",version_major=0,version_minor=1,version_patch=0,version_description="Initial, automatically created.")
            ds.save();ds.set_released(); 

                    

class Event(ShareableModel):
    '''
    Something that has happened to a specific instance and you want to get notified about; 
    so you can subscribe to a type of event for a specific data set / DataSet
    '''
    # The DataSet
    dataset = models.ForeignKey(DataSet)
    # the event type
    type = models.CharField(max_length=50, default="New version", db_index=True)
    # when it was fired
    timestamp = models.DateTimeField(auto_now_add=True)
    # if all notifications have been prepared e.g. relevant Notification instances are saved
    processed = models.BooleanField(default=False, db_index=True)



class SubscriptionToThis(ShareableModel):
    '''
    The subscriptions other systems do to my data
    '''
    first_version_UKCL = models.CharField(default='', max_length=750, db_index=True)
    # where to send the notification; remote_url, in the case of a KS, will be something like http://root.beta.thekoa.org/notify
    # the actual notification will have the UKCL of the DataSet and the UKCL of the EventType
    remote_url = models.CharField(max_length=200)
    # I send a first notification that can be used to get the data the first time
    first_notification_prepared = models.BooleanField(default=False, db_index=True)
    # when I get a subscription I try to see whether on the other side there is a KnowledgeServer correctly responding to api/ks_info
    remote_ks = models.ForeignKey(KnowledgeServer, null=True, blank=True)



class Notification(ShareableModel):
    '''
    When an event happens for an instance, for each corresponding subscription
    I create a  Notification; cron will send it and change its status to sent
    '''
    event = models.ForeignKey(Event)
    sent = models.BooleanField(default=False, db_index=True)
    remote_url = models.CharField(max_length=200)



class SubscriptionToOther(ShareableModel):
    '''
    The subscriptions I make to other systems' data
    '''
    # The UKCL I am subscribing to 
    URL = models.CharField(max_length=200)
    first_version_UKCL = models.CharField(max_length=200, db_index=True)



class NotificationReceived(ShareableModel):
    '''
    When I receive a notification it is stored here and processed asynchronously in cron 
    '''
    # URL to fetch the new data
    URL_dataset = models.CharField(max_length=200)
    URL_structure = models.CharField(max_length=200)
    processed = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    

    
class ApiResponse():
    '''
    
    '''
    success = "success"
    failure = "failure"
    
    def __init__(self, status="", message="", content="", datetime_generated_utc=datetime.utcnow()): #, deprecated=False, deprecation_message=""):
        self.status = status
        self.message = message
        self.content = content
        self.response = ""
        self.datetime_generated_utc = datetime_generated_utc
#         self.deprecation_message = deprecation_message
#         self.deprecated = deprecated
    
    def urlopen(self, remote_url):
        response = urlopen(remote_url)
        self.response = response.read().decode("utf-8")
        self.parse(self.response)
        
    def invoke_oks_api(self, oks, api, args):
        oks_url = KsUrl(oks)
        local_url = reverse(api, args=args)
        self.urlopen(oks_url.home() + local_url)
        
    def xml(self, prettyfy = False):
        exported_xml = "<Export ExportDateTime=\"" + self.datetime_generated_utc.isoformat() + "\" Status=\"" + self.status + "\" Message=\"" + self.message + "\">" + self.content + "</Export>"
        if prettyfy:
            xmldoc = minidom.parseString(exported_xml)
            return xmldoc.toprettyxml(indent="    ")
        else:
            return exported_xml

    def json(self):
#         if self.deprecated:
#             ret_str +=  '", "deprecated" : "' + self.deprecation_message
        return json.dumps({"status" : self.status, "message" : self.message, "datetime_generated_utc" : self.datetime_generated_utc.isoformat(), "content" : self.content}, sort_keys=False, default=json_serial)
    
    def parse(self, json_response):
        self.response = json_response
        decoded = json.loads(self.response)
        self.status = decoded['status']
        self.message = decoded['message']
        self.content = decoded['content']
#         if "deprecated" in decoded:
#             self.deprecated = True
#             self.deprecation_message = decoded['deprecation_message']


def json_serial(obj):
    """
        JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")


        
class ExternalReferenceNotFoundOnMaterialized(Exception):
    """While materializing an external reference was not found, we must create 
       a DanglingReference so that we can fix it when it comes"""
    pass



class DynamicModelContainer(SerializableModel):
    '''
    Some apps/modules/model containers
    are imported from other OKSs; we need a list of them so that 
    we can load them dynamically using 
    django.core.signals.request_started 
    '''
    name = models.CharField(max_length=500)
    