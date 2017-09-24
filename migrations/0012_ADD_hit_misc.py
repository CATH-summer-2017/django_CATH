# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-23 16:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tst', '0011_hitPR'),
    ]

    operations = [
        migrations.CreateModel(
            name='hit_misc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hmm_evalue', models.FloatField(default=None, null=True)),
                ('hmm_overlap', models.FloatField(default=None, null=True)),
                ('prc_evalue', models.FloatField(default=None, null=True)),
                ('prc_overlap', models.FloatField(default=None, null=True)),
                ('ssap_score', models.FloatField(default=None, null=True)),
                ('ssap_align', models.IntegerField(default=None, null=True)),
                ('prc_align', models.IntegerField(default=None, null=True)),
                ('prc_seqid', models.FloatField(default=None, null=True)),
                ('rmsd', models.FloatField(default=None, null=True)),
                ('hit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='tst.hit4cath2cath')),
            ],
        ),
    ]
