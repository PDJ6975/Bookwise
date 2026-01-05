# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BookWise** is a Django-based book recommendation system for a university project (AII - Aplicaciones Informáticas Inteligentes). The system uses:
- **BeautifulSoup** for web scraping (QueLibroLeo and Lecturalia)
- **Whoosh** for full-text search indexing
- **Content-based recommendation system** using Dice coefficient
- **Django** for web framework and user management

**Key Architecture Decision**: Books are stored exclusively in Whoosh index (not in Django database). Django SQLite stores only users and their book ratings.

## Common Commands

### Development Server
```bash
# Run Django development server
python manage.py runserver

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser
```

### Web Scraping
```bash
# Scrape and index books from all sources (~400 books)
python main/whoosh_utils.py

# Test scraping from specific source
python main/scraping.py lecturalia          # Only Lecturalia
python main/scraping.py quelibroleo         # Only QueLibroLeo (all genres)
python main/scraping.py quelibroleo humor   # QueLibroLeo single genre
```

### Whoosh Index Operations
```bash
# Create/rebuild index with scraped data (from Django shell)
python manage.py shell
>>> from main.whoosh_utils import indexar_libros, limpiar_indice
>>> from main.scraping import extraer_todos_libros, filtrar_duplicados
>>> libros = extraer_todos_libros()
>>> libros = filtrar_duplicados(libros)
>>> indexar_libros(libros)

# Quick test searches
>>> from main.whoosh_utils import buscar, buscar_por_genero, obtener_generos
>>> buscar("amor", campo='titulo')
>>> buscar_por_genero("Ensayo")
>>> obtener_generos()
```

## Project Structure

```
bookwise/
├── manage.py
├── db.sqlite3                  # Only users and ratings
├── Index/                      # Whoosh index (all book data)
├── bookwise/                   # Django project settings
│   ├── settings.py
│   └── urls.py
└── main/                       # Main Django app
    ├── models.py               # Valoracion model only
    ├── views.py                # Web views (TO BE IMPLEMENTED)
    ├── forms.py                # Search/rating forms (TO BE IMPLEMENTED)
    ├── scraping.py             # BeautifulSoup scrapers
    ├── whoosh_utils.py         # Whoosh indexing and search
    ├── recommender.py          # Content-based recommender (TO BE IMPLEMENTED)
    ├── generos.py              # Genre normalization mappings
    ├── admin.py                # Django admin configuration
    ├── templates/              # HTML templates (empty placeholders)
    └── static/                 # CSS/JS assets
```

## Code Architecture

### Data Flow
1. **Scraping** → `scraping.py` extracts books from web sources
2. **Normalization** → `generos.py` maps source genres to canonical genres
3. **Indexing** → `whoosh_utils.py` stores books in Whoosh index
4. **Search** → Users query Whoosh for books
5. **Rating** → Users rate books (stored in Django DB)
6. **Recommendations** → System analyzes user's rated book genres and recommends similar books

### Web Scraping (`scraping.py`)

**QueLibroLeo Strategy**:
- Scrapes by genre category (17 genres available)
- URL pattern: `https://quelibroleo.com/mejores-genero/{genre}?page={page}`
- Extracts: title, author, synopsis, rating (1-10), votes, cover image
- Uses genre slug to canonical genre mapping via `generos.py`

**Lecturalia Strategy**:
- Scrapes best-rated books list
- URL pattern: `https://www.lecturalia.com/libros/va/mejor-valorados/{page}`
- Performs detail page extraction for each book (deeper scraping)
- Extracts genre, synopsis, and full metadata from individual book pages

**Duplicate Handling**: `filtrar_duplicados()` normalizes titles and removes duplicates

### Whoosh Integration (`whoosh_utils.py`)

**Schema**:
```python
titulo=TEXT(stored=True)           # Full-text searchable
autor=TEXT(stored=True)            # Full-text searchable
genero=KEYWORD(stored=True)        # Exact match, comma-separated
sinopsis=TEXT(stored=True)         # Full-text searchable
valoracion=NUMERIC(float)          # Book's average rating
num_votos=NUMERIC(int)             # Number of votes
url=ID(stored=True, unique=True)   # Source URL (unique key)
portada=ID(stored=True)            # Cover image URL
fuente=KEYWORD(stored=True)        # 'quelibroleo' or 'lecturalia'
```

**Key Functions**:
- `indexar_libros(libros)` - Index a list of book dicts
- `buscar(query, campo, limite)` - Search single field
- `buscar_multicampo(query, campos, limite)` - Search multiple fields
- `buscar_por_genero(genero, limite)` - Genre-specific search
- `obtener_todos_libros()` - Get all indexed books
- `obtener_generos()` - Get list of all genres

