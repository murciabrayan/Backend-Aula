#!/bin/bash
set -euo pipefail

APP_DIR="/var/app/current"
PYTHON_BIN="$(find /var/app/venv -path '*/bin/python' | head -n 1)"

if [ -z "${PYTHON_BIN}" ]; then
  echo "No se encontro el interprete de Python del entorno virtual." >&2
  exit 1
fi

cd "${APP_DIR}"
"${PYTHON_BIN}" manage.py generate_academic_alerts --periods 1 2 3 4
