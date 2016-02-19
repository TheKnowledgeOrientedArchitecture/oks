# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.apps.registry import apps
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.db.migrations import operations
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.migration import Migration
from django.db.migrations.state import ModelState, ProjectState


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
                    attributes += comma + key.name + ' : "' + str(value) + '"'
                    comma = "<br>"
        if format == 'DICT':
            return tmp_dict
        else:
            return attributes

    def orm_metadata(self, export_format):
        '''
        
        '''
        model = apps.get_model(self.module, self.name)
        model_opts = model._meta
        old_project_state = ProjectState()
        new_project_state = ProjectState()
#         new_project_state.add_model(model)
        autodetector = MigrationAutodetector(old_project_state, new_project_state)
        autodetector.generated_operations = {}

        # code from MigrationAutodetector.generate_created_models
        # Gather related fields
        related_fields = {}
        primary_key_rel = None
        for field in model_opts.local_fields:
            if field.rel:
                if field.rel.to:
                    if field.primary_key:
                        primary_key_rel = field.rel.to
                    elif not field.rel.parent_link:
                        related_fields[field.name] = field
                # through will be none on M2Ms on swapped-out models;
                # we can treat lack of through as auto_created=True, though.
                if getattr(field.rel, "through", None) and not field.rel.through._meta.auto_created:
                    related_fields[field.name] = field
        for field in model_opts.local_many_to_many:
            if field.rel.to:
                related_fields[field.name] = field
            if getattr(field.rel, "through", None) and not field.rel.through._meta.auto_created:
                related_fields[field.name] = field
        # Are there unique/index_together to defer?
#         unique_together = model_state.options.pop('unique_together', None)
#         index_together = model_state.options.pop('index_together', None)
#         order_with_respect_to = model_state.options.pop('order_with_respect_to', None)
        # Depend on the deletion of any possible proxy version of us
        dependencies = [
            (self.module, self.name, None, False),
        ]
        # Depend on all bases
#         for base in model_state.bases:
#             if isinstance(base, six.string_types) and "." in base:
#                 base_app_label, base_name = base.split(".", 1)
#                 dependencies.append((base_app_label, base_name, None, True))
        # Depend on the other end of the primary key if it's a relation
        if primary_key_rel:
            dependencies.append((
                primary_key_rel._meta.app_label,
                primary_key_rel._meta.object_name,
                None,
                True
            ))
        # Generate creation operation
        autodetector.add_operation(
            self.module,
            operations.CreateModel(
                name=self.name,
                fields=[d for d in model_opts.fields if d not in related_fields.values()],
                options=model_opts,
                bases=self.__class__.__bases__,
                managers=model_opts.managers,
            ),
            dependencies=dependencies,
            beginning=True,
        )
     
        # autodetector.generated_operations
        metadata = None
        fields = []
        if export_format == 'XML':
            metadata = "<Fields>"
        if export_format == 'JSON':
            metadata = '"Fields": ['
        if export_format == 'DICT':
            metadata = {}
        for field in autodetector.generated_operations[self.module][0].fields:
            if export_format == 'XML':
                sf = '<Field name="' + field.name + '">'
                sf += "</Field>"
            if export_format == 'JSON':
                sf = '{"name": "' + field.name + '", "type": "' + field.__class__.__name__ + '", "null": "' + str(field.null) + '"'
                if field.max_length != None:
                    sf += ', "max_length": "' + str(field.max_length) + '"'
                sf += ', "is_relation": "' + str(field.is_relation) + '", "column": "' + field.column + '"'
                if field.default not in {None, NOT_PROVIDED}:
                    sf += ', "default": "' + str(field.default) + '"'
                sf += '}'
            if export_format == 'DICT':
                sf = {"name": field.name}
            fields.append(sf)
            field.many_to_many
            field.many_to_one
        if export_format == 'XML':
            metadata += " ".join(fields) + "</Fields>"
        if export_format == 'JSON':
            metadata += ", ".join(fields) + "]"
        if export_format == 'DICT':
            metadata['Fields'] = fields
        return metadata
    
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

