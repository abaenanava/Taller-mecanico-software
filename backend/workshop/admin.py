from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Client, User, WorkOrder
admin.site.register(User, UserAdmin)
admin.site.register(WorkOrder)
admin.site.register(Client)
