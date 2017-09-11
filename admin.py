# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *
admin.site.register(node_stat)
admin.site.register(classification)

# Register your models here.
# from .models import Question
# admin.site.register(Question)