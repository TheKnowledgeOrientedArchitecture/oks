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
    the_koa_org = Organization();the_koa_org.id=1;the_koa_org.name="theKOA.org";
    the_koa_org.UKCL="-";the_koa_org.website='http://www.theKOA.org';the_koa_org.logo='http://www.thekoa.org/sites/thekoa.org/files/logothekoa.org_.png';
    the_koa_org.description="The Knowledge Oriented Architecture organization.";the_koa_org.save(using=db_alias)
    
    the_koa_org_ks = KnowledgeServer(pk=1, name="Root Open Knowledge Server", scheme="http", netloc="root.beta.thekoa.org", 
                                     UKCL="-",
                                     description="The Open Knowledge Server serving the structures and datasets used by any other Knowledge Server.", 
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
    mmDanglingReference=ModelMetadata();mmDanglingReference.name="DanglingReference";mmDanglingReference.module="knowledge_server";mmDanglingReference.save(using=db_alias)

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
     
    # DATASETSTRUCTURE  dssOrganizationKS
    en18.child_nodes.add(en19); en18.save(using=db_alias)
    dssOrganizationKS=DataSetStructure(multiple_releases=False,root_node=en18,name=DataSetStructure.organization_DSN,
                                     description="An Organization and its Knowledge Servers",UKCL="")
    dssOrganizationKS.save(using=db_alias)
    mmOrganization.dataset_structure = dssOrganizationKS; mmOrganization.save(using=db_alias)
    mmKnowledgeServer.dataset_structure = dssOrganizationKS; mmKnowledgeServer.save(using=db_alias)

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
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root = mmModelMetadata,description="Model metadata of ModelMetadata",creation_date="2015-08-31",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
     
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,       
                 root=mmStructureNode,description="Model metadata of StructureNode",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmDataSetStructure,description="Model metadata of DataSetStructure",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmOrganization,description="Model metadata of Organization",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmDataSet,description="Model metadata of DataSet",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmKnowledgeServer,description="Model metadata of KnowledgeServer",    
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmEvent,description="Model metadata of Event",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmSubscriptionToThis,description="Model metadata of SubscriptionToThis",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmSubscriptionToOther,description="Model metadata of SubscriptionToOther",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmNotification,description="Model metadata of Notification",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmNotificationReceived,description="Model metadata of NotificationReceived",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmLicense,description="Model metadata of License",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssModelMetadataFields,owner_organization=the_koa_org,
                 root=mmDanglingReference,description="Model metadata of DanglingReference",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();

    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode,owner_organization=the_koa_org,
                 root=dssModelMetadataFields,description="DataSet structure of ModelMetadata-Fields",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode,owner_organization=the_koa_org,
                 root=dssDataSetStructureStructureNode,description="DataSet structure of DataSetStructure-StructureNode",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssDataSetStructureStructureNode,owner_organization=the_koa_org,
                 root=dssOrganizationKS,description="DataSet structure of Organization-KnowledgeServer",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks,dataset_structure=dssOrganizationKS,owner_organization=the_koa_org,
                 root=the_koa_org,description="Organization TheKoa.org",
                 version_major=0,version_minor=1,version_patch=0,version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssDataSetStructureStructureNode,owner_organization=the_koa_org,
                 root=esLicenseList,description="DataSet structure of List of licenses",
                 version_major=0, version_minor=1, version_patch=0, version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssDataSetStructureStructureNode,owner_organization=the_koa_org,
                 root=dssLicense,description="DataSet structure of a License",
                 version_major=0, version_minor=1, version_patch=0, version_description="",version_released=True)
    ds.save(using=db_alias);
    ds.set_dataset_on_instances();

    ######## BEGIN LICENSES DATA

    # Let's create the organizations to which we will attribute the licenses
    data_dict = {"name": "Creative Commons", "website": "http://creativecommons.org", "description": ""}
    cc_org = Organization.create_with_dataset(dssOrganizationKS, data_dict, db_alias, ks=the_koa_org_ks)

    
    ##################### Creative Commons Attribution #####################

    ccby10 = License()
    ccby10.name = "Creative Commons Attribution 1.0 Generic"
    ccby10.short_name = "CC-BY-1.0"
    ccby10.attribution = True
    ccby10.share_alike = False
    ccby10.commercial_use = True
    ccby10.derivatives = True
    ccby10.url_info = "http://creativecommons.org/licenses/by/1.0"
    ccby10.reccomended_by_opendefinition = False
    ccby10.conformant_for_opendefinition = True
    ccby10.legalcode = ''
    ccby10.save(using=db_alias)
    ds_ccby10 = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org,
                        root=ccby10, version_major=1, version_minor=0, version_patch=0, version_description="")
    ds_ccby10.save(using=db_alias)

    ccby20 = License()
    ccby20.name = "Creative Commons Attribution 2.0 Generic"
    ccby20.short_name = "CC-BY-2.0"
    ccby20.attribution = True
    ccby20.share_alike = False
    ccby20.commercial_use = True
    ccby20.derivatives = True
    ccby20.url_info = "http://creativecommons.org/licenses/by/2.0"
    ccby20.reccomended_by_opendefinition = False
    ccby20.conformant_for_opendefinition = True
    ccby20.legalcode = ''
    ccby20.save(using=db_alias)
    ds_ccby20 = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ds_ccby10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccby20, version_major=2, version_minor=0, version_patch=0, version_description="")
    ds_ccby20.save(using=db_alias)

    ccby25 = License()
    ccby25.name = "Creative Commons Attribution 2.5 Generic"
    ccby25.short_name = "CC-BY-2.5"
    ccby25.attribution = True
    ccby25.share_alike = False
    ccby25.commercial_use = True
    ccby25.derivatives = True
    ccby25.url_info = "http://creativecommons.org/licenses/by/2.5"
    ccby25.reccomended_by_opendefinition = False
    ccby25.conformant_for_opendefinition = True
    ccby25.legalcode = ''
    ccby25.save(using=db_alias)
    ds_ccby25 = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ds_ccby10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccby25, version_major=2, version_minor=5, version_patch=0, version_description="")
    ds_ccby25.save(using=db_alias)

    ccby30 = License()
    ccby30.name = "Creative Commons Attribution 3.0 Unported"
    ccby30.short_name = "CC-BY-3.0"
    ccby30.attribution = True
    ccby30.share_alike = False
    ccby30.commercial_use = True
    ccby30.derivatives = True
    ccby30.url_info = "http://creativecommons.org/licenses/by/2.0"
    ccby30.reccomended_by_opendefinition = False
    ccby30.conformant_for_opendefinition = True
    ccby30.legalcode = ''
    ccby30.save(using=db_alias)
    ds_ccby30 = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ds_ccby10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccby30, version_major=3, version_minor=0, version_patch=0, version_description="")
    ds_ccby30.save(using=db_alias)

    ccby40 = License()
    ccby40.name = "Creative Commons Attribution 4.0 International"
    ccby40.short_name = "CC-BY-4.0"
    ccby40.attribution = True
    ccby40.share_alike = False
    ccby40.commercial_use = True
    ccby40.derivatives = True
    ccby40.url_info = "http://creativecommons.org/licenses/by/4.0"
    ccby40.reccomended_by_opendefinition = True
    ccby40.conformant_for_opendefinition = True
    ccby40.legalcode = ''
    ccby40.save(using=db_alias)
    ds_ccby40 = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ds_ccby10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccby40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds_ccby40.save(using=db_alias)
    ds_ccby40.licenses.add(ccby40)
    ds_ccby40.save(using=db_alias)

    # On creativecommons.org "Except where otherwise noted, content on this site is licensed under a Creative Commons Attribution 4.0 International license." 
    ds_ccby10.licenses.add(ccby40)
    ds_ccby10.save(using=db_alias)
    ds_ccby20.licenses.add(ccby40)
    ds_ccby20.save(using=db_alias)
    ds_ccby25.licenses.add(ccby40)
    ds_ccby25.save(using=db_alias)
    ds_ccby30.licenses.add(ccby40)
    ds_ccby30.save(using=db_alias)

    ##################### END Creative Commons Attribution #####################

    # Creative Commons CCZero
    cczero = License()
    cczero.name = "Creative Commons CCZero"
    cczero.short_name = "CC0"
    cczero.attribution = False
    cczero.share_alike = False
    cczero.commercial_use = True
    cczero.derivatives = True
    cczero.url_info = "http://creativecommons.org/publicdomain/zero/1.0/"
    cczero.reccomended_by_opendefinition = True
    cczero.conformant_for_opendefinition = True
    cczero.legalcode = ''
    cczero.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=cczero, version_major=1, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### Creative Commons Attribution-ShareAlike #####################

    ccbysa10 = License()
    ccbysa10.name = "Creative Commons Attribution-ShareAlike 1.0 Generic"
    ccbysa10.short_name = "CC-BY-SA-1.0"
    ccbysa10.attribution = True
    ccbysa10.share_alike = True
    ccbysa10.commercial_use = True
    ccbysa10.derivatives = True
    ccbysa10.url_info = "http://creativecommons.org/licenses/by-sa/1.0/"
    ccbysa10.reccomended_by_opendefinition = False
    ccbysa10.conformant_for_opendefinition = True
    ccbysa10.legalcode = ''
    ccbysa10.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbysa10, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbysa20 = License()
    ccbysa20.name = "Creative Commons Attribution-ShareAlike 2.0 Generic"
    ccbysa20.short_name = "CC-BY-SA-2.0"
    ccbysa20.attribution = True
    ccbysa20.share_alike = True
    ccbysa20.commercial_use = True
    ccbysa20.derivatives = True
    ccbysa20.url_info = "http://creativecommons.org/licenses/by-sa/2.0"
    ccbysa20.reccomended_by_opendefinition = False
    ccbysa20.conformant_for_opendefinition = True
    ccbysa20.legalcode = ''
    ccbysa20.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbysa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbysa20, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbysa25 = License()
    ccbysa25.name = "Creative Commons Attribution-ShareAlike 2.5 Generic"
    ccbysa25.short_name = "CC-BY-SA-2.5"
    ccbysa25.attribution = True
    ccbysa25.share_alike = True
    ccbysa25.commercial_use = True
    ccbysa25.derivatives = True
    ccbysa25.url_info = "http://creativecommons.org/licenses/by-sa/2.5"
    ccbysa25.reccomended_by_opendefinition = False
    ccbysa25.conformant_for_opendefinition = True
    ccbysa25.legalcode = ''
    ccbysa25.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbysa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbysa25, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbysa30 = License()
    ccbysa30.name = "Creative Commons Attribution-ShareAlike 3.0 Unported"
    ccbysa30.short_name = "CC-BY-SA-3.0"
    ccbysa30.attribution = True
    ccbysa30.share_alike = True
    ccbysa30.commercial_use = True
    ccbysa30.derivatives = True
    ccbysa30.url_info = "http://creativecommons.org/licenses/by-sa/3.0"
    ccbysa30.reccomended_by_opendefinition = False
    ccbysa30.conformant_for_opendefinition = True
    ccbysa30.legalcode = ''
    ccbysa30.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbysa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbysa30, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbysa40 = License()
    ccbysa40.name = "Creative Commons Attribution-ShareAlike 4.0 International"
    ccbysa40.short_name = "CC-BY-SA-4.0"
    ccbysa40.attribution = True
    ccbysa40.share_alike = True
    ccbysa40.commercial_use = True
    ccbysa40.derivatives = True
    ccbysa40.url_info = "http://creativecommons.org/licenses/by-sa/4.0"
    ccbysa40.reccomended_by_opendefinition = True
    ccbysa40.conformant_for_opendefinition = True
    ccbysa40.legalcode = ''
    ccbysa40.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbysa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbysa40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### END Creative Commons Attribution-ShareAlike #####################

    ##################### Creative Commons Attribution-NonCommercial-ShareAlike #####################

    ccbyncsa10 = License()
    ccbyncsa10.name = "Creative Commons Attribution-NonCommercial-ShareAlike 1.0 Generic"
    ccbyncsa10.short_name = "CC BY-NC-SA 1.0"
    ccbyncsa10.attribution = True
    ccbyncsa10.share_alike = True
    ccbyncsa10.commercial_use = False
    ccbyncsa10.derivatives = True
    ccbyncsa10.url_info = "http://creativecommons.org/licenses/by-nc-sa/1.0/"
    ccbyncsa10.reccomended_by_opendefinition = False
    ccbyncsa10.conformant_for_opendefinition = False
    ccbyncsa10.legalcode = ''
    ccbyncsa10.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncsa10, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncsa20 = License()
    ccbyncsa20.name = "Creative Commons Attribution-NonCommercial-ShareAlike 2.0 Generic"
    ccbyncsa20.short_name = "CC BY-NC-SA 2.0"
    ccbyncsa20.attribution = True
    ccbyncsa20.share_alike = True
    ccbyncsa20.commercial_use = False
    ccbyncsa20.derivatives = True
    ccbyncsa20.url_info = "http://creativecommons.org/licenses/by-nc-sa/2.0"
    ccbyncsa20.reccomended_by_opendefinition = False
    ccbyncsa20.conformant_for_opendefinition = False
    ccbyncsa20.legalcode = ''
    ccbyncsa20.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncsa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncsa20, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncsa25 = License()
    ccbyncsa25.name = "Creative Commons Attribution-NonCommercial-ShareAlike 2.5 Generic"
    ccbyncsa25.short_name = "CC BY-NC-SA 2.5"
    ccbyncsa25.attribution = True
    ccbyncsa25.share_alike = True
    ccbyncsa25.commercial_use = False
    ccbyncsa25.derivatives = True
    ccbyncsa25.url_info = "http://creativecommons.org/licenses/by-nc-sa/2.5"
    ccbyncsa25.reccomended_by_opendefinition = False
    ccbyncsa25.conformant_for_opendefinition = False
    ccbyncsa25.legalcode = ''
    ccbyncsa25.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncsa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncsa25, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncsa30 = License()
    ccbyncsa30.name = "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported"
    ccbyncsa30.short_name = "CC BY-NC-SA 3.0"
    ccbyncsa30.attribution = True
    ccbyncsa30.share_alike = True
    ccbyncsa30.commercial_use = False
    ccbyncsa30.derivatives = True
    ccbyncsa30.url_info = "http://creativecommons.org/licenses/by-nc-sa/3.0"
    ccbyncsa30.reccomended_by_opendefinition = False
    ccbyncsa30.conformant_for_opendefinition = False
    ccbyncsa30.legalcode = ''
    ccbyncsa30.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncsa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncsa30, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncsa40 = License()
    ccbyncsa40.name = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International"
    ccbyncsa40.short_name = "CC BY-NC-SA 4.0"
    ccbyncsa40.attribution = True
    ccbyncsa40.share_alike = True
    ccbyncsa40.commercial_use = False
    ccbyncsa40.derivatives = True
    ccbyncsa40.url_info = "http://creativecommons.org/licenses/by-nc-sa/4.0"
    ccbyncsa40.reccomended_by_opendefinition = False
    ccbyncsa40.conformant_for_opendefinition = False
    ccbyncsa40.legalcode = ''
    ccbyncsa40.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncsa10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncsa40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### END Creative Commons NonCommercial-Attribution-ShareAlike #####################


    ##################### Creative Commons Attribution-NoDerivs-NonCommercial #####################

    ccbyncnd10 = License()
    ccbyncnd10.name = "Creative Commons Attribution-NoDerivs-NonCommercial 1.0 Generic"
    ccbyncnd10.short_name = "CC BY-NC-ND 1.0"
    ccbyncnd10.attribution = True
    ccbyncnd10.share_alike = True
    ccbyncnd10.commercial_use = False
    ccbyncnd10.derivatives = False
    ccbyncnd10.url_info = "http://creativecommons.org/licenses/by-nc-nd/1.0/"
    ccbyncnd10.reccomended_by_opendefinition = False
    ccbyncnd10.conformant_for_opendefinition = False
    ccbyncnd10.legalcode = ''
    ccbyncnd10.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncnd10, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncnd20 = License()
    ccbyncnd20.name = "Creative Commons Attribution-NonCommercial-NoDerivs 2.0 Generic"
    ccbyncnd20.short_name = "CC BY-NC-ND 2.0"
    ccbyncnd20.attribution = True
    ccbyncnd20.share_alike = True
    ccbyncnd20.commercial_use = False
    ccbyncnd20.derivatives = False
    ccbyncnd20.url_info = "http://creativecommons.org/licenses/by-nc-nd/2.0"
    ccbyncnd20.reccomended_by_opendefinition = False
    ccbyncnd20.conformant_for_opendefinition = False
    ccbyncnd20.legalcode = ''
    ccbyncnd20.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncnd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncnd20, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncnd25 = License()
    ccbyncnd25.name = "Creative Commons Attribution-NonCommercial-NoDerivs 2.5 Generic"
    ccbyncnd25.short_name = "CC BY-NC-ND 2.5"
    ccbyncnd25.attribution = True
    ccbyncnd25.share_alike = True
    ccbyncnd25.commercial_use = False
    ccbyncnd25.derivatives = False
    ccbyncnd25.url_info = "http://creativecommons.org/licenses/by-nc-nd/2.5"
    ccbyncnd25.reccomended_by_opendefinition = False
    ccbyncnd25.conformant_for_opendefinition = False
    ccbyncnd25.legalcode = ''
    ccbyncnd25.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncnd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncnd25, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncnd30 = License()
    ccbyncnd30.name = "Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported"
    ccbyncnd30.short_name = "CC BY-NC-ND 3.0"
    ccbyncnd30.attribution = True
    ccbyncnd30.share_alike = True
    ccbyncnd30.commercial_use = False
    ccbyncnd30.derivatives = False
    ccbyncnd30.url_info = "http://creativecommons.org/licenses/by-nc-nd/3.0"
    ccbyncnd30.reccomended_by_opendefinition = False
    ccbyncnd30.conformant_for_opendefinition = False
    ccbyncnd30.legalcode = ''
    ccbyncnd30.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncnd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncnd30, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbyncnd40 = License()
    ccbyncnd40.name = "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International"
    ccbyncnd40.short_name = "CC BY-NC-ND 4.0"
    ccbyncnd40.attribution = True
    ccbyncnd40.share_alike = True
    ccbyncnd40.commercial_use = False
    ccbyncnd40.derivatives = False
    ccbyncnd40.url_info = "http://creativecommons.org/licenses/by-nc-nd/4.0"
    ccbyncnd40.reccomended_by_opendefinition = False
    ccbyncnd40.conformant_for_opendefinition = False
    ccbyncnd40.legalcode = ''
    ccbyncnd40.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbyncnd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbyncnd40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### END Creative Commons Attribution-NoDerivs-NonCommercial #####################



    ##################### Creative Commons Attribution-NonCommercial #####################

    ccbync10 = License()
    ccbync10.name = "Creative Commons Attribution-NonCommercial 1.0 Generic"
    ccbync10.short_name = "CC BY-NC 1.0"
    ccbync10.attribution = True
    ccbync10.share_alike = True
    ccbync10.commercial_use = False
    ccbync10.derivatives = True
    ccbync10.url_info = "http://creativecommons.org/licenses/by-nc/1.0/"
    ccbync10.reccomended_by_opendefinition = False
    ccbync10.conformant_for_opendefinition = False
    ccbync10.legalcode = ''
    ccbync10.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbync10, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbync20 = License()
    ccbync20.name = "Creative Commons Attribution-NonCommercial 2.0 Generic"
    ccbync20.short_name = "CC BY-NC 2.0"
    ccbync20.attribution = True
    ccbync20.share_alike = True
    ccbync20.commercial_use = False
    ccbync20.derivatives = True
    ccbync20.url_info = "http://creativecommons.org/licenses/by-nc/2.0"
    ccbync20.reccomended_by_opendefinition = False
    ccbync20.conformant_for_opendefinition = False
    ccbync20.legalcode = ''
    ccbync20.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbync10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbync20, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbync25 = License()
    ccbync25.name = "Creative Commons Attribution-NonCommercial 2.5 Generic"
    ccbync25.short_name = "CC BY-NC 2.5"
    ccbync25.attribution = True
    ccbync25.share_alike = True
    ccbync25.commercial_use = False
    ccbync25.derivatives = True
    ccbync25.url_info = "http://creativecommons.org/licenses/by-nc/2.5"
    ccbync25.reccomended_by_opendefinition = False
    ccbync25.conformant_for_opendefinition = False
    ccbync25.legalcode = ''
    ccbync25.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbync10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbync25, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbync30 = License()
    ccbync30.name = "Creative Commons Attribution-NonCommercial 3.0 Unported"
    ccbync30.short_name = "CC BY-NC 3.0"
    ccbync30.attribution = True
    ccbync30.share_alike = True
    ccbync30.commercial_use = False
    ccbync30.derivatives = True
    ccbync30.url_info = "http://creativecommons.org/licenses/by-nc/3.0"
    ccbync30.reccomended_by_opendefinition = False
    ccbync30.conformant_for_opendefinition = False
    ccbync30.legalcode = ''
    ccbync30.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbync10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbync30, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbync40 = License()
    ccbync40.name = "Creative Commons Attribution-NonCommercial 4.0 International"
    ccbync40.short_name = "CC BY-NC 4.0"
    ccbync40.attribution = True
    ccbync40.share_alike = True
    ccbync40.commercial_use = False
    ccbync40.derivatives = True
    ccbync40.url_info = "http://creativecommons.org/licenses/by-nc/4.0"
    ccbync40.reccomended_by_opendefinition = False
    ccbync40.conformant_for_opendefinition = False
    ccbync40.legalcode = ''
    ccbync40.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbync10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbync40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### END Creative Commons Attribution-NonCommercial #####################



    ##################### Creative Commons Attribution-NoDerivatives #####################

    ccbynd10 = License()
    ccbynd10.name = "Creative Commons Attribution-NoDerivs-NonCommercial 1.0 Generic"
    ccbynd10.short_name = "CC BY-ND 1.0"
    ccbynd10.attribution = True
    ccbynd10.share_alike = True
    ccbynd10.commercial_use = False
    ccbynd10.derivatives = False
    ccbynd10.url_info = "http://creativecommons.org/licenses/by-nd/1.0/"
    ccbynd10.reccomended_by_opendefinition = False
    ccbynd10.conformant_for_opendefinition = False
    ccbynd10.legalcode = ''
    ccbynd10.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbynd10, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbynd20 = License()
    ccbynd20.name = "Creative Commons Attribution-NonCommercial-NoDerivs 2.0 Generic"
    ccbynd20.short_name = "CC BY-ND 2.0"
    ccbynd20.attribution = True
    ccbynd20.share_alike = True
    ccbynd20.commercial_use = False
    ccbynd20.derivatives = False
    ccbynd20.url_info = "http://creativecommons.org/licenses/by-nd/2.0"
    ccbynd20.reccomended_by_opendefinition = False
    ccbynd20.conformant_for_opendefinition = False
    ccbynd20.legalcode = ''
    ccbynd20.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbynd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbynd20, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbynd25 = License()
    ccbynd25.name = "Creative Commons Attribution-NonCommercial-NoDerivs 2.5 Generic"
    ccbynd25.short_name = "CC BY-ND 2.5"
    ccbynd25.attribution = True
    ccbynd25.share_alike = True
    ccbynd25.commercial_use = False
    ccbynd25.derivatives = False
    ccbynd25.url_info = "http://creativecommons.org/licenses/by-nd/2.5"
    ccbynd25.reccomended_by_opendefinition = False
    ccbynd25.conformant_for_opendefinition = False
    ccbynd25.legalcode = ''
    ccbynd25.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbynd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbynd25, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbynd30 = License()
    ccbynd30.name = "Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported"
    ccbynd30.short_name = "CC BY-ND 3.0"
    ccbynd30.attribution = True
    ccbynd30.share_alike = True
    ccbynd30.commercial_use = False
    ccbynd30.derivatives = False
    ccbynd30.url_info = "http://creativecommons.org/licenses/by-nd/3.0"
    ccbynd30.reccomended_by_opendefinition = False
    ccbynd30.conformant_for_opendefinition = False
    ccbynd30.legalcode = ''
    ccbynd30.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbynd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbynd30, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ccbynd40 = License()
    ccbynd40.name = "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International"
    ccbynd40.short_name = "CC BY-ND 4.0"
    ccbynd40.attribution = True
    ccbynd40.share_alike = True
    ccbynd40.commercial_use = False
    ccbynd40.derivatives = False
    ccbynd40.url_info = "http://creativecommons.org/licenses/by-nd/4.0"
    ccbynd40.reccomended_by_opendefinition = False
    ccbynd40.conformant_for_opendefinition = False
    ccbynd40.legalcode = ''
    ccbynd40.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, first_version_id=ccbynd10.id, dataset_structure=dssLicense,version_released=True,owner_organization=cc_org, 
                 root=ccbynd40, version_major=4, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(ccby40)
    ds.save(using=db_alias)

    ##################### END Creative Commons Attribution-NoDerivatives #####################

    # Against DRM 
    adrm = License()
    adrm.name = "Against DRM"
    adrm.short_name = ""
    adrm.legalcode = '''
<p>
<strong>1. Definitions</strong><br /><br />

<strong>Access control mechanism</strong>: a technological measure which, in the ordinary course of its operation, requires the application of information, or a process or a treatment, with the authority of the copyright owner or related rights owner, to gain access to the work.<br /><br />

<strong>Acts authorised by licensor</strong>: acts concerning granted rights (in particular, act of access, act of copy, act of modification, act of sharing).<br /><br />

<strong>Acts not authorised by licensor</strong>: acts concerning copyright or possible moral rights.<br /><br />

<strong>Author/s</strong>: the creator/s of an original work or the creator/s of a derivative work.<br /><br />

<strong>Broadcasting</strong>: the use of any means of distribution over a distance, such as telegraph, telephone, radio, television and other comparable media, including communication to the public by satellite and cable retransmission.<br /><br />

<strong>Copy control mechanism</strong>: a technological measure which, in the ordinary course of its operation, prevents, restricts, or otherwise limits the exercise of a right of the copyright owner or related rights owner.<br /><br />

<strong>Derivative work</strong>: a work based upon the copyrightable work released under the terms and the conditions of this license.<br /><br />

<strong>Distribution</strong>: the marketing, the placing in circulation or the making available to the public, by whatever means and for whatever purpose, of a work or of copies thereof.<br /><br />

<strong>Elaboration</strong>: all forms of modification, adaptation and transformation of a work.<br /><br />

<strong>Lending</strong>: the making available for use of originals, of copies or of carriers of copyright works, for a limited period of time and for purposes other than those referred to in the paragraph 16.<br /><br />

<strong>Licensee</strong>: the person acquiring rights under the terms and the conditions of this license.<br /><br />

<strong>Licensor</strong>: the person offering the work under the terms and the conditions of this license.<br /><br />

<strong>Moral rights</strong>: the author's right, recognized in some countries, to claim authorship of the work and to object to any distortion, mutilation or other modification of, or other derogatory action in relation to, the said work, which would be prejudicial to his honor or reputation; other author's rights recognized as moral rights in some countries.<br /><br />

<strong>Original work</strong>: a work not based upon another work.<br /><br />

<strong>Related rights</strong>: the rights that belong to the performers, the producers of phonograms and broadcasting organizations in relation to their performances, phonograms and broadcasts respectively.<br /><br />

<strong>Rental</strong>: the making available for use of originals, of copies or of carriers of copyright works, for a limited period of time and for direct or indirect economic or commercial advantage.<br /><br />

<strong>Reproduction</strong>: the multiplication of copies of a work by any means, such as copying by hand, printing, lithography, engraving, photography, phonography, cinematography and any other process of reproduction.<br /><br />

<strong>Transcription</strong>: the use of means suitable for transforming an oral work into a written work or into a work reproduced by one of the methods referred to in the preceding paragraph.<br /><br />

<strong>Translation</strong>: the translation of the work into another language or dialect.<br /><br />

<strong>Work</strong>: the copyrightable work released under the terms and the conditions of this license.<br /><br /></p>


<p>
<strong>2. License's area of applicability</strong><br /><br />

This license concerns copyright and related rights: this license does not treat any other right.<br /><br />

Nothing in this license is intended to prevent or restrict the exercise of rights not treated in this license,
such as rights concerning privacy, private property, sale and other personal or private rights.<br /><br />

Nothing in this license is intended to prevent or restrict the private use of any lawful technological measure.<br /><br />

Nothing in this license is intended to prevent or restrict any limitation on the exclusive rights of the copyright owner or related rights owner under copyright law or other applicable law.<br /><br />

This license is applicable to the works of the mind having a creative character and belonging to literature, music, figurative arts, architecture, theater or cinematography, whatever their mode or form of expression.<br /><br /></p>


<p>
<strong>3. Object</strong><br /><br />

In particular, this license is applicable to:<br /><br />

a. literary, dramatic, scientific, didactic and religious works, whether in written or oral form;<br /><br />

b. musical works and compositions, with or without words, dramatico-musical works and musical variations that themselves constitute original works;<br /><br />

c. choreographic works and works of dumb show, the form of which is fixed in writing or otherwise;<br /><br />

d. works of sculpture, painting, drawing, engraving and similar figurative arts, including scenic art;<br /><br />

e. architectural plans and works;<br /><br />

f. works of cinematographic art, whether silent or with sound;<br /><br />

g. works of photographic art and works expressed with processes analogous to photography;<br /><br />

h. industrial design works that have creative character or inherent artistic character;<br /><br />

i. collective works formed by the assembling of works, or parts of works, and possessing the character of a self-contained creation resulting from selection and coordination with a specific literary, scientific, didactic, religious, political or artistic aim, such as encyclopedias, dictionaries, anthologies, magazines and newspapers;<br /><br />

j. works of a creative character derived from any such work, such as translations into another language, transformations into any other literary or artistic form, modifications and additions constituting a substantial remodeling of the original work, adaptations, arrangements, abridgments and variations which do not constitute an original work.<br /><br /></p>


<p>
<strong>4. Grant of rights</strong><br /><br />

Licensor authorizes licensee to exercise the following rights:<br />
a. right of reproduction;<br />
b. right of distribution;<br />
c. right of publishing (also in a collection);<br />
d. right of public performance or recitation;<br />
e. right of broadcasting;<br />
f. right of modification;<br />
g. right of elaboration;<br />
h. right of transcription;<br />
i. right of translation;<br />
j. right of lending;<br />
k. right of rental;<br />
l. right of commercial use.<br /><br /></p>


<p>
<strong>5. Related rights and sublicensing</strong><br /><br />

Licensor declares to be related rights owner and he authorizes licensee to exercise them.<br /><br />

If the work is not object of related rights, preceding paragraph must be considered as void and having no legal effect.<br /><br />

Licensee may not sublicense the work.<br /><br /></p>


<p>
<strong>6. No DRM</strong><br /><br />

This license is incompatible with any technology, device or component that, in the normal course of its operation, is designed to prevent or restrict acts which are authorised or not authorised by licensor:
this incompatibility causes the inapplicability of the license to the work.<br /><br />

In particular:<br />
a. it is not possible to release validly under this license works or derivative works whose access control mechanism and/or copy control mechanism prevents or restricts quantitatively and/or qualitatively access to, fruition, copy, modification and/or sharing of them;<br />
b. in conformity with this license, it is not allowed to prevent or restrict quantitatively and/or qualitatively access to, fruition, copy, modification, and/or sharing of works or derivative works through an access control mechanism and/or a copy control mechanism;<br />
c. in conformity with this license, it is not allowed to prevent or restrict the exercise of a granted right through any digital, analog or physical method.<br /><br /></p>


<p>
<strong>7. Copyleft clause</strong><br /><br />

Derivative works, performances of the work, phonograms in which the work is fixed, broadcastings of the work must be released with a license that provides:<br />
a. the renunciation to exclusive exercise of rights referred to in the articles 4 and 5;<br />
b. the same type of clause described in article 6;<br />
c. the same type of clause described in this article.<br /><br /></p>


<p>
<strong>8. Resolutory clause</strong><br /><br />

Any breach of this license (in particular, the breach of the articles 6 and 7) will automatically void this license, without the necessity of any communication from licensor.<br />

<br /></p>


<p>
<strong>9. DISCLAIMER</strong><br /><br />

TO THE EXTENT PERMITTED BY APPLICABLE LAW, LICENSOR OFFERS THE WORK "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED. TO THE EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT WILL LICENSOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY OR CONSEQUENTIAL DAMAGES HOWEVER CAUSED.<br /><br /></p>


<p>
<strong>10. Copyright notice</strong><br /><br />

[Original work] Copyright (C) [year/s] [name/s of author/s]<br />
[Work] Copyright (C) [year/s] [name/s of author/s]<br />
[Derivative work] Copyright (C) [year/s] [name/s of author/s]<br /><br />

Licensee must keep intact copyright notice and all notices that refer to this license.<br /><br />

Licensee must include a copy of this license with every copy of the work the licensee distributes, publicly demonstrates or publicly performs.<br /><br /></p>'''
    adrm.attribution = True
    adrm.share_alike = True
    adrm.commercial_use = True
    adrm.derivatives = True
    adrm.url_info = "http://www.freecreations.org/Against_DRM2.html"
    adrm.reccomended_by_opendefinition = False
    adrm.conformant_for_opendefinition = True
    adrm.legalcode = ''
    adrm.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True,
                 root=adrm, version_major=2, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)
    ds.licenses.add(adrm)
    ds.save(using=db_alias)

    
    
    # Open Data Commons Public Domain Dedication and Licence
    pddl = License()
    pddl.name = "Open Data Commons Public Domain Dedication and Licence"
    pddl.short_name = "PDDL"
    pddl.attribution = False
    pddl.share_alike = False
    pddl.commercial_use = True
    pddl.derivatives = True
    pddl.url_info = "http://opendatacommons.org/licenses/pddl/1.0/"
    pddl.reccomended_by_opendefinition = True
    pddl.conformant_for_opendefinition = True
    pddl.legalcode = ''
    pddl.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=pddl, version_major=1, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)

    # Open Data Commons Attribution License 
    odcby = License()
    odcby.name = "Open Data Commons Attribution License"
    odcby.short_name = "ODC-BY"
    odcby.attribution = True
    odcby.share_alike = False
    odcby.commercial_use = True
    odcby.derivatives = True
    odcby.url_info = "http://opendatacommons.org/licenses/by/1.0/"
    odcby.reccomended_by_opendefinition = True
    odcby.conformant_for_opendefinition = True
    odcby.legalcode = ''
    odcby.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=odcby, version_major=1, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)

    # Open Data Commons Open Database License 
    odbl = License()
    odbl.name = "Open Data Commons Open Database License"
    odbl.short_name = "ODbL"
    odbl.attribution = True
    odbl.share_alike = False
    odbl.commercial_use = True
    odbl.derivatives = True
    odbl.url_info = "http://opendatacommons.org/licenses/odbl/1.0/"
    odbl.reccomended_by_opendefinition = True
    odbl.conformant_for_opendefinition = True
    odbl.legalcode = ''
    odbl.save(using=db_alias)
    ds = DataSet(knowledge_server=the_koa_org_ks, dataset_structure=dssLicense,version_released=True, 
                 root=odbl, version_major=1, version_minor=0, version_patch=0, version_description="")
    ds.save(using=db_alias)

    ######## END LICENSES DATA

    # 2 DataSet/Views "License List"
    # opendefinition.org conformant
    ds = DataSet(knowledge_server=the_koa_org_ks, filter_text="conformant_for_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant licenses.")
    ds.save(using=db_alias)

    # opendefinition.org conformant and reccomended
    ds = DataSet(knowledge_server=the_koa_org_ks, filter_text="reccomended_by_opendefinition=True", dataset_structure=esLicenseList, description="All opendefinition.org conformant and reccomended licenses.")
    ds.save(using=db_alias)

    # Now that I have licenses I can assign them to each initial DataSet I have created so far
    # ccbysa40 o ccby40 ?? 
    for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssModelMetadataFields):
        ds.licenses.add(ccbysa40)
        ds.save()
    for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssDataSetStructureStructureNode):
        ds.licenses.add(ccbysa40)
        ds.save()
    for ds in DataSet.objects.using(db_alias).filter(dataset_structure=dssOrganizationKS):
        ds.licenses.add(ccbysa40)
        ds.save()
    
class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0002_auto_20160309_0617'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

