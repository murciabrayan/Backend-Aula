from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalendarView, CalendarEventViewSet

router = DefaultRouter()
router.register('events', CalendarEventViewSet, basename='calendar-events')

urlpatterns = [
    path('', CalendarView.as_view(), name='calendar'),  # GET calendario (tareas + eventos)
    path('', include(router.urls)),                     # CRUD eventos
]