# scraping.py
from bs4 import BeautifulSoup
import urllib.request
import re
import os
import ssl

# Evitar error SSL
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

PAGINAS_LECTURALIA = 2
PAGINAS_QUELIBROLEO = 3

# Lista de géneros de QueLibroLeo (17 géneros -> 3 páginas / género)
GENEROS_QUELIBROLEO = [
    'biografias-memorias',
    'clasicos-de-la-literatura',
    'comics-novela-grafica',
    'economia-empresa-marketing',
    'ensayo',
    'fantastica-ciencia-ficcion',
    'ficcion-literaria',
    'historica-y-aventuras',
    'humor',
    'infantil-y-juvenil',
    'lecturas-complementarias',
    'literatura-contemporanea',
    'narrativa',
    'no-ficcion',
    'novela-negra-intriga-terror',
    'poesia-teatro',
    'romantica-erotica'
]


def extraer_libros_quelibroleo(generos=None):
    """Extrae libros mejor valorados de QueLibroLeo por género
    
    Args:
        generos: Lista de géneros a extraer. Si es None, extrae todos.
    """
    lista = []
    generos_a_extraer = generos if generos else GENEROS_QUELIBROLEO
    
    for genero in generos_a_extraer:
        print(f"  Extrayendo género: {genero}...")
        
        for p in range(1, PAGINAS_QUELIBROLEO + 1):
            url = f"https://quelibroleo.com/mejores-genero/{genero}?sort=&page={p}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                f = urllib.request.urlopen(req)
                s = BeautifulSoup(f, 'lxml')
                
                # Los libros están en: div.item
                items = s.find_all('div', class_='item')
                
                for item in items:
                    try:
                        # URL del libro
                        enlace = item.find('a', class_='left_side')
                        if not enlace:
                            continue
                        url_libro = enlace.get('href', '')
                        
                        # Título: div.col-lg-8 a span b
                        col_info = item.find('div', class_='col-lg-8')
                        if not col_info:
                            continue
                        
                        titulo_tag = col_info.find('b')
                        titulo = titulo_tag.get_text(strip=True) if titulo_tag else ''
                        
                        # Autor: div.col-lg-8 small a
                        autor_tag = col_info.find('small')
                        if autor_tag:
                            autor_link = autor_tag.find('a')
                            autor = autor_link.get_text(strip=True) if autor_link else autor_tag.get_text(strip=True)
                        else:
                            autor = ''
                        
                        # Sinopsis: div.tab-pane div.text p
                        sinopsis = ''
                        text_div = item.find('div', class_='text')
                        if text_div:
                            p_tag = text_div.find('p')
                            if p_tag:
                                sinopsis = p_tag.get_text(strip=True)
                                # Limpiar el enlace de "seguir leyendo"
                                if sinopsis:
                                    sinopsis = sinopsis.split('...')[0] + '...' if '...' in sinopsis else sinopsis
                        
                        # Estadísticas: div.estadisticas
                        estadisticas = item.find('div', class_='estadisticas')
                        valoracion = 0.0
                        num_votos = 0
                        num_criticas = 0
                        
                        if estadisticas:
                            # Nota media: span
                            nota_span = estadisticas.find('span')
                            if nota_span:
                                nota_text = nota_span.get_text(strip=True).replace(',', '.')
                                try:
                                    valoracion = float(nota_text)
                                except:
                                    pass
                            
                            # Número de votos: i.numero_votos a
                            votos_tag = estadisticas.find('i', class_='numero_votos')
                            if votos_tag:
                                votos_text = votos_tag.get_text(strip=True)
                                num_votos = int(''.join(filter(str.isdigit, votos_text)))
                            
                            # Número de críticas: i.numero_criticas a
                            criticas_tag = estadisticas.find('i', class_='numero_criticas')
                            if criticas_tag:
                                criticas_text = criticas_tag.get_text(strip=True)
                                num_criticas = int(''.join(filter(str.isdigit, criticas_text)))
                        
                        # Género formateado (capitalizar)
                        genero_formateado = genero.replace('-', ' ').title()
                        
                        lista.append({
                            'titulo': titulo,
                            'autor': autor,
                            'genero': genero_formateado,
                            'sinopsis': sinopsis,
                            'valoracion': valoracion,
                            'num_votos': num_votos,
                            'num_criticas': num_criticas,
                            'url': url_libro,
                            'fuente': 'quelibroleo'
                        })
                        
                    except Exception as e:
                        print(f"    Error extrayendo libro: {e}")
                        continue
                        
            except Exception as e:
                print(f"    Error en página {p} de {genero}: {e}")
                continue
    
    return lista


