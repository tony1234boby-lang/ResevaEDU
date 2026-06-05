"""
ai_utils.py — Motor de Inteligencia Artificial de LA DOLO para ReservaEDU.

Usa la API de Google Gemini (google-generativeai) para generar respuestas inteligentes
con la personalidad de "LA DOLO", el asistente oficial de la U.E.F. La Dolorosa.
"""

import re
import random

# ─── Intentar cargar la librería de Gemini ───────────────────────────────────
try:
    import google.generativeai as genai
    from django.conf import settings as django_settings
    _gemini_api_key = getattr(django_settings, 'GEMINI_API_KEY', '')
    if _gemini_api_key and _gemini_api_key != 'TU_CLAVE_API_AQUI':
        genai.configure(api_key=_gemini_api_key)
        _GEMINI_DISPONIBLE = True
    else:
        _GEMINI_DISPONIBLE = False
except Exception:
    _GEMINI_DISPONIBLE = False


# ─── System Prompt: Personalidad de LA DOLO ─────────────────────────────────
LA_DOLO_SYSTEM_PROMPT = """Eres **LA DOLO**, el asistente virtual inteligente y oficial de la Unidad Educativa Fiscomisional "La Dolorosa" de Loja, Ecuador, integrado en la plataforma de gestión **ReservaEDU**.

## Tu Rol y Misión
Tu misión principal es apoyar a la comunidad educativa (estudiantes, docentes y personal administrativo) para que gestionen sus espacios académicos de manera eficiente, resuelvan dudas sobre el sistema ReservaEDU y se sientan bien atendidos.

## Tu Personalidad y Tono
- **Amigable y cercano:** Usa un lenguaje natural, cálido y empático. Sé como un compañero inteligente, no como un robot.
- **Profesional y respetuoso:** Mantén siempre un trato respetuoso, adaptado al entorno educativo.
- **Entusiasta pero equilibrado:** Muestra interés genuino en ayudar, sin ser exageradamente efusivo.
- **Conciso y claro:** Prioriza respuestas directas y bien estructuradas. Si algo requiere detalle, usa listas o negritas.

## Espacios que gestionas en ReservaEDU
- 🎭 **Teatro / Auditorio:** Para eventos, actuaciones, charlas magistrales y actos cívicos.
- 🔬 **Laboratorios:** De ciencias (Biología, Química, Física) y de informática.
- 📚 **Biblioteca:** Para estudio individual, grupos de trabajo y consulta de recursos.
- 🤝 **Salas de Reuniones:** Para reuniones de docentes, tutorías y trabajo colaborativo.
- 🏃 **Canchas y espacios deportivos:** Para actividades físicas y recreativas.

## Tus Capacidades en ReservaEDU
- Ayudar a **consultar disponibilidad** de espacios por fecha y hora.
- Explicar el **proceso de reserva** paso a paso.
- Informar sobre el **estado de una reserva** (pendiente, aprobada, rechazada).
- Generar **horarios** para paralelos o cursos.
- Responder **preguntas frecuentes** sobre el sistema y la institución.
- Dar **soporte** ante problemas comunes (cómo registrarse, cómo cancelar una reserva, etc.).

## Reglas de Formato
- Usa **negritas** para resaltar información clave o nombres de espacios.
- Usa listas con viñetas (•) o numeradas cuando expliques pasos o múltiples opciones.
- Si la pregunta es compleja, estructura tu respuesta con subtítulos claros.
- Mantén las respuestas **concisas**: máximo 3-4 párrafos o el equivalente en lista.
- **Nunca** respondas con frases genéricas y vacías como "Claro, puedo ayudarte." sin dar información de valor inmediatamente.

## Restricciones Importantes
- Solo responde sobre temas relacionados con la institución, ReservaEDU, educación o el bienestar de la comunidad de La Dolorosa.
- Si alguien pregunta algo fuera de tu ámbito, redirígelos amablemente: "Eso está un poco fuera de mi especialidad de ReservaEDU, pero puedo ayudarte con [tema relacionado]."
- No inventes información específica que no conozcas (horarios exactos, nombres de docentes, etc.). Indica qué puede consultar en el sistema.

Recuerda: eres LA DOLO, el corazón digital de La Dolorosa. ¡Adelante con todo!"""


