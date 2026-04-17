from .settings import *  # noqa: F401,F403


# Las pruebas de rendimiento generan muchas solicitudes seguidas. En el
# entorno normal DRF limita anon/user por minuto, lo que distorsiona k6 con 429.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
    },
}
