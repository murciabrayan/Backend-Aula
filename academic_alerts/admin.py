from django.contrib import admin

from .models import AcademicAlert, AcademicAlertEvent


class AcademicAlertEventInline(admin.TabularInline):
    model = AcademicAlertEvent
    extra = 0
    readonly_fields = (
        "event_type",
        "title",
        "notes",
        "actor",
        "created_at",
    )
    can_delete = False


@admin.register(AcademicAlert)
class AcademicAlertAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "period",
        "alert_type",
        "level",
        "status",
        "next_follow_up_due_at",
        "created_at",
    )
    list_filter = (
        "period",
        "alert_type",
        "level",
        "status",
        "course",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "course__nombre",
        "title",
    )
    inlines = [AcademicAlertEventInline]


@admin.register(AcademicAlertEvent)
class AcademicAlertEventAdmin(admin.ModelAdmin):
    list_display = (
        "alert",
        "event_type",
        "actor",
        "visible_to_student",
        "created_at",
    )
    list_filter = (
        "event_type",
        "visible_to_student",
        "created_at",
    )
    search_fields = (
        "alert__title",
        "alert__student__first_name",
        "alert__student__last_name",
        "notes",
        "title",
    )
