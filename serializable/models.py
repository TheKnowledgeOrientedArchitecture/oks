# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

import logging
from datetime import datetime

from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, ManyToManyDescriptor


logger = logging.getLogger(__name__)

class SerializableModel(models.Model):
    types_serialized_as_tags = ["CharField"]
    is_a_placeholder = models.BooleanField(default=False, db_column='oks_internals_placeholder', db_index=True)

    def generic_content_types_attributes(self):
        '''
        see documentation for GenericForeignKey
        ''' 
        attributes = []
        for key in self._meta.virtual_fields:
            attributes.append(key.ct_field)
        return attributes
                
    def generic_foreign_key_attributes(self):
        '''
        see documentation for GenericForeignKey
        ''' 
        attributes = []
        for key in self._meta.virtual_fields:
            attributes.append((key.name, key.ct_field, key.fk_field))
        return attributes
                
    def foreign_key_attributes(self): 
        attributes = []
        # I must exclude each generic content types for GenericForeignKey
        generic = self.generic_content_types_attributes()
        for key in self._meta.fields:
            if key.__class__.__name__ == "ForeignKey" and (not key.name in generic):
                attributes.append(key.name)
        return attributes
                
    def many_to_many_attributes(self): 
        attributes = []
        for key in self._meta.many_to_many:
            if key.__class__.__name__ == "ManyToManyField":
                attributes.append(key.name)
        return attributes
                
    def virtual_field_attributes(self): 
        '''
        see documentation for GenericForeignKey
        ''' 
        attributes = []
        for key in self._meta.virtual_fields:
                attributes.append(key.name)
        return attributes
                
    def serialized_tags(self, parent_class=None):
        '''
        invoked only for XML
        we serialize using tags instead of attributes so that we can add CDATA and have any content in strings
            <KnowledgeServer .....    html_home="<strong>Welcome!</strong>" .... />  wouldn't work
        will do this instead:
            <KnowledgeServer .....  > ....   <html_home><![CDATA[<strong>Welcome!</strong>]]></html_home>  ... </KnowledgeServer>
        
        ###########################################################################
        Current policy is to have CharField as tags; see types_serialized_as_tags
        ###########################################################################
        '''
        attributes = ""
        parent_class_attributes = []
        if parent_class:
            parent_class_attributes = list(key.name for key in parent_class._meta.fields)
        
        for key in self._meta.fields: 
            if key.__class__.__name__ != "ForeignKey":
                value = getattr(self, key.name)
                if value is None:
                    value = ""
                # if it is an instance of a class that has to be serialized as tags and it is not an 
                # attribute of the parent_class I serialize it as a tag with CDATA
                if key.__class__.__name__ in SerializableModel.types_serialized_as_tags and (not key.name in parent_class_attributes):
                    attributes += '<' + key.name + '><![CDATA[' + str(value) + ']]></' + key.name + '>'
        return attributes
    
    def serialized_attributes(self, parent_class=None, format='XML'):
        '''
        parent_class is used only if format is XML; see comment above on serialized_tags
        parent_class is the parent class of the object being serialized; it is a class
        with standard attributes that do not need to be serialized as tags
        Currently parent_class is always ShareableModel
        '''
        attributes = ""
        comma = ""
        tmp_dict = {}
        parent_class_attributes = []
        if parent_class:
            parent_class_attributes = list(key.name for key in parent_class._meta.fields)
        
        for key in self._meta.fields: 
            if key.__class__.__name__ != "ForeignKey":
                value = getattr(self, key.name)
                if value is None:
                    pass # I do not export an attribute that can be None/null
                elif format == 'XML':
                    # if it is an instance of a class that has to be serialized as tags I do not serialize it
                    # as attribute unless it is an attribute of the parent_class ( that is a normally 
                    # ShareableModel class whose attributes should not contain characters that need to be
                    # put into CDATA tags ) 
                    if (not key.__class__.__name__ in SerializableModel.types_serialized_as_tags) or key.name in parent_class_attributes:
                        attributes += ' ' + key.name + '="' + str(value) + '"'  
                elif format == 'JSON':
                    attributes += comma + '"' + key.name + '" : "' + str(value) + '"'
                    comma = ", "
                elif format == 'DICT':
                    tmp_dict[key.name] = value
                elif format == 'HTML':
                    attributes += comma + key.name + ' : "' + str(value) + '"'
                    comma = "<br>"
        if format == 'DICT':
            return tmp_dict
        else:
            return attributes

    def SetNotNullFields(self, db_alias=''):
        '''
        I need to make sure that every SerializableModel can be saved on the database right after being created (*)
        hence I need to give a value to any attribute that can't be null
        (*) It's needed because during the import I can find a reference to an instance whose data is further away in the file
        then I create the instance in the DB just with the UKCL but no other data
        Sometimes self._state.db is not set as self is not saved yet; then I must have db_alias passed explicitly
        '''
        if db_alias == '':
            db_alias = self._state.db
        for key in self._meta.fields:
            if  (not key.null) and key.__class__.__name__ != "ForeignKey" and (not key.primary_key):
                if (not getattr(self, key.name)):
                    if key.default in {None, NOT_PROVIDED}:
                        if key.__class__.__name__ in ("CharField", "TextField"):
                            if key.blank:
                                setattr(self, key.name, "")
                            else:
                                setattr(self, key.name, "dummy")
                        elif key.__class__.__name__ in ("IntegerField", "FloatField"):
                            setattr(self, key.name, 0)
                        elif key.__class__.__name__ in ("DateField", "DateTimeField"):
                            setattr(self, key.name, datetime.now())
                        else:
                            logger.warning("SetNotNullFields %s %s" % (key.name, key.__class__))
                            setattr(self, key.name, key.__class__())
            if (not key.null) and key.__class__.__name__ == "ForeignKey" and (not key.primary_key):
                try:
                    getattr(self, key.name)
                except:
                    setattr(self, key.name, key.related_model.placeholder(db_alias))
            
    @classmethod
    def placeholder(cls, db_alias):
        ps = cls.objects.using(db_alias).filter(is_a_placeholder=True)
        if len(ps.all()) == 0:
            p = cls()
            p.SetNotNullFields(db_alias)
            p.save(using=db_alias)
            return p
        else:
            return ps.all()[0]

    @staticmethod
    def compare(first, second):
        return first.serialized_attributes(format='JSON') == second.serialized_attributes(format='JSON')

    @staticmethod
    def get_parent_field_name(parent, attribute):
        '''
        TODO: describe *Descriptor or link to docs
              make sure it is complete (e.g. we are not missing any other *Descriptor)
        '''
        related_parent = getattr(parent._meta.concrete_model, attribute)
        # ManyToManyDescriptor must be before ReverseManyToOneDescriptor because:
        # class ManyToManyDescriptor(ReverseManyToOneDescriptor):
        if isinstance(related_parent, ManyToManyDescriptor):
            return ""
        if isinstance(related_parent, ReverseManyToOneDescriptor):
            return related_parent.field.name
        msg="###############################################Error get_parent_field_name, parent: " + parent.__class__.__name__ + " " + str(parent.id) + ", attribute:\"" + attribute + '" ###########################################################' 
        logger.critical(msg)
        raise Exception(msg)


    # TODO: Add a method to list all the relationships pointing at this model; find the comment below in delete_children
    # I NEED TO LIST TODO:ALL THE RELATIONSHIPS POINTING AT THIS MODEL

    class Meta:
        abstract = True

