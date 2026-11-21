from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.TeacherMe.as_view()),
    path('sessions/', views.Sessions.as_view()),
    path('sessions/<uuid:session_id>/', views.SessionDetail.as_view()),
    path('sessions/<uuid:session_id>/close/', views.CloseSession.as_view()),
    path('public/<str:token>/', views.PublicSession.as_view()),
    path('public/<str:token>/join/', views.JoinSession.as_view()),
    path('participations/<uuid:session_id>/', views.ParticipantState.as_view()),
]
