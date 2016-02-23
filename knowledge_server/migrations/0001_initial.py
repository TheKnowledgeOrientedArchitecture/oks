# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('description', models.CharField(default='', max_length=2000)),
                ('root_instance_id', models.PositiveIntegerField(null=True, blank=True)),
                ('filter_text', models.CharField(max_length=200, null=True, blank=True)),
                ('version_major', models.IntegerField(null=True, blank=True)),
                ('version_minor', models.IntegerField(null=True, blank=True)),
                ('version_patch', models.IntegerField(null=True, blank=True)),
                ('version_description', models.CharField(default='', max_length=2000)),
                ('release_date', models.DateTimeField(auto_now_add=True)),
                ('version_date', models.DateTimeField(auto_now_add=True)),
                ('version_released', models.BooleanField(default=False)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetStructure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=2000)),
                ('is_shallow', models.BooleanField(default=False)),
                ('is_a_view', models.BooleanField(default=False)),
                ('multiple_releases', models.BooleanField(default=False)),
                ('namespace', models.CharField(max_length=500, blank=True)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('type', models.CharField(default='New version', max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
                ('dataset', models.ForeignKey(to='knowledge_server.DataSet')),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KnowledgeServer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('name', models.CharField(max_length=500, blank=True)),
                ('description', models.CharField(max_length=2000, blank=True)),
                ('this_ks', models.BooleanField(default=False)),
                ('scheme', models.CharField(max_length=50)),
                ('netloc', models.CharField(max_length=200)),
                ('html_home', models.CharField(default='', max_length=4000)),
                ('html_disclaimer', models.CharField(default='', max_length=4000)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ModelMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('module', models.CharField(max_length=500)),
                ('description', models.CharField(default='', max_length=2000)),
                ('table_name', models.CharField(default='', max_length=255, db_column='tableName')),
                ('id_field', models.CharField(default='id', max_length=255, db_column='idField')),
                ('name_field', models.CharField(default='name', max_length=255, db_column='nameField')),
                ('description_field', models.CharField(default='description', max_length=255, db_column='descriptionField')),
                ('dataset_structure', models.ForeignKey(blank=True, to='knowledge_server.DataSetStructure', null=True)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('sent', models.BooleanField(default=False)),
                ('remote_url', models.CharField(max_length=200)),
                ('event', models.ForeignKey(to='knowledge_server.Event')),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationReceived',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('URL_dataset', models.CharField(max_length=200)),
                ('URL_structure', models.CharField(max_length=200)),
                ('processed', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('name', models.CharField(max_length=500, blank=True)),
                ('description', models.CharField(max_length=2000, blank=True)),
                ('website', models.CharField(max_length=500, blank=True)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StructureNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('attribute', models.CharField(max_length=255, blank=True)),
                ('method_to_retrieve', models.CharField(max_length=255, null=True, blank=True)),
                ('external_reference', models.BooleanField(default=False, db_column='externalReference')),
                ('is_many', models.BooleanField(default=False, db_column='isMany')),
                ('child_nodes', models.ManyToManyField(related_name='parent', to='knowledge_server.StructureNode', blank=True)),
                ('model_metadata', models.ForeignKey(to='knowledge_server.ModelMetadata')),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToOther',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('URI', models.CharField(max_length=200)),
                ('first_version_URIInstance', models.CharField(max_length=200)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToThis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('first_version_URIInstance', models.CharField(default='', max_length=2000)),
                ('remote_url', models.CharField(max_length=200)),
                ('first_notification_prepared', models.BooleanField(default=False)),
                ('remote_ks', models.ForeignKey(blank=True, to='knowledge_server.KnowledgeServer', null=True)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DanglingReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(default='', max_length=2000)),
                ('URI_imported_instance', models.CharField(max_length=2000)),
                ('URI_previous_version', models.CharField(max_length=2000, null=True, blank=True)),
                ('URI_actual_instance', models.CharField(default='', max_length=2000)),
                ('URI_structure', models.CharField(default='', max_length=2000)),
                ('URI_dataset', models.CharField(default='', max_length=2000)),
                ('dataset_I_belong_to', models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='knowledgeserver',
            name='organization',
            field=models.ForeignKey(to='knowledge_server.Organization'),
        ),
        migrations.AddField(
            model_name='datasetstructure',
            name='root_node',
            field=models.ForeignKey(related_name='dataset_type', to='knowledge_server.StructureNode'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='dataset_structure',
            field=models.ForeignKey(to='knowledge_server.DataSetStructure'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='filter_dataset',
            field=models.ForeignKey(related_name='+', blank=True, to='knowledge_server.DataSet', null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='first_version',
            field=models.ForeignKey(related_name='versions', blank=True, to='knowledge_server.DataSet', null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='licenses',
            field=models.ManyToManyField(to='licenses.License'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='owner_knowledge_server',
            field=models.ForeignKey(to='knowledge_server.KnowledgeServer'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='root_content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
    ]
