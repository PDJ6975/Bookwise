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


def extraer_todos_libros():
    """Extrae libros de todas las fuentes"""
    libros = []
    
    print("Extrayendo de Lecturalia...")
    libros.extend(extraer_libros_lecturalia())
    
    # TODO: Añadir aquí la extracción de Quelibroleo cuando esté lista
    
    print(f"Total libros extraídos: {len(libros)}")
    return libros


# Para probar el scraping directamente
if __name__ == '__main__':
    libros = extraer_todos_libros()
    for libro in libros[:10]: 
        print(f"\n{libro['titulo']} - {libro['autor']}")
        print(f"  Género: {libro['genero']}")
        print(f"  Valoración: {libro['valoracion']} ({libro['num_votos']} votos)")
        print(f"  Sinopsis: {libro['sinopsis'][:100]}...")
