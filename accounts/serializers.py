from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 👇 info extra que quieras enviar
        token['email'] = user.email
        token['cedula'] = user.cedula
        token['role'] = user.role
        return token
