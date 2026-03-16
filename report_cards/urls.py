from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminCoursesForReportsView,
    AdminStudentsByCourseView,
    StudentReportCardView,
    StudentReportCardPDFView,
    CourseReportCardsZIPView,
    IndicatorViewSet,
    SubjectIndicatorAssignmentViewSet,
)

router = DefaultRouter()
router.register(r"indicators", IndicatorViewSet, basename="report-card-indicators")
router.register(r"indicator-assignments", SubjectIndicatorAssignmentViewSet, basename="report-card-indicator-assignments")

urlpatterns = [
    path("", include(router.urls)),
    path("courses/", AdminCoursesForReportsView.as_view(), name="report-courses"),
    path("courses/<int:course_id>/students/", AdminStudentsByCourseView.as_view(), name="report-course-students"),
    path("courses/<int:course_id>/report-cards/zip/", CourseReportCardsZIPView.as_view(), name="course-report-cards-zip"),
    path("students/<int:student_id>/report-card/", StudentReportCardView.as_view(), name="student-report-card"),
    path("students/<int:student_id>/report-card/pdf/", StudentReportCardPDFView.as_view(), name="student-report-card-pdf"),
]