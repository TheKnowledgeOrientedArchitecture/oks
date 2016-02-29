# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations
from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure

def forwards_func(apps, schema_editor):
    test_client_org = Organization();test_client_org.name="A demo Organization";test_client_org.website='http://demo.example.com';test_client_org.description="This is just a demo Organization.";
    test_client_org.save(using='default')
    id_on_default_db = test_client_org.id
    test_client_org.id = None
    test_client_org.save(using='materialized')
    m_test_client_org = test_client_org
    test_client_org = Organization.objects.get(pk=id_on_default_db)
    
    root_ks = KnowledgeServer.this_knowledge_server('default')
    root_ks.this_ks = False
    root_ks.save()
    root_ks = KnowledgeServer.this_knowledge_server()
    root_ks.this_ks = False
    root_ks.save()
    
    m_test_client_org_ks = KnowledgeServer(name="A demo OKS used as a client.", scheme="http", netloc="client.thekoa.org", description="Just a test.", organization=test_client_org, this_ks=True,html_home="", html_disclaimer="This web site is solely for test purposes. Feel free to contact us.")
    m_test_client_org_ks.save(using='materialized')
    test_client_org_ks = m_test_client_org_ks
    test_client_org_ks.id = None
    test_client_org_ks.UKCL = ""
    test_client_org_ks.save(using='default')
    
    # m_test_client_org and test_client_org have the wrong UKCL because they where created before their Knowledge Server
    # I fix this:
    m_test_client_org.UKCL = ""
    m_test_client_org.save()
    test_client_org.UKCL = ""
    test_client_org.save()
    
    m_es = DataSetStructure.objects.using('materialized').get(name = DataSetStructure.organization_DSN)
    es = DataSetStructure.objects.get(UKCL = m_es.UKCL)
    ei = DataSet(knowledge_server=test_client_org_ks,root=test_client_org,dataset_structure=es,
                 description="A test Organization and their KSs",version_major=0,version_minor=1,version_patch=0)
    ei.save(using='default');ei.first_version_id=ei.id;ei.save(using='default')
    # let's materialize the ei; I cannot release it as I saved manually the ks in materialized (I cannot do otherwise as it 
    # is needed to generateUKCL every time something is saved)
    ei.materialize(ei.shallow_structure().root_node, processed_instances = [])

class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

