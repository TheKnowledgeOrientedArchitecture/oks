# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_server', '0001_initial'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='dataset_I_belong_to',
            field=models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True),
        ),
    ]
