"""
Restauración de los archivos subidos a la plataforma (documentos de alumnos,
firmas, tareas, cartas de permiso...) a partir de un respaldo diario.

El respaldo es `archivos_FECHA.tar.gz.enc`: un paquete cifrado con
`openssl enc -aes-256-cbc -pbkdf2`, que contiene `manifiesto.tsv` y la carpeta
`media/...` con cada archivo en la misma ruta que tiene en Cloudinary.

La base de datos guarda esa ruta (public_id) para encontrar cada archivo, así
que se vuelven a subir con EXACTAMENTE la misma ruta: al terminar, los enlaces
de la base funcionan de nuevo sin tocar la base.

Seguridad
---------
Por defecto NO toca los archivos reales: exige --prefijo y sube todo bajo esa
carpeta (útil para simulacros). Para restaurar sobre las rutas reales de
producción hay que pasar --destino-real de forma explícita.

Uso
---
    set CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD
    set BACKUP_PASSPHRASE=la_clave_de_cifrado

    # Simulacro (no toca nada real):
    python restaurar_archivos.py archivos_FECHA.tar.gz.enc --prefijo simulacro/

    # Ver qué haría, sin subir nada:
    python restaurar_archivos.py archivos_FECHA.tar.gz.enc --prefijo simulacro/ --ensayo

    # Recuperación real (solo ante una pérdida en Cloudinary):
    python restaurar_archivos.py archivos_FECHA.tar.gz.enc --destino-real

    # Borrar los archivos de un simulacro:
    python restaurar_archivos.py --borrar-prefijo simulacro/
"""

import argparse
import hashlib
import io
import os
import sys
import tarfile
import time
import urllib.parse

import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Parámetros por defecto de `openssl enc -aes-256-cbc -pbkdf2`
PBKDF2_ITERATIONS = 10000
TIPOS_CLOUDINARY = ("image", "raw", "video")


# ----------------------------------------------------------------------------
# Descifrado (compatible con openssl enc -aes-256-cbc -pbkdf2 -salt)
# ----------------------------------------------------------------------------
def descifrar(datos: bytes, clave: str) -> bytes:
    if not datos.startswith(b"Salted__"):
        raise ValueError("El archivo no tiene el formato de openssl (falta 'Salted__').")
    sal, cifrado = datos[8:16], datos[16:]
    material = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, PBKDF2_ITERATIONS, 48)
    key, iv = material[:32], material[32:]
    descifrador = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    con_relleno = descifrador.update(cifrado) + descifrador.finalize()
    quitar = padding.PKCS7(128).unpadder()
    try:
        return quitar.update(con_relleno) + quitar.finalize()
    except ValueError as exc:
        raise ValueError("No se pudo descifrar: la clave es incorrecta.") from exc


# ----------------------------------------------------------------------------
# Cloudinary (API directa, firmada)
# ----------------------------------------------------------------------------
class Cloudinary:
    def __init__(self, url: str):
        partes = urllib.parse.urlparse(url)
        if partes.scheme != "cloudinary" or not partes.hostname:
            raise ValueError("CLOUDINARY_URL debe tener la forma cloudinary://API_KEY:API_SECRET@CLOUD")
        self.key = partes.username
        self.secret = partes.password
        self.cloud = partes.hostname

    def _firmar(self, params: dict) -> str:
        cadena = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.sha1((cadena + self.secret).encode()).hexdigest()

    def subir(self, contenido: bytes, public_id: str, tipo: str, sobrescribir: bool) -> dict:
        params = {
            "public_id": public_id,
            "overwrite": "true" if sobrescribir else "false",
            "invalidate": "true",
            "timestamp": str(int(time.time())),
        }
        params["signature"] = self._firmar(params)
        params["api_key"] = self.key
        url = f"https://api.cloudinary.com/v1_1/{self.cloud}/{tipo}/upload"
        respuesta = requests.post(url, data=params, files={"file": ("archivo", contenido)}, timeout=120)
        if respuesta.status_code != 200:
            raise RuntimeError(f"Cloudinary respondió {respuesta.status_code}: {respuesta.text[:200]}")
        return respuesta.json()

    def descargar(self, public_id: str, tipo: str) -> bytes:
        url = (f"https://res.cloudinary.com/{self.cloud}/{tipo}/upload/v1/"
               + urllib.parse.quote(public_id))
        respuesta = requests.get(url, timeout=60)
        respuesta.raise_for_status()
        return respuesta.content

    def borrar_prefijo(self, prefijo: str) -> int:
        borrados = 0
        for tipo in TIPOS_CLOUDINARY:
            url = f"https://api.cloudinary.com/v1_1/{self.cloud}/resources/{tipo}/upload"
            respuesta = requests.delete(url, params={"prefix": prefijo},
                                        auth=(self.key, self.secret), timeout=60)
            if respuesta.status_code == 200:
                borrados += len(respuesta.json().get("deleted", {}))
        return borrados


