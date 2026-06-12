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
from .ai_utils import investigar_internet



def get_google_picture(user):
    """Obtiene la URL de la foto de perfil de Google del usuario."""
    if not user or not user.is_authenticated:
        return ''
    try:
        from allauth.socialaccount.models import SocialAccount
        social = SocialAccount.objects.filter(user=user, provider='google').first()
        if social:
            return social.extra_data.get('picture', '')
    except Exception:
        pass
    return ''

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
def notificar_reserva(reserva, accion, comentario=None, notificar_todos=False, notificar_personas=None):
    recipientes = set()
    
    # El solicitante siempre es notificado
    recipientes.add(reserva.usuario)
    
    # El administrador es notificado
    for admin in User.objects.filter(is_superuser=True):
        recipientes.add(admin)
        
    # El responsable del espacio es notificado
    if reserva.espacio.responsable:
        recipientes.add(reserva.espacio.responsable)

    if notificar_todos:
        for u in User.objects.all():
            recipientes.add(u)

    mapping = {
        'Padre Rector': ('padre_rector', 'Padre Rector', ''),
        'Lic. Jorge Sarmiento': ('jorge_sarmiento', 'Jorge', 'Sarmiento'),
        'Lic. Patricio Espinoza': ('patricio_espinoza', 'Patricio', 'Espinoza'),
        'Secretaría': ('secretaria', 'Secretaría', ''),
        'Otros Licenciados': ('otros_licenciados', 'Otros Licenciados', ''),
    }

    if notificar_personas:
        for p in notificar_personas:
            if p in mapping:
                username, first_name, last_name = mapping[p]
                user_obj, _ = User.objects.get_or_create(
                    username=username,
                    defaults={'first_name': first_name, 'last_name': last_name, 'email': f"{username}@reservaedu.edu"}
                )
                recipientes.add(user_obj)
        
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
    # Redirigir al login si el usuario no está autenticado
    if not request.user.is_authenticated:
        return redirect('login')

    if not Espacio.objects.exists():
        from django.contrib.auth.models import User
        responsable_user = User.objects.filter(is_superuser=True).first()
        if not responsable_user:
            responsable_user = User.objects.create_superuser('admin', 'admin@reservaedu.edu', 'admin123')
            
        espacios_data = [
            {
                "nombre": "Mini Teatro",
                "categoria": "Teatro",
                "descripcion": "Espacio majestuoso de acústica impecable, ideal para eventos culturales y académicos de gran escala.",
                "capacidad": 450,
                "imagen_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCPX8ytcOeNLDqht-x2jWKMtnldPCDQ5iAr4zpay9oAJGRHvafkD4IX8YVVInSmMdhvdtBavFY_KXpRtNDkJyp_ZvRYS2XI_B3g3NwgkSxbBKzlpv4u2hc4nFF-haxzvYsuS4tHIUhj4kMn2QAhDKn3to3xVZ6Rw2Mwz_YrvfGnxci1BjUO0Z47KUAeiaQU-9znaZTqYIDX3gVZeX3jE7ojANqwWJhyRLJke9OIMtj5Kc3lbhb6OjwIck4OHax0GrAXkGROcIH_Hbcw",
                "responsable": responsable_user
            },
            {
                "nombre": "Sala de Reuniones",
                "categoria": "Sala de reuniones",
                "descripcion": "Sala equipada con tecnología de punta para videoconferencias y juntas directivas.",
                "capacidad": 12,
                "imagen_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDuHgoTSD5TH1RGwZnskaU07mWuz8zFd6sW0ggTWACtBdICPbcXfqbdtWIR7Dxm1ul2GJdpgmolyXqiBfYWk8GFVuVAt-0MRVIMPAKRrxAuFisKHRiWX3GNbloNvfXvliFOBzlDXTtFNdaXTM4YGpVbdwhJWiYl8BOHS7k-HcnDvJHj3MhdiHZy6tiluoSmfueD5HtoB_7b0L4fko2r9k1oEpuSp84_HOe-HzvftMRRCOA3Yc5WBM1uWPPtBMFQHv7W36XxHbfaOPp7",
                "responsable": responsable_user
            },
            {
                "nombre": "Biblioteca",
                "categoria": "Biblioteca",
                "descripcion": "Un oasis de conocimiento con miles de volúmenes y estaciones de estudio silenciosas.",
                "capacidad": 80,
                "imagen_url": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&q=80&w=800",
                "responsable": responsable_user
            },
            {
                "nombre": "Laboratorio de Informática",
                "categoria": "Laboratorio",
                "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
                "capacidad": 25,
                "imagen_url": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=80&w=800",
                "responsable": responsable_user
            },
            {
                "nombre": "Coliseo Deportivo",
                "categoria": "Deportivo",
                "descripcion": "Instalaciones deportivas completas para básquetbol, fútbol sala y eventos deportivos escolares.",
                "capacidad": 600,
                "imagen_url": "https://images.unsplash.com/photo-1541252260730-0412e8e2108e?auto=format&fit=crop&q=80&w=800",
                "responsable": responsable_user
            }
        ]
        for data in espacios_data:
            Espacio.objects.get_or_create(nombre=data["nombre"], defaults=data)

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
    
    mis_reservas = []
    if user_actual and user_actual.is_authenticated:
        notificaciones = Notificacion.objects.filter(usuario=user_actual, leida=False).order_by('-fecha')[:5]
        notificaciones_count = Notificacion.objects.filter(usuario=user_actual, leida=False).count()
        mis_reservas = Reserva.objects.filter(usuario=user_actual).order_by('-fecha')

    is_sec = es_secretaria(user_actual) if user_actual else False
    google_picture = get_google_picture(request.user)

    return render(request, 'index.html', {
        'espacios': espacios,
        'user_simulated': user_simulated,
        'sim_username': sim_username,
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': is_sec,
        'google_picture': google_picture,
        'mis_reservas': mis_reservas,
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
            estado='aprobada'
        )
        
        try:
            reserva.full_clean()
            reserva.save()
            
            # Registrar historial
            HistorialReserva.objects.create(
                reserva=reserva,
                usuario=request.user,
                accion='creacion',
                comentario=f"Reserva creada y aprobada automáticamente por {request.user.username}"
            )
            
            # Opciones de Notificación del Formulario
            notificar_todos = request.POST.get('notificar_todos') == 'true'
            notificar_personas = request.POST.getlist('notificar_personas')

            # Notificaciones
            notificar_reserva(
                reserva, 
                'aprobacion', 
                notificar_todos=notificar_todos, 
                notificar_personas=notificar_personas
            )
            
            from django.contrib import messages
            messages.success(request, f"¡Reserva confirmada en {espacio.nombre} para el {fecha} ({hora_inicio} - {hora_fin})!")
            
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
        'es_secretaria': es_secretaria(request.user),
        'google_picture': get_google_picture(request.user),
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
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fecha = data.get('date')
            hora_inicio = data.get('start_time')
            hora_fin = data.get('end_time')
        except Exception:
            fecha = request.POST.get('date')
            hora_inicio = request.POST.get('start_time')
            hora_fin = request.POST.get('end_time')
            
        reserva.fecha = fecha
        reserva.hora_inicio = hora_inicio
        reserva.hora_fin = hora_fin
        
        try:
            reserva.full_clean()
            reserva.save()
            
            # Registrar historial
            HistorialReserva.objects.create(
                reserva=reserva,
                usuario=request.user,
                accion='modificacion',
                comentario=f"Reserva modificada por el usuario. Nueva fecha: {fecha}, Horario: {hora_inicio} - {hora_fin}"
            )
            
            # Notificaciones
            notificar_reserva(reserva, 'modificacion', comentario=f"Nueva fecha: {fecha}, Horario: {hora_inicio} - {hora_fin}")
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'success'})
                
            from django.contrib import messages
            messages.success(request, "¡Reserva modificada con éxito!")
            return redirect('mis_reservas')
        except ValidationError as e:
            error_msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            
            from django.contrib import messages
            messages.error(request, f"Error al modificar: {error_msg}")
            
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
    
    # Marcar todas como leídas si se solicita
    if request.GET.get('marcar_todas'):
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        return redirect('lista_notificaciones')
    
    # Cargar notificaciones del header
    notificaciones_cinco = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    return render(request, 'notificaciones.html', {
        'todas_notificaciones': notifs,
        'notificaciones': notificaciones_cinco,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_secretaria(request.user),
        'google_picture': get_google_picture(request.user),
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
    next_url = request.GET.get('next') or 'inicio'
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
        return redirect(next_url)
    return redirect('login')

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('inicio')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})

