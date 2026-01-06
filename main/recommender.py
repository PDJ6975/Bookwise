# recommender.py
"""
Sistema de Recomendación Basado en Contenido.

Flujo del usuario:
1. Añade libro a "Por Leer" (Mi Librería)
2. Lo mueve a "Leídos" y le da 1-5 estrellas
3. El sistema construye su perfil basado en libros con >=4 estrellas

Algoritmo:
1. Construir perfil del usuario (géneros y autores preferidos)
2. Calcular similitud con Coeficiente de Dice
3. Combinar: 60% similitud género + 20% autor favorito + 20% popularidad
4. Si no hay perfil -> mostrar los más populares
"""

if __name__ == '__main__':
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookwise.settings')
    django.setup()

from collections import Counter
from main.models import LibroUsuario
from main.whoosh_utils import obtener_todos_libros
import math


# ============================================================================
# COEFICIENTE DE DICE
# ============================================================================

def coeficiente_dice(conjunto_a, conjunto_b):
    """
    Calcula el Coeficiente de Dice entre dos conjuntos.
    """
    if not conjunto_a or not conjunto_b:
        return 0.0
    
    interseccion = len(conjunto_a & conjunto_b)
    
    if interseccion == 0:
        return 0.0
    
    return (2.0 * interseccion) / (len(conjunto_a) + len(conjunto_b))


# ============================================================================
# CONSTRUCCIÓN DEL PERFIL DE USUARIO
# ============================================================================

def construir_perfil_usuario(usuario_id):
    """
    Construye el perfil del usuario basado en sus libros leídos.
    
    Solo considera libros con valoración >= 4 estrellas (le gustaron).
    
    Ponderación:
        - 5 estrellas -> peso 2 (le encantó)
        - 4 estrellas -> peso 1 (le gustó)
        - < 4 estrellas -> no se considera
    
    Returns:
        dict: {
            'generos': set de géneros preferidos (top 5),
            'autores': set de autores favoritos (top 3),
            'titulos_leidos': set de títulos ya leídos (para excluir)
        }
    """
    # Obtener libros leídos con valoración positiva (>= 4)
    libros_leidos = LibroUsuario.objects.filter(
        usuario_id=usuario_id,
        estado='leido',
        valoracion__gte=4
    )
    
    generos_ponderados = Counter()
    autores_ponderados = Counter()
    titulos_leidos = set()
    
    for libro in libros_leidos:
        # Calcular peso según valoración
        if libro.valoracion >= 5:
            peso = 2  
        else:
            peso = 1  
        
        # Agregar género al perfil
        if libro.genero:
            generos_ponderados[libro.genero.strip()] += peso
        
        # Agregar autor al perfil
        if libro.autor:
            autores_ponderados[libro.autor.strip()] += peso
        
        # Guardar título para excluir después
        titulos_leidos.add(libro.titulo.lower().strip())
    
    # También excluir libros en "Por Leer"
    libros_por_leer = LibroUsuario.objects.filter(
        usuario_id=usuario_id,
        estado='por_leer'
    )
    for libro in libros_por_leer:
        titulos_leidos.add(libro.titulo.lower().strip())
    
    # Top 5 géneros preferidos
    top_generos = set(g for g, _ in generos_ponderados.most_common(5))
    
    # Top 3 autores favoritos
    top_autores = set(a for a, _ in autores_ponderados.most_common(3))
    
    return {
        'generos': top_generos,
        'autores': top_autores,
        'titulos_leidos': titulos_leidos,
        'num_libros_perfil': len(libros_leidos)
    }


# ============================================================================
# CÁLCULO DE SCORE
# ============================================================================

def calcular_score(libro, perfil):
    """
    Calcula el score de recomendación para un libro.
    
    Componentes:
        - 60% Similitud de géneros (Coeficiente de Dice)
        - 20% Bonus si es autor favorito
        - 20% Popularidad del libro (valoración + votos)
    
    Args:
        libro: dict con datos del libro 
        perfil: dict con perfil del usuario
    
    Returns:
        float: Score de 0 a 100
    """
    # 1. SIMILITUD DE GÉNEROS (60%)
    generos_libro = set()
    if libro.get('genero'):
        generos_libro = {libro['genero'].strip()}
    
    similitud = coeficiente_dice(perfil['generos'], generos_libro)
    score_genero = similitud * 0.60
    
    # 2. BONUS POR AUTOR FAVORITO (20%)
    score_autor = 0.0
    autor_libro = libro.get('autor', '').strip()
    if autor_libro and autor_libro in perfil['autores']:
        score_autor = 0.20
    
    # 3. POPULARIDAD DEL LIBRO (20%)
    # Combinamos valoración (escala 0-5) y número de votos
    valoracion = libro.get('valoracion', 0) or 0
    num_votos = libro.get('num_votos', 0) or 0
    
    # Normalizar valoración a 0-1
    valoracion_norm = min(valoracion / 5.0, 1.0)
    
    # Normalizar votos
    votos_norm = min(math.log10(num_votos + 1) / 3.0, 1.0) if num_votos > 0 else 0
    
    # Combinar valoración (70%) y votos (30%) para la popularidad
    popularidad = (valoracion_norm * 0.7) + (votos_norm * 0.3)
    score_popularidad = popularidad * 0.20
    
    # SCORE FINAL (0 a 1, luego escalamos a 0-100)
    score_total = score_genero + score_autor + score_popularidad
    
    return score_total * 100


