###  Descripción  
Este proyecto es el **backend del sistema Aula**, desarrollado con **Django** y **Django REST Framework**.  
Proporciona una **API REST** para la gestión de autenticación, cursos, tareas y entregas, utilizando **PostgreSQL** como base de datos.

📂 Repositorio: (https://github.com/murciabrayan/Backend-Aula)

---

### ⚙️ Configuración del entorno

#### 1️⃣ Clonar el repositorio  
```bash
git clone https://github.com/murciabrayan/Backend-Aula.git
cd Backend-Aula

### Crear Entorno virtual y dependencias

python -m venv venv
venv\Scripts\activate  # En Windows
source venv/bin/activate  #(en Linux/Mac)
pip install -r requirements.txt

Configuración en settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gimnasio',
        'USER': 'postgres',
        'PASSWORD': 'cafune123',
        'HOST': 'localhost',
        'PORT': '5434',
    }
}


Documentacion de Postman:
https://documenter.getpostman.com/view/48002548/2sB3Wnx2vB