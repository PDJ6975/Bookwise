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
    """Vista Galería"""
    return render(request, 'main/galeria.html')


def mi_libreria(request):
    """Vista Mi Librería"""
    return render(request, 'main/mi_libreria.html')


def login(request):
    """Vista Login"""
    return render(request, 'main/login.html')
