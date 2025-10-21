from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('height', 'width', 'image', 'bio')}),
    ) # type: ignore
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('height', 'width', 'image', 'bio')}),
    )

    list_display = ('username', 'email', 'is_active')
