# Backend Aula

Backend del proyecto **Proyecto Aula - Gimnasio Los Cerros**, desarrollado con **Django 5** y **Django REST Framework**.

Expone la API principal de la plataforma académica e institucional y soporta autenticación, gestión de usuarios, cursos, tareas, asistencia, boletines, alertas, permisos, contenido público de landing y notificaciones.

## Características

- API REST para paneles de administrador, docente y estudiante.
- Autenticación JWT.
- Inicio de sesión con Google.
- Recuperación de contraseña por correo.
- Gestión de usuarios y carga masiva.
- Gestión de cursos, áreas, materias e indicadores.
- Tareas, entregas y calificaciones.
- Asistencia con trazabilidad de eventos.
- Boletines académicos en PDF.
- Alertas académicas con flujo de seguimiento.
- Permisos institucionales con respuesta firmada.
- Landing pública editable desde administración.
- Notificaciones internas.
- Almacenamiento de archivos con **Cloudinary** en producción.
- Preparado para despliegue en **Render** con PostgreSQL.

## Stack

- Python 3.13+
- Django 5.2
- Django REST Framework
- SimpleJWT
- PostgreSQL
- Gunicorn
- WhiteNoise
- Cloudinary
- ReportLab

## Módulos principales

```text
accounts/           Usuarios, perfiles, autenticación, Google y documentos
courses/            Cursos, áreas y materias
assignments/        Tareas y entregas
attendance/         Asistencia y eventos de asistencia
report_cards/       Boletines, configuración e indicadores
academic_alerts/    Alertas tempranas y seguimiento
calendar_app/       Calendario académico
notifications/      Notificaciones internas
permission_letters/ Permisos institucionales
landing_content/    Noticias, galería, documentos y calendario público
backend_project/    Configuración global, settings y utilidades
```

## Requisitos

- Python 3.13+ recomendado
- PostgreSQL
- pip
- entorno virtual (`venv`)

## Instalación

```bash
git clone https://github.com/murciabrayan/Backend-Aula.git
cd Backend-Aula
python -m venv venv
```

### Activar entorno virtual

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## Variables de entorno

La aplicación usa variables de entorno para separar local, pruebas y producción.

### Variables mínimas para entorno local

```env
DJANGO_SECRET_KEY=tu_clave_local
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=gimnasio
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=tu_google_client_id.apps.googleusercontent.com
```

### Variables importantes en producción

```env
DJANGO_SECRET_KEY=tu_clave_secreta
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-backend.onrender.com,www.tu-dominio.com,tu-dominio.com

DATABASE_URL=postgres://usuario:clave@host:5432/base_de_datos

FRONTEND_URL=https://www.tu-dominio.com
CORS_ALLOWED_ORIGINS=https://www.tu-dominio.com,https://tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://www.tu-dominio.com,https://tu-dominio.com

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_correo_institucional@gmail.com
EMAIL_HOST_PASSWORD=tu_clave_de_aplicacion

LANDING_CONTACT_EMAIL=tu_correo_institucional@gmail.com

DRF_THROTTLE_ANON=10000/min
DRF_THROTTLE_USER=10000/min

SECURE_SSL_REDIRECT=True

CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
```

## Base de datos

### Migraciones

```bash
python manage.py migrate
```

### Crear administrador local

```bash
python manage.py createsuperuser
```

### Comando auxiliar del proyecto

Existe además el comando:

```bash
python manage.py ensure_admin
```

Usado en despliegue para garantizar un usuario administrador cuando se configura por variables de entorno.

## Ejecución local

```bash
python manage.py runserver
```

Disponible normalmente en:

```text
http://127.0.0.1:8000
```

## Configuraciones disponibles

### Desarrollo

```bash
python manage.py runserver
```

Usa:

```text
backend_project.settings
```

### Producción

```bash
python manage.py runserver --settings=backend_project.production_settings
```

### Pruebas

```bash
python manage.py test --settings=backend_project.test_settings
```

### Rendimiento

```bash
python manage.py runserver --settings=backend_project.performance_settings
```

## Endpoints principales

Algunos grupos relevantes de endpoints:

- `/api/token/`
- `/api/token/refresh/`
- `/api/auth/google/`
- `/api/password-reset/`
- `/api/profile/`
- `/api/users/`
- `/api/courses/`
- `/api/subjects/`
- `/api/assignments/`
- `/api/submissions/`
- `/api/attendance/`
- `/api/report-cards/`
- `/api/calendar/`
- `/api/permission-letters/`
- `/api/mis-notificaciones/`
- `/api/landing/`

## Pruebas

### Ejecutar pruebas generales

```bash
python manage.py test --settings=backend_project.test_settings
```

### Verificación de seguridad de despliegue

```bash
python manage.py check --deploy --settings=backend_project.production_settings
```

### Pruebas específicas

Ejemplo:

```bash
python manage.py test attendance --settings=backend_project.test_settings
```

## Despliegue

El backend está preparado para **Render**.

### Build

El proyecto incluye:

- `build.sh`
- `render.yaml`
- `Procfile`
- `nixpacks.toml`

### Start command de producción

La lógica de producción utiliza migraciones, `gunicorn` y el settings de producción.

## Producción actual

Backend desplegado en:

```text
https://tu-backend.onrender.com
```

Frontend conectado:

```text
https://www.tu-dominio.com
```

## Archivos y persistencia

En producción los archivos se almacenan en **Cloudinary**, lo que evita pérdida de:

- fotos de perfil,
- firmas,
- permisos firmados,
- documentos de usuarios,
- imágenes de landing.

## Correo

El backend soporta envío de:

- credenciales de bienvenida,
- recuperación de contraseña,
- mensajes de contacto,
- flujos asociados al onboarding.

## Repositorio relacionado

Frontend:

```text
https://github.com/murciabrayan/frontend-aula
```
