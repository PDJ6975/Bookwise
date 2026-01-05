from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('galeria/', views.galeria, name='galeria'),
    path('mi-libreria/', views.mi_libreria, name='mi_libreria'),
    path('login/', views.login, name='login'),
]
