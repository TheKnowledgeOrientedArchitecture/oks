# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from django.db import models
from serializable.models import SerializableModel

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
    if kwargs['instance'].URIInstance == "":
        try:
            kwargs['instance'].URIInstance = kwargs['instance'].generate_URIInstance()
            if kwargs['instance'].URIInstance != "":
                kwargs['instance'].save()
        except Exception as e:
            print (e.message)

class ShareableModel(SerializableModel):
    '''
    URIInstance is the unique identifier of this ShareableModel in this KS
    When a ShareableModel gets imported from XML of from a remote KS a new
    URIInstance is generated using generate_URIInstance
    '''
    URIInstance = models.CharField(max_length=2000L)
    '''
    URI_imported_instance if the instance comes from XML (or a remote KS) this attribute
    stores the URIInstance as it is in the XML. Doing so I can update an instance with data
    from XML and still have a proper local URIInstance
    '''
    URI_imported_instance = models.CharField(max_length=2000L)
    '''
    URI_previous_version is the URIInstance of the previous version if 
    this record has been created with the new_version method.
    It is used when materializing to update the relationships from old to new records
    '''
    URI_previous_version = models.CharField(max_length=2000L, null=True, blank=True)
    objects = CustomModelManager()

    def generate_URIInstance(self):
        '''
        *** method that works on the same database where self is saved ***
        This method is quite forgiving; there is no ModelMetadata? Then I use the class name and id_field="pk"
        there is no DataSetStructure? Then I use the app name
        '''
        try:
            # http://stackoverflow.com/questions/10375019/get-database-django-model-object-was-queried-from
            db_alias = self._state.db
            this_ks = KnowledgeServer.this_knowledge_server()

            # removing tail ".models"from_xml
            namespace = self.__class__.__module__[:-7]
            try:
                se = self.get_model_metadata(db_alias=db_alias)
                name = se.name
                id_field = se.id_field
                if se.dataset_structure != None:
                    namespace = se.dataset_structure.namespace
            except:
                name = self.__class__.__name__
                id_field = "pk"
            return this_ks.uri() + "/" + namespace + "/" + name + "/" + str(getattr(self, id_field))
        except Exception as es:
            print ("Exception 'generate_URIInstance' " + self.__class__.__name__ + "." + str(self.pk) + ":" + es.message)
            return ""
    
    def get_model_metadata (self, class_name="", db_alias='materialized'):
        '''
        *** method that works BY DEFAULT on the materialized database ***
        finds the instance of class ModelMetadata where the name corresponds to the name of the class of self
        '''
        logger = utils.poor_mans_logger()
        try:
            if class_name == "":
                return ModelMetadata.objects.using(db_alias).get(name=self.__class__.__name__)
            else:
                return ModelMetadata.objects.using(db_alias).get(name=class_name)
        except:
            logger.error('get_model_metadata - db_alias = ' + db_alias + ' - class_name self.__class__.__name__= ' + class_name + " " + self.__class__.__name__)
            
    def structures(self):
        '''
        Lists the structures whose root is of the same class of self
        '''
        return DataSetStructure.objects.filter(root_node__model_metadata=self.get_model_metadata())

    def serialized_URI_MM(self, export_format='XML'):
        if export_format == 'XML':
            return ' URIModelMetadata="' + self.get_model_metadata().URIInstance + '" '  
        if export_format == 'JSON':
            return ' "URIModelMetadata" : "' + self.get_model_metadata().URIInstance + '" '
        
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
            dss.URIInstance = dss.generate_URIInstance()
            dss.save(using=db_alias)
        return dss 
        
    def shallow_structure_node(self, db_alias='default'):
        '''
        it creates a StructureNode used to serialize (to_xml) self. It has the ModelMetadata 
        and references to ForeignKeys and ManyToMany
        '''
        node = StructureNode()
        node.model_metadata = self.get_model_metadata() 
        node.external_reference = False
        node.is_many = False
        node.save(using=db_alias)
        node.child_nodes = []
        for fk in self.foreign_key_attributes():
            node_fk = StructureNode()
            if getattr(self, fk) is None:
                # the attribute is not set so I can't get its __class__.__name__ and I take it from the model
                class_name = self._meta.get_field(fk).rel.model.__name__
                try:
                    node_fk.model_metadata = self.get_model_metadata(class_name)
                except Exception as ex:
                    logger = utils.poor_mans_logger()
                    logger.error("shallow_structure_node class_name = " + class_name + " - " + ex.message)
            else:
                node_fk.model_metadata = getattr(self, fk).get_model_metadata()
            node_fk.external_reference = True
            node_fk.attribute = fk
            node_fk.is_many = False
            node_fk.save(using=db_alias)
            node.child_nodes.add(node_fk)
        for rm in self.related_manager_attributes():
            # TODO: shallow_structure_node: implement self.related_manager_attributes case
            pass
        for mrm in self.many_related_manager_attributes():
            # TODO: shallow_structure_node: implement self.many_related_manager_attributes case
            pass
        node.save(using=db_alias)
        return node

    def serialize(self, node=None, exported_instances=[], export_format='XML'):
        '''
        formats so far: {'XML' | 'JSON'}

            If within a structure I have already exported this instance I don't want to duplicate all details hence I just export it's 
            URIInstance, name and ModelMetadata URI. Then I need to add an attribute so that when importing it I will recognize that 
            its details are somewhere else in the file
            <..... URIModelMetadata="....." URIInstance="...." attribute="...." REFERENCE_IN_THIS_FILE=""
            the TAG "REFERENCE_IN_THIS_FILE" is used to mark the fact that attributes values are somewhere else in the file
        '''
        export_format = export_format.upper()
        serialized = ""
        # if there is no node I export just this object creating a shallow DataSetStructure 
        if node is None:
            node = self.shallow_structure().root_node
        if node.is_many:
            # the attribute correspond to a list of instances of the model_metadata 
            tag_name = node.model_metadata.name
        else:
            tag_name = self.__class__.__name__ if node.attribute == "" else node.attribute
        # already exported, I just export a short reference with the URIInstance
        if self.URIInstance and self.URIInstance in exported_instances and node.model_metadata.name_field:
            if export_format == 'XML':
                xml_name = " " + node.model_metadata.name_field + "=\"" + getattr(self, node.model_metadata.name_field) + "\""
                return '<' + tag_name + ' REFERENCE_IN_THIS_FILE=\"\"' + self.serialized_URI_MM(export_format) + xml_name + ' URIInstance="' + self.URIInstance + '"/>'  
            if export_format == 'JSON':
                xml_name = ' "' + node.model_metadata.name_field + '" : "' + getattr(self, node.model_metadata.name_field) + '"'
                if node.is_many:
                    return ' { "REFERENCE_IN_THIS_FILE" : \"\", ' + self.serialized_URI_MM(export_format) + ", " + xml_name + ', "URIInstance": "' + self.URIInstance + '"} '
                else:
                    return '"' + tag_name + '" : { "REFERENCE_IN_THIS_FILE" : \"\", ' + self.serialized_URI_MM(export_format) + ", " + xml_name + ', "URIInstance": "' + self.URIInstance + '"}'  
        
        exported_instances.append(self.URIInstance) 
        if not node.external_reference:
            try:
                outer_comma = ""
                for child_node in node.child_nodes.all():
                    if child_node.is_many:
                        child_instances = eval("self." + child_node.attribute + ".all()")
                        if export_format == 'XML':
                            serialized += "<" + child_node.attribute + ">"
                        if export_format == 'JSON':
                            serialized += outer_comma + ' "' + child_node.attribute + '" : ['
                        innner_comma = ''
                        for child_instance in child_instances:
                            # let's prevent infinite loops if self relationships
                            if (child_instance.__class__.__name__ != self.__class__.__name__) or (self.pk != child_node.pk):
                                if export_format == 'JSON':
                                    serialized += innner_comma
                                serialized += child_instance.serialize(child_node, exported_instances=exported_instances, export_format=export_format)
                            innner_comma = ", "
                        if export_format == 'XML':
                            serialized += "</" + child_node.attribute + ">"
                        if export_format == 'JSON':
                            serialized += "]"
                    else:
                        child_instance = eval("self." + child_node.attribute)
                        if not child_instance is None:
                            serialized += child_instance.serialize(child_node, export_format=export_format, exported_instances=exported_instances)
                    outer_comma = ", "
            except Exception as ex:
                print(str(ex))
            if export_format == 'XML':
                return '<' + tag_name + self.serialized_URI_MM(export_format) + self.serialized_attributes(export_format) + '>' + serialized + '</' + tag_name + '>'
            if export_format == 'JSON':
                if node.is_many:
                    return ' { ' + self.serialized_URI_MM(export_format) + ', ' + self.serialized_attributes(export_format) + outer_comma + serialized + ' }'
                else:
                    return '"' + tag_name + '" : { ' + self.serialized_URI_MM(export_format) + ', ' + self.serialized_attributes(export_format) + outer_comma + serialized + ' }'
        else:
            # node.external_reference = True
            xml_name = ''
            json_name = ''
            if node.model_metadata.name_field != "":
                if export_format == 'XML':
                    xml_name = " " + node.model_metadata.name_field + "=\"" + getattr(self, node.model_metadata.name_field) + "\""
                if export_format == 'JSON':
                    json_name = ', "' + node.model_metadata.name_field + '": "' + getattr(self, node.model_metadata.name_field) + '"'
            if export_format == 'XML':
                return '<' + tag_name + self.serialized_URI_MM() + 'URIInstance="' + self.URIInstance + '" ' + self._meta.pk.attname + '="' + str(self.pk) + '"' + xml_name + '/>'
            if export_format == 'JSON':
                if node.is_many:
                    return '{ ' + self.serialized_URI_MM(export_format) + ', "URIInstance" : "' + self.URIInstance + '", "' + self._meta.pk.attname + '" : "' + str(self.pk) + '"' + json_name + ' }'
                else:
                    return '"' + tag_name + '" :  { ' + self.serialized_URI_SE(export_format) + ', "URIInstance" : "' + self.URIInstance + '", "' + self._meta.pk.attname + '" : "' + str(self.pk) + '"' + json_name + ' }'
            
    def from_xml(self, xmldoc, structure_node, parent=None):
        '''
        from_xml gets from xmldoc the attributes of self and saves it; it searches for child nodes according
        to structure_node.child_nodes, creates instances of child objects and calls itself recursively
        Every tag corresponds to a MetatadaModel, hence it
            contains a tag URIMetadataModel which points to the KS managing the MetadataModel
        
        Each ShareableModel(SerializableModel) has URIInstance and URI_imported_instance attributes. 
        
        external_reference
            the first ShareableModel in the XML cannot be marked as an external_reference in the structure_node
            from_xml doesn't get called recursively for external_references which are to be found in the database
            or to remain dangling references
        '''
        logger = utils.poor_mans_logger()
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
            module_name = structure_node.model_metadata.module
            actual_class = utils.load_class(module_name + ".models", structure_node.model_metadata.name) 
            try:
                instance = actual_class.retrieve(xmldoc.attributes["URIInstance"].firstChild.data)
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
                        setattr(self, "URIInstance", xmldoc.attributes["URIInstance"].firstChild.data)
                        self.SetNotNullFields()
                        self.save()
                    except:
                        logger.error("Error in REFERENCE_IN_THIS_FILE TAG setting attribute URIInstance for instance of class " + self.__class__.__name__)
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
                    if key.__class__.__name__ == "BooleanField":
                        setattr(self, key.name, xmldoc.attributes[key.name].firstChild.data.lower() == "true") 
                    elif key.__class__.__name__ == "IntegerField":
                        setattr(self, key.name, int(xmldoc.attributes[key.name].firstChild.data))
                    else:
                        setattr(self, key.name, xmldoc.attributes[key.name].firstChild.data)
                except:
                    logger.error("Error extracting from xml \"" + key.name + "\" for object of class \"" + self.__class__.__name__ + "\" with PK " + str(self.pk))
        # in the previous loop I have set the pk too; I must set it to None before saving
        self.pk = None

        # I set the URIInstance to "" so that one is generated automatically; URI_imported_instance is the field
        # that allows me to track provenance
        self.URIInstance = ""
        try:
            # URI_imported_instance stores the URIInstance from the XML
            self.URI_imported_instance = xmldoc.attributes["URIInstance"].firstChild.data
        except:
            # there's no URIInstance in the XML; it doesn't make sense but it will be created from scratch here
            pass
        # I must set foreign_key child nodes BEFORE SAVING self otherwise I get an error for ForeignKeys not being set
        for child_node in structure_node.child_nodes.all():
            if child_node.attribute == 'first_version':
                pass
            elif child_node.attribute in self.foreign_key_attributes():
                try:
                    # ASSERT: in the XML there is exactly at most one child tag
                    child_tag = xmldoc.getElementsByTagName(child_node.attribute)
                    if len(child_tag) == 1:
                        xml_child_node = xmldoc.getElementsByTagName(child_node.attribute)[0] 
                        # I search for the corresponding ModelMetadata
                         
                        se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                        # TODO: I'd like the module name to be function of the organization and namespace
                        assert (child_node.model_metadata.name == se.name), "child_node.model_metadata.name - se.name: " + child_node.model_metadata.name + ' - ' + se.name
                        module_name = child_node.model_metadata.module
                        actual_class = utils.load_class(module_name + ".models", child_node.model_metadata.name)
                        if child_node.external_reference:
                            '''
                            If it is an external reference I must search for it in the database first;  
                            if it is not there I fetch it using it's URI and then create it in the database
                            '''
                            # it can be a self relation; if so instance is self
                            if self.URIInstance == xml_child_node.attributes["URIInstance"].firstChild.data:
                                instance = self 
                            else:
                                try:
                                    # let's search it in the database
                                    instance = actual_class.retrieve(xml_child_node.attributes["URIInstance"].firstChild.data)
                                except ObjectDoesNotExist:
                                    # TODO: if it is not there I fetch it using it's URI and then create it in the database
                                    pass
                                except Exception as ex:
                                    logger.error("\"" + module_name + ".models " + se.name + "\" has no instance with URIInstance \"" + xml_child_node.attributes["URIInstance"].firstChild.data + " " + ex.message)
                                    raise Exception("\"" + module_name + ".models " + se.name + "\" has no instance with URIInstance \"" + xml_child_node.attributes["URIInstance"].firstChild.data + " " + ex.message)
                        else:
                            instance = actual_class()
                            # from_xml takes care of saving instance with a self.save() at the end
                            instance.from_xml(xml_child_node, child_node)  # the fourth parameter, "parent" shouldn't be necessary in this case as this is a ForeignKey
                        setattr(self, child_node.attribute, instance)
                except Exception as ex:
                    logger.error("from_xml: " + ex.message)
                    raise Exception("from_xml: " + ex.message)
                 
        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        # TODO: UGLY PATCH: see #143
        if self.__class__.__name__ == 'DataSet':
            self.first_version = None
        # I can save now
        self.save()
        # TODO: UGLY PATCH: see #143
        if self.__class__.__name__ == 'DataSet':
            '''
            if the first_version has been imported here then I use it, otherwise self
            '''
            self.first_version = self
            try:
                first_version_tag = xmldoc.getElementsByTagName('first_version')
                if len(first_version_tag) == 1:
                    first_version_URIInstance = xmldoc.getElementsByTagName('first_version')[0].attributes["URIInstance"].firstChild.data
                    instance = DataSet.retrieve(first_version_URIInstance)
                    self.first_version = instance
            except:
                pass
            self.save()
        # TODO: CHECK maybe the following comment is wrong and  URIInstance is always set 
        # from_xml can be invoked on an instance retrieved from the database (where URIInstance is set)
        # or created on the fly (and URIInstance is not set); in the latter case, only now I can generate URIInstance
        # as I have just saved it and I have a local ID
        
        for child_node in structure_node.child_nodes.all():
            # I have already processed foreign keys, I skip them now
            if (not child_node.attribute in self.foreign_key_attributes()):
                # ASSERT: in the XML there is exactly one child tag
                xml_attribute_node = xmldoc.getElementsByTagName(child_node.attribute)[0]
                if child_node.is_many:
                    for xml_child_node in xml_attribute_node.childNodes:
                        se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                        module_name = child_node.model_metadata.module
                        assert (child_node.model_metadata.name == se.name), "child_node.name - se.name: " + child_node.model_metadata.name + ' - ' + se.name
                        actual_class = utils.load_class(module_name + ".models", child_node.model_metadata.name)
                        if child_node.external_reference:
                            instance = actual_class.retrieve(xml_child_node.attributes["URIInstance"].firstChild.data)
                            # TODO: il test successivo forse si fa meglio guardando il concrete_model - capire questo test e mettere un commento
                            if child_node.attribute in self._meta.fields:
                                setattr(instance, child_node.attribute, self)
                                instance.save()
                            else:  
                                setattr(self, child_node.attribute, instance)
                                self.save()
                        else:
                            instance = actual_class()
                            # is_many = True, I need to add this instance to self
                            instance.from_xml(xml_child_node, child_node, self)
                            related_parent = getattr(self._meta.concrete_model, child_node.attribute)
                            related_list = getattr(self, child_node.attribute)
                            # if it is not there yet ...
                            if long(instance.id) not in [long(i.id) for i in related_list.all()]:
                                # I add it
                                related_list.add(instance)
                                self.save()
                else:
                    # is_many == False
                    xml_child_node = xml_attribute_node
                    se = ShareableModel.model_metadata_from_xml_tag(xml_child_node)
                    module_name = child_node.model_metadata.module
                    assert (child_node.model_metadata.name == se.name), "child_node.name - se.name: " + child_node.model_metadata.name + ' - ' + se.name
                    actual_class = utils.load_class(module_name + ".models", child_node.model_metadata.name)
                    if child_node.external_reference:
                        instance = actual_class.retrieve(xml_child_node.attributes["URIInstance"].firstChild.data)
                        # TODO: il test succesivo forse si fa meglio guardando il concrete_model - capire questo test e mettere un commento
                        if child_node.attribute in self._meta.fields:
                            setattr(instance, child_node.attribute, self)
                            instance.save()
                        else:  
                            setattr(self, child_node.attribute, instance)
                            self.save()
                    else:
                        instance = actual_class()
                        instance.from_xml(xml_child_node, child_node, self)
        
    def new_version(self, sn, processed_instances, parent=None):
        '''
        invoked by DataSet.new_version that wraps it in a transaction
        it recursively invokes itself to create a new version of the full structure
        
        processed_instances is a dictionary where the key is the old URIInstance and 
        the data is the new one
        
        returns the newly created instance
        '''

        if sn.external_reference:
            # if it is an external reference I do not need to create a new instance
            return self

        if self.URIInstance and str(self.URIInstance) in processed_instances.keys():
            # already created, I get it and return it
            return self.__class__.objects.get(URIInstance=processed_instances[str(self.URIInstance)])
        
        new_instance = self.__class__()
        if parent:
