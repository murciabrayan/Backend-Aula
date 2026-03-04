# courses/urls.py
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, SubjectViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'subjects', SubjectViewSet, basename='subjects')

urlpatterns = router.urls