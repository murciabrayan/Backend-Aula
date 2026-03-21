from django.contrib import admin

from .models import Attendance, AttendanceEvent


class AttendanceEventInline(admin.TabularInline):
    model = AttendanceEvent
    extra = 0
    readonly_fields = (
        "action",
        "summary",
        "notes",
        "actor",
        "actor_role",
        "created_at",
    )
    can_delete = False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "date",
        "status",
        "is_justified",
        "justification_type",
        "created_by",
        "updated_by",
    )
    list_filter = (
        "status",
        "is_justified",
        "justification_type",
        "course",
        "date",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "course__nombre",
    )
    inlines = [AttendanceEventInline]


@admin.register(AttendanceEvent)
class AttendanceEventAdmin(admin.ModelAdmin):
    list_display = (
        "attendance",
        "action",
        "actor",
        "actor_role",
        "created_at",
    )
    list_filter = (
        "action",
        "actor_role",
        "created_at",
    )
    search_fields = (
        "attendance__student__first_name",
        "attendance__student__last_name",
        "summary",
        "notes",
    )
