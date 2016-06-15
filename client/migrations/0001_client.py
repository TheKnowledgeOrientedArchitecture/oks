# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations
from knowledge_server.models import Organization, KnowledgeServer, DataSet, DataSetStructure, StructureNode, ModelMetadata

def forwards_func(apps, schema_editor):
    org_ks={
      "KnowledgeServer": {"name": "A CLIENT OKS to test importing other OKS' stuff.", "netloc": "client.beta.thekoa.org", "description": "It has no datasets; just browse and import from other OKSs.", "html_home": "<h3>This is an OKS used as a client to import datasets from other OKSs.</h3><p>Try browsing another OKS if you already know its URL. Otherwise please <a href=\"http://www.thekoa.org/contact\">contact us</a>.</p>", "html_disclaimer": "<h4>This is an OKS used as a client to import datasets from other OKSs.</h4><p>Try browsing another OKS if you already know its URL. Otherwise please <a href=\"http://www.thekoa.org/contact\">contact us</a>.</p>"}
     }
    KnowledgeServer.create_this_ks(org_ks)
        


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0003_initial_data'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

