from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework import viewsets, permissions
from .models import User, StudentProfile, TeacherProfile
from .serializers import UserSerializer, StudentProfileSerializer, TeacherProfileSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ✅ Modificado: ahora permite filtrar usuarios por rol (teacher/student)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # 👈 Esto lo vuelve a dejar claro para el router
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')

        if role:
            queryset = queryset.filter(role__iexact=role)

        return queryset



class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
