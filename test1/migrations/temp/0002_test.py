# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations
from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure, StructureNode, ModelMetadata
from test1.models import Continent, SubContinent, State, Region, Province
from knowledge_server.utils import KsUrl

def forwards_func(apps, schema_editor):
    org_ks={
      "Organization": {"name": "A test Organization", "website": "http://new_org.example.com", "description": ""}, 
      "KnowledgeServer": {"name": "A test OKS.", "netloc": "test.thekoa.org", "description": "It has some datasets and structures", "html_home": "", "html_disclaimer": ""}
     }
    KnowledgeServer.create_this_ks(org_ks)
    this_ks_d = KnowledgeServer.this_knowledge_server('default')
    
    dssContinentState=DataSetStructure()
    dssContinentState.name="Test Continent-SubContinent-State";
    dssContinentState.SetNotNullFields()
    dssContinentState.save()

    mmContinent=dssContinentState.create_model_metadata(name="Continent",module="test1",name_field="name",description_field="")
    mmSubContinent=dssContinentState.create_model_metadata(name="SubContinent",module="test1",name_field="name",description_field="")
    mmState=dssContinentState.create_model_metadata(name="State",module="test1",name_field="name",description_field="")
    
    # It creates ModelMetadata and a DataSet for each of them; having the DataSetStructure makes it
    # possible to release and materialize the datasets with dangling references that will be
    # resolved once the dss is released and materialized. 
    KnowledgeServer.register_models([mmContinent, mmSubContinent, mmState])
     
    # it creates the root node from the ModelMetadata provided
    dssContinentState.root_model_metadata(mmContinent)
    # child nodes for two attributes/fields
    dssContinentState.root_node.children_for(["subcontinent_set", "state_set"], this_ks_d.netloc)
    dssContinentState.save()
    
    dss_dss = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN)
    
    ds = DataSet(description='DataSet for data set structure "Continent-SubContinent-State"', knowledge_server=this_ks_d, dataset_structure=dss_dss, root=dssContinentState, version_major=0, version_minor=1, version_patch=0, version_description="")
    ds.save();
    ds.set_released()
        
    europe = Continent();europe.name="Europe";europe.save()
    asia = Continent();asia.name="Asia";asia.save()
    south_europe=SubContinent();south_europe.name="South Europe";south_europe.continent=europe;south_europe.save()
    central_europe=SubContinent();central_europe.name="Central Europe";central_europe.continent=europe;central_europe.save()
    italy=State();italy.name="Italy";italy.sub_continent=south_europe;italy.continent=europe;italy.save()
    spain=State();spain.name="Spain";spain.sub_continent=south_europe;spain.continent=europe;spain.save()
    germany=State();germany.name="Germany";germany.sub_continent=central_europe;germany.continent=europe;germany.save()
    
    ds = DataSet(knowledge_server=this_ks_d,dataset_structure=dssContinentState,root=europe,
                 description="Europe",version_major=0,version_minor=1,version_patch=0,version_description="")
    ds.save();ds.set_released(); 
    ds = DataSet(knowledge_server=this_ks_d,dataset_structure=dssContinentState,root=asia,
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

