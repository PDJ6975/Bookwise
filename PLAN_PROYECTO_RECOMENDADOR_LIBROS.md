# 📚 BookWise - Sistema de Recomendación de Libros

## Plan de Proyecto Simplificado

**Autor:** Antonio  
**Fecha:** Enero 2026  
**Asignatura:** Acceso Inteligente a la Información  
**Tiempo estimado:** 10 horas | **Valor:** 1 punto

---

## 1. IDEA RESUMIDA

Aplicación web que permite buscar libros y obtener recomendaciones personalizadas basadas en géneros.

**Flujo del sistema:**
1. **Scraping** → BeautifulSoup extrae libros de Quelibroleo + Lecturalia
2. **Whoosh** → Almacena libros directamente (sin BD intermedia)
3. **Django** → Interfaz web + usuarios + valoraciones
4. **SR Contenido** → Recomendar por géneros + valoración

**Almacenamiento:**
- **Whoosh Index** → Libros (título, autor, género, valoración, etc.)
- **Django SQLite** → Solo usuarios y sus valoraciones

---

## 2. ESTRATEGIA DE SCRAPING

### 2.1 Quelibroleo (FUENTE PRINCIPAL)

**URL Base:** `https://quelibroleo.com/mejores-genero?page=X`

**Datos extraídos:** Título, Autor, Género, Resumen, Nota media, Num votos, Num críticas

### 2.2 Lecturalia (COMPLEMENTO)

**URL Base:** `https://www.lecturalia.com/libros/va/mejor-valorados`

**Datos extraídos:** Título, Autor, Género, Valoración, Num comentarios

### 2.3 Resumen

| Web | Páginas | Libros | Tiempo |
|-----|---------|--------|--------|
| Quelibroleo | 5 | ~250 | ~30s |
| Lecturalia | 5 | ~150 | ~30s |
| **TOTAL** | 10 | **~400** | **~1 min** |

---

## 3. ESQUEMA WHOOSH

```python
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC

schema = Schema(
    titulo=TEXT(stored=True),
    autor=TEXT(stored=True),
    genero=KEYWORD(stored=True, lowercase=True),
    sinopsis=TEXT(stored=True),
    valoracion=NUMERIC(stored=True, decimal_places=2),
    num_votos=NUMERIC(stored=True),
    num_criticas=NUMERIC(stored=True),
    url=ID(stored=True),
    fuente=ID(stored=True)
)
```

---

## 4. ESTRUCTURA DEL PROYECTO

```
BookWise/
├── manage.py
├── bookwise/
│   ├── settings.py
│   └── urls.py
├── main/
│   ├── models.py          # Solo Usuario y Valoracion
│   ├── views.py           # Vistas web
│   ├── urls.py
│   ├── forms.py
│   ├── scraping.py        # Extrae libros (BeautifulSoup)
│   ├── whoosh_utils.py    # Almacenar y buscar en Whoosh
│   ├── recommender.py     # SR basado en contenido
│   └── templates/
├── Index/                  # Índice Whoosh (libros)
└── db.sqlite3             # Solo usuarios y valoraciones
```

---

## 5. SCRAPING (siguiendo estructura del ejemplo)

