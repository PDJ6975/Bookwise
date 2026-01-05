from django.shortcuts import render
from main.whoosh_utils import obtener_generos


def index(request):
    """Vista principal - Descubrir"""
    generos = obtener_generos()
    return render(request, 'main/index.html', {'generos': generos})


def galeria(request):
    """Vista Galería"""
    return render(request, 'main/galeria.html')


def mi_libreria(request):
    """Vista Mi Librería"""
    return render(request, 'main/mi_libreria.html')


def login(request):
    """Vista Login"""
    return render(request, 'main/login.html')
