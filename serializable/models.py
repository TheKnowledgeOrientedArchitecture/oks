# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.db import models

class SerializableModel(models.Model):
    classes_serialized_as_tags = ["CharField"]

    def foreign_key_attributes(self): 
        attributes = []
        for key in self._meta.fields:
            if key.__class__.__name__ == "ForeignKey":
                attributes.append(key.name)
        return attributes
                
    def related_manager_attributes(self): 
        attributes = ""
        for key in self._meta.fields:
            if key.__class__.__name__ == "RelatedManager":
                attributes += ' ' + key.name + '="' + str(getattr(self, key.name)) + '"'
        return attributes
                
    def many_related_manager_attributes(self): 
        attributes = ""
        for key in self._meta.fields:
            if key.__class__.__name__ == "ManyRelatedManager":
                attributes += ' ' + key.name + '="' + str(getattr(self, key.name)) + '"'
        return attributes
     
    def serialized_tags(self, parent_class=None):
        '''
        invoked only for XML
        we serialize using tags instead of attributes so that we can add CDATA and have any content in strings
            <KnowledgeServer .....    html_home="<strong>Welcome!</strong>" .... />  wouldn't work
        will do this instead:
            <KnowledgeServer .....  > ....   <html_home><![CDATA[<strong>Welcome!</strong>]]></html_home>  ... </KnowledgeServer>
        
        ###########################################################################
        Current policy is to have CharField as tags; see classes_serialized_as_tags
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
                if key.__class__.__name__ in SerializableModel.classes_serialized_as_tags and (not key.name in parent_class_attributes):
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
                    value = ""
                if format == 'XML':
                    # if it is an instance of a class that has to be serialized as tags I do not serialize it
                    # as attribute unless it is an attribute of the parent_class ( that is a normally 
                    # ShareableModel class whose attributes should not contain characters that need to be
                    # put into CDATA tags ) 
                    if (not key.__class__.__name__ in SerializableModel.classes_serialized_as_tags) or key.name in parent_class_attributes:
                        attributes += ' ' + key.name + '="' + str(value) + '"'  
                if format == 'JSON':
                    attributes += comma + '"' + key.name + '" : "' + str(value) + '"'
                    comma = ", "
                if format == 'DICT':
                    tmp_dict[key.name] = value
                if format == 'HTML':
                    attributes += comma + '"' + key.name + '" : "' + str(value) + '"'
                    comma = "<br>"
        if format == 'DICT':
            return tmp_dict
        else:
            return attributes

    def SetNotNullFields(self):
        '''
        I need to make sure that every SerializableModel can be saved on the database right after being created (*)
        hence I need to give a value to any attribute that can't be null
        (*) It's needed because during the import I can find a reference to an instance whose data is further away in the file
        then I create the instance in the DB just with the URIInstance but no other data
        '''
        for key in self._meta.fields:
            if (not key.null) and key.__class__.__name__ != "ForeignKey" and (not key.primary_key):
                if key.__class__.__name__ in ("CharField", "TextField"):
                    if key.blank:
                        setattr(self, key.name, "")
                    else:
                        setattr(self, key.name, "dummy")
                if key.__class__.__name__ in ("IntegerField", "FloatField"):
                    setattr(self, key.name, 0)
                if key.__class__.__name__ in ("DateField", "DateTimeField"):
                    setattr(self, key.name, datetime.now())
                
    @staticmethod
    def compare(first, second):
        return first.serialized_attributes(format='JSON') == second.serialized_attributes(format='JSON')

    @staticmethod
    def get_parent_field_name(parent, attribute):
        '''
        TODO: describe *ObjectsDescriptor or link to docs
              make sure it is complete (e.g. we are not missing any other *ObjectsDescriptor)
        '''
        field_name = ""
        related_parent = getattr(parent._meta.concrete_model, attribute)
        if related_parent.__class__.__name__ == "ForeignRelatedObjectsDescriptor":
            field_name = related_parent.related.field.name
        if related_parent.__class__.__name__ == "ReverseSingleRelatedObjectDescriptor":
            field_name = related_parent.field.name
        return field_name

    
    # Add a method to list all the relationships pointing at this model; find the comment below in delete_children
    # I NEED TO LIST TODO:ALL THE RELATIONSHIPS POINTING AT THIS MODEL

    class Meta:
        abstract = True