def extraer_libros_lecturalia():
    """Extrae libros mejor valorados de Lecturalia (listado + detalle de cada libro)"""
    lista = []
    
    for p in range(1, PAGINAS_LECTURALIA + 1):
        url = f"https://www.lecturalia.com/libros/va/mejor-valorados/{p}"
        
        print(f"  Extrayendo página {p} de Lecturalia...")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            f = urllib.request.urlopen(req)
            s = BeautifulSoup(f, 'lxml')
            
            # Los libros están en: div.datalist.datalist--img > ul > li
            datalist = s.find('div', class_='datalist--img')
            if not datalist:
                print(f"  No se encontró la lista de libros en página {p}")
                continue
            
            libros_li = datalist.find_all('li')
            
            for li in libros_li:
                try:
                    # Buscar los enlaces del libro
                    enlaces = li.find_all('a')
                    if len(enlaces) < 2:
                        continue
                    
                    # Primer enlace: título y URL del libro
                    titulo = enlaces[0].get_text(strip=True)
                    url_libro = enlaces[0].get('href', '')
                    if not url_libro.startswith('http'):
                        url_libro = 'https://www.lecturalia.com' + url_libro
                    
                    # Segundo enlace: autor
                    autor = enlaces[1].get_text(strip=True)
                    
                    # Extraer detalles adicionales de la página del libro
                    libro_detalle = extraer_detalle_libro(url_libro)
                    
                    lista.append({
                        'titulo': titulo,
                        'autor': autor,
                        'genero': libro_detalle.get('genero', 'Sin género'),
                        'sinopsis': libro_detalle.get('sinopsis', ''),
                        'valoracion': libro_detalle.get('valoracion', 0.0),
                        'num_votos': libro_detalle.get('num_votos', 0),
                        'url': url_libro,
                        'fuente': 'lecturalia'
                    })
                    
                except Exception as e:
                    print(f"  Error extrayendo libro: {e}")
                    continue
                    
        except Exception as e:
            print(f"  Error en página {p}: {e}")
            continue
    
    return lista


def extraer_detalle_libro(url_libro):
    """Extrae detalles adicionales de la página individual del libro"""
    detalle = {
        'genero': 'Sin género',
        'sinopsis': '',
        'valoracion': 0.0,
        'num_votos': 0
    }
    
    try:
        req = urllib.request.Request(url_libro, headers={'User-Agent': 'Mozilla/5.0'})
        f = urllib.request.urlopen(req)
        s = BeautifulSoup(f, 'lxml')
        
        # Buscar los datos en la ficha del libro (ul dentro de profile__data)
        profile_data = s.find('div', class_='profile__data')
        if profile_data:
            items = profile_data.find_all('li')
            for item in items:
                texto = item.get_text()
                
                # Género/Temas: buscar el enlace después de "Temas:"
                if 'Temas:' in texto:
                    enlace_genero = item.find('a')
                    if enlace_genero:
                        detalle['genero'] = enlace_genero.get_text(strip=True)
                
                # Nota media: formato "8 / 10 (151 votos)"
                if 'Nota media:' in texto:
                    # Extraer número antes de " / 10"
                    match = re.search(r'(\d+(?:[.,]\d+)?)\s*/\s*10\s*\((\d+)\s*votos?\)', texto)
                    if match:
                        nota = match.group(1).replace(',', '.')
                        detalle['valoracion'] = float(nota)
                        detalle['num_votos'] = int(match.group(2))
        
        # Sinopsis: texto dentro de div.profile__text div.text
        profile_text = s.find('div', class_='profile__text')
        if profile_text:
            text_div = profile_text.find('div', class_='text')
            if text_div:
                # Eliminar elementos que no queremos (h2, divs de publicidad, participantes)
                for elemento in text_div.find_all(['h2', 'div']):
                    elemento.decompose()
                
                # Eliminar el párrafo de "Ha participado en esta ficha"
                for p in text_div.find_all('p', class_='participate'):
                    p.decompose()
                
                # Obtener todo el texto restante
                sinopsis = text_div.get_text(separator=' ', strip=True)
                
                detalle['sinopsis'] = sinopsis.strip()
        
    except Exception as e:
        print(f"  Error extrayendo detalle de {url_libro}: {e}")
    
    return detalle


def extraer_todos_libros(fuente='todo', generos_quelibroleo=None):
    """Extrae libros de las fuentes especificadas
    
    Args:
        fuente: 'todo', 'lecturalia' o 'quelibroleo'
        generos_quelibroleo: Lista de géneros para QueLibroLeo (solo si fuente incluye quelibroleo)
    """
    libros = []
    
    if fuente in ['todo', 'quelibroleo']:
        print("Extrayendo de QueLibroLeo...")
        libros.extend(extraer_libros_quelibroleo(generos_quelibroleo))
    
    if fuente in ['todo', 'lecturalia']:
        print("Extrayendo de Lecturalia...")
        libros.extend(extraer_libros_lecturalia())
    
    print(f"Total libros extraídos: {len(libros)}")
    return libros


def mostrar_libros(libros):
    """Muestra los libros extraídos"""
    for libro in libros:
        print(f"\n{libro['titulo']} - {libro['autor']}")
        print(f"  Género: {libro['genero']}")
        print(f"  Valoración: {libro['valoracion']} ({libro['num_votos']} votos)")
        sinopsis = libro['sinopsis'][:100] if libro['sinopsis'] else '(sin sinopsis)'
        print(f"  Sinopsis: {sinopsis}...")


# Para probar el scraping directamente
if __name__ == '__main__':
    import sys
    
    # Uso: python scraping.py [fuente] [genero]
    # Ejemplos:
    #   python scraping.py                     -> Extrae todo
    #   python scraping.py lecturalia          -> Solo Lecturalia
    #   python scraping.py quelibroleo         -> QueLibroLeo (todos los géneros)
    #   python scraping.py quelibroleo humor   -> QueLibroLeo solo género 'humor'
    
    fuente = 'todo'
    generos = None
    
    if len(sys.argv) >= 2:
        fuente = sys.argv[1]
    
    if len(sys.argv) >= 3 and fuente == 'quelibroleo':
        generos = [sys.argv[2]]
    
    print(f"\n=== Scraping: {fuente} ===")
    if generos:
        print(f"    Géneros: {generos}")
    print()
    
    libros = extraer_todos_libros(fuente, generos)
    mostrar_libros(libros)
