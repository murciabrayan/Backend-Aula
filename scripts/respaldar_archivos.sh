#!/usr/bin/env bash
# =============================================================================
# Respaldo de TODOS los archivos subidos a la plataforma.
# -----------------------------------------------------------------------------
# Los archivos (documentos de alumnos, firmas, tareas, cartas de permiso, etc.)
# no viven en la base de datos: estan en Cloudinary y la base solo guarda su
# ruta. Este script lee esas rutas de la base y descarga cada archivo.
#
# Si un solo archivo no se puede descargar, el script termina con error: asi el
# respaldo diario falla de forma visible en lugar de quedar incompleto en
# silencio.
#
# Uso:   DB_URL=postgresql://... ./respaldar_archivos.sh <carpeta_destino>
# Vars:  PSQL (binario psql), PYTHON (python3), CLOUDINARY_CLOUD
# Salida en la carpeta destino:
#   lista.txt       rutas encontradas en la base
#   manifiesto.tsv  ruta · tipo · content-type · bytes, por archivo
#   media/...       los archivos, con la misma ruta que tienen en Cloudinary
# =============================================================================
set -euo pipefail

DB_URL="${DB_URL:?Falta DB_URL}"
PSQL="${PSQL:-psql}"
PY="${PYTHON:-python3}"
CLOUD="${CLOUDINARY_CLOUD:-dp0tzbjal}"
DEST="${1:?Indica la carpeta destino}"

# Todos los campos de archivo de la aplicacion (FileField / ImageField).
# Si se agrega un campo de archivo nuevo a un modelo, hay que sumarlo aqui.
SQL="
select profile_photo      from accounts_user                               where coalesce(profile_photo,'')      <> ''
union select signature_image  from accounts_user                           where coalesce(signature_image,'')    <> ''
union select file             from accounts_userdocument                   where coalesce(file,'')               <> ''
union select archivo          from assignments_assignment                  where coalesce(archivo,'')            <> ''
union select archivo          from assignments_submission                  where coalesce(archivo,'')            <> ''
union select attachment       from attendance_attendance                   where coalesce(attachment,'')         <> ''
union select image            from landing_content_landingnews             where coalesce(image,'')              <> ''
union select image            from landing_content_landinggalleryitem      where coalesce(image,'')              <> ''
union select file             from landing_content_landingdocument         where coalesce(file,'')               <> ''
union select document         from permission_letters_permissionletter     where coalesce(document,'')           <> ''
union select signed_document  from permission_letters_permissionletterrecipient where coalesce(signed_document,'') <> ''
order by 1;"

mkdir -p "$DEST"
"$PSQL" "$DB_URL" -At -c "$SQL" > "$DEST/lista.txt"
: > "$DEST/manifiesto.tsv"

total=0
ok=0
fail=0
while IFS= read -r ruta || [ -n "$ruta" ]; do
  ruta="${ruta%$'\r'}"
  [ -z "$ruta" ] && continue
  total=$((total + 1))

  codificada=$("$PY" -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$ruta")
  destino="$DEST/$ruta"
  mkdir -p "$(dirname "$destino")"

  descargado=0
  # Cloudinary separa los archivos por tipo; se prueban los tres posibles.
  for tipo in image raw video; do
    url="https://res.cloudinary.com/$CLOUD/$tipo/upload/v1/$codificada"
    if info=$(curl -fsSL --retry 3 --retry-delay 2 -w '%{content_type}\t%{size_download}' -o "$destino" "$url" 2>/dev/null); then
      printf '%s\t%s\t%s\n' "$ruta" "$tipo" "$info" >> "$DEST/manifiesto.tsv"
      descargado=1
      break
    fi
  done

  if [ "$descargado" -eq 1 ]; then
    ok=$((ok + 1))
  else
    rm -f "$destino"
    fail=$((fail + 1))
    echo "NO SE PUDO DESCARGAR: $ruta" >&2
  fi
done < "$DEST/lista.txt"

echo "Archivos en la base: $total | descargados: $ok | fallidos: $fail"
[ "$fail" -eq 0 ]