#           I have a parent; let's set it
            field_name = ShareableModel.get_parent_field_name(parent, sn.attribute)
            if field_name:
                setattr(new_instance, field_name, parent)
                
        for sn_child_node in sn.child_nodes.all():
            if sn_child_node.attribute in self.foreign_key_attributes():
                # not is_many
                child_instance = eval("self." + sn_child_node.attribute)
                new_child_instance = child_instance.new_version(sn_child_node, processed_instances)
                setattr(new_instance, sn_child_node.attribute, new_child_instance)  # the parameter "parent" shouldn't be necessary in this case as this is a ForeignKey
                
        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        new_instance.save()
                
        for sn_child_node in sn.child_nodes.all():
            if sn_child_node.is_many:
                child_instances = eval("self." + sn_child_node.attribute + ".all()")
                for child_instance in child_instances:
                    # let's prevent infinite loops if self relationships
                    if (child_instance.__class__.__name__ == self.__class__.__name__) and (self.pk == sn_child_node.pk):
                        eval("new_instance." + sn_child_node.attribute + ".add(new_instance)")
                    else:
                        new_child_instance = child_instance.new_version(sn_child_node, processed_instances, new_instance)
            else:
                # not is_many
                child_instance = eval("self." + sn_child_node.attribute)
                new_child_instance = child_instance.new_version(sn_child_node, processed_instances, self)
                setattr(new_instance, sn_child_node.attribute, new_child_instance)
        
        for key in self._meta.fields:
            if key.__class__.__name__ != "ForeignKey" and self._meta.pk != key:
                setattr(new_instance, key.name, eval("self." + key.name))
        new_instance.URI_previous_version = new_instance.URIInstance
        new_instance.URIInstance = ""
        new_instance.save()
        # after saving
        processed_instances[str(self.URIInstance)] = new_instance.URIInstance
        return new_instance

    def materialize(self, sn, processed_instances, parent=None):
        '''
        invoked by DataSet.set_released that wraps it in a transaction
        it recursively invokes itself to copy the full structure to the materialized DB
        
        ASSERTION: URIInstance remains the same on the materialized database
        
        processed_instances is a list of processed URIInstance 
        
        TODO: before invoking this method a check is done to see whether it is already materialized; is it done always? 
        If so shall we move it inside this method?
        '''

        if sn.external_reference:
            try:
                return self.__class__.objects.using('ksm').get(URIInstance=self.URIInstance)
            except Exception as ex:
                new_ex = Exception("ShareableModel.materialize: self.URIInstance: " + self.URIInstance + " searching it on ksm: " + ex.message + " Should we add it to dangling references?????")
                raise ex

        if self.URIInstance and str(self.URIInstance) in processed_instances:
            # already materialized it, I return that one 
            return self.__class__.objects.using('ksm').get(URIInstance=self.URIInstance)
        
        new_instance = self.__class__()
        if parent:
#           I have a parent; let's set it
            field_name = ShareableModel.get_parent_field_name(parent, sn.attribute)
            if field_name:
                setattr(new_instance, field_name, parent)
          
        list_of_self_relationships_pointing_to_self = []      
        for sn_child_node in sn.child_nodes.all():
            if sn_child_node.attribute in self.foreign_key_attributes():
                # not is_many
                # if they are nullable I do nothing
                try:
                    child_instance = getattr(self, sn_child_node.attribute)
                    
                    # e.g. DataSet.root is a self relationship often set to self; I am materializing self
                    # so I don't have it; I return self; I could probably do the same also in the other case
                    # because what actually counts for Django is the pk
                    if self == child_instance:
                        # In Django ORM it seems not possible to have not nullable self relationships pointing to self
                        # I make not nullable in the model (this becomes a general constraint!); 
                        # put them in a list and save them after saving new_instance
                        list_of_self_relationships_pointing_to_self.append(sn_child_node.attribute)
                    else:
                        new_child_instance = child_instance.materialize(sn_child_node, processed_instances)
                        setattr(new_instance, sn_child_node.attribute, new_child_instance)  # the parameter "parent" shouldn't be necessary in this case as this is a ForeignKey
                except Exception as ex:
#                     print("ShareableModel.materialize: " + self.__class__.__name__ + " " + str(self.pk) + " attribute \"" + sn_child_node.attribute + "\" " + ex.message)
                    pass
        for key in self._meta.fields:
            if key.__class__.__name__ != "ForeignKey" and self._meta.pk != key:
                setattr(new_instance, key.name, eval("self." + key.name))
        
        # I have added all attributes corresponding to ForeignKey, I can save it so that I can use it as a parent for the other attributes
        new_instance.save(using='ksm')
        if len(list_of_self_relationships_pointing_to_self) > 0:
            for attribute in list_of_self_relationships_pointing_to_self:
                setattr(new_instance, attribute, new_instance)
            new_instance.save(using='ksm')
        
        for sn_child_node in sn.child_nodes.all():
            if not (sn_child_node.attribute in self.foreign_key_attributes()):
                if sn_child_node.is_many:
                    child_instances = eval("self." + sn_child_node.attribute + ".all()")
                    for child_instance in child_instances:
                        # let's prevent infinite loops if self relationships
                        if (child_instance.__class__.__name__ == self.__class__.__name__) and (self.pk == sn_child_node.pk):
                            eval("new_instance." + sn_child_node.attribute + ".add(new_instance)")
                        else:
                            new_child_instance = child_instance.materialize(sn_child_node, processed_instances, new_instance)
                else:
                    # not is_many
                    child_instance = eval("self." + sn_child_node.attribute)
                    new_child_instance = child_instance.materialize(sn_child_node, processed_instances, self)
                    setattr(new_instance, sn_child_node.attribute, new_child_instance)
        
        new_instance.save(using='ksm')
        # after saving
        processed_instances.append(new_instance.URIInstance)
        return new_instance

    def delete_children(self, etn, parent=None):
        '''
        invoked by DataSet.delete_entire_dataset that wraps it in a transaction
        it recursively invokes itself to delete children's children; self is in the 
        materialized database
        
        It is invoked only if DataSet.dataset_structure.multiple_releases = False
        Then I also have to remap foreign keys pointing to it in the materialized DB and
        in default DB
        '''

        # I delete the children; must do it before remapping foreignkeys otherwise some will escape deletion
        for sn_child_node in etn.child_nodes.all():
            if not sn_child_node.external_reference:
                if sn_child_node.is_many:
                    child_instances = eval("self." + sn_child_node.attribute + ".all()")
                    for child_instance in child_instances:
                        # let's prevent deleting self; self will be deleted by who has invoked this method 
                        if (child_instance.__class__.__name__ != self.__class__.__name__) or (self.pk != sn_child_node.pk):
                            child_instance.delete_children(sn_child_node, self)
                            child_instance.delete()
                else:
                    # not is_many
                    child_instance = eval("self." + sn_child_node.attribute)
                    child_instance.delete_children(sn_child_node, self)
                    child_instance.delete()
        
        try:
            # before deleting self I must remap foreignkeys pointing at it to the new instances
            # let's get the instance it should point to
            '''
            There could be more than one; imagine the case of an Italian Province split into two of them (Region Sardinia
            had four provinces and then they become 4) then there will be two new instances with the same URI_previous_version.
            TODO: we should also take into account the case when a new_materialized_instance can have more than URI_previous_version; this
            situation requires redesign of the model and db
            '''
            new_materialized_instances = self.__class__.objects.using('ksm').filter(URI_previous_version=self.URIInstance)
            new_instances = self.__class__.objects.filter(URI_previous_version=self.URIInstance)
            self_on_default_db = self.__class__.objects.filter(URIInstance=self.URIInstance)
            
            assert (len(new_materialized_instances) == len(new_instances)), 'ShareableModel.delete_children self.URIInstance="' + self.URIInstance + '": "(len(new_materialized_instances ' + str(new_materialized_instances) + ') != len(new_instances' + str(new_instances) + '))"'
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
                raise Exception('NOT IMPLEMENTED in ShareableModel.delete_children: mapping between different versions: URIInstance "' + self.URIInstance + '" has ' + str(len(new_instances)) + ' materialized records that have this as URI_previous_version.') 
        except Exception as e:
            print(e.message)

    @staticmethod
    def simple_entity_from_xml_tag(xml_child_node):
        URIInstance = xml_child_node.attributes["URIModelMetadata"].firstChild.data
        try:
            se = ModelMetadata.objects.get(URIInstance=URIInstance)
        except:
            '''
            I go get it from the appropriate KS
            TODO: David
            See API definition here: http://redmine.davide.galletti.name/issues/33
            When I get a ModelMetadata I must generate its model in an appropriate module; the module
            name must be generated so that it is unique based on the ModelMetadata's BASE URI and on the module 
            name; 
            ModelMetadata URI 1: "http://finanze.it/KS/fattura"
            ModelMetadata URI 2: "http://finanze.it/KS/sanzione"
            
            TODO: When importing an DataSet from another KS, its root will point to either self or to an DataSet
            that is on the other KS; in the latter case I search for this root DataSet using the field 
            SharableModel.URI_imported_instance; if I find it I set root to point to it otherwise
            I set it to self.
            '''
            # estrarre l'url del KS
            ks_url = ""
            # encode di URIInstance
            URIInstance_base64 = ""
            # wget ks_url + "/ks/api/simple_entity_definition/" + URIInstance_base64
            raise Exception("NOT IMPLEMENTED in simple_entity_from_xml_tag: get ModelMetadata from appropriate KS.")
        return se

    @classmethod
    def retrieve(cls, URIInstance):
        '''
        It returns an instance of a ShareableModel stored in this KS
        It searches first on the URIInstance field (e.g. is it already an instance of this KS? ) 
        It searches then on the URI_imported_instance field (e.g. has is been imported in this KS from the same source? )
        It fetches the instance from the source as it is not in this KS yet 
        '''
        actual_instance = None
        try:
            actual_instance = cls.objects.get(URIInstance=URIInstance)
        except Exception as ex:
            try:
                actual_instance = cls.objects.get(URI_imported_instance=URIInstance)
            except Exception as ex:
                raise ex
        return actual_instance

    @staticmethod
    def intersect_list(first, second):
        first_URIInstances = list(i.URIInstance for i in first)
        return filter(lambda x: x.URIInstance in first_URIInstances, second)
            
    class Meta:
        abstract = True

