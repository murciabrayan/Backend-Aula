"""Throttles especificos para endpoints sensibles (login, reset de contrasena).

Usan scopes propios ('login', 'password_reset') con limites fijos definidos en
settings.DEFAULT_THROTTLE_RATES. Asi quedan protegidos frente a fuerza bruta y
bombardeo de correos, independientemente de los limites globales anon/user
(que en produccion estan muy altos).
"""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"
