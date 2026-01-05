from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from main.whoosh_utils import obtener_generos, buscar_por_genero
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