```python
# scraping.py
from bs4 import BeautifulSoup
import urllib.request
import os, ssl

# Evitar error SSL
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

PAGINAS_QUELIBROLEO = 5
PAGINAS_LECTURALIA = 5

def extraer_libros_quelibroleo():
    """Extrae libros de la sección mejores por género de Quelibroleo"""
    lista = []
    
    for p in range(1, PAGINAS_QUELIBROLEO + 1):
        url = f"https://quelibroleo.com/mejores-genero?page={p}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        
        # Ajustar selectores según HTML real de la web
        libros = s.find_all('div', class_='libro-item')  # Selector a verificar
        
        for libro in libros:
            try:
                titulo = libro.find('a', class_='titulo').string.strip()
                autor = libro.find('a', class_='autor').string.strip()
                genero = libro.find('span', class_='genero').string.strip()
                sinopsis = libro.find('p', class_='resumen').string.strip() if libro.find('p', class_='resumen') else ''
                
                # Extraer valoración numérica
                val_text = libro.find('span', class_='nota').string.strip()
                valoracion = float(val_text.replace(',', '.'))
                
                # Extraer número de votos y críticas
                votos_text = libro.find('a', class_='votos').string.strip()
                num_votos = int(''.join(filter(str.isdigit, votos_text)))
                
                criticas_text = libro.find('a', class_='criticas').string.strip()
                num_criticas = int(''.join(filter(str.isdigit, criticas_text)))
                
                enlace = libro.find('a', class_='titulo')['href']
                
                lista.append({
                    'titulo': titulo,
                    'autor': autor,
                    'genero': genero,
                    'sinopsis': sinopsis,
                    'valoracion': valoracion,
                    'num_votos': num_votos,
                    'num_criticas': num_criticas,
                    'url': enlace,
                    'fuente': 'quelibroleo'
                })
            except Exception as e:
                print(f"Error extrayendo libro: {e}")
                continue
    
    return lista


def extraer_libros_lecturalia():
    """Extrae libros mejor valorados de Lecturalia"""
    lista = []
    
    for p in range(1, PAGINAS_LECTURALIA + 1):
        if p == 1:
            url = "https://www.lecturalia.com/libros/va/mejor-valorados"
        else:
            url = f"https://www.lecturalia.com/libros/va/mejor-valorados/pag-{p}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        
        # Ajustar selectores según HTML real
        libros = s.find_all('div', class_='libro')  # Selector a verificar
        
        for libro in libros:
            try:
                titulo = libro.find('h2').a.string.strip()
                autor = libro.find('span', class_='autor').a.string.strip()
                genero = libro.find('span', class_='genero').string.strip() if libro.find('span', class_='genero') else 'Sin género'
                sinopsis = libro.find('p', class_='sinopsis').string.strip() if libro.find('p', class_='sinopsis') else ''
                
                # Valoración en escala 1-5, convertir a 1-10
                val_text = libro.find('span', class_='valoracion').string.strip()
                valoracion = float(val_text.replace(',', '.')) * 2
                
                enlace = libro.find('h2').a['href']
                
                lista.append({
                    'titulo': titulo,
                    'autor': autor,
                    'genero': genero,
                    'sinopsis': sinopsis,
                    'valoracion': valoracion,
                    'num_votos': 0,
                    'num_criticas': 0,
                    'url': enlace,
                    'fuente': 'lecturalia'
                })
            except Exception as e:
                print(f"Error extrayendo libro: {e}")
                continue
    
    return lista


def extraer_todos_libros():
    """Extrae libros de todas las fuentes"""
    libros = []
    
    print("Extrayendo de Quelibroleo...")
    libros.extend(extraer_libros_quelibroleo())
    
    print("Extrayendo de Lecturalia...")
    libros.extend(extraer_libros_lecturalia())
    
    print(f"Total libros extraídos: {len(libros)}")
    return libros
```

---

## 6. ALMACENAMIENTO EN WHOOSH (siguiendo estructura del ejemplo)

```python
# whoosh_utils.py
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser
import os, shutil

INDEX_DIR = "Index"

# Define el esquema de la información
schema = Schema(
    titulo=TEXT(stored=True),
    autor=TEXT(stored=True),
    genero=KEYWORD(stored=True, lowercase=True, commas=True),
    sinopsis=TEXT(stored=True),
    valoracion=NUMERIC(stored=True, decimal_places=2),
    num_votos=NUMERIC(stored=True),
    num_criticas=NUMERIC(stored=True),
    url=ID(stored=True),
    fuente=ID(stored=True)
)


def almacenar_datos():
    """Extrae libros y los almacena en el índice Whoosh"""
    from main.scraping import extraer_todos_libros
    
    # Eliminamos el directorio del índice, si existe
    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
    os.mkdir(INDEX_DIR)
    
    # Creamos el índice
    ix = create_in(INDEX_DIR, schema=schema)
    
    # Creamos un writer para poder añadir documentos al índice
    writer = ix.writer()
    
    # Extraemos los libros
    lista = extraer_todos_libros()
    
    i = 0
    for libro in lista:
        # Añade cada libro al índice
        writer.add_document(
            titulo=libro['titulo'],
            autor=libro['autor'],
            genero=libro['genero'],
            sinopsis=libro['sinopsis'],
            valoracion=libro['valoracion'],
            num_votos=libro['num_votos'],
            num_criticas=libro['num_criticas'],
            url=libro['url'],
            fuente=libro['fuente']
        )
        i += 1
    
    writer.commit()
    return i  # Número de libros indexados


def buscar_por_titulo(texto):
    """Busca libros por título"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        query = QueryParser("titulo", ix.schema).parse(texto)
        results = searcher.search(query, limit=20)
        return [dict(r) for r in results]


def buscar_por_autor(autor):
    """Busca libros por autor"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        query = QueryParser("autor", ix.schema).parse(f'"{autor}"')
        results = searcher.search(query, limit=None)
        return [dict(r) for r in results]


def buscar_por_genero(genero):
    """Busca libros por género"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        query = QueryParser("genero", ix.schema).parse(genero)
        results = searcher.search(query, limit=None)
        return [dict(r) for r in results]


def buscar_multicampo(texto):
    """Busca en título, autor y sinopsis"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        parser = MultifieldParser(["titulo", "autor", "sinopsis"], ix.schema)
        query = parser.parse(texto)
        results = searcher.search(query, limit=20)
        return [dict(r) for r in results]


def obtener_todos_libros():
    """Devuelve todos los libros del índice"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        results = searcher.search(QueryParser("titulo", ix.schema).parse("*"), limit=None)
        return [dict(r) for r in results]


def obtener_lista_generos():
    """Devuelve lista de todos los géneros"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        return [term.decode('utf-8') for term in searcher.lexicon('genero')]


def obtener_lista_autores():
    """Devuelve lista de todos los autores"""
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        return [term.decode('utf-8') for term in searcher.lexicon('autor')]
```

