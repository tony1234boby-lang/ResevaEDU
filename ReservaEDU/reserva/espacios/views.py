from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
from django.utils import timezone
import json

from .forms import CustomUserCreationForm
from .models import Espacio, Reserva, HistorialReserva, Notificacion

# Helper para verificar si un usuario es del grupo Secretaría o Superusuario
def es_secretaria(user):
    return user.is_authenticated and (user.groups.filter(name='Secretaría').exists() or user.is_superuser)

# Decorador personalizado para requerir el rol de Secretaría
def secretaria_required(view_func):
    def wrapper(request, *args, **kwargs):
        if es_secretaria(request.user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("No tienes permisos de Secretaría para realizar esta acción.")
    return wrapper

# Helper para enviar notificaciones en base de datos y simular logs de correo
def notificar_reserva(reserva, accion, comentario=None):
    recipientes = set()
    
    # El solicitante siempre es notificado
    recipientes.add(reserva.usuario)
    
    # El administrador es notificado
    for admin in User.objects.filter(is_superuser=True):
        recipientes.add(admin)
        
    # El responsable del espacio es notificado
    if reserva.espacio.responsable:
        recipientes.add(reserva.espacio.responsable)
        
    # Construir mensaje según la acción
    if accion == 'creacion':
        mensaje = f"Nueva reserva solicitada para '{reserva.espacio.nombre}' el {reserva.fecha} ({reserva.hora_inicio} - {reserva.hora_fin}) por {reserva.usuario.username}."
    elif accion == 'aprobacion':
        mensaje = f"Tu reserva para '{reserva.espacio.nombre}' el {reserva.fecha} ha sido APROBADA."
        if comentario:
            mensaje += f" Observaciones: {comentario}"
    elif accion == 'rechazo':
        mensaje = f"Tu reserva para '{reserva.espacio.nombre}' el {reserva.fecha} ha sido RECHAZADA."
        if comentario:
            mensaje += f" Motivo: {comentario}"
    elif accion == 'cancelacion':
        mensaje = f"La reserva para '{reserva.espacio.nombre}' el {reserva.fecha} ha sido CANCELADA por el usuario."
    else:
        mensaje = f"Actualización en reserva '{reserva.espacio.nombre}': {accion}"

    for usuario in recipientes:
        if usuario:
            Notificacion.objects.create(usuario=usuario, reserva=reserva, mensaje=mensaje)
            # Simulación de correo electrónico
            email_address = usuario.email or f"{usuario.username}@reservaedu.edu"
            print(f"[SIMULACIÓN EMAIL] De: noreply@reservaedu.edu | Para: {email_address} | Asunto: Actualización de Reserva - ReservaEDU | Mensaje: {mensaje}")

def lista_espacios(request):
    espacios = Espacio.objects.all()
    sim_username = request.GET.get('user')
    user_simulated = True if sim_username else False
    
    # Si simulamos un usuario, buscaremos el objeto User correspondiente
    sim_user_obj = None
    if user_simulated:
        sim_user_obj, _ = User.objects.get_or_create(username=sim_username)
        # Forzar rol secretaría si el sim_username es 'secretaria'
        if sim_username == 'secretaria':
            grupo, _ = Group.objects.get_or_create(name='Secretaría')
            if not sim_user_obj.groups.filter(name='Secretaría').exists():
                sim_user_obj.groups.add(grupo)

    # Cargar notificaciones para el header
    notificaciones = []
    notificaciones_count = 0
    user_actual = sim_user_obj if user_simulated else request.user
    
    if user_actual and user_actual.is_authenticated:
        notificaciones = Notificacion.objects.filter(usuario=user_actual, leida=False).order_by('-fecha')[:5]
        notificaciones_count = Notificacion.objects.filter(usuario=user_actual, leida=False).count()

    is_sec = es_secretaria(user_actual) if user_actual else False

    return render(request, 'index.html', {
        'espacios': espacios,
        'user_simulated': user_simulated,
        'sim_username': sim_username,
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': is_sec,
    })

@login_required
def reservar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)
    error_msg = None
    
    if request.method == 'POST':
        fecha = request.POST.get('date')
        hora_inicio = request.POST.get('start_time')
        hora_fin = request.POST.get('end_time')
        
        reserva = Reserva(
            usuario=request.user,
            espacio=espacio,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado='pendiente'
        )
        
        try:
            reserva.full_clean()
            reserva.save()
            
            # Registrar historial
            HistorialReserva.objects.create(
                reserva=reserva,
                usuario=request.user,
                accion='creacion',
                comentario=f"Reserva creada por {request.user.username} (Pendiente de aprobación)"
            )
            
            # Notificaciones
            notificar_reserva(reserva, 'creacion')
            
            return redirect('mis_reservas')
        except ValidationError as e:
            error_msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            
    # Cargar notificaciones del header
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    return render(request, 'formulario.html', {
        'espacio': espacio,
        'error_msg': error_msg,
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_secretaria(request.user)
    })

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Cargar notificaciones del header
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    return render(request, 'mis_reservas.html', {
        'mis_reservas': reservas,
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_secretaria(request.user)
    })

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    # Notificar antes de borrar o marcar
    notificar_reserva(reserva, 'cancelacion')
    
    # Registrar en historial si quisiéramos conservar el registro.
    # Como la reserva se va a eliminar o cambiar de estado, hagamos un delete simple o marquemos como rechazada/cancelada.
    # Dado que el requerimiento 10 dice "no permitir conflictos de horarios", borrar es lo más limpio para liberar el slot.
    reserva.delete()
    
    return redirect('mis_reservas')

