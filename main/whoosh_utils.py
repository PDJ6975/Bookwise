# whoosh_utils.py
import os
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, NUMERIC, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Every
from .scraping import extraer_todos_libros, filtrar_duplicados

# Directorio del índice
INDEX_DIR = os.path.join(os.path.dirname(__file__), '..', 'Index')


def normalizar_valoracion(valoracion):
    """Normaliza valoración de escala 1-10 a escala 1-5 con incrementos de 0.5"""
    if valoracion is None or valoracion == 0:
        return 0.0

    # Convertir de escala 1-10 a escala 1-5
    valor_5 = valoracion / 2.0

    # Redondear al 0.5 más cercano
    return round(valor_5 * 2) / 2


def get_schema():
    """Define el schema del índice de libros"""
    return Schema(
        titulo=TEXT(stored=True),
        autor=TEXT(stored=True),
        genero=TEXT(stored=True),
        sinopsis=TEXT(stored=True),
        valoracion=NUMERIC(stored=True, numtype=float),
        num_votos=NUMERIC(stored=True, numtype=int),
        url=ID(stored=True, unique=True),
        portada=ID(stored=True),
        fuente=KEYWORD(stored=True)
    )


def crear_indice():
    """Crea el directorio y el índice vacío"""
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)
    
    schema = get_schema()
    ix = create_in(INDEX_DIR, schema)
    print(f"Índice creado en: {INDEX_DIR}")
    return ix


def abrir_indice():
    """Abre el índice existente"""
    if exists_in(INDEX_DIR):
        return open_dir(INDEX_DIR)
    else:
        return crear_indice()


def indexar_libros(libros):
    """Indexa una lista de libros en Whoosh
    
    Args:
        libros: Lista de diccionarios con los datos de los libros
    """
    ix = crear_indice()
    writer = ix.writer()
    
    for libro in libros:
        writer.add_document(
            titulo=libro['titulo'],
            autor=libro['autor'],
            genero=libro['genero'],
            sinopsis=libro['sinopsis'],
            valoracion=normalizar_valoracion(float(libro.get('valoracion', 0))),
            num_votos=int(libro.get('num_votos', 0)),
            url=libro['url'],
            portada=libro.get('portada', ''),
            fuente=libro['fuente']
        )
    
    writer.commit()
    print(f"Indexados {len(libros)} libros")
    return ix


def buscar(query_str, campo='titulo', limite=10):
    """Búsqueda simple en un campo
    
    Args:
        query_str: Texto a buscar
        campo: Campo donde buscar (titulo, autor, genero, sinopsis)
        limite: Número máximo de resultados
    """
    ix = abrir_indice()
    with ix.searcher() as searcher:
        parser = QueryParser(campo, ix.schema)
        query = parser.parse(query_str)
        results = searcher.search(query, limit=limite)
        
        libros = [dict(hit) for hit in results]
    
    return libros


def buscar_multicampo(query_str, campos=None, limite=10):
    """Búsqueda en múltiples campos
    
    Args:
        query_str: Texto a buscar
        campos: Lista de campos (por defecto: titulo, autor, sinopsis)
        limite: Número máximo de resultados
    """
    if campos is None:
        campos = ['titulo', 'autor', 'sinopsis']
    
    ix = abrir_indice()
    with ix.searcher() as searcher:
        parser = MultifieldParser(campos, ix.schema)
        query = parser.parse(query_str)
        results = searcher.search(query, limit=limite)
        
        libros = [dict(hit) for hit in results]
    
    return libros


def buscar_por_genero(genero, limite=50):
    """Busca libros de un género específico"""
    return buscar(genero, campo='genero', limite=limite)


def obtener_todos_libros():
    """Retorna todos los libros del índice"""
    ix = abrir_indice()
    with ix.searcher() as searcher:
        results = searcher.search(Every(), limit=None)
        libros = [dict(hit) for hit in results]
    
    return libros


def obtener_generos():
    """Retorna lista de géneros únicos"""
    libros = obtener_todos_libros()
    generos = set()
    for libro in libros:
        if libro.get('genero'):
            generos.add(libro['genero'])

    return sorted(list(generos))


def contar_libros():
    """Retorna el número de libros indexados"""
    ix = abrir_indice()
    with ix.searcher() as searcher:
        return searcher.doc_count()


def limpiar_indice():
    """Elimina todos los documentos del índice"""
    ix = abrir_indice()
    writer = ix.writer()
    writer.delete_by_query(Every())
    writer.commit()
    print("Índice limpiado")


# Para probar directamente
if __name__ == '__main__':
    
    print("=== Creando índice con datos de scraping ===\n")
    
    # Extraer y filtrar libros
    libros = extraer_todos_libros()
    libros = filtrar_duplicados(libros)
    
    # Indexar
    indexar_libros(libros)
    
    print(f"\n=== Índice creado con {contar_libros()} libros ===")
    
    # Pruebas de búsqueda
    print("\n--- Prueba: buscar 'amor' en título ---")
    resultados = buscar("amor", campo='titulo', limite=5)
    for r in resultados:
        print(f"  {r['titulo']} - {r['autor']}")
    
    print("\n--- Prueba: buscar por género 'Ensayo' ---")
    resultados = buscar_por_genero("Ensayo", limite=5)
    for r in resultados:
        print(f"  {r['titulo']} - {r['genero']}")
    
    print(f"\n--- Géneros disponibles ({len(obtener_generos())}) ---")
    for g in obtener_generos():
        print(f"  {g}")