class ModelMetadata(ShareableModel):
    '''
    A ModelMetadata roughly contains the meta-data describing a table in a database or a class if we have an ORM
    '''
    # this name corresponds to the class name
    name = models.CharField(max_length=100L)
    # for Django it corresponds to the module which contains the class 
    module = models.CharField(max_length=100L)
    description = models.CharField(max_length=2000L, default="")
    table_name = models.CharField(max_length=255L, db_column='tableName', default="")
    id_field = models.CharField(max_length=255L, db_column='idField', default="id")
    name_field = models.CharField(max_length=255L, db_column='nameField', default="name")
    description_field = models.CharField(max_length=255L, db_column='descriptionField', default="description")
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
        nodes = StructureNode.objects.using('ksm').filter(simple_entity=self, external_reference=external_reference)
        try:
            for node in nodes:
                entry_node = node
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
            print ("dataset_structures type(self): " + str(type(self)) + " self.id " + str(self.id) + ex.message)
            print ("visited_nodes_ids : " + str(visited_nodes_ids))
        return types

class AttributeType(ShareableModel):
    name = models.CharField(max_length=255L, blank=True)
    widgets = models.ManyToManyField('application.Widget', blank=True)

class Attribute(ShareableModel):
    name = models.CharField(max_length=255L, blank=True)
    simple_entity = models.ForeignKey('ModelMetadata', null=True, blank=True)
    type = models.ForeignKey('AttributeType')
    def __str__(self):
        return self.model_metadata.name + "." + self.name