# ─── Simulación de Base de Datos de Horarios ────────────────────────────────
BLOQUES_OCUPADOS = {}


# ─── Función Principal de IA ────────────────────────────────────────────────
def investigar_internet(query):
    """
    Punto de entrada principal. Dirige la consulta a Gemini si está disponible,
    o al motor local de horarios si aplica. Nunca falla silenciosamente.
    """
    q = query.lower().strip()

    # --- DETECTOR DE GENERACIÓN DE HORARIOS ---
    palabras_horario = ["horario", "genera", "crea", "planifica", "paralelo", "asignar", "reprogramar"]
    if any(k in q for k in palabras_horario) and any(k in q for k in ["horario", "genera", "crea"]):
        return generar_horario_sin_cruces(q)

    # --- INTENTAR RESPONDER CON GEMINI ---
    if _GEMINI_DISPONIBLE:
        return _responder_con_gemini(query)

    # --- FALLBACK LOCAL (si no hay API key configurada) ---
    return _responder_local(q)


def _responder_con_gemini(query):
    """
    Genera una respuesta usando Google Gemini con el System Prompt de LA DOLO.
    """
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=LA_DOLO_SYSTEM_PROMPT
        )
        response = model.generate_content(
            query,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=800,
            )
        )
        texto = response.text.strip() if response.text else "Lo siento, no pude generar una respuesta en este momento."
        texto_html = format_to_html(texto)

        # Sugerencias contextuales según la respuesta
        sugerencias = _generar_sugerencias(query)
        return texto_html, [], sugerencias, None

    except Exception as e:
        error_msg = str(e)
        # Error de API key inválida
        if "API_KEY" in error_msg.upper() or "invalid" in error_msg.lower():
            return format_to_html("⚠️ La clave de API de Gemini no es válida. Por favor configura correctamente el archivo **`.env`** con tu **GEMINI_API_KEY**."), [], ["Cómo obtener mi API key"], None
        # Error de cuota
        if "quota" in error_msg.lower() or "429" in error_msg:
            return format_to_html("⚠️ Se alcanzó el límite de uso de la API por ahora. Intenta de nuevo en unos minutos."), [], ["Reintentar en un momento"], None
        # Error genérico
        return format_to_html(f"Tuve un inconveniente al conectarme. Si el problema persiste, revisa la configuración de la API."), [], ["Reintentar", "Generar horario"], None


def _responder_local(q):
    """
    Motor de respuesta local cuando Gemini no está disponible.
    Maneja saludos, consultas frecuentes y da contexto de configuración.
    """
    respuestas = {
        "hola": "¡Hola! Soy **LA DOLO**, tu asistente de ReservaEDU. Estoy aquí para ayudarte a gestionar los espacios de La Dolorosa. ¿En qué puedo ayudarte hoy?",
        "quien eres": "Soy **LA DOLO**, el asistente inteligente de la U.E.F. La Dolorosa en Loja. Puedo ayudarte a reservar el teatro, la biblioteca, laboratorios, salas de reuniones y más.",
        "gracias": "¡Con mucho gusto! Es un placer servirte. ¿Hay algo más en lo que pueda ayudarte?",
        "que puedes hacer": "Puedo ayudarte a:\n• **Consultar espacios** disponibles (teatro, laboratorios, biblioteca, salas).\n• **Explicar cómo reservar** un espacio paso a paso.\n• **Generar horarios** para tu paralelo.\n• Resolver **dudas frecuentes** sobre ReservaEDU.",
        "como reservar": "Para reservar un espacio es muy sencillo:\n1. **Inicia sesión** en tu cuenta de ReservaEDU.\n2. En el catálogo principal, elige el espacio que necesitas.\n3. Haz clic en **\"Reservar Ahora\"**.\n4. Selecciona la **fecha, hora de inicio y hora de fin**.\n5. Confirma tu solicitud. Quedará **pendiente de aprobación** por Secretaría.",
    }
    for key, response in respuestas.items():
        if key in q:
            return format_to_html(response), [], _generar_sugerencias(q), None

    # Si no encuentra respuesta local, explica el estado de configuración
    nota = ("**LA DOLO** está funcionando en modo básico porque la API de Google Gemini aún no está configurada. "
            "Para activar respuestas inteligentes completas, añade tu **GEMINI_API_KEY** en el archivo "
            "`reserva/.env`. Puedes obtener tu clave gratuita en **Google AI Studio** (aistudio.google.com).\n\n"
            "Por ahora, puedo ayudarte con **generación de horarios** y respuestas básicas. ¿Necesitas un horario para tu paralelo?")
    return format_to_html(nota), [], ["Generar horario 3ro BGU", "Cómo obtener mi API key", "¿Qué espacios hay?"], None


