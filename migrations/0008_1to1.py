# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-22 12:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tst', '0007_ISShits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hmmprofile',
            name='cath_node',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='tst.classification'),
        ),
    ]