class StructureNode(ShareableModel):
    simple_entity = models.ForeignKey('ModelMetadata')
    # attribute is blank for the entry point
    attribute = models.CharField(max_length=255L, blank=True)
    # "parent" assert: there is only one parent so we should change to 
    # TODO: parent = models.ForeignKey('StructureNode', null=True, blank=True)
    child_nodes = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="parent")
    # if not external_reference all attributes are exported, otherwise only the id
    external_reference = models.BooleanField(default=False, db_column='externalReference')
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
            node_method(instance, status)
        # loop on children

        for child_node in self.child_nodes.all():
            if child_node.is_many:
                child_instances = eval("instance." + child_node.attribute + ".all()")
                for child_instance in child_instances:
                    # let's prevent infinite loops if self relationships
                    if (child_instance.__class__.__name__ != instance.__class__.__name__) or (instance.pk != child_node.pk):
                        child_node.navigate(child_instance, instance_method_name, node_method_name, status, children_before)
            else:
                child_instance = eval("instance." + child_node.attribute)
                if not child_instance is None:
                    child_node.navigate(child_instance, instance_method_name, node_method_name, status, children_before)
            
        if children_before and instance_method_name:
            instance_method(instance, status)
        if children_before and node_method_name:
            node_method(instance, status)
        
    def navigate_helper_list_by_type(self, instance, status):
        # if status['output'] is None I create a dictionary whose keys will be 
        # different ModelMetadata and whose values will be list without repetition
        # of instances of the classes corresponding to that ModelMetadata
        if not 'output' in status.keys():
            status['output'] = {}
        if not self.simple_entity in status['output'].keys():
            status['output'][self.simple_entity] = []
        if not instance in status['output'][self.simple_entity]:
            status['output'][self.simple_entity].append(instance)

