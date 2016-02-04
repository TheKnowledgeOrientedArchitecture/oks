# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals
from django.db import migrations
from knowledge_server.models import Organization, KnowledgeServer, ModelMetadata, AttributeType, Attribute, StructureNode, DataSetStructure, DataSet

def forwards_func(apps, schema_editor):
    
    db_alias = schema_editor.connection.alias
    
    # this data must be created on the root ks but also on any other as it is essential for basic ks operation
    # 
    the_koa_org = Organization();the_koa_org.id=1;the_koa_org.name="the Knowledge Oriented Architecture";
    the_koa_org.URIInstance="-";the_koa_org.URI_imported_instance="http://rootks.thekoa.org/knowledge_server/Organization/1";the_koa_org.website='http://www.theKOA.org';
    the_koa_org.description="the Knowledge Oriented Architecture organization .....";the_koa_org.save(using=db_alias)
    
    the_koa_org_ks = KnowledgeServer(pk=1, name="theKOA.org root Open Knowledge Server", scheme="http", netloc="rootks.thekoa.org", 
                                     URIInstance="-",URI_imported_instance="http://rootthe_koa_org.URIInstance="";the_koa_org.URIInstance="";ks.thekoa.org/knowledge_server/KnowledgeServer/1", 
                                     description="The main OKS, defining the main structures and datasets used by any other Knowledge Server.", 
                                     organization=the_koa_org, this_ks=True,html_home="rootks html_home",html_disclaimer="rootks html_disclaimer")
    the_koa_org_ks.save(using=db_alias)
    the_koa_org_ks.URIInstance=""; the_koa_org_ks.save(using=db_alias)
    the_koa_org.URIInstance="";    the_koa_org.save(using=db_alias)
    #ModelMetadata
    mmModelMetadata=ModelMetadata();mmModelMetadata.name="ModelMetadata";mmModelMetadata.module="knowledge_server";mmModelMetadata.save(using=db_alias)
    mmAttribute=ModelMetadata();mmAttribute.name="Attribute";mmAttribute.module="knowledge_server";mmAttribute.description_field="";mmAttribute.save(using=db_alias)
    mmAttributeType=ModelMetadata();mmAttributeType.name="AttributeType";mmAttributeType.module="knowledge_server";mmAttributeType.description_field="";mmAttributeType.save(using=db_alias)
    mmStructureNode=ModelMetadata();mmStructureNode.name="StructureNode";mmStructureNode.module="knowledge_server";mmStructureNode.name_field="attribute";mmStructureNode.description_field="";mmStructureNode.save(using=db_alias)
    mmDataSetStructure=ModelMetadata();mmDataSetStructure.name="DataSetStructure";mmDataSetStructure.module="knowledge_server";mmDataSetStructure.description_field;mmDataSetStructure.save(using=db_alias)
    mmOrganization=ModelMetadata();mmOrganization.name="Organization";mmOrganization.module="knowledge_server";mmOrganization.save(using=db_alias)
    mmDataSet=ModelMetadata();mmDataSet.name="DataSet";mmDataSet.module="knowledge_server";mmDataSet.name_field="";mmDataSet.description_field="";mmDataSet.save(using=db_alias)
    mmKnowledgeServer=ModelMetadata();mmKnowledgeServer.name="KnowledgeServer";mmKnowledgeServer.module="knowledge_server";mmKnowledgeServer.save(using=db_alias)
    mmLicense=ModelMetadata();mmLicense.name="License";mmLicense.module="licenses";mmLicense.save(using=db_alias)
 
#     # AttributeType
#     atText=AttributeType();atText.name="Text";atText.save(using=db_alias)
#     atDate=AttributeType();atDate.name="Date";atDate.save(using=db_alias)
#     atForeignKey=AttributeType();atForeignKey.name="ForeignKey";atForeignKey.save(using=db_alias)
#  
#     # Attributes for ModelMetadata
#     aname=Attribute();aname.name="name";aname.type=atText;aname.model_metadata=mmModelMetadata;aname.save(using=db_alias)
#     aURIInstance=Attribute();aURIInstance.name="URIInstance";aURIInstance.type=atText;aURIInstance.model_metadata=mmModelMetadata;aURIInstance.save(using=db_alias)
#     amodule=Attribute();amodule.name="module";amodule.type=atText;amodule.model_metadata=mmModelMetadata;amodule.save(using=db_alias)
#     atable_name=Attribute();atable_name.name="table_name";atable_name.type=atText;atable_name.model_metadata=mmModelMetadata;atable_name.save(using=db_alias)
#     aid_field=Attribute();aid_field.name="id_field";aid_field.type=atText;aid_field.model_metadata=mmModelMetadata;aid_field.save(using=db_alias)
#     aname_field=Attribute();aname_field.name="name_field";aname_field.type=atText;aname_field.model_metadata=mmModelMetadata;aname_field.save(using=db_alias)
#     adescription_field=Attribute();adescription_field.name="description_field";adescription_field.type=atText;adescription_field.model_metadata=mmModelMetadata;adescription_field.save(using=db_alias)
#     adescription=Attribute();adescription.name="description";adescription.type=atText;adescription.model_metadata=mmModelMetadata;adescription.save(using=db_alias)
     
    # StructureNode for "ModelMetadata-attributes"     root_node=en1
    en1=StructureNode();en1.model_metadata=mmModelMetadata;en1.save(using=db_alias) 
    en2=StructureNode();en2.model_metadata=mmAttribute;en2.attribute="attribute_set";en2.is_many=True;en2.save(using=db_alias)
    en3=StructureNode();en3.model_metadata=mmAttributeType;en3.attribute="type";en3.save(using=db_alias)
    # StructureNode for "DataSetStructure-StructureNode"    root_node=en22
    en4=StructureNode();en4.model_metadata=mmDataSetStructure;en4.save(using=db_alias)
    en5=StructureNode();en5.model_metadata=mmStructureNode;en5.attribute="root_node";en5.save(using=db_alias)
    en6=StructureNode();en6.model_metadata=mmModelMetadata;en6.attribute="model_metadata";en6.external_reference=True;en6.save(using=db_alias)
    en7=StructureNode();en7.model_metadata=mmStructureNode;en7.attribute="child_nodes";en7.is_many=True;en7.save(using=db_alias)
    # StructureNode for "Organization-KS"     root_node=en18
    en18=StructureNode();en18.model_metadata=mmOrganization;en18.save(using=db_alias)
    en19=StructureNode();en19.model_metadata=mmKnowledgeServer;en19.attribute="knowledgeserver_set";en19.is_many=True;en19.save(using=db_alias)
    
    # DATASETSTRUCTURE dssModelMetadataAttributes
    en1.child_nodes.add(en2); en1.save(using=db_alias)
    en2.child_nodes.add(en3); en2.save(using=db_alias)
    dssModelMetadataAttributes=DataSetStructure();dssModelMetadataAttributes.multiple_releases=False;
    dssModelMetadataAttributes.root_node=en1;dssModelMetadataAttributes.name=DataSetStructure.model_metadata_DSN;
    dssModelMetadataAttributes.description="Metadata describing a model in the ORM, i.e. something closely related to what is stored in a database table, and its attributes.";
    dssModelMetadataAttributes.namespace="knowledge_server";dssModelMetadataAttributes.save(using=db_alias)

    mmModelMetadata.dataset_structure = dssModelMetadataAttributes; mmModelMetadata.save(using=db_alias)
     