def obtener_motivo(libro, perfil):
    """
    Genera el motivo de la recomendación para mostrar al usuario.
    """
    generos_libro = set()
    if libro.get('genero'):
        generos_libro = {libro['genero'].strip()}
    
    # ¿Es autor favorito?
    autor_libro = libro.get('autor', '').strip()
    if autor_libro and autor_libro in perfil['autores']:
        return f"Te gusta {autor_libro}"
    
    # ¿Coincide algún género?
    generos_comunes = perfil['generos'] & generos_libro
    if generos_comunes:
        return f"Te gusta: {', '.join(list(generos_comunes)[:2])}"
    
    return "Popular"


# ============================================================================
# FUNCIÓN PRINCIPAL DE RECOMENDACIÓN
# ============================================================================

def recomendar_libros(usuario_id, n=4):
    """
    Genera recomendaciones personalizadas para un usuario.
    
    Algoritmo:
        1. Construir perfil del usuario
        2. Si no hay perfil -> devolver los más populares
        3. Calcular score para cada libro candidato
        4. Excluir libros ya en la librería del usuario
        5. Ordenar y devolver top N
    
    Args:
        usuario_id: ID del usuario
        n: Número de recomendaciones (default: 4)
    
    Returns:
        list: Lista de dicts con libro + score + motivo
    """
    # Construir perfil del usuario
    perfil = construir_perfil_usuario(usuario_id)
    
    # Obtener todos los libros del índice Whoosh
    todos_libros = obtener_todos_libros()
    
    # CASO: Usuario sin perfil -> devolver los más populares
    if not perfil['generos']:
        # Calcular score de popularidad combinando valoración + votos
        # Prioriza libros bien valorados con muchos votos
        import math
        
        def score_popularidad(libro):
            valoracion = libro.get('valoracion', 0) or 0
            num_votos = libro.get('num_votos', 0) or 0
            # Multiplicamos valoración por log de votos para balancear
            return valoracion * math.log10(num_votos + 1)
        
        libros_ordenados = sorted(
            todos_libros,
            key=score_popularidad,
            reverse=True
        )
        
        # Excluir libros ya en la librería
        recomendaciones = []
        for libro in libros_ordenados:
            titulo_lower = libro.get('titulo', '').lower().strip()
            if titulo_lower not in perfil['titulos_leidos']:
                libro_rec = dict(libro)
                # Score basado en popularidad real
                libro_rec['score'] = round(score_popularidad(libro) * 10, 1)
                libro_rec['motivo'] = 'Popular'
                recomendaciones.append(libro_rec)
                
                if len(recomendaciones) >= n:
                    break
        
        return recomendaciones
    
    # CASO: Usuario con perfil -> calcular scores personalizados
    candidatos = []
    
    for libro in todos_libros:
        titulo_lower = libro.get('titulo', '').lower().strip()
        
        # Excluir libros ya en la librería del usuario
        if titulo_lower in perfil['titulos_leidos']:
            continue
        
        # Calcular score
        score = calcular_score(libro, perfil)
        
        # Solo incluir si tiene alguna relevancia
        if score > 0:
            libro_rec = dict(libro)
            libro_rec['score'] = round(score, 1)
            libro_rec['motivo'] = obtener_motivo(libro, perfil)
            candidatos.append(libro_rec)
    
    # Ordenar por score descendente
    candidatos.sort(key=lambda x: x['score'], reverse=True)
    
    return candidatos[:n]


# ============================================================================
# FUNCIONES AUXILIARES PARA LAS VISTAS
# ============================================================================

def obtener_recomendaciones_para_vista(usuario_id, n=4):
    """
    Wrapper para usar en las vistas de Django.
    """
    return recomendar_libros(usuario_id, n=n)


def diagnosticar_perfil(usuario_id):
    """
    Genera información del perfil para mostrar al usuario.
    """
    perfil = construir_perfil_usuario(usuario_id)
    
    tiene_perfil = len(perfil['generos']) > 0
    
    if tiene_perfil:
        mensaje = f"Basado en {perfil['num_libros_perfil']} libros que te gustaron. Géneros: {', '.join(perfil['generos'])}"
    else:
        mensaje = "Valora algunos libros para personalizar las recomendaciones."
    
    return {
        'tiene_perfil': tiene_perfil,
        'generos_preferidos': list(perfil['generos']),
        'autores_favoritos': list(perfil['autores']),
        'num_libros': perfil['num_libros_perfil'],
        'mensaje': mensaje
    }


# ============================================================================
# PRUEBAS
# ============================================================================

if __name__ == '__main__':
    print("=== Test Coeficiente de Dice ===\n")
    
    # Caso 1: Idénticos
    a = {'Narrativa', 'Drama'}
    b = {'Narrativa', 'Drama'}
    print(f"Dice({a}, {b}) = {coeficiente_dice(a, b):.2f}  # Esperado: 1.0")
    
    # Caso 2: Parcial
    a = {'Narrativa', 'Drama'}
    b = {'Narrativa', 'Romance'}
    print(f"Dice({a}, {b}) = {coeficiente_dice(a, b):.2f}  # Esperado: 0.5")
    
    # Caso 3: Sin overlap
    a = {'Narrativa'}
    b = {'Terror'}
    print(f"Dice({a}, {b}) = {coeficiente_dice(a, b):.2f}  # Esperado: 0.0")
    
    # Caso 4: Vacío
    a = set()
    b = {'Terror'}
    print(f"Dice({a}, {b}) = {coeficiente_dice(a, b):.2f}  # Esperado: 0.0")
    
    # Test con usuario real
    print("\n=== Test Recomendaciones ===\n")
    recs = recomendar_libros(usuario_id=9999, n=3)
    for i, rec in enumerate(recs):
        print(f"{i+1}. {rec['titulo'][:40]} | Score: {rec['score']} | {rec['motivo']}")
