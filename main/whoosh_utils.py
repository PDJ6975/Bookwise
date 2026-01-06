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
    """Indexa una lista de libros en Whoosh"""
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
    """Búsqueda simple en un campo"""
    ix = abrir_indice()
    with ix.searcher() as searcher:
        parser = QueryParser(campo, ix.schema)
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

# BÚSQUEDAS AVANZADAS

def buscar_filtrado(query_str="", campos=None, generos=None, valoracion_min=None,
                    valoracion_max=None, votos_min=None, fuente=None, limite=20):
    """
    Búsqueda con múltiples filtros combinados (AND).

    Args:
        query_str: Texto a buscar (opcional)
        campos: Lista de campos donde buscar (por defecto: ['titulo', 'autor', 'sinopsis'])
        generos: Lista de géneros (búsqueda OR entre ellos)
        valoracion_min: Valoración mínima
        valoracion_max: Valoración máxima
        votos_min: Número mínimo de votos
        fuente: Fuente específica ('quelibroleo' o 'lecturalia')
        limite: Número máximo de resultados
    """
    from whoosh.query import And, Or, Term, NumericRange

    # Campos por defecto si no se especifican
    if campos is None:
        campos = ['titulo', 'autor', 'sinopsis']

    ix = abrir_indice()
    with ix.searcher() as searcher:
        filtros = []

        # Búsqueda de texto general en los campos especificados
        if query_str:
            parser = MultifieldParser(campos, ix.schema)
            text_query = parser.parse(query_str)
            filtros.append(text_query)

        # Filtro por géneros (OR entre ellos)
        if generos and len(generos) > 0:
            genero_queries = [Term("genero", g) for g in generos]
            filtros.append(Or(genero_queries))

        # Filtro por valoración
        if valoracion_min is not None or valoracion_max is not None:
            min_val = valoracion_min if valoracion_min is not None else 0.0
            max_val = valoracion_max if valoracion_max is not None else 5.0
            filtros.append(NumericRange("valoracion", min_val, max_val))

        # Filtro por votos mínimos
        if votos_min is not None:
            filtros.append(NumericRange("num_votos", votos_min, None))

        # Filtro por fuente
        if fuente:
            filtros.append(Term("fuente", fuente))

        # Combinar todos los filtros con AND
        if filtros:
            query_final = And(filtros)
        else:
            query_final = Every()

        results = searcher.search(query_final, limit=limite)
        libros = [dict(hit) for hit in results]

    return libros


def buscar_por_rango_valoracion(min_val, max_val, limite=20):
    """
    Búsqueda por rango de valoración.

    Args:
        min_val: Valoración mínima (1.0-5.0)
        max_val: Valoración máxima (1.0-5.0)
        limite: Número máximo de resultados
    """
    from whoosh.query import NumericRange

    ix = abrir_indice()
    with ix.searcher() as searcher:
        query = NumericRange("valoracion", min_val, max_val)
        results = searcher.search(query, limit=limite)
        libros = [dict(hit) for hit in results]

    return libros


def buscar_populares(votos_min=50, limite=20):
    """
    Búsqueda de libros populares (con muchos votos), ordenados por valoración.

    Args:
        votos_min: Número mínimo de votos
        limite: Número máximo de resultados
    """
    from whoosh.query import NumericRange
    from whoosh import sorting

    ix = abrir_indice()
    with ix.searcher() as searcher:
        query = NumericRange("num_votos", votos_min, None)

        # Ordenar por valoración descendente
        facet = sorting.FieldFacet("valoracion", reverse=True)
        results = searcher.search(query, limit=limite, sortedby=facet)

        libros = [dict(hit) for hit in results]

    return libros


def buscar_ordenado(query_str, campo_orden="valoracion", descendente=True, limite=20):
    """
    Búsqueda con ordenación personalizada.

    Args:
        query_str: Texto a buscar
        campo_orden: Campo por el que ordenar (valoracion, num_votos, titulo, autor)
        descendente: True para orden descendente, False para ascendente
        limite: Número máximo de resultados
    """
    from whoosh import sorting

    ix = abrir_indice()
    with ix.searcher() as searcher:
        parser = MultifieldParser(['titulo', 'autor', 'sinopsis'], ix.schema)
        query = parser.parse(query_str)

        # Configurar ordenación
        facet = sorting.FieldFacet(campo_orden, reverse=descendente)
        results = searcher.search(query, limit=limite, sortedby=facet)

        libros = [dict(hit) for hit in results]

    return libros


def buscar_booleana(query_str, limite=20):
    """
    Búsqueda booleana avanzada con operadores AND, OR, NOT.

    Args:
        query_str: Query con sintaxis booleana.
                  Ej: "autor:García AND genero:Ficción"
                  Ej: "titulo:amor OR titulo:guerra"
                  Ej: "genero:Ficción NOT genero:Infantil"
        limite: Número máximo de resultados
    """
    ix = abrir_indice()
    with ix.searcher() as searcher:
        parser = MultifieldParser(['titulo', 'autor', 'genero', 'sinopsis'], ix.schema)
        query = parser.parse(query_str)
        results = searcher.search(query, limit=limite)

        libros = [dict(hit) for hit in results]

    return libros


def buscar_por_multiples_generos(generos_list, limite=20):
    """
    Búsqueda por múltiples géneros (OR).

    Args:
        generos_list: Lista de géneros
        limite: Número máximo de resultados
    """
    from whoosh.query import Or, Term

    ix = abrir_indice()
    with ix.searcher() as searcher:
        # Crear query OR con todos los géneros
        genero_queries = [Term("genero", g) for g in generos_list]
        query = Or(genero_queries)

        results = searcher.search(query, limit=limite)
        libros = [dict(hit) for hit in results]

    return libros


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
