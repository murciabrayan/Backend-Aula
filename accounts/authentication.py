from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class ScopedJWTAuthentication(JWTAuthentication):
    """Keep the temporary Aula demo identity out of institutional APIs."""

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            return None
        user, token = authenticated
        if user.role == 'AULA_DEMO' and not request.path.startswith('/api/aula/'):
            raise AuthenticationFailed('Esta cuenta solo puede ingresar al Aula Interactiva.')
        return user, token
