# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals
import logging
from django.db import migrations
from knowledge_server.models import Organization, KnowledgeServer, ModelMetadata, StructureNode, DataSetStructure, DataSet
from licenses.models import License

logger = logging.getLogger(__name__)

def forwards_func(apps, schema_editor):
    
    db_alias = schema_editor.connection.alias
    
    # this data must be created on the root ks but also on any other as it is essential for basic ks operation
    # 
    the_koa_org = Organization();the_koa_org.id=1;the_koa_org.name="the Knowledge Oriented Architecture";
    the_koa_org.UKCL="-";the_koa_org.website='http://www.theKOA.org';
    the_koa_org.description="the Knowledge Oriented Architecture organization .....";the_koa_org.save(using=db_alias)
    
    the_koa_org_ks = KnowledgeServer(pk=1, name="theKOA.org root Open Knowledge Server", scheme="http", netloc="root.beta.thekoa.org", 
                                     UKCL="-",
                                     description="The main OKS, defining the main structures and datasets used by any other Knowledge Server.", 
                                     organization=the_koa_org, this_ks=True,html_home="root html_home",html_disclaimer="root html_disclaimer")
    the_koa_org_ks.save(using=db_alias)
    #ModelMetadata
    mmModelMetadata=ModelMetadata();mmModelMetadata.UKCL=the_koa_org_ks.url();mmModelMetadata.name="ModelMetadata";mmModelMetadata.module="knowledge_server";mmModelMetadata.save(using=db_alias)
    # UKCL generation relies on the UKCL (only it's netloc) of its model metadata; for this record it is recursive so 
    # we have to make a workaround: we set a fake one with the correct netloc and then we generate it
    mmModelMetadata.UKCL=mmModelMetadata.generate_UKCL()
    mmModelMetadata.save(using=db_alias)
    # now that we have a UKCL on the ModelMetadata of ModelMetadata we can generate normally the other UKCL of ModelMetadata
    mmField=ModelMetadata();mmField.name="Field";mmField.module="django.db.models.fields";mmField.description_field="";mmField.save(using=db_alias)
    mmStructureNode=ModelMetadata();mmStructureNode.name="StructureNode";mmStructureNode.module="knowledge_server";mmStructureNode.name_field="attribute";mmStructureNode.description_field="";mmStructureNode.save(using=db_alias)
    mmDataSetStructure=ModelMetadata();mmDataSetStructure.name="DataSetStructure";mmDataSetStructure.module="knowledge_server";mmDataSetStructure.description_field;mmDataSetStructure.save(using=db_alias)
    mmOrganization=ModelMetadata();mmOrganization.name="Organization";mmOrganization.module="knowledge_server";mmOrganization.save(using=db_alias)
    mmDataSet=ModelMetadata();mmDataSet.name="DataSet";mmDataSet.module="knowledge_server";mmDataSet.name_field="";mmDataSet.description_field="";mmDataSet.save(using=db_alias)
    mmKnowledgeServer=ModelMetadata();mmKnowledgeServer.name="KnowledgeServer";mmKnowledgeServer.module="knowledge_server";mmKnowledgeServer.save(using=db_alias)
    mmEvent=ModelMetadata();mmEvent.name="Event";mmEvent.module="knowledge_server";mmEvent.save(using=db_alias)
    mmSubscriptionToThis=ModelMetadata();mmSubscriptionToThis.name="SubscriptionToThis";mmSubscriptionToThis.module="knowledge_server";mmSubscriptionToThis.save(using=db_alias)
    mmSubscriptionToOther=ModelMetadata();mmSubscriptionToOther.name="SubscriptionToOther";mmSubscriptionToOther.module="knowledge_server";mmSubscriptionToOther.save(using=db_alias)
    mmNotification=ModelMetadata(); mmNotification.name="Notification"; mmNotification.module="knowledge_server"; mmNotification.save(using=db_alias)
    mmNotificationReceived=ModelMetadata(); mmNotificationReceived.name="NotificationReceived"; mmNotificationReceived.module="knowledge_server"; mmNotificationReceived.save(using=db_alias)
    mmLicense=ModelMetadata();mmLicense.name="License";mmLicense.module="licenses";mmLicense.save(using=db_alias)

    # we trigger the generation of the UKCL by setting it to "" and saving
    # we couldn't do it before having the corresponding ModelMetadata
    the_koa_org_ks.UKCL=""; the_koa_org_ks.save(using=db_alias)
    the_koa_org.UKCL="";    the_koa_org.save(using=db_alias)

    # StructureNode for "ModelMetadata-fields"
    en1=StructureNode();en1.model_metadata=mmModelMetadata;en1.save(using=db_alias) 
    en2=StructureNode();en2.model_metadata=mmField;en2.method_to_retrieve="orm_metadata";en2.is_many=True;en2.save(using=db_alias)
    en3=StructureNode();en3.model_metadata=mmDataSetStructure;en3.attribute="dataset_structure";en3.external_reference=True;en3.save(using=db_alias)
    # StructureNode for "DataSetStructure-StructureNode"
    en4=StructureNode();en4.model_metadata=mmDataSetStructure;en4.save(using=db_alias)
    en5=StructureNode();en5.model_metadata=mmStructureNode;en5.attribute="root_node";en5.save(using=db_alias)
    en6=StructureNode();en6.model_metadata=mmModelMetadata;en6.attribute="model_metadata";en6.external_reference=True;en6.save(using=db_alias)
    en7=StructureNode();en7.model_metadata=mmStructureNode;en7.attribute="child_nodes";en7.is_many=True;en7.save(using=db_alias)
    # StructureNode for "Organization-KS"
    en18=StructureNode();en18.model_metadata=mmOrganization;en18.save(using=db_alias)
    en19=StructureNode();en19.model_metadata=mmKnowledgeServer;en19.attribute="knowledgeserver_set";en19.is_many=True;en19.save(using=db_alias)
    # StructureNode for "License"
    en20=StructureNode();en20.model_metadata=mmLicense;en20.save(using=db_alias)
    
    
    
    # DATASETSTRUCTURE dssModelMetadataFields
    en1.child_nodes.add(en2);en1.child_nodes.add(en3);en1.save(using=db_alias)
    dssModelMetadataFields=DataSetStructure();dssModelMetadataFields.multiple_releases=False;
    dssModelMetadataFields.root_node=en1;dssModelMetadataFields.name=DataSetStructure.model_metadata_DSN;
    dssModelMetadataFields.description="Metadata describing a model in the ORM, i.e. something closely related to what is stored in a database table, and its fields.";
    dssModelMetadataFields.save(using=db_alias)

    mmModelMetadata.dataset_structure = dssModelMetadataFields; mmModelMetadata.save(using=db_alias)
    mmField.dataset_structure = dssModelMetadataFields; mmField.save(using=db_alias)
    

    # DATASETSTRUCTURE  dssDataSetStructureStructureNode
    en4.child_nodes.add(en5); en4.save(using=db_alias)
    en5.child_nodes.add(en6); en5.child_nodes.add(en7); en5.save(using=db_alias)
    en7.child_nodes.add(en6); en7.child_nodes.add(en7); en7.save(using=db_alias)
    dssDataSetStructureStructureNode=DataSetStructure(multiple_releases=False,root_node=en4,
                                                                name=DataSetStructure.dataset_structure_DSN,
                                                                description="A graph of simple entities that have relationships with one another and whose instances share the same version, status, ...")
    dssDataSetStructureStructureNode.save(using=db_alias)
    mmDataSetStructure.dataset_structure = dssDataSetStructureStructureNode; mmDataSetStructure.save(using=db_alias)
    dssModelMetadataFields.save(using=db_alias);dssDataSetStructureStructureNode.save(using=db_alias); #saving again to create UKCL via the post_save signal
     
    mmStructureNode.dataset_structure = dssDataSetStructureStructureNode; mmStructureNode.save(using=db_alias)
    en1.save(using=db_alias);en2.save(using=db_alias);en4.save(using=db_alias);
    en5.save(using=db_alias);en6.save(using=db_alias);en7.save(using=db_alias);en18.save(using=db_alias);en19.save(using=db_alias)
     
     
    # DATASETSTRUCTURE  eOrganizationKS
    en18.child_nodes.add(en19); en18.save(using=db_alias)
    eOrganizationKS=DataSetStructure(multiple_releases=False,root_node=en18,name=DataSetStructure.organization_DSN,
                                     description="An Organization and its Knowledge Servers",UKCL="")
    eOrganizationKS.save(using=db_alias)
    mmOrganization.dataset_structure = eOrganizationKS; mmOrganization.save(using=db_alias)
    mmKnowledgeServer.dataset_structure = eOrganizationKS; mmKnowledgeServer.save(using=db_alias)

    # DATASETSTRUCTURE  License
    dssLicense = DataSetStructure();dssLicense.multiple_releases = True;dssLicense.is_shallow = True;
    dssLicense.root_node = en20;dssLicense.name = DataSetStructure.license_DSN;dssLicense.description = "License information";
    dssLicense.save(using=db_alias)
    mmLicense.dataset_structure = dssLicense; mmLicense.save(using=db_alias)



    # DataSetStructure "view" for the list of licenses
    en21 = StructureNode();en21.model_metadata = mmLicense;en21.save(using=db_alias)
    esLicenseList = DataSetStructure();esLicenseList.is_a_view = True;
    esLicenseList.root_node = en21;esLicenseList.name = "List of licenses";esLicenseList.description = "List of all released licenses";
    esLicenseList.save(using=db_alias)

     
    # DataSet
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,
                 root = mmModelMetadata,description="Model metadata of ModelMetadata",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
     
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmStructureNode,description="Model metadata of StructureNode",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmDataSetStructure,description="Model metadata of DataSetStructure",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmOrganization,description="Model metadata of Organization",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmDataSet,description="Model metadata of DataSet",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmKnowledgeServer,description="Model metadata of KnowledgeServer",    
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmEvent,description="Model metadata of Event",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmSubscriptionToThis,description="Model metadata of SubscriptionToThis",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmSubscriptionToOther,description="Model metadata of SubscriptionToOther",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmNotification,description="Model metadata of Notification",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmNotificationReceived,description="Model metadata of NotificationReceived",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,       
                 root=mmLicense,description="Model metadata of License",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)

    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=dssModelMetadataFields,description="DataSet structure of ModelMetadata-Fields",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=dssDataSetStructureStructureNode,description="DataSet structure of DataSetStructure-StructureNode",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode, 
                 root=eOrganizationKS,description="DataSet structure of Organization-KnowledgeServer",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=eOrganizationKS,                  
                 root=the_koa_org,description="Organization TheKoa.org",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id=ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssDataSetStructureStructureNode,
                 root=esLicenseList,description="DataSet structure of List of licenses",
                 version_major=0, version_minor=1, version_patch=0, version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssDataSetStructureStructureNode,
                 root=dssLicense,description="DataSet structure of a License",
                 version_major=0, version_minor=1, version_patch=0, version_description="",version_released=True)
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.set_dataset_on_instances();ei.save(using=db_alias)

    ######## BEGIN LICENSES DATA
    
    # Against DRM 
    adrm = License()
    adrm.name = "Against DRM"
    adrm.short_name = ""
    adrm.attribution = True
    adrm.share_alike = True
    adrm.url_info = "http://opendefinition.org/licenses/against-drm"
    adrm.reccomended_by_opendefinition = False
    adrm.conformant_for_opendefinition = True
    adrm.legalcode = ''
    adrm.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=adrm, version_major=2, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # Creative Commons Attribution 1.0
    ccby10 = License()
    ccby10.name = "Creative Commons Attribution 1.0"
    ccby10.short_name = "CC-BY-1.0"
    ccby10.attribution = True
    ccby10.share_alike = False
    ccby10.url_info = "http://creativecommons.org/licenses/by/1.0"
    ccby10.reccomended_by_opendefinition = False
    ccby10.conformant_for_opendefinition = True
    ccby10.legalcode = ''
    ccby10.save(using=db_alias)
    ei_ccby10 = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                        root=ccby10, version_major=1, version_minor=0, version_patch=0, version_description="")
    ei_ccby10.save(using=db_alias);ei_ccby10.first_version_id = ei_ccby10.id;ei_ccby10.save(using=db_alias)

    # above reccomended; below other conformant
    
    # Creative Commons CCZero
    cczero = License()
    cczero.name = "Creative Commons CCZero"
    cczero.short_name = "CC0"
    cczero.attribution = False
    cczero.share_alike = False
    cczero.url_info = "http://opendefinition.org/licenses/cc-zero"
    cczero.reccomended_by_opendefinition = True
    cczero.conformant_for_opendefinition = True
    cczero.legalcode = ''
    cczero.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=cczero, version_major=1, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # Open Data Commons Public Domain Dedication and Licence
    pddl = License()
    pddl.name = "Open Data Commons Public Domain Dedication and Licence"
    pddl.short_name = "PDDL"
    pddl.attribution = False
    pddl.share_alike = False
    pddl.url_info = "http://opendefinition.org/licenses/odc-pddl"
    pddl.reccomended_by_opendefinition = True
    pddl.conformant_for_opendefinition = True
    pddl.legalcode = ''
    pddl.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=pddl, version_major=1, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # Creative Commons Attribution 4.0
    ccby40 = License()
    ccby40.name = "Creative Commons Attribution 4.0"
    ccby40.short_name = "CC-BY-4.0"
    ccby40.attribution = True
    ccby40.share_alike = False
    ccby40.url_info = "http://creativecommons.org/licenses/by/4.0"
    ccby40.reccomended_by_opendefinition = True
    ccby40.conformant_for_opendefinition = True
    ccby40.legalcode = ''
    ccby40.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ei_ccby10.id, dataset_structure=dssLicense,version_released=True, 
                 root=ccby40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias)

    # Open Data Commons Attribution License 
    odcby = License()
    odcby.name = "Open Data Commons Attribution License"
    odcby.short_name = "ODC-BY"
    odcby.attribution = True
    odcby.share_alike = False
    odcby.url_info = "http://opendefinition.org/licenses/odc-by"
    odcby.reccomended_by_opendefinition = True
    odcby.conformant_for_opendefinition = True
    odcby.legalcode = ''
    odcby.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=odcby, version_major=1, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # Creative Commons Attribution Share-Alike 4.0  
    ccbysa40 = License()
    ccbysa40.name = "Creative Commons Attribution Share-Alike 4.0"
    ccbysa40.short_name = "CC-BY-SA-4.0"
    ccbysa40.attribution = True
    ccbysa40.share_alike = True
    ccbysa40.url_info = "http://opendefinition.org/licenses/cc-by-sa"
    ccbysa40.reccomended_by_opendefinition = True
    ccbysa40.conformant_for_opendefinition = True
    ccbysa40.legalcode = ''
    ccbysa40.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=ccbysa40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # Open Data Commons Open Database License 
    odbl = License()
    odbl.name = "Open Data Commons Open Database License"
    odbl.short_name = "ODbL"
    odbl.attribution = True
    odbl.share_alike = False
    odbl.url_info = "http://opendefinition.org/licenses/odc-odbl"
    odbl.reccomended_by_opendefinition = True
    odbl.conformant_for_opendefinition = True
    odbl.legalcode = ''
    odbl.save(using=db_alias)
    ei = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=odbl, version_major=1, version_minor=0, version_patch=0, version_description="")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    ######## END LICENSES DATA

    # 2 DataSet/Views "License List"
    # opendefinition.org conformant
    ei = DataSet(knowledge_server=the_koa_org_ks, filter_text="conformant_for_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant licenses.")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

    # opendefinition.org conformant and reccomended
    ei = DataSet(knowledge_server=the_koa_org_ks, filter_text="reccomended_by_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant and reccomended licenses.")
    ei.save(using=db_alias);ei.first_version_id = ei.id;ei.save(using=db_alias)

class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0002_auto_20160309_0617'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

