# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=255L, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AttributeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=255L, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('description', models.CharField(default=b'', max_length=2000L)),
                ('root_instance_id', models.PositiveIntegerField(null=True, blank=True)),
                ('filter_text', models.CharField(max_length=200L, null=True, blank=True)),
                ('version_major', models.IntegerField(null=True, blank=True)),
                ('version_minor', models.IntegerField(null=True, blank=True)),
                ('version_patch', models.IntegerField(null=True, blank=True)),
                ('version_description', models.CharField(default=b'', max_length=2000L)),
                ('release_date', models.DateTimeField(auto_now_add=True)),
                ('version_date', models.DateTimeField(auto_now_add=True)),
                ('version_released', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetStructure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=200L)),
                ('description', models.CharField(max_length=2000L)),
                ('is_shallow', models.BooleanField(default=False)),
                ('is_a_view', models.BooleanField(default=False)),
                ('multiple_releases', models.BooleanField(default=False)),
                ('namespace', models.CharField(max_length=500L, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('type', models.CharField(default=b'New version', max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
                ('dataset', models.ForeignKey(to='knowledge_server.DataSet')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KnowledgeServer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=500L, blank=True)),
                ('description', models.CharField(max_length=2000L, blank=True)),
                ('this_ks', models.BooleanField(default=False)),
                ('scheme', models.CharField(max_length=50L)),
                ('netloc', models.CharField(max_length=200L)),
                ('html_home', models.CharField(default=b'', max_length=4000L)),
                ('html_disclaimer', models.CharField(default=b'', max_length=4000L)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ModelMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=100L)),
                ('module', models.CharField(max_length=100L)),
                ('description', models.CharField(default=b'', max_length=2000L)),
                ('table_name', models.CharField(default=b'', max_length=255L, db_column=b'tableName')),
                ('id_field', models.CharField(default=b'id', max_length=255L, db_column=b'idField')),
                ('name_field', models.CharField(default=b'name', max_length=255L, db_column=b'nameField')),
                ('description_field', models.CharField(default=b'description', max_length=255L, db_column=b'descriptionField')),
                ('dataset_structure', models.ForeignKey(blank=True, to='knowledge_server.DataSetStructure', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('sent', models.BooleanField(default=False)),
                ('remote_url', models.CharField(max_length=200L)),
                ('event', models.ForeignKey(to='knowledge_server.Event')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationReceived',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('URL_dataset', models.CharField(max_length=200L)),
                ('URL_structure', models.CharField(max_length=200L)),
                ('processed', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('name', models.CharField(max_length=500L, blank=True)),
                ('description', models.CharField(max_length=2000L, blank=True)),
                ('website', models.CharField(max_length=500L, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StructureNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('attribute', models.CharField(max_length=255L, blank=True)),
                ('external_reference', models.BooleanField(default=False, db_column=b'externalReference')),
                ('is_many', models.BooleanField(default=False, db_column=b'isMany')),
                ('child_nodes', models.ManyToManyField(related_name='parent', to='knowledge_server.StructureNode', blank=True)),
                ('model_metadata', models.ForeignKey(to='knowledge_server.ModelMetadata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToOther',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('URI', models.CharField(max_length=200L)),
                ('first_version_URIInstance', models.CharField(max_length=200L)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToThis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('URIInstance', models.CharField(max_length=2000L)),
                ('URI_imported_instance', models.CharField(max_length=2000L)),
                ('URI_previous_version', models.CharField(max_length=2000L, null=True, blank=True)),
                ('first_version_URIInstance', models.CharField(max_length=2000L)),
                ('remote_url', models.CharField(max_length=200L)),
                ('first_notification_prepared', models.BooleanField(default=False)),
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
            field=models.ForeignKey(blank=True, to='knowledge_server.DataSet', null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='firt_version',
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
        migrations.AddField(
            model_name='attribute',
            name='model_metadata',
            field=models.ForeignKey(blank=True, to='knowledge_server.ModelMetadata', null=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='type',
            field=models.ForeignKey(to='knowledge_server.AttributeType'),
        ),
    ]