#     mmAttribute.dataset_structure = dssModelMetadataAttributes; mmAttribute.save(using=db_alias)
#     aname.save(using=db_alias);aURIInstance.save(using=db_alias);amodule.save(using=db_alias);atable_name.save(using=db_alias);aid_field.save(using=db_alias);aname_field.save(using=db_alias);adescription_field.save(using=db_alias);adescription.save(using=db_alias)
#      
#     mmAttributeType.dataset_structure = dssModelMetadataAttributes; mmAttributeType.save(using=db_alias)
#     atText.save(using=db_alias);atDate.save(using=db_alias);atForeignKey.save(using=db_alias); #saving again to create URIInstance via the post_save signal
     
    # DATASETSTRUCTURE  dssDataSetStructureStructureNode
    en4.child_nodes.add(en5); en4.save(using=db_alias)
    en5.child_nodes.add(en6); en5.child_nodes.add(en7); en5.save(using=db_alias)
    en7.child_nodes.add(en6); en7.child_nodes.add(en7); en7.save(using=db_alias)
    dssDataSetStructureStructureNode=DataSetStructure(id=2,multiple_releases=False,root_node=en4,
                                                                name=DataSetStructure.dataset_structure_DSN,
                                                                description="A graph of simple entities that have relationships with one another and whose instances share the same version, status, ...",
                                                                namespace="knowledge_server")
    dssDataSetStructureStructureNode.save(using=db_alias)
    mmDataSetStructure.dataset_structure = dssDataSetStructureStructureNode; mmDataSetStructure.save(using=db_alias)
    dssModelMetadataAttributes.save(using=db_alias);dssDataSetStructureStructureNode.save(using=db_alias); #saving again to create URIInstance via the post_save signal
     
    mmStructureNode.dataset_structure = dssDataSetStructureStructureNode; mmStructureNode.save(using=db_alias)
    en1.save(using=db_alias);en2.save(using=db_alias);en3.save(using=db_alias);en4.save(using=db_alias);
    en5.save(using=db_alias);en6.save(using=db_alias);en7.save(using=db_alias);en18.save(using=db_alias);en19.save(using=db_alias)
     
     
    # DATASETSTRUCTURE  eOrganizationKS
    en18.child_nodes.add(en19); en18.save(using=db_alias)
    eOrganizationKS=DataSetStructure(id=4,multiple_releases=False,root_node=en18,name=DataSetStructure.organization_DSN,
                                     namespace="knowledge_server",description="An Organization and its Knowledge Servers",URIInstance="")
    eOrganizationKS.save(using=db_alias)
    mmOrganization.dataset_structure = eOrganizationKS; mmOrganization.save(using=db_alias)
    mmKnowledgeServer.dataset_structure = eOrganizationKS; mmKnowledgeServer.save(using=db_alias)
     
    # DataSet
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,
                 root = mmModelMetadata,
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    # DataSet has no DataSetStructure, I create the shallow one so that I can set DataSetStructure.namespace
    # and hence generate the URIInstance for each instance of DataSet
    es = ei.shallow_structure(db_alias)
    es.namespace = "knowledge_server"
    es.save(using=db_alias)
    mmDataSet.dataset_structure = es
    mmDataSet.save(using=db_alias)
    ei.save(using=db_alias)
     
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmAttribute,                                   
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmAttributeType,                               
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmStructureNode,                         
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmDataSetStructure,                             
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmOrganization,                                
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmDataSet,                              
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataAttributes,       
                 root=mmKnowledgeServer,                             
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=dssModelMetadataAttributes,                       
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=dssDataSetStructureStructureNode,
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=eOrganizationKS,                               
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)
    ei = DataSet(owner_knowledge_server=the_koa_org_ks,dataset_structure=eOrganizationKS,                  
                 root=the_koa_org,                                   
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.save(using=db_alias)



class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

