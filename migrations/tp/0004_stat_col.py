# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 15:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tst', '0003_init_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain_stat',
            name='maha_dist',
            field=models.FloatField(null=True),
        ),
    ]
