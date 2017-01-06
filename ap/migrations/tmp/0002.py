# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import migrations

from knowledge_server.models import KnowledgeServer, DataSet, DataSetStructure, Workflow


def forwards_func(apps, schema_editor):
    this_ks_d = KnowledgeServer.this_knowledge_server('default')

    dss_workflow = DataSetStructure(name='Workflow')
    dss_workflow.description = 'Workflow-Method-Attribute-PermissionStatement'
    dss_workflow.SetNotNullFields()
    dss_workflow.save()

    mm_workflow = Workflow().get_model_metadata(db_alias='default')
    models_for_dss_workflow = [
        {"name": "Attribute", "module": "ap", "name_field": "", "description_field": ""},
        {"name": "Widget", "module": "ap", "name_field": "", "description_field": ""},
        {"name": "AttributeInAMethod", "module": "ap", "name_field": "", "description_field": ""},
        {"name": "PermissionStatement", "module": "ap", "name_field": "", "description_field": ""},
    ]
    mm_attribute, mm_widget, mm_attribute_in_a_method, mm_permission_statement, mm_permission_holder = dss_workflow.create_many_model_metadata(models_for_dss_workflow)

    mm_workflow_method = dss_workflow.create_model_metadata(name="WorkflowMethod",module="ap")
    mm_attribute = dss_workflow.create_model_metadata(name="Attribute",module="ap",name_field="",description_field="")
    mm_widget = dss_workflow.create_model_metadata(name="Widget",module="ap",name_field="",description_field="")
    mm_attribute_in_a_method = dss_workflow.create_model_metadata(name="AttributeInAMethod",module="ap",name_field="",description_field="")
    mm_permission_statement = dss_workflow.create_model_metadata(name="PermissionStatement",module="ap",name_field="",description_field="")
    # check quale DSS
    mm_attribute_type = dss_workflow.create_model_metadata( name="AttributeType", module="ap" )
    mm_attribute_group = dss_workflow.create_model_metadata( name="AttributeGroup", module="ap" )
    # WorkflowsMethods è un many to many through, va fatto ?
    WorkflowTransition
    Application
    ModelMetadataSearch
    ApplicationStructureNodeSearch
    AttributeInASearch
    KSUser
    KSRole
    KSGroup
    # check quale DSS; sul diagramma sul foglio?

    # It creates a DataSet for each of them; having the DataSetStructure makes it
    # possible to release and materialize the datasets with dangling references that will be
    # resolved once the dss is released and materialized. 
    KnowledgeServer.register_models([mm_workflow_method, mm_attribute_in_a_method, mm_permission_statement, mm_attribute, mm_attribute_type, mm_attribute_group, mm_widget, mm_permission_holder])

    # it creates the root node from the ModelMetadata provided
    dss_workflow.root_model_metadata(mm_workflow)
    # child nodes for two attributes/fields
    dss_workflow.root_node.children_nodes_for(["methods"], this_ks_d.netloc)
    dss_workflow.root_node.children_external_references_nodes_for( [ "type" ], this_ks_d.netloc )

    method_node = dss_workflow.root_node.child_nodes.all()[0]
    method_node.children_external_references_nodes_for(["initial_statuses", "final_status"], this_ks_d.netloc)
    method_node.children_nodes_for(["attributeinamethod_set", "permission"], this_ks_d.netloc)
    attribute_in_a_method_node = [cn for cn in method_node.child_nodes.all() if cn.attribute == "attributeinamethod_set"][0]
    attribute_in_a_method_node.children_external_references_nodes_for( [ "attribute", "custom_widget" ], this_ks_d.netloc )

    permission_node = [cn for cn in method_node.child_nodes.all() if cn.attribute == "permission"][0]
    permission_node.children_external_references_nodes_for( [ "permission_holder" ], this_ks_d.netloc )

    dss_workflow.save()
    
    dss_dss = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN)
    ds = DataSet(description='DataSet for data set structure "Workflow-Method-Attribute-PermissionStatement"', knowledge_server=this_ks_d, dataset_structure=dss_dss, root=dss_workflow, version_major=0, version_minor=1, version_patch=0, version_description="")
    ds.save()
    ds.set_released()
        

    # Application now is on its own dataset structure so we don't create it and just use the shallow one
    mm_application = dss_workflow.create_model_metadata(name='Application',module='ap',name_field="name",description_field="description")
    KnowledgeServer.register_models([mm_application])



#     europe = Continent();europe.name="Europe";europe.save()
#     asia = Continent();asia.name="Asia";asia.save()
#     south_europe=SubContinent();south_europe.name="South Europe";south_europe.continent=europe;south_europe.save()
#     central_europe=SubContinent();central_europe.name="Central Europe";central_europe.continent=europe;central_europe.save()
#     italy=State();italy.name="Italy";italy.sub_continent=south_europe;italy.continent=europe;italy.save()
#     spain=State();spain.name="Spain";spain.sub_continent=south_europe;spain.continent=europe;spain.save()
#     germany=State();germany.name="Germany";germany.sub_continent=central_europe;germany.continent=europe;germany.save()
#     
#     ds = DataSet(knowledge_server=this_ks_d,dataset_structure=dssContinentState,root=europe,
#                  description="Europe",version_major=0,version_minor=1,version_patch=0,version_description="")
#     ds.save();ds.set_released(); 
#     ds = DataSet(knowledge_server=this_ks_d,dataset_structure=dssContinentState,root=asia,
#                  description="Asia",version_major=0,version_minor=1,version_patch=0,version_description="")
#     ds.save();ds.set_released(); 


class Migration(migrations.Migration):

    dependencies = [
        ('ap', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