def google_settings(request):
    from django.conf import settings
    return {
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', '')
    }


def api_reservas_horario(request):
    """
    Endpoint JSON que devuelve las reservas (pendientes y aprobadas)
    para poblar el horario automático en el frontend.
    Admite filtros user_only=true y upcoming=true para uso personalizado.
    """
    from django.db.models import Q
    from datetime import date

    reservas = Reserva.objects.filter(
        Q(estado='aprobada') | Q(estado='pendiente')
    )

    user_only = request.GET.get('user_only') == 'true'
    upcoming = request.GET.get('upcoming') == 'true'

    if user_only and request.user.is_authenticated:
        reservas = reservas.filter(usuario=request.user)
    if upcoming:
        reservas = reservas.filter(fecha__gte=timezone.localdate())

    reservas = reservas.select_related('espacio', 'usuario').order_by('fecha', 'hora_inicio')

    data = []
    for r in reservas:
        data.append({
            'id': r.id,
            'espacio': r.espacio.nombre,
            'espacio_id': r.espacio.id,
            'categoria': r.espacio.categoria,
            'usuario': r.usuario.get_full_name() or r.usuario.username,
            'usuario_username': r.usuario.username,
            'fecha': str(r.fecha),
            'hora_inicio': str(r.hora_inicio)[:5],
            'hora_fin': str(r.hora_fin)[:5],
            'estado': r.estado,
        })
    return JsonResponse({'reservas': data})

