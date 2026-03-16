from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AcademicAlertViewSet, StudentAcademicSummaryView

router = DefaultRouter()
router.register(r"", AcademicAlertViewSet, basename="academic-alerts")

urlpatterns = [
    path("student-summary/", StudentAcademicSummaryView.as_view(), name="student-academic-summary"),
    path("", include(router.urls)),
]