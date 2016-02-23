# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default=b'', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=50)),
                ('human_readable', models.TextField(null=True, blank=True)),
                ('legalcode', models.TextField(default='')),
                ('adaptation_shared', models.NullBooleanField()),
                ('attribution', models.NullBooleanField()),
                ('share_alike', models.NullBooleanField()),
                ('commercial_use', models.NullBooleanField()),
                ('url_info', models.CharField(max_length=160, null=True, blank=True)),
                ('reccomended_by_opendefinition', models.NullBooleanField()),
                ('conformant_for_opendefinition', models.NullBooleanField()),
                ('image', models.CharField(max_length=160, null=True, blank=True)),
                ('image_small', models.CharField(max_length=160, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
