# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-09 06:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('knowledge_server', '0001_initial'),
        ('licenses', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('ap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='licenses',
            field=models.ManyToManyField(to='licenses.License'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='root_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='danglingreference',
            name='dataset_I_belong_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet'),
        ),
        migrations.AddField(
            model_name='danglingreference',
            name='structure_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.StructureNode'),
        ),
        migrations.AddField(
            model_name='danglingreference',
            name='UKCL_previous_version',
            field=models.CharField(blank=True, max_length=750, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='current_status',
            field=models.ForeignKey( blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='knowledge_server.WorkflowStatus' ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dataset',
            name='workflow',
            field=models.ForeignKey( blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                        related_name='workflow_dataset', to='knowledge_server.Workflow' ),
            preserve_default=False,
        ),
    ]
