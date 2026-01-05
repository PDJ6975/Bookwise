from django.shortcuts import render
from main.whoosh_utils import obtener_generos, buscar_por_genero


def index(request):
    """Vista principal - Descubrir"""
    generos = obtener_generos()

    # Obtener un libro representativo para cada género
    categorias = []
    for genero in generos:
        libros = buscar_por_genero(genero, limite=1)
        if libros:
            categorias.append({
                'nombre': genero,
                'libro': libros[0]
            })

    return render(request, 'main/index.html', {'categorias': categorias})


def galeria(request):
    """Vista Galería - Catálogo de libros por categoría"""
    generos = obtener_generos()
    genero_filtrado = request.GET.get('genero', None)
    
    # Si hay un género específico, mostrar solo ese
    if genero_filtrado:
        libros = buscar_por_genero(genero_filtrado, limite=50)
        libros_por_genero = {genero_filtrado: libros} if libros else {}
    else:
        # Mostrar todos los géneros
        libros_por_genero = {}
        for genero in generos:
            libros = buscar_por_genero(genero, limite=50)
            if libros:
                libros_por_genero[genero] = libros
    
    return render(request, 'main/galeria.html', {
        'libros_por_genero': libros_por_genero,
        'generos': generos,
        'genero_filtrado': genero_filtrado
    })


def mi_libreria(request):
    """Vista Mi Librería"""
    return render(request, 'main/mi_libreria.html')


def login(request):
    """Vista Login"""
    return render(request, 'main/login.html')
