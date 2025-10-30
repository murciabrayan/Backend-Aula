from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

# 🔹 Importaciones de tus apps
from accounts.views_profile import user_profile, change_password
from accounts.views import (
    CustomTokenObtainPairView,
    UserViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
)
from accounts.views_password_reset import (
    forgot_password,
    reset_password,
)
from courses.views import CourseViewSet

# 🔹 Routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'students', StudentProfileViewSet)
router.register(r'teachers', TeacherProfileViewSet)
router.register(r'courses', CourseViewSet)

# 🔹 URLs principales
urlpatterns = [
    path('admin/', admin.site.urls),

    # Perfil y cambio de contraseña
    path('api/profile/', user_profile, name='user_profile'),
    path('api/change-password/', change_password, name='change_password'),

    # JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API principales
    path('api/', include(router.urls)),

    # Recuperación de contraseña
    path('api/password-reset/', forgot_password, name='forgot_password'),
    path('api/password-reset/<uidb64>/<token>/', reset_password, name='reset_password'),

    # Asignación de tareas (assignments)
    path('api/', include('assignments.urls')),
]

# 🔹 Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
