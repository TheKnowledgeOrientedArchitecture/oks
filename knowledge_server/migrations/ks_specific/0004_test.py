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
      "KnowledgeServer": {"name": "A demo OKS populated with some test data.", "netloc": "test.beta.thekoa.org", "description": "", "html_home": "", "html_disclaimer": ""}
     }
    KnowledgeServer.create_this_ks(org_ks)


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0003_initial_data'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

