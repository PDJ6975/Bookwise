from django.shortcuts import render
from main.whoosh_utils import obtener_todos_libros


def index(request):
    """Vista principal que muestra todos los libros"""
    libros = obtener_todos_libros()
    return render(request, 'main/index.html', {'libros': libros})
