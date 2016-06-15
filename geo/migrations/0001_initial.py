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
        ('knowledge_server', '0003_initial_data'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Continent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('license', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='licenses.License')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('continent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.Continent')),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubContinent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UKCL', models.CharField(blank=True, default='', max_length=750, db_index=True)),
                ('UKCL_previous_version', models.CharField(blank=True, max_length=750, null=True, db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('continent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geo.Continent')),
                ('dataset_I_belong_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='knowledge_server.DataSet')),
                ('is_a_placeholder',models.BooleanField(db_column='oks_internals_placeholder', default=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='state',
            name='sub_continent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.SubContinent'),
        ),
        migrations.AddField(
            model_name='region',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geo.State'),
        ),
        migrations.AddField(
            model_name='province',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.Region'),
        ),
        migrations.AddField(
            model_name='province',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='geo.State'),
        ),
    ]
