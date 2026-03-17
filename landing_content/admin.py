from django.contrib import admin

from .models import (
    LandingCalendarEntry,
    LandingDocument,
    LandingGalleryItem,
    LandingNews,
)


@admin.register(LandingNews)
class LandingNewsAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "display_order", "is_active")
    list_filter = ("is_active", "published_at")
    search_fields = ("title", "summary")


@admin.register(LandingGalleryItem)
class LandingGalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "event_date", "display_order", "is_active")
    list_filter = ("is_active", "event_date")
    search_fields = ("title", "detail")


@admin.register(LandingDocument)
class LandingDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "display_order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")


@admin.register(LandingCalendarEntry)
class LandingCalendarEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "event_date", "display_order", "is_active")
    list_filter = ("is_active", "event_date")
    search_fields = ("title", "detail")