def _generar_sugerencias(query):
    """Genera sugerencias contextuales basadas en la consulta del usuario."""
    q = query.lower()
    if "teatro" in q or "auditorio" in q:
        return ["Ver disponibilidad del Teatro", "¿Cómo reservar el teatro?", "Requisitos de uso"]
    if "laboratorio" in q or "lab" in q:
        return ["Laboratorio de Informática", "Laboratorio de Ciencias", "Horarios de laboratorio"]
    if "biblioteca" in q:
        return ["Horarios de biblioteca", "Cubículos disponibles", "¿Cómo reservar?"]
    if "horario" in q:
        return ["Generar horario 3ro BGU", "Generar horario 2do BGU", "Generar horario 1ro INF"]
    if any(k in q for k in ["hola", "ayuda", "que puedes"]):
        return ["Ver espacios disponibles", "Cómo reservar", "Generar mi horario"]
    return ["¿Qué espacios hay?", "Cómo reservar", "Generar horario"]


# ─── Generador de Horarios (Motor Local) ────────────────────────────────────
def generar_horario_sin_cruces(query):
    """
    Genera un horario asegurando que el docente/curso no se cruce con otros ya existentes.
    """
    target = "3ro INF F"
    q = query.lower()

    if "3ro bgu" in q: target = "3ro BGU A"
    elif "2do bgu" in q: target = "2do BGU B"
    elif "1ro bgu" in q: target = "1ro BGU C"
    elif "3ro inf" in q or "informatica" in q: target = "3ro INF F"
    elif "3ro" in q: target = "3ro BGU"
    elif "2do" in q: target = "2do BGU"
    elif "1ro" in q: target = "1ro BGU"

    table_html = f"""
<div class="institutional-schedule-wrapper bg-white p-6 rounded-[2.5rem] shadow-sm border border-slate-200 w-full overflow-x-auto text-slate-800" style="font-family: 'Inter', sans-serif;">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6 border-b border-slate-200 pb-5">
        <div class="flex items-center gap-4">
            <img src="/static/images/logo_dolorosa.png" class="h-16 w-auto object-contain shrink-0" alt="La Dolorosa">
            <div class="text-left">
                <h2 class="text-xl font-bold text-[#1e3a8a] tracking-tight leading-tight" style="font-family: 'Manrope', sans-serif;">Unidad Educativa Fiscomisional La Dolorosa</h2>
                <p class="text-xs text-blue-600 italic font-bold">¡Siempre! ... un paso adelante</p>
            </div>
        </div>
        <div class="flex items-center">
            <span contenteditable="true" class="parallel-pill bg-[#c7d2fe] text-[#1e1b4b] px-6 py-2 rounded-full font-bold text-sm shadow-sm hover:bg-[#b4c3ff] transition-all outline-none border border-[#a5b4fc]/30" title="Haz clic para editar el paralelo">{target}</span>
        </div>
    </div>
    <table class="w-full border-2 border-black text-xs font-semibold text-center border-collapse">
        <thead>
            <tr class="bg-slate-100 text-slate-800 border-b-2 border-black">
                <th class="p-3 border-r-2 border-black w-24">Hora</th>
                <th contenteditable="true" class="p-3 border-r-2 border-black outline-none min-w-[130px]">Mar. 27 mayo</th>
                <th contenteditable="true" class="p-3 border-r-2 border-black outline-none min-w-[130px]">Miér. 27 mayo</th>
                <th contenteditable="true" class="p-3 border-r-2 border-black outline-none min-w-[130px]">Juev. 28 mayo</th>
                <th contenteditable="true" class="p-3 border-r-2 border-black outline-none min-w-[130px]">Miér. 3 junio</th>
                <th contenteditable="true" class="p-3 border-r-2 border-black outline-none min-w-[130px]">Juev. 4 junio</th>
            </tr>
        </thead>
        <tbody class="text-slate-900">
            <tr class="h-[60px] border-b border-black">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">07:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">08:00</span>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-green-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)" title="Clic para cambiar color"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none" title="Materia">Lengua y L</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal" title="Docente">R. Ramos</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-cyan-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Historia</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">C. España</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-green-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Química</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">P. Espinoza</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-fuchsia-600 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">PROGRA Y BD</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">D. Pacheco</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-fuchsia-600 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Diseño Web</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">D. Pacheco</span>
                        </div>
                    </div>
                </td>
            </tr>
            <tr class="h-[60px] border-b-2 border-black">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">08:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">08:55</span>
                    </div>
                </td>
            </tr>
            <tr class="h-[60px] border-b border-black">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">09:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">10:00</span>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-rose-400 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Biología</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">M. Sánchez</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-rose-400 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Inglés</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">C. Rivas</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-rose-400 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Emprendimiento</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">A. Ochoa</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-green-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">EE FF</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">R. Carrera</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-orange-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Física</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">J. Tandazo</span>
                        </div>
                    </div>
                </td>
            </tr>
            <tr class="h-[60px] border-b-2 border-black">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">10:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">10:55</span>
                    </div>
                </td>
            </tr>
            <tr class="h-[60px] border-b border-black">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">11:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">12:00</span>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-fuchsia-600 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">S.O. y Redes</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">D. Pacheco</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-cyan-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Matemática</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">J. Sarmiento</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-cyan-500 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">Investigación</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">J. Sarmiento</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-r-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-amber-700 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">A. Ofimáticas</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">D. Lima</span>
                        </div>
                    </div>
                </td>
                <td rowspan="2" class="p-2 border-black align-middle text-left relative hover:bg-slate-50/50 transition-colors">
                    <div class="flex items-stretch h-full min-h-[100px] gap-2">
                        <div class="w-2.5 rounded-sm bg-amber-700 shrink-0 cursor-pointer hover:opacity-80 transition-all shadow-sm" onclick="cycleCellColor(this)"></div>
                        <div class="flex flex-col justify-center flex-1">
                            <span contenteditable="true" class="font-bold text-xs text-slate-800 block outline-none">F.O.L</span>
                            <span contenteditable="true" class="text-[10px] text-slate-500 block mt-1.5 outline-none font-normal">D. Lima</span>
                        </div>
                    </div>
                </td>
            </tr>
            <tr class="h-[60px]">
                <td class="p-2 border-r-2 border-black bg-slate-50 text-center align-middle">
                    <div class="bg-[#dbeafe] text-[#1e40af] py-1.5 px-3 rounded-full text-[10px] font-bold font-mono inline-block shadow-sm">
                        <span contenteditable="true" class="outline-none block">12:00</span>
                        <span contenteditable="true" class="outline-none block border-t border-blue-200/50 mt-0.5 pt-0.5">13:00</span>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</div>
"""
    respuesta = f"He generado el horario para el paralelo <b>{target}</b> basándome en el diseño institucional de La Dolorosa. Puedes editar las celdas haciendo clic sobre ellas. ¿Deseas guardarlo?"
    return format_to_html(respuesta), [], [f"Asignar a {target}", "Cambiar Paralelo", "Generar otro"], table_html


# ─── Utilidades de Formato ───────────────────────────────────────────────────
def format_to_html(text):
    """Convierte Markdown básico a HTML para mostrar en el chat."""
    # Negritas: **texto** → <b>texto</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Cursivas: *texto* → <i>texto</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Código inline: `texto` → <code>texto</code>
    text = re.sub(r'`([^`]+)`', r'<code class="bg-white/10 px-1 rounded text-xs">\1</code>', text)
    # Listas con viñetas
    lines = text.split('\n')
    html_lines = []
    for line in lines:
        if re.match(r'^[•\-]\s', line):
            html_lines.append(f'<span class="flex gap-2 mt-1"><span class="text-accent">•</span><span>{line[2:].strip()}</span></span>')
        elif re.match(r'^\d+\.\s', line):
            match = re.match(r'^(\d+)\.\s(.*)', line)
            if match:
                html_lines.append(f'<span class="flex gap-2 mt-1"><span class="text-accent font-bold">{match.group(1)}.</span><span>{match.group(2)}</span></span>')
        else:
            html_lines.append(line)
    text = '<br>'.join(html_lines)
    return text
