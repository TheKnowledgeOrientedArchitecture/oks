# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations
from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure

def forwards_func(apps, schema_editor):
    org_ks={
      "Organization": {"name": "A test Organization", "website": "http://new_org.example.com", "description": ""}, 
      "KnowledgeServer": {"name": "A demo OKS used as a client.", "netloc": "client.thekoa.org", "description": "", "html_home": "", "html_disclaimer": ""}
     }
    KnowledgeServer.create_this_ks(org_ks)
    
# 
#     new_org = Organization();new_org.name = "A test Organization";new_org.website = 'http://new_org.example.com';new_org.description = "";
#     new_org.save()
#     new_org_ks = KnowledgeServer(name="A demo OKS used as a client.", scheme="http", netloc="client.thekoa.org", description="", organization=new_org, this_ks=False, html_home="", html_disclaimer="")
#     new_org_ks.save()
#     
#     dss_org = DataSetStructure.get_from_name(DataSetStructure.organization_DSN)
#     ds = DataSet(description='', knowledge_server=new_org_ks, dataset_structure=dss_org, 
#                  root=new_org, version_major=0, version_minor=1, version_patch=0, version_description="")
#     ds.save()
#     ds.set_released()
#     
#     new_org_ks.set_as_this_ks()
#     new_org.regenerate_UKCL()
#     ds.regenerate_UKCL()


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0003_initial_data'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

