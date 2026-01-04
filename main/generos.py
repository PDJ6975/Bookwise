# generos.py
"""
Módulo de normalización de géneros literarios.
Centraliza el mapeo de géneros de distintas fuentes a géneros canónicos.
"""

# Géneros canónicos del sistema (16 géneros)
GENEROS_CANONICOS = [
    'Biografías y Memorias',
    'Ciencia Ficción y Fantasía',
    'Clásicos',
    'Cómic y Novela Gráfica',
    'Economía y Empresa',
    'Ensayo',
    'Ficción Literaria',
    'Histórica y Aventuras',
    'Humor',
    'Infantil y Juvenil',
    'Literatura Contemporánea',
    'Narrativa',
    'No Ficción',
    'Novela Negra y Terror',
    'Poesía y Teatro',
    'Romántica'
]

# Mapeo: slug de QueLibroLeo -> género canónico
MAPEO_QUELIBROLEO = {
    'biografias-memorias': 'Biografías y Memorias',
    'clasicos-de-la-literatura': 'Clásicos',
    'comics-novela-grafica': 'Cómic y Novela Gráfica',
    'economia-empresa-marketing': 'Economía y Empresa',
    'ensayo': 'Ensayo',
    'fantastica-ciencia-ficcion': 'Ciencia Ficción y Fantasía',
    'ficcion-literaria': 'Ficción Literaria',
    'historica-y-aventuras': 'Histórica y Aventuras',
    'humor': 'Humor',
    'infantil-y-juvenil': 'Infantil y Juvenil',
    'lecturas-complementarias': 'No Ficción',
    'literatura-contemporanea': 'Literatura Contemporánea',
    'narrativa': 'Narrativa',
    'no-ficcion': 'No Ficción',
    'novela-negra-intriga-terror': 'Novela Negra y Terror',
    'poesia-teatro': 'Poesía y Teatro',
    'romantica-erotica': 'Romántica',
}

# Mapeo: género de Lecturalia -> género canónico
MAPEO_LECTURALIA = {
    'acción y aventuras': 'Histórica y Aventuras',
    'autoayuda y superación': 'No Ficción',
    'ciencia ficción': 'Ciencia Ficción y Fantasía',
    'fantástica': 'Ciencia Ficción y Fantasía',
    'histórica': 'Histórica y Aventuras',
    'historia': 'Histórica y Aventuras',
    'infantil y juvenil': 'Infantil y Juvenil',
    'memorias y biografías': 'Biografías y Memorias',
    'misterio y suspense': 'Novela Negra y Terror',
    'narrativa': 'Narrativa',
    'terror': 'Novela Negra y Terror',
    'romántica': 'Romántica',
}


def normalizar_genero_quelibroleo(slug):
    """Normaliza un slug de género de QueLibroLeo"""
    return MAPEO_QUELIBROLEO.get(slug, slug.replace('-', ' ').title())


def normalizar_genero_lecturalia(genero):
    """Normaliza un género de Lecturalia"""
    if not genero:
        return 'Sin género'
    clave = genero.lower().strip()
    return MAPEO_LECTURALIA.get(clave, genero.strip().title())