---

## 7. MODELOS DJANGO (Mínimos)

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Valoracion(models.Model):
    """Valoración de un usuario sobre un libro (identificado por título)"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo_libro = models.CharField(max_length=500)  # Referencia al libro en Whoosh
    puntuacion = models.IntegerField()  # 1-5
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'titulo_libro')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo_libro}: {self.puntuacion}"
```

---

## 8. SISTEMA DE RECOMENDACIÓN

```python
# recommender.py
from collections import Counter
from main.models import Valoracion
from main.whoosh_utils import buscar_por_genero, obtener_todos_libros, open_dir, QueryParser

INDEX_DIR = "Index"

def dice(set_a, set_b):
    """Coeficiente de Dice: similitud entre conjuntos"""
    if not set_a or not set_b:
        return 0.0
    interseccion = len(set_a & set_b)
    return (2.0 * interseccion) / (len(set_a) + len(set_b))


def obtener_libro_por_titulo(titulo):
    """Obtiene un libro del índice por su título exacto"""
    from whoosh.index import open_dir
    from whoosh.qparser import QueryParser
    
    ix = open_dir(INDEX_DIR)
    with ix.searcher() as searcher:
        query = QueryParser("titulo", ix.schema).parse(f'"{titulo}"')
        results = searcher.search(query, limit=1)
        if results:
            return dict(results[0])
    return None


def perfil_usuario(usuario_id):
    """
    Construye perfil del usuario basado en sus valoraciones altas (>=4)
    Retorna: set de géneros preferidos
    """
    valoraciones = Valoracion.objects.filter(
        usuario_id=usuario_id,
        puntuacion__gte=4
    )
    
    generos = Counter()
    for v in valoraciones:
        libro = obtener_libro_por_titulo(v.titulo_libro)
        if libro and libro.get('genero'):
            peso = v.puntuacion - 3  # 4→1, 5→2
            # El género puede tener varios valores separados por comas
            for g in libro['genero'].split(','):
                generos[g.strip()] += peso
    
    # Top 5 géneros preferidos
    return set(g for g, _ in generos.most_common(5))


def recomendar(usuario_id, n=10):
    """
    Recomienda libros basándose en:
    - 70% similitud de géneros (Dice)
    - 30% valoración del libro (normalizada)
    """
    perfil = perfil_usuario(usuario_id)
    
    # Libros ya valorados (excluir)
    valorados = set(Valoracion.objects.filter(
        usuario_id=usuario_id
    ).values_list('titulo_libro', flat=True))
    
    # Si no hay perfil, devolver los mejor valorados
    if not perfil:
        todos = obtener_todos_libros()
        todos_ordenados = sorted(todos, key=lambda x: x.get('valoracion', 0), reverse=True)
        return [(libro.get('valoracion', 0) * 10, libro) for libro in todos_ordenados[:n]]
    
    # Obtener todos los libros
    todos_libros = obtener_todos_libros()
    
    candidatos = []
    for libro in todos_libros:
        # Excluir libros ya valorados
        if libro.get('titulo') in valorados:
            continue
        
        # Géneros del libro
        generos_libro = set()
        if libro.get('genero'):
            generos_libro = set(g.strip() for g in libro['genero'].split(','))
        
        # Similitud por géneros (70%)
        sim_generos = dice(perfil, generos_libro)
        
        # Bonus por valoración alta (30%) - normalizado a 0-1
        valoracion = libro.get('valoracion', 0)
        bonus_valoracion = valoracion / 10.0  # Asumiendo escala 0-10
        
        # Score final
        score = (0.7 * sim_generos) + (0.3 * bonus_valoracion)
        
        if score > 0:
            candidatos.append((score, libro))
    
    # Ordenar por score descendente
    candidatos.sort(key=lambda x: x[0], reverse=True)
    
    return [(round(score * 100, 1), libro) for score, libro in candidatos[:n]]
```

---

## 9. VISTAS DJANGO

```python
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from main.whoosh_utils import almacenar_datos, buscar_multicampo, obtener_lista_generos, buscar_por_genero
from main.recommender import recomendar
from main.models import Valoracion

def index(request):
    """Página principal"""
    return render(request, 'index.html')


def cargar_datos(request):
    """Ejecuta el scraping y almacena en Whoosh"""
    if request.method == 'POST':
        try:
            num_libros = almacenar_datos()
            messages.success(request, f'Se han indexado {num_libros} libros correctamente.')
        except Exception as e:
            messages.error(request, f'Error al cargar datos: {e}')
    return redirect('index')


def buscar(request):
    """Búsqueda de libros"""
    resultados = []
    query = request.GET.get('q', '')
    
    if query:
        resultados = buscar_multicampo(query)
    
    return render(request, 'buscar.html', {
        'resultados': resultados,
        'query': query
    })


def buscar_genero(request):
    """Búsqueda por género"""
    generos = obtener_lista_generos()
    resultados = []
    genero_seleccionado = request.GET.get('genero', '')
    
    if genero_seleccionado:
        resultados = buscar_por_genero(genero_seleccionado)
    
    return render(request, 'buscar_genero.html', {
        'generos': generos,
        'resultados': resultados,
        'genero_seleccionado': genero_seleccionado
    })


@login_required
def valorar_libro(request):
    """Valorar un libro"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        puntuacion = int(request.POST.get('puntuacion'))
        
        Valoracion.objects.update_or_create(
            usuario=request.user,
            titulo_libro=titulo,
            defaults={'puntuacion': puntuacion}
        )
        messages.success(request, f'Has valorado "{titulo}" con {puntuacion} estrellas.')
    
    return redirect('buscar')


