# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it

from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DanglingReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_actual_instance', models.CharField(default='', max_length=750, db_index=True)),
                ('oks_home',models.CharField(blank=True, max_length=255)),
                ('object_with_dangling_content_type',models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('object_with_dangling_instance_id',models.PositiveIntegerField(blank=True, null=True)),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('description', models.CharField(default='', max_length=2000)),
                ('root_instance_id', models.PositiveIntegerField(blank=True, null=True)),
                ('filter_text', models.CharField(blank=True, max_length=200, null=True)),
                ('creation_date', models.DateTimeField(blank=True, null=True)),
                ('version_major', models.IntegerField(blank=True, null=True, db_index=True)),
                ('version_minor', models.IntegerField(blank=True, null=True, db_index=True)),
                ('version_patch', models.IntegerField(blank=True, null=True, db_index=True)),
                ('version_description', models.CharField(default='', max_length=2000)),
                ('release_date', models.DateTimeField(auto_now_add=True)),
                ('version_date', models.DateTimeField(auto_now_add=True)),
                ('version_released', models.BooleanField(default=False, db_index=True)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataSetStructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=2000, default='')),
                ('is_shallow', models.BooleanField(default=False)),
                ('is_a_view', models.BooleanField(default=False)),
                ('multiple_releases', models.BooleanField(default=False)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('type', models.CharField(default='New version', max_length=50, db_index=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False, db_index=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.DataSet')),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KnowledgeServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(blank=True, max_length=2000)),
                ('this_ks', models.BooleanField(default=False)),
                ('scheme', models.CharField(max_length=50, default='http')),
                ('netloc', models.CharField(max_length=200)),
                ('html_home', models.CharField(default='', max_length=4000)),
                ('html_disclaimer', models.CharField(default='', max_length=4000)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ModelMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('module', models.CharField(max_length=500, db_index=True)),
                ('description', models.CharField(default='', max_length=2000)),
                ('table_name', models.CharField(db_column='tableName', default='', max_length=255)),
                ('id_field', models.CharField(db_column='idField', default='id', max_length=255)),
                ('name_field', models.CharField(db_column='nameField', default='name', max_length=255)),
                ('description_field', models.CharField(db_column='descriptionField', default='description', max_length=255)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('dataset_structure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.DataSetStructure')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('sent', models.BooleanField(default=False, db_index=True)),
                ('remote_url', models.CharField(max_length=200)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.Event')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationReceived',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('URL_dataset', models.CharField(max_length=200)),
                ('URL_structure', models.CharField(max_length=200)),
                ('processed', models.BooleanField(default=False, db_index=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(blank=True, max_length=2000)),
                ('website', models.CharField(blank=True, max_length=500)),
                ('logo', models.CharField(blank=True, max_length=500)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StructureNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('attribute', models.CharField(blank=True, max_length=255)),
                ('method_to_retrieve', models.CharField(blank=True, max_length=255, null=True)),
                ('external_reference', models.BooleanField(db_column='externalReference', default=False, db_index=True)),
                ('is_many', models.BooleanField(db_column='isMany', default=False)),
                ('child_nodes', models.ManyToManyField(blank=True, related_name='parent', to='knowledge_server.StructureNode')),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('model_metadata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.ModelMetadata',blank=True, null=True)),
                ('fk_field', models.CharField(default='', max_length=255)),
                ('ct_field', models.CharField(default='', max_length=255)),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToOther',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('URL', models.CharField(max_length=200)),
                ('first_version_UKCL', models.CharField(max_length=200, db_index=True)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubscriptionToThis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('first_version_UKCL', models.CharField(default='', max_length=750, db_index=True)),
                ('remote_url', models.CharField(max_length=200)),
                ('first_notification_prepared', models.BooleanField(default=False, db_index=True)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('remote_ks', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.KnowledgeServer')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DynamicModelContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='knowledgeserver',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.Organization'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='owner_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.Organization'),
        ),
        migrations.AddField(
            model_name='datasetstructure',
            name='root_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dataset_type', to='knowledge_server.StructureNode'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='dataset_structure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.DataSetStructure'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='filter_dataset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='first_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='knowledge_server.DataSet'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='knowledge_server',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.KnowledgeServer'),
        ),
    ]
