# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations
from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure, StructureNode, ModelMetadata
from test1.models import Continent, SubContinent, State, Region, Province

def forwards_func(apps, schema_editor):
    new_org = Organization();new_org.name = "A test Organization";new_org.website = 'http://new_org.example.com';new_org.description = "";
    new_org.save()
    new_org_ks = KnowledgeServer(name="A test OKS.", scheme="http", netloc="test.thekoa.org", description="It has some datasets and structures", organization=new_org, this_ks=False, html_home="", html_disclaimer="")
    new_org_ks.save()
    
    dss_org = DataSetStructure.get_from_name(DataSetStructure.organization_DSN)
    ds = DataSet(description='', knowledge_server=new_org_ks, dataset_structure=dss_org, 
                 root=new_org, version_major=0, version_minor=1, version_patch=0, version_description="")
    ds.save()
    ds.set_released()
    
    new_org_ks.set_as_this_ks()
    new_org.regenerate_UKCL()
    new_org_ks = KnowledgeServer.this_knowledge_server('default')
    ds.regenerate_UKCL()
    
    mmContinent=ModelMetadata();mmContinent.name="Continent";mmContinent.module="test1";mmContinent.name_field="name";mmContinent.description_field="";mmContinent.save()
    mmSubContinent=ModelMetadata();mmSubContinent.name="SubContinent";mmSubContinent.module="test1";mmSubContinent.name_field="name";mmSubContinent.description_field="";mmSubContinent.save()
    mmState=ModelMetadata();mmState.name="State";mmState.module="test1";mmState.name_field="name";mmState.description_field="";mmState.save()


    
    c_sn=StructureNode();c_sn.model_metadata=mmContinent;c_sn.save()
    sc_sn=StructureNode();sc_sn.is_many=True;sc_sn.attribute="subcontinent_set";sc_sn.model_metadata=mmSubContinent;sc_sn.save()
    s_sn=StructureNode();s_sn.is_many=True;s_sn.attribute="state_set";s_sn.model_metadata=mmState;s_sn.save()
    c_sn.child_nodes.add(sc_sn);c_sn.child_nodes.add(s_sn)
    dssContinentState=DataSetStructure();dssContinentState.multiple_releases=False;
    dssContinentState.root_node=c_sn;dssContinentState.name="Test Continent-SubContinent-State";
    dssContinentState.description="Test Continent-SubContinent-State";
    dssContinentState.save()

    dss_dss = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN)
    
    ds = DataSet(description='Dataset for data set structure "Continent-SubContinent-State"', knowledge_server=new_org_ks, dataset_structure=dss_dss, root=dssContinentState, version_major=0, version_minor=1, version_patch=0, version_description="")
    ds.save();
    ds.set_released()
        
    mmContinent.dataset_structure=dssContinentState;mmContinent.save()
    mmSubContinent.dataset_structure=dssContinentState;mmSubContinent.save()
    mmState.dataset_structure=dssContinentState;mmState.save()
    
    dssModelMetadataFields=DataSetStructure.get_from_name(DataSetStructure.model_metadata_DSN)
    
    ds = DataSet(knowledge_server=new_org_ks,dataset_structure=dssModelMetadataFields,root = mmContinent,
                 description="Continent ModelMetadata",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 
    #secondo me questo set released non funziona perché la dssContinentState non è ancora materializzata; ma se lo facessimo
    #prima la sua materializzazione non funzionerebbe perché i mm non sono materializzati

    ds = DataSet(knowledge_server=new_org_ks,dataset_structure=dssModelMetadataFields,root = mmSubContinent,
                 description="SubContinent ModelMetadata",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 

    ds = DataSet(knowledge_server=new_org_ks,dataset_structure=dssModelMetadataFields,root = mmState,
                 description="State ModelMetadata",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 


    europe = Continent();europe.name="Europe";europe.save()
    asia = Continent();asia.name="Asia";asia.save()
    south_europe=SubContinent();south_europe.name="South Europe";south_europe.continent=europe;south_europe.save()
    central_europe=SubContinent();central_europe.name="Central Europe";central_europe.continent=europe;central_europe.save()
    italy=State();italy.name="Italy";italy.sub_continent=south_europe;italy.continent=europe;italy.save()
    spain=State();spain.name="Spain";spain.sub_continent=south_europe;spain.continent=europe;spain.save()
    germany=State();germany.name="Germany";germany.sub_continent=central_europe;germany.continent=europe;germany.save()
    
    ds = DataSet(knowledge_server=new_org_ks,dataset_structure=dssContinentState,root=europe,
                 description="Europe",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 
    ds = DataSet(knowledge_server=new_org_ks,dataset_structure=dssContinentState,root=asia,
                 description="Asia",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 


class Migration(migrations.Migration):

    dependencies = [
        ('test1', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