@login_required
def proximas_reservas(request):
    """
    Vista que renderiza la agenda y calendario de reservas futuras del usuario autenticado.
    """
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    # Para la barra flotante y conteos en menús
    mis_reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha')
    
    espacios = Espacio.objects.all()
    
    return render(request, 'proximas_reservas.html', {
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_secretaria(request.user),
        'mis_reservas': mis_reservas,
        'espacios': espacios,
    })


@login_required
def ayuda(request):
    """
    Vista que renderiza la sección de Ayuda y Tutoriales del sistema.
    """
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha')[:5]
    notificaciones_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    es_sec = es_secretaria(request.user)
    google_picture = get_google_picture(request.user)
    mis_reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha')

    return render(request, 'ayuda.html', {
        'notificaciones': notificaciones,
        'notificaciones_count': notificaciones_count,
        'es_secretaria': es_sec,
        'google_picture': google_picture,
        'mis_reservas': mis_reservas,
    })

@login_required
def api_notificaciones_nuevas(request):
    """
    Endpoint JSON que devuelve las nuevas notificaciones (mostrado=False)
    para el usuario actual y las marca como mostradas.
    """
    nuevas = Notificacion.objects.filter(usuario=request.user, mostrado=False)
    
    data = []
    for n in nuevas:
        data.append({
            'id': n.id,
            'mensaje': n.mensaje,
            'reserva_id': n.reserva.id,
            'espacio': n.reserva.espacio.nombre,
            'fecha': str(n.reserva.fecha),
            'horario': f"{n.reserva.hora_inicio.strftime('%H:%M')} - {n.reserva.hora_fin.strftime('%H:%M')}",
        })
        n.mostrado = True
        n.save()
        
    return JsonResponse({'nuevas': data})