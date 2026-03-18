import re


PASSWORD_POLICY_MESSAGE = (
    "La contrasena debe tener minimo 8 caracteres, al menos una mayuscula, "
    "un numero y un caracter especial."
)


def validate_password_strength(password: str):
    password = password or ""

    if len(password) < 8:
        raise ValueError(PASSWORD_POLICY_MESSAGE)

    if not re.search(r"[A-Z]", password):
        raise ValueError(PASSWORD_POLICY_MESSAGE)

    if not re.search(r"\d", password):
        raise ValueError(PASSWORD_POLICY_MESSAGE)

    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