class DataSetStructure(ShareableModel):
    dataset_structure_name = "Dataset structure"
    simple_entity_dataset_structure_name = "Entity"
    organization_dataset_structure_name = "Organization and Open Knowledge Servers"
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
    name = models.CharField(max_length=200L)
    description = models.CharField(max_length=2000L)
    '''
    an DataSetStructure is shallow when it is automatically created to export a ModelMetadata; 
    is_shallow = True means that all foreignKeys and related attributes are external references
    '''
    is_shallow = models.BooleanField(default=False)
    '''
    an DataSetStructure is a view if it is not used to determine the structure of an DataSet
    hence it is used for example to export some data
    '''
    is_a_view = models.BooleanField(default=False)
    '''
    the entry point of the structure; the class StructureNode has then child_nodes of the same class 
    hence it defines the structure
    assert: the root_node is the entr_point for only one structure so we should change to 
    '''
    root_node = models.ForeignKey('StructureNode', related_name='dataset_type')
    '''
    when multiple_releases is true more than one instance get materialized
    otherwise just one; it defaults to False just not to make it nullable;
    a default is indicated as shallow structures are created without specifying it
    makes no sense when is_a_view
    '''
    multiple_releases = models.BooleanField(default=False)
    
    '''
    TODO: the namespace is defined in the organization owner of this DataSetStructure
    within that organization (or maybe within the KS in that Organization)
    names of ModelMetadata are unique. When importing a ModelMetadata from
    an external KS we need to create a namespace (and a corresponding module
    where the class of the model must live) with a unique name. It can
    be done combining the netloc of the URI of the KS with the namespace;
    so when I import a WorkFlow from the namespace "entity" of rootks.thekoa.org 
    in my local KS it will live in the namespace/module:
        something like: rootks.thekoa.org_entity
    Within that namespace the KS it originated from ensures the ModelMetadata name
    is unique; locally in my KS I make sure there is no other namespace of that form
    (maybe not allowing "_"?)
    '''
    namespace = models.CharField(max_length=500L, blank=True)
    
    def navigate(self, dataset, instance_method_name, node_method_name, children_before = True):
        '''
        Many methods do things on each node navigating in the structure
        This is a generic method that takes a method as a parameter
        and executes it on the actual instance of each node; the signature of such method must be:
            def generic_structure_node_method(self, instance, status)
        each method can add whatever it wants to the status and set its output to status.output
        the instance_method_name must be a method of SerializableModelMetadata so that it is implemented
        by any instance of any node.
        If children_before the method is invoked on the children first
        '''
        status = {}
        if self.is_a_view:
            # I have to do it on all instances that match the dataset criteria
            for instance in dataset.get_instances():
                self.root_node.navigate(instance, instance_method_name, node_method_name, status, children_before)
        else:
            instance = dataset.get_instance()
            self.root_node.navigate(instance, instance_method_name, node_method_name, status, children_before)
        return status['output']
    
        

