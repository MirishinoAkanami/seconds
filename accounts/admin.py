from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Announcement, StoreSettings

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Seconds Profile', {'fields': ('role', 'contact_number', 'address', 'birthday', 'agreed_to_terms', 'profile_picture')}),
    )

admin.site.register(Announcement)
admin.site.register(StoreSettings)
