# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 09:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marackerapi', '0017_auto_20170702_1758'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='marackerapplication',
            name='slug',
        ),
        migrations.AlterField(
            model_name='marackerapplication',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
