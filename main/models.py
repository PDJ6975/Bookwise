from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Puntuación',
        help_text='Valoración de 1 a 5 estrellas'
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
