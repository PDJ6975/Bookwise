from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from main.whoosh_utils import (
    obtener_generos, buscar_por_genero, buscar_filtrado,
    buscar_populares, buscar_ordenado, buscar_booleana
)
from main.models import LibroUsuario


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
    if not request.user.is_authenticated:
        return render(request, 'main/mi_libreria.html', {
            'por_leer': [],
            'leidos': [],
            'no_autenticado': True
        })
    
    libros_usuario = LibroUsuario.objects.filter(usuario=request.user)
    por_leer = libros_usuario.filter(estado='por_leer')
    leidos = libros_usuario.filter(estado='leido')
    
    return render(request, 'main/mi_libreria.html', {
        'por_leer': por_leer,
        'leidos': leidos
    })


@login_required
def agregar_libro(request):
    """Agregar libro a la librería del usuario"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor', '')
        portada = request.POST.get('portada', '')
        genero = request.POST.get('genero', '')
        sinopsis = request.POST.get('sinopsis', '')
        
        # Verificar si ya existe
        if not LibroUsuario.objects.filter(usuario=request.user, titulo=titulo).exists():
            LibroUsuario.objects.create(
                usuario=request.user,
                titulo=titulo,
                autor=autor,
                portada=portada,
                genero=genero,
                sinopsis=sinopsis,
                estado='por_leer'
            )
        
        # Redirigir a donde venía o a mi librería
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/mi-libreria/'))
        return redirect(next_url)
    
    return redirect('mi_libreria')


@login_required
def marcar_leido(request, libro_id):
    """Marcar libro como leído y añadir valoración"""
    libro = get_object_or_404(LibroUsuario, id=libro_id, usuario=request.user)
    
    if request.method == 'POST':
        valoracion = request.POST.get('valoracion')
        libro.estado = 'leido'
        libro.fecha_leido = timezone.now()
        if valoracion:
            libro.valoracion = float(valoracion)
        libro.save()
    
    return redirect('mi_libreria')


@login_required
def eliminar_libro(request, libro_id):
    """Eliminar libro de la librería"""
    libro = get_object_or_404(LibroUsuario, id=libro_id, usuario=request.user)
    libro.delete()
    return redirect('mi_libreria')


def login_view(request):
    """Vista Login"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'main/login.html')


def registro_view(request):
    """Vista Registro"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
        elif len(password) < 4:
            messages.error(request, 'La contraseña debe tener al menos 4 caracteres')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            auth_login(request, user)
            messages.success(request, f'¡Cuenta creada! Bienvenido, {user.username}')
            return redirect('index')
    
    return render(request, 'main/registro.html')


def logout_view(request):
    """Vista Logout"""
    auth_logout(request)
    messages.info(request, 'Has cerrado sesión')
    return redirect('index')


def buscar_avanzado(request):
    """Vista de Búsqueda Avanzada con filtros complejos"""
    generos_disponibles = obtener_generos()
    resultados = []
    query_debug = ""
    tipo_busqueda = ""

    # Preservar parámetros de búsqueda para mantener estado del formulario
    texto_busqueda = request.GET.get('q', '').strip()
    modo_busqueda = request.GET.get('modo', 'filtrado')
    valoracion_min = request.GET.get('valoracion_min', '0')
    solo_populares = request.GET.get('solo_populares', '')
    fuente = request.GET.get('fuente', '')
    ordenar_por = request.GET.get('ordenar', 'relevancia')
    generos_seleccionados = request.GET.getlist('generos')

    if request.method == 'GET' and request.GET.get('buscar'):
        # Obtener parámetros del formulario
        texto_busqueda = request.GET.get('q', '').strip()
        modo_busqueda = request.GET.get('modo', 'filtrado')

        # Campos de búsqueda
        campos = []
        if request.GET.get('campo_titulo'):
            campos.append('titulo')
        if request.GET.get('campo_autor'):
            campos.append('autor')
        if request.GET.get('campo_sinopsis'):
            campos.append('sinopsis')

        # Filtros
        generos_seleccionados = request.GET.getlist('generos')
        valoracion_min = request.GET.get('valoracion_min')
        solo_populares = request.GET.get('solo_populares')
        fuente = request.GET.get('fuente', '')
        ordenar_por = request.GET.get('ordenar', 'relevancia')

        # Convertir valoración a float
        try:
            val_min = float(valoracion_min) if valoracion_min else None
        except ValueError:
            val_min = None

        # Votos mínimos si solo_populares está activado
        votos_min = 50 if solo_populares else None

        # Ejecutar búsqueda según el modo
        if modo_busqueda == 'filtrado':
            # BÚSQUEDA FILTRADA
            tipo_busqueda = "Búsqueda Filtrada Multicampo"
            resultados = buscar_filtrado(
                query_str=texto_busqueda,
                generos=generos_seleccionados if generos_seleccionados else None,
                valoracion_min=val_min,
                votos_min=votos_min,
                fuente=fuente if fuente else None,
                limite=50
            )

            # Construir query debug
            parts = []
            if texto_busqueda:
                parts.append(f"texto:'{texto_busqueda}'")
            if generos_seleccionados:
                parts.append(f"géneros:{generos_seleccionados}")
            if val_min:
                parts.append(f"valoración≥{val_min}")
            if votos_min:
                parts.append(f"votos≥{votos_min}")
            if fuente:
                parts.append(f"fuente:{fuente}")
            query_debug = " AND ".join(parts) if parts else "todos los libros"

        elif modo_busqueda == 'booleana':
            # BÚSQUEDA BOOLEANA
            tipo_busqueda = "Búsqueda Booleana (AND/OR/NOT)"
            resultados = buscar_booleana(texto_busqueda, limite=50)
            query_debug = texto_busqueda

        elif modo_busqueda == 'populares':
            # BÚSQUEDA DE POPULARES
            tipo_busqueda = "Libros Populares (ordenados por valoración)"
            resultados = buscar_populares(votos_min=votos_min or 50, limite=50)
            query_debug = f"libros con ≥{votos_min or 50} votos, ordenados por valoración"

        # Ordenar resultados si se especifica
        if ordenar_por != 'relevancia' and resultados and modo_busqueda == 'filtrado':
            if ordenar_por == 'valoracion':
                resultados = sorted(resultados, key=lambda x: x.get('valoracion', 0), reverse=True)
            elif ordenar_por == 'popularidad':
                resultados = sorted(resultados, key=lambda x: x.get('num_votos', 0), reverse=True)
            elif ordenar_por == 'titulo':
                resultados = sorted(resultados, key=lambda x: x.get('titulo', ''))

    return render(request, 'main/buscar_avanzado.html', {
        'generos': generos_disponibles,
        'resultados': resultados,
        'query_debug': query_debug,
        'tipo_busqueda': tipo_busqueda,
        'num_resultados': len(resultados),
        # Preservar estado del formulario
        'q': texto_busqueda,
        'modo': modo_busqueda,
        'valoracion_min': valoracion_min,
        'solo_populares': solo_populares,
        'fuente': fuente,
        'ordenar': ordenar_por,
        'generos_seleccionados': generos_seleccionados,
    })
