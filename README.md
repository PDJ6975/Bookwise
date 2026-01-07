# BookWise - Un Sistema de Recomendación de Libros

## Requisitos

- Python 3.10+
- pip

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos
python manage.py migrate

# 4. Crear usuario administrador
python manage.py createsuperuser

# 5. Ejecutar servidor
python manage.py runserver
```

## Acceso

Abrir http://127.0.0.1:8000/

## Funcionalidades

- **Catálogo**: 579 libros de QueLibroLeo y Lecturalia (ya indexados en Whoosh). Los administradores pueden actualizar el catálogo desde el menú
- **Búsqueda avanzada**: Por título, autor, género, valoración
- **Mi Librería**: Guardar libros y valorarlos (0.5 - 5 estrellas)
- **Recomendaciones**: Basadas en tus géneros y autores favoritos (usando el Coeficiente de Dice)

## Probar el sistema de recomendación

1. Registrarse o iniciar sesión
2. Añadir libros a "Mi Librería" desde la Galería
3. Marcarlos como "Leídos" y darles valoración ≥ 4 estrellas
4. Volver a "Descubrir" para ver recomendaciones personalizadas

## Estructura

```
bookwise/
├── Index/           # Índice Whoosh (579 libros)
├── main/
│   ├── scraping.py      # Web scraping
│   ├── whoosh_utils.py  # Búsqueda Whoosh
│   ├── recommender.py   # Sistema de recomendación
│   └── templates/       # Vistas HTML
└── manage.py
```