@login_required
def recomendaciones(request):
    """Muestra recomendaciones personalizadas"""
    recomendados = recomendar(request.user.id, n=10)
    return render(request, 'recomendaciones.html', {
        'recomendaciones': recomendados
    })
```

---

## 10. URLS

```python
# main/urls.py
from django.urls import path
from main import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cargar/', views.cargar_datos, name='cargar'),
    path('buscar/', views.buscar, name='buscar'),
    path('buscar-genero/', views.buscar_genero, name='buscar_genero'),
    path('valorar/', views.valorar_libro, name='valorar'),
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),
]
```

---

## 11. CRONOGRAMA (10 HORAS)

| Bloque | Tarea | Tiempo |
|--------|-------|--------|
| **1** | Setup Django + Modelo Valoracion | 0.5h |
| **2** | Scraping Quelibroleo (adaptar selectores) | 2h |
| **3** | Scraping Lecturalia (adaptar selectores) | 1.5h |
| **4** | Whoosh (almacenar + búsquedas) | 1.5h |
| **5** | SR basado en contenido | 1.5h |
| **6** | Vistas + Templates | 2h |
| **7** | Testing + PDF + PPT | 1h |
| **TOTAL** | | **10h** |

---

## 12. CHECKLIST FINAL

### Requisitos técnicos:
- [ ] **BeautifulSoup**: Quelibroleo + Lecturalia (2 webs ✓)
- [ ] **Whoosh**: Almacenamiento + búsquedas múltiples
- [ ] **SR**: Basado en contenido con Dice
- [ ] **Django**: Interfaz web, login, valoraciones

### Entregables:
- [ ] Proyecto Django con índice Whoosh (~400 libros)
- [ ] PDF (máx 4 páginas)
- [ ] Presentación PPT (~10 min)

---

## 13. COMANDOS RÁPIDOS

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install django beautifulsoup4 lxml whoosh

# Django
python manage.py migrate
python manage.py createsuperuser

# Cargar datos (desde la web o shell)
python manage.py shell
>>> from main.whoosh_utils import almacenar_datos
>>> almacenar_datos()

# Ejecutar
python manage.py runserver
```

---

**Arquitectura final:**
- **Whoosh** = Almacén de libros (scraping directo, sin BD intermedia)
- **Django SQLite** = Solo usuarios y valoraciones
- **Tiempo total:** ~10 horas | **Scraping:** ~1 minuto | **Libros:** ~400
