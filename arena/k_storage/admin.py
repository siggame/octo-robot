from django.contrib import admin

# Register your models here.

from k_storage.models import DataPoint

admin.site.register(DataPoint)
