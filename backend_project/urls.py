from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from django import get_version

# Importaciones
from accounts.views_profile import user_profile, change_password
from accounts.views import (
    complete_initial_password,
    CustomTokenObtainPairView,
    UserViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
)
from accounts.views_password_reset import (
    forgot_password,
    reset_password,
)
from accounts.views_google import google_login
from accounts.models import User

# IMPORTAR VIEWSETS
from courses.views import CourseViewSet, SubjectViewSet, AreaViewSet

# Routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'students', StudentProfileViewSet)
router.register(r'teachers', TeacherProfileViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'areas', AreaViewSet)


def root_status(_request):
    response = {
        'status': 'ok',
        'service': 'proyecto-aula-backend',
        'message': 'Backend activo',
        'django_version': get_version(),
    }
    try:
        response['db'] = 'ok'
        response['user_count'] = User.objects.count()
    except Exception as exc:
        response['db'] = 'error'
        response['db_error'] = str(exc)
    return JsonResponse(response)

urlpatterns = [
    path('', root_status, name='root_status'),
    path('admin/', admin.site.urls),

    # Perfil
    path('api/profile/', user_profile, name='user_profile'),
    path('api/change-password/', change_password, name='change_password'),
    path('api/complete-initial-password/', complete_initial_password, name='complete_initial_password'),

    # JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Google login
    path('api/auth/google/', google_login, name='google_login'),

    # API routers
    path('api/', include(router.urls)),

    # Password reset
    path('api/password-reset/', forgot_password, name='forgot_password'),
    path('api/password-reset/<uidb64>/<token>/', reset_password, name='reset_password'),

    # Assignments
    path('api/', include('assignments.urls')),

    # Notifications
    path('api/', include('notifications.urls')),

    # Calendar
    path('api/calendar/', include('calendar_app.urls')),

    # Boletines
    path('api/report-cards/', include('report_cards.urls')),

    # ASISTENCIA
    path('api/', include('attendance.urls')),
    
    # Alertas
    path('api/academic-alerts/', include('academic_alerts.urls')),

    # Landing content
    path('api/landing/', include('landing_content.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
