from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.index, name='index'),
    path('galeria/', views.galeria, name='galeria'),
    path('mi-libreria/', views.mi_libreria, name='mi_libreria'),
    path('mi-libreria/agregar/', views.agregar_libro, name='agregar_libro'),
    path('mi-libreria/marcar-leido/<int:libro_id>/', views.marcar_leido, name='marcar_leido'),
    path('mi-libreria/eliminar/<int:libro_id>/', views.eliminar_libro, name='eliminar_libro'),
    path('buscar-avanzado/', views.buscar_avanzado, name='buscar_avanzado'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    # Administración
    path('administracion/scraping/', views.realizar_scraping, name='realizar_scraping'),
]