# ----------------------------------------------------------------------------
def leer_paquete(ruta_enc: str, clave: str):
    with open(ruta_enc, "rb") as f:
        tar_gz = descifrar(f.read(), clave)
    with tarfile.open(fileobj=io.BytesIO(tar_gz), mode="r:gz") as tar:
        miembros = {m.name.lstrip("./"): m for m in tar.getmembers() if m.isfile()}
        manifiesto = tar.extractfile(miembros["manifiesto.tsv"]).read().decode("utf-8")
        archivos = []
        for linea in manifiesto.splitlines():
            if not linea.strip():
                continue
            ruta, tipo, content_type, tamano = linea.split("\t")
            contenido = tar.extractfile(miembros[ruta]).read()
            archivos.append((ruta, tipo, content_type, int(tamano), contenido))
    return archivos


def main() -> int:
    p = argparse.ArgumentParser(description="Restaura a Cloudinary los archivos de un respaldo.")
    p.add_argument("paquete", nargs="?", help="archivos_FECHA.tar.gz.enc")
    destino = p.add_mutually_exclusive_group()
    destino.add_argument("--prefijo", help="Carpeta de simulacro, p. ej. simulacro/ (no toca lo real)")
    destino.add_argument("--destino-real", action="store_true",
                         help="Restaurar sobre las rutas reales de producción")
    p.add_argument("--sobrescribir", action="store_true",
                   help="Reemplazar archivos que ya existan en el destino")
    p.add_argument("--ensayo", action="store_true", help="Mostrar qué se haría, sin subir nada")
    p.add_argument("--borrar-prefijo", metavar="PREFIJO",
                   help="Borrar de Cloudinary todo lo que esté bajo ese prefijo (limpiar simulacros)")
    args = p.parse_args()

    url = os.environ.get("CLOUDINARY_URL", "").strip()
    if not url:
        print("Falta la variable CLOUDINARY_URL.", file=sys.stderr)
        return 2
    nube = Cloudinary(url)

    if args.borrar_prefijo:
        if args.borrar_prefijo.strip("/") in ("", "media"):
            print("Por seguridad no se permite borrar ese prefijo.", file=sys.stderr)
            return 2
        print(f"Borrados: {nube.borrar_prefijo(args.borrar_prefijo)} archivos bajo '{args.borrar_prefijo}'")
        return 0

    if not args.paquete:
        p.error("Indica el paquete .tar.gz.enc")
    if not args.prefijo and not args.destino_real:
        p.error("Por seguridad indica --prefijo (simulacro) o --destino-real (recuperación real).")

    clave = os.environ.get("BACKUP_PASSPHRASE", "").strip()
    if not clave:
        print("Falta la variable BACKUP_PASSPHRASE.", file=sys.stderr)
        return 2

    archivos = leer_paquete(args.paquete, clave)
    prefijo = "" if args.destino_real else args.prefijo
    print(f"Paquete descifrado: {len(archivos)} archivos. Destino: "
          f"{'RUTAS REALES DE PRODUCCIÓN' if args.destino_real else prefijo}")

    ok, fallidos = 0, []
    for ruta, tipo, content_type, tamano, contenido in archivos:
        public_id = prefijo + ruta
        if args.ensayo:
            print(f"  [ensayo] {tipo:5} {tamano:>9} B  {public_id}")
            continue
        try:
            nube.subir(contenido, public_id, tipo, args.sobrescribir)
            # Verificación: se vuelve a descargar y se compara byte a byte
            devuelto = nube.descargar(public_id, tipo)
            if hashlib.sha256(devuelto).digest() != hashlib.sha256(contenido).digest():
                raise RuntimeError("lo descargado no coincide con el respaldo")
            ok += 1
        except Exception as exc:  # noqa: BLE001 - se reporta y se sigue con el resto
            fallidos.append((public_id, str(exc)))

    if args.ensayo:
        return 0
    print(f"Restaurados y verificados: {ok} de {len(archivos)}")
    for public_id, error in fallidos:
        print(f"  FALLÓ: {public_id} -> {error}")
    return 0 if not fallidos else 1


if __name__ == "__main__":
    sys.exit(main())
