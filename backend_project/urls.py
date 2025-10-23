from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import (
    CustomTokenObtainPairView,
    UserViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
)
from rest_framework_simplejwt.views import TokenRefreshView

# 👇 Importa el ViewSet de cursos
from courses.views import CourseViewSet

# 🔹 Router principal
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'students', StudentProfileViewSet)
router.register(r'teachers', TeacherProfileViewSet)
router.register(r'courses', CourseViewSet)  # 👈 Nuevo endpoint para cursos

# 🔹 URLs globales
urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔑 Autenticación JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #  Endpoints REST
    path('api/', include(router.urls)),
]
