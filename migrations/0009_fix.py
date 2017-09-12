# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-12 13:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tst', '0008_1to1'),
    ]

    operations = [
        migrations.CreateModel(
            name='hit_summary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hcount', models.IntegerField(default=0)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tst.classification')),
                ('seqDB', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tst.seqDB')),
            ],
        ),
    ]
