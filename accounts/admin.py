from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, StudentProfile, TeacherProfile, AdminProfile


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'cedula', 'first_name', 'last_name', 'role', 'is_staff')
    search_fields = ('email', 'cedula', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'cedula', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'cedula', 'password1', 'password2', 'role'),
        }),
    )


admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(AdminProfile)
admin.site.unregister(Group)  # opcional
