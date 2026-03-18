from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LandingCalendarEntryViewSet,
    LandingContactMessageView,
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
    path("contact/", LandingContactMessageView.as_view(), name="landing-contact"),
    path("", include(router.urls)),
]