### Genre Normalization (`generos.py`)

Centralizes genre mapping from scraping sources to 16 canonical genres:
- Biografías y Memorias
- Ciencia Ficción y Fantasía
- Clásicos
- Cómic y Novela Gráfica
- Economía y Empresa
- Ensayo
- Ficción Literaria
- Histórica y Aventuras
- Humor
- Infantil y Juvenil
- Literatura Contemporánea
- Narrativa
- No Ficción
- Novela Negra y Terror
- Poesía y Teatro
- Romántica

**Functions**:
- `normalizar_genero_quelibroleo(slug)` - Maps QueLibroLeo genre slug
- `normalizar_genero_lecturalia(genero)` - Maps Lecturalia genre text

### Django Models (`models.py`)

**Valoracion Model**:
```python
usuario = ForeignKey(User)           # Django auth user
titulo_libro = CharField(max_length=500)  # Reference to book in Whoosh
puntuacion = FloatField(1.0-10.0)    # User's rating (1-10 scale)
fecha = DateTimeField(auto_now_add=True)
actualizado = DateTimeField(auto_now=True)
```

**Important**: Books are NOT in Django DB. `titulo_libro` is a string reference to look up the book in Whoosh index.

### Recommendation System (`recommender.py`)

**Status**: Empty placeholder file (needs implementation)

**Planned Algorithm** (Content-Based with Dice Coefficient):
1. Build user profile from highly-rated books (puntuacion >= 7.0)
2. Extract set of favorite genres from user's rated books
3. For each candidate book:
   - Calculate Dice coefficient between user's genres and book's genres
   - Dice formula: `2 * |A ∩ B| / (|A| + |B|)`
   - Boost score by book's overall rating (30% weight)
4. Return top-N books ranked by similarity score

**Key Functions to Implement**:
- `perfil_usuario(usuario_id)` - Extract user's favorite genres
- `recomendar(usuario_id, n=10)` - Generate top-N recommendations
- `dice(set_a, set_b)` - Calculate Dice coefficient

**Reference Pattern** (from project plan):
```python
def dice(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    interseccion = len(set_a & set_b)
    return (2.0 * interseccion) / (len(set_a) + len(set_b))

def recomendar(usuario_id, n=10):
    # 70% genre similarity + 30% book rating
    score = (0.7 * sim_generos) + (0.3 * bonus_valoracion)
```

### Views and Templates

**Status**:
- `views.py` - Empty placeholder (only has imports)
- `templates/` - Empty HTML files created (base.html, index.html, buscar.html, buscar_genero.html, recomendaciones.html)
- `forms.py` - Empty file

**Views to Implement**:
- `index` - Homepage
- `buscar` - Multi-field book search
- `buscar_genero` - Genre-based browsing
- `valorar_libro` - Rate a book (requires login)
- `recomendaciones` - Personalized recommendations (requires login)

**URL Routing**: Not configured yet (need to add `main.urls` to `bookwise/urls.py`)

## Development Workflow

### When working on frontend:
1. Create forms in `forms.py` for search and rating inputs
2. Implement view functions in `views.py`
3. Add URL patterns to `main/urls.py` and include in `bookwise/urls.py`
4. Build HTML templates extending `base.html`
5. Style with CSS in `main/static/`

### When working on recommendations:
1. Implement core algorithm in `recommender.py`
2. Test with Django shell using real user data
3. Integrate into `views.py` for web access
4. Create template to display recommendations

### Testing scraping changes:
1. Modify scraper in `scraping.py`
2. Test with: `python main/scraping.py <source> [genre]`
3. Verify data with `verificar_libros()` function
4. Rebuild index with `python main/whoosh_utils.py`

## Important Notes

- **Do NOT add books to Django models** - they belong in Whoosh only
- **Rating scale is 1.0-10.0** (not 1-5) as specified in Valoracion model validators
- **Genre normalization is critical** - always use `generos.py` functions when scraping
- **Duplicate detection** uses normalized titles (lowercase, no punctuation)
- **User authentication** required for rating and recommendations
- The `main` app is not yet added to `INSTALLED_APPS` in settings.py - add it when implementing views

## Project Requirements (for context)

- Scrape ~400 books from 2 sources (QueLibroLeo + Lecturalia)
- Implement complex Whoosh searches (multi-field, genre, author, etc.)
- Content-based recommender using Dice coefficient
- User-friendly Django interface with authentication
- Deadline: January 12, 2026
