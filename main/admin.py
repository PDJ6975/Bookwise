from django.contrib import admin
from .models import Valoracion


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo_libro', 'puntuacion', 'fecha')
    list_filter = ('puntuacion', 'fecha', 'usuario')
    search_fields = ('titulo_libro', 'usuario__username')
    readonly_fields = ('fecha', 'actualizado')
    ordering = ('-fecha',)
    
    fieldsets = (
        ('Información del libro', {
            'fields': ('titulo_libro',)
        }),
        ('Valoración', {
            'fields': ('usuario', 'puntuacion')
        }),
        ('Fechas', {
            'fields': ('fecha', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
