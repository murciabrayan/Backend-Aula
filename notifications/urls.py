from django.urls import path
from .views import MyNotificationsView, MarkAsReadView, NotificationDetailView

urlpatterns = [
    path("mis-notificaciones/", MyNotificationsView.as_view()),
    path("notificaciones/<int:pk>/leer/", MarkAsReadView.as_view()),
    path("notificaciones/<int:pk>/", NotificationDetailView.as_view()),
]
