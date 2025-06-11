from django.contrib import admin
from .models import Information
from .models import Event
# Register your models here.
admin.site.register(Information)
admin.site.register(Event)