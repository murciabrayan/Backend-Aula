from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LandingCalendarEntryViewSet,
    LandingContentView,
    LandingDocumentViewSet,
    LandingGalleryItemViewSet,
    LandingNewsViewSet,
)

router = DefaultRouter()
router.register(r"news", LandingNewsViewSet, basename="landing-news")
router.register(r"gallery", LandingGalleryItemViewSet, basename="landing-gallery")
router.register(r"documents", LandingDocumentViewSet, basename="landing-documents")
router.register(r"calendar", LandingCalendarEntryViewSet, basename="landing-calendar")

urlpatterns = [
    path("content/", LandingContentView.as_view(), name="landing-content"),
    path("", include(router.urls)),
]

