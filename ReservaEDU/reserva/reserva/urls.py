from django.contrib import admin
from django.urls import path, include
from espacios import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', views.lista_espacios, name='inicio'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('registro/', views.registro, name='registro'),
    path('social-mock/', views.social_auth_mock, name='social_mock'),
    path('social-login-callback/', views.social_login_callback, name='social_login_callback'),
    path('investigar-ia/', views.inteligencia_universal, name='investigar_ia'),
    
    # Reservas
    path('reservar/<int:espacio_id>/', views.reservar_espacio, name='reservar_espacio'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    
    # Secretaría
    path('secretaria/dashboard/', views.dashboard_secretaria, name='dashboard_secretaria'),
    path('secretaria/aprobar/<int:reserva_id>/', views.aprobar_reserva, name='aprobar_reserva'),
    path('secretaria/rechazar/<int:reserva_id>/', views.rechazar_reserva, name='rechazar_reserva'),
    
    # Notificaciones
    path('notificaciones/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/leer/<int:notificacion_id>/', views.leer_notificacion, name='leer_notificacion'),

    # API Horario automático
    path('api/reservas-horario/', views.api_reservas_horario, name='api_reservas_horario'),
    path('proximas-reservas/', views.proximas_reservas, name='proximas_reservas'),
    path('ayuda/', views.ayuda, name='ayuda'),
    
    # PWA Puntos de entrada
    path('serviceworker.js', TemplateView.as_view(template_name='serviceworker.js', content_type='application/javascript'), name='serviceworker.js'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
]