@login_required
@secretaria_required
def dashboard_secretaria(request):
    reservas_pendientes = Reserva.objects.filter(estado='pendiente').order_by('fecha', 'hora_inicio')
    reservas_aprobadas = Reserva.objects.filter(estado='aprobada').order_by('-fecha_decision')
    reservas_rechazadas = Reserva.objects.filter(estado='rechazada').order_by('-fecha_decision')
    
    # Cargar notificaciones del header
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    return render(request, 'dashboard.html', {
        'pendientes': reservas_pendientes,
        'aprobadas': reservas_aprobadas,
        'rechazadas': reservas_rechazadas,
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': True
    })

@login_required
@secretaria_required
def aprobar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        reserva.estado = 'aprobada'
        reserva.observaciones = observaciones
        reserva.fecha_decision = timezone.now()
        reserva.decidido_por = request.user
        reserva.save()
        
        # Registrar en Historial
        HistorialReserva.objects.create(
            reserva=reserva,
            usuario=request.user,
            accion='aprobacion',
            comentario=f"Aprobada con observaciones: {observaciones}" if observaciones else "Aprobada sin observaciones"
        )
        
        # Notificar
        notificar_reserva(reserva, 'aprobacion', observaciones)
        
    return redirect('dashboard_secretaria')

@login_required
@secretaria_required
def rechazar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        motivo = request.POST.get('observaciones', '')
        reserva.estado = 'rechazada'
        reserva.observaciones = motivo
        reserva.fecha_decision = timezone.now()
        reserva.decidido_por = request.user
        reserva.save()
        
        # Registrar en Historial
        HistorialReserva.objects.create(
            reserva=reserva,
            usuario=request.user,
            accion='rechazo',
            comentario=f"Rechazada por motivo: {motivo}" if motivo else "Rechazada sin detalles"
        )
        
        # Notificar
        notificar_reserva(reserva, 'rechazo', motivo)
        
    return redirect('dashboard_secretaria')

@login_required
def lista_notificaciones(request):
    notifs = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Cargar notificaciones del header
    notificaciones_cinco = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    return render(request, 'notificaciones.html', {
        'todas_notificaciones': notifs,
        'notificaciones': notificaciones_cinco,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_secretaria(request.user)
    })

@login_required
def leer_notificacion(request, notificacion_id):
    notif = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notif.leida = True
    notif.save()
    return JsonResponse({'status': 'success'})

def inteligencia_universal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '')
        resultado = investigar_internet(query)
        return JsonResponse({
            'respuesta': resultado[0],
            'fuentes': resultado[1],
            'sugerencias': resultado[2],
            'extra_table': resultado[3] if len(resultado) > 3 else None
        })
    return JsonResponse({'error': 'Metodo no permitido'}, status=405)

def social_auth_mock(request):
    provider = request.GET.get('provider', 'Google')
    return render(request, 'social_mock.html', {'provider': provider})

def social_login_callback(request):
    username_raw = request.GET.get('user')
    email = request.GET.get('email', '')
    if username_raw:
        username = username_raw.lower().replace(' ', '_')[:30]
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.email = email
            parts = username_raw.split(' ')
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = ' '.join(parts[1:])
            user.save()
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('inicio')
    return redirect('login')

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('inicio')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})

def google_settings(request):
    from django.conf import settings
    return {
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', '')
    }