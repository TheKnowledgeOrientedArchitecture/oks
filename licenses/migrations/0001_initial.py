# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-09 06:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('knowledge_server', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=50)),
                ('human_readable', models.TextField(blank=True, null=True)),
                ('legalcode', models.TextField(default='')),
                ('adaptation_shared', models.NullBooleanField()),
                ('attribution', models.NullBooleanField()),
                ('share_alike', models.NullBooleanField()),
                ('commercial_use', models.NullBooleanField()),
                ('derivatives', models.NullBooleanField()),
                ('url_info', models.CharField(blank=True, max_length=160, null=True)),
                ('reccomended_by_opendefinition', models.NullBooleanField()),
                ('conformant_for_opendefinition', models.NullBooleanField()),
                ('image', models.CharField(blank=True, max_length=160, null=True)),
                ('image_small', models.CharField(blank=True, max_length=160, null=True)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
