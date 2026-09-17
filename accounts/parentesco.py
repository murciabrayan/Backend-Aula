"""Normalizacion del parentesco del acudiente.

Permite que el valor llegue como codigo ("TIO"), como etiqueta con tildes
("Tío") o en minusculas ("abuela"), util sobre todo para la carga masiva
por Excel donde el usuario escribe el texto a mano.
"""

import unicodedata


def normalize_parentesco(value):
    """Devuelve el codigo en mayusculas y sin tildes (p. ej. "Tío" -> "TIO")."""
    if not value:
        return ""

    text = str(value).strip()
    # Descompone los acentos y elimina las marcas diacriticas.
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_accents.upper()
