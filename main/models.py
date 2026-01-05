from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class LibroUsuario(models.Model):
    """
    Libro guardado en la librería de un usuario.
    """
    ESTADO_CHOICES = [
        ('por_leer', 'Por leer'),
        ('leido', 'Leído'),
    ]
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='libros_guardados',
        verbose_name='Usuario'
    )
    titulo = models.CharField(max_length=500, verbose_name='Título')
    autor = models.CharField(max_length=300, verbose_name='Autor', blank=True)
    portada = models.URLField(max_length=1000, verbose_name='Portada', blank=True)
    genero = models.CharField(max_length=100, verbose_name='Género', blank=True)
    sinopsis = models.TextField(verbose_name='Sinopsis', blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='por_leer',
        verbose_name='Estado'
    )
    valoracion = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        null=True,
        blank=True,
        verbose_name='Mi valoración'
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_leido = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Libro de usuario'
        verbose_name_plural = 'Libros de usuarios'
        unique_together = ('usuario', 'titulo')
        ordering = ['-fecha_agregado']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo} ({self.get_estado_display()})"


class Valoracion(models.Model):
    """
    Valoración de un usuario sobre un libro.
    El libro se identifica por su título (almacenado en Whoosh).
    """
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='valoraciones',
        verbose_name='Usuario'
    )
    titulo_libro = models.CharField(
        max_length=500,
        verbose_name='Título del libro'
    )
    puntuacion = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)],
        verbose_name='Puntuación',
        help_text='Valoración de 1.0 a 10.0 estrellas'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de valoración'
    )
    actualizado = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'Valoración'
        verbose_name_plural = 'Valoraciones'
        unique_together = ('usuario', 'titulo_libro')
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['titulo_libro']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo_libro}: {self.puntuacion}"
