from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informazioni personali', {'fields': ('first_name', 'last_name', 'email', 'date_of_birth')}),
        ('Permessi', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Date importanti', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name')
    ordering = ('username',)