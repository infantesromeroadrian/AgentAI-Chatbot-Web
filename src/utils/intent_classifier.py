"""
Módulo para clasificación de intenciones de los mensajes de usuarios.
Proporciona funciones para determinar el tipo de agente más adecuado
para manejar cada mensaje basado en su contenido y contexto.
"""
import re
import unicodedata
import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logger = logging.getLogger(__name__)

# Palabras clave asociadas a cada tipo de agente
INTENT_KEYWORDS = {
    'EngineerAgent': [
        'técnico', 'tecnico', 'problema', 'configurar', 'instalar', 'error', 
        'funciona', 'integración', 'integracion', 'api', 'desarrollo', 'servidor',
        'cloud', 'implementación', 'implementacion', 'arquitectura', 'tecnología', 'tecnologia',
        'plataforma', 'software', 'aplicación', 'aplicacion', 'sistema', 'infraestructura',
        'hosting', 'base de datos', 'seguridad', 'programación', 'programacion', 'código', 'codigo',
        'soporte técnico', 'soporte tecnico', 'implementar', 'conectar', 'backend', 'frontend'
    ],
    'SalesAgent': [
        'precio', 'costo', 'pagar', 'plan', 'contratar', 'comprar', 'adquirir',
        'presupuesto', 'oferta', 'descuento', 'tarifas', 'inversión', 'inversion',
        'propuesta', 'comercial', 'venta', 'cotización', 'cotizacion', 'contrato',
        'facturación', 'facturacion', 'paquete', 'suscripción', 'suscripcion', 'precios',
        'promoción', 'promocion', 'pago', 'dinero', 'euros', 'cuesta', 'costar', 'valor',
        'económico', 'economico', 'costes', 'mensualidad', 'anualidad', 'financiación', 'financiacion',
        'cotizar', 'precio', 'costará', 'costara', 'costo', 'vale', 'valer', 'interesado en',
        'proforma', 'comprar', 'adquirir', 'contratar'
    ],
    'DataCollectionAgent': [
        'formulario', 'datos', 'contacto', 'email', 'teléfono', 'telefono',
        'llamar', 'nombre', 'empresa', 'información', 'informacion', 'contactarme',
        'representante', 'asesor', 'registrar', 'visita', 'reunión', 'reunion',
        'demo', 'demostración', 'demostracion', 'prueba', 'gratuita', 'trial',
        'correo', 'dirección', 'direccion', 'móvil', 'movil', 'celular', 'whatsapp',
        'contactar', 'comunicar', 'comunicarse', 'interesado'
    ],
    'GeneralAgent': [
        'hola', 'información', 'informacion', 'ayuda', 'servicio', 'solución', 'solucion',
        'explicar', 'contar', 'qué es', 'que es', 'cómo', 'como', 'cuál', 'cual',
        'beneficios', 'ventajas', 'características', 'caracteristicas', 'funcionalidades',
        'diferencia', 'similar', 'competencia', 'alternativas', 'mejor', 'recomendación',
        'recomendacion', 'opinión', 'opinion', 'experiencia', 'caso de éxito', 'caso de exito'
    ]
}

# Frases completas que indican una intención específica
INTENT_PHRASES = {
    'EngineerAgent': [
        'cómo funciona', 'como funciona', 'cómo se integra', 'como se integra',
        'cómo se implementa', 'como se implementa', 'necesito ayuda técnica',
        'necesito ayuda tecnica', 'tengo un problema técnico', 'tengo un problema tecnico',
        'puedo conectar', 'es compatible con', 'requisitos técnicos', 'requisitos tecnicos'
    ],
    'SalesAgent': [
        'cuánto cuesta', 'cuanto cuesta', 'qué precio tiene', 'que precio tiene',
        'tienen descuentos', 'hay promociones', 'formas de pago', 'métodos de pago',
        'metodos de pago', 'planes disponibles', 'quiero contratar', 'quiero comprar',
        'estoy interesado en cotizar', 'necesito cotizar', 'quiero una cotización',
        'quiero cotización', 'quiero cotizacion', 'pueden cotizar', 'me gustaría cotizar',
        'precio para', 'costo de', 'interesado en comprar', 'interesado en contratar',
        'interesado en adquirir', 'cuanto me costaría', 'quiero una propuesta comercial'
    ],
    'DataCollectionAgent': [
        'quiero que me contacten', 'me gustaría hablar con un representante',
        'me gustaria hablar con un representante', 'pueden llamarme',
        'quiero una demostración', 'quiero una demostracion',
        'necesito que me contacte un asesor', 'mi correo es', 'mi email es',
        'mi teléfono es', 'mi telefono es', 'mis datos son', 'quiero dejar mis datos'
    ]
}

def normalize_text(text: str) -> str:
    """
    Normaliza el texto para búsqueda de palabras clave, eliminando acentos 
    y convirtiendo a minúsculas.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    
    return text

def classify_intent(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Clasifica la intención del mensaje del usuario y determina qué tipo de agente
    debería manejarlo.
    
    Args:
        message: Mensaje del usuario
        context: Contexto de la conversación (opcional)
        
    Returns:
        Diccionario con probabilidades para cada tipo de agente
    """
    # Normalizar mensaje
    normalized_message = normalize_text(message)
    
    # Inicializar puntuaciones con valor base
    scores = {
        'GeneralAgent': 0.4,  # Prioridad base aún más alta para el agente general
        'SalesAgent': 0.1,
        'EngineerAgent': 0.1,
        'DataCollectionAgent': 0.0  # Iniciar con cero para forzar que solo sea activado explícitamente
    }
    
    # Verificar primero si es una pregunta sobre servicios o información general
    service_info_patterns = [
        'qué servicios', 'que servicios', 'qué ofrece', 'que ofrece',
        'qué hace', 'que hace', 'información sobre', 'informacion sobre',
        'cuáles son', 'cuales son', 'qué es', 'que es'
    ]
    
    # Si es una pregunta sobre servicios, dar alta prioridad al GeneralAgent inmediatamente
    if any(pattern in normalized_message for pattern in service_info_patterns):
        scores['GeneralAgent'] += 0.6
        scores['DataCollectionAgent'] = 0.0  # Asegurar que no se active para preguntas de información
        # Incluso podemos cortar el procesamiento aquí y devolver scores
        if '?' in message:
            return scores
    
    # Incrementar puntuación por palabras clave encontradas
    for agent_type, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            # Verificar si la palabra clave está presente como palabra completa
            keyword_pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(keyword_pattern, normalized_message):
                # Dar peso especial a palabras relacionadas con cotizaciones para el agente de ventas
                if agent_type == 'SalesAgent' and keyword in ['cotizar', 'cotización', 'cotizacion', 'precio', 'costo']:
                    scores[agent_type] += 0.25  # Mayor peso para términos de ventas críticos
                else:
                    scores[agent_type] += 0.15
    
    # Incrementar puntuación por frases específicas (mayor peso)
    for agent_type, phrases in INTENT_PHRASES.items():
        for phrase in phrases:
            if normalize_text(phrase) in normalized_message:
                if agent_type == 'SalesAgent':
                    scores[agent_type] += 0.35  # Mayor peso para frases de ventas
                else:
                    scores[agent_type] += 0.25
    
    # Analizar el contexto de la conversación si está disponible
    if context:
        scores = apply_context_adjustments(scores, message, context)
    
    # Verificar límites de valores
    for agent_type in scores:
        scores[agent_type] = min(scores[agent_type], 1.0)
        scores[agent_type] = max(scores[agent_type], 0.0)
    
    return scores

def apply_context_adjustments(agent_scores, user_message, context):
    """
    Ajusta las puntuaciones de los agentes basándose en el contexto de la conversación.
    """
    message_normalized = user_message.lower()
    
    # Reducir significativamente el peso base del DataCollectionAgent para evitar
    # que capture consultas generales
    if 'DataCollectionAgent' in agent_scores:
        agent_scores['DataCollectionAgent'] *= 0.4  # Reducción más agresiva
    
    # 1. Verificar consultas de información general que deben ir al GeneralAgent
    general_info_patterns = [
        '¿qué', 'que', '¿cuál', 'cual', '¿cómo', 'como', 
        'servicios', 'ofrecen', 'ofrece', 'about', 'acerca'
    ]
    
    is_info_query = any(pattern in message_normalized for pattern in general_info_patterns)
    if is_info_query and len(message_normalized.split()) < 15:
        # Es probablemente una consulta de información
        if 'GeneralAgent' in agent_scores:
            agent_scores['GeneralAgent'] += 0.3  # Aumentar más
        if 'DataCollectionAgent' in agent_scores:
            agent_scores['DataCollectionAgent'] -= 0.7  # Reducir más agresivamente
    
    # 2. Verificar si es un mensaje corto o inicial
    if len(message_normalized.split()) <= 3:
        # Mensajes muy cortos generalmente son mejor manejados por el agente general
        if 'GeneralAgent' in agent_scores:
            agent_scores['GeneralAgent'] += 0.25  # Aumentar más
        if 'DataCollectionAgent' in agent_scores:
            agent_scores['DataCollectionAgent'] -= 0.5  # Reducir más
    
    # 3. Detectar explícitamente solicitudes de cotización para SalesAgent
    quote_terms = ['cotizar', 'cotización', 'precio', 'costo', 'valor', 'planes', 'oferta']
    if any(term in message_normalized for term in quote_terms):
        if 'SalesAgent' in agent_scores:
            agent_scores['SalesAgent'] += 0.5  # Prioridad alta
        if 'DataCollectionAgent' in agent_scores:
            agent_scores['DataCollectionAgent'] -= 0.4  # Reducir
    
    # 4. Detectar explícitamente solicitudes de demostración o contacto
    contact_terms = ['contactar', 'llamar', 'contacto', 'teléfono', 'email', 'correo']
    demo_terms = ['demostración', 'demo', 'probar', 'prueba']
    
    is_contact_request = any(term in message_normalized for term in contact_terms)
    is_demo_request = any(term in message_normalized for term in demo_terms)
    
    # Solo aumentar DataCollectionAgent si es explícitamente una solicitud de contacto o demo
    if (is_contact_request or is_demo_request) and 'DataCollectionAgent' in agent_scores:
        agent_scores['DataCollectionAgent'] += 0.4
    
    # 5. Mantener continuidad de conversación con el agente actual
    if context and 'history' in context and context['history']:
        last_entry = context['history'][-1] if context['history'] else None
        if last_entry and 'agent' in last_entry:
            current_agent = last_entry['agent']
            
            # Si el mensaje es corto, favorece continuar con el mismo agente
            if len(message_normalized.split()) < 5 and current_agent in agent_scores:
                agent_scores[current_agent] += 0.2
    
    # Registro para depuración
    logger.debug(f"Agent scores after context adjustment: {agent_scores}")
    
    return agent_scores

def detect_agent_change_keywords(message: str) -> Optional[str]:
    """
    Detecta si el mensaje contiene palabras clave explícitas para cambiar a un
    tipo específico de agente.
    
    Args:
        message: Mensaje del usuario
        
    Returns:
        Nombre del agente al que cambiar, o None si no se detecta
    """
    normalized_message = normalize_text(message)
    
    # Palabras clave explícitas para cada tipo de agente
    explicit_agent_keywords = {
        'EngineerAgent': [
            'hablar con técnico', 'hablar con tecnico', 'hablar con un técnico',
            'hablar con un tecnico', 'quiero hablar con soporte',
            'necesito ayuda técnica', 'necesito ayuda tecnica',
            'quiero hablar con ingeniería', 'quiero hablar con ingenieria',
            'me gustaria hablar con alguien tecnico', 'me gustaría hablar con un técnico',
            'hablar con alguien tecnico', 'hablar con alguien técnico',
            'quiero al tecnico', 'quiero al técnico', 'pasar al tecnico',
            'pasar al técnico', 'cambiar a tecnico', 'cambiar a técnico',
            'conectar con tecnico', 'conectar con técnico',
            'pasa al departamento tecnico', 'pasa al departamento técnico',
            'necesito soporte tecnico', 'necesito soporte técnico',
            'tecnico', 'técnico'
        ],
        'SalesAgent': [
            'hablar con ventas', 'hablar con un vendedor', 'hablar con comercial',
            'hablar con un comercial', 'departamento de ventas',
            'información de precios', 'informacion de precios',
            'me gustaria hablar con ventas', 'me gustaría hablar con ventas',
            'pasar a ventas', 'cambiar a ventas', 'conectar con ventas',
            'quiero hablar con un comercial', 'necesito hablar con ventas',
            'ventas', 'comercial', 'cotizacion', 'cotización', 'precios',
            'presupuesto', 'costo', 'pago', 'precio'
        ],
        'DataCollectionAgent': [
            'quiero registrarme', 'quiero dejar mis datos', 'completar formulario',
            'enviar mis datos', 'quiero que me contacten',
            'me gustaria dejar mis datos', 'me gustaría dejar mis datos',
            'hablar con agente de datos', 'pasar a datos', 'cambiar a datos',
            'conectar con datos', 'registro', 'formulario', 'contacto',
            'datos', 'contactarme'
        ],
        'GeneralAgent': [
            'información general', 'informacion general', 'volver al inicio',
            'empezar de nuevo', 'reiniciar conversación', 'reiniciar conversacion',
            'pasar a general', 'cambiar a general', 'agente general',
            'general', 'inicio', 'reiniciar', 'empezar'
        ]
    }
    
    for agent_type, phrases in explicit_agent_keywords.items():
        for phrase in phrases:
            # Verificar si la frase está contenida en el mensaje normalizado
            if normalize_text(phrase) in normalized_message:
                return agent_type
            
            # También verificar coincidencia exacta para frases de una sola palabra
            if len(phrase.split()) == 1 and normalize_text(phrase).strip() == normalized_message.strip():
                return agent_type
    
    return None

def get_confidence_explanation(scores: Dict[str, float], selected_agent: str) -> str:
    """
    Genera una explicación de por qué se seleccionó un agente específico.
    Útil para debugging y logging.
    
    Args:
        scores: Puntuaciones para cada tipo de agente
        selected_agent: Agente seleccionado
        
    Returns:
        Explicación en formato texto
    """
    all_scores = ", ".join([f"{agent}: {score:.2f}" for agent, score in sorted(
        scores.items(), key=lambda x: x[1], reverse=True)])
    
    return f"Agente seleccionado: {selected_agent} con confianza {scores[selected_agent]:.2f}. " \
           f"Todas las puntuaciones: {all_scores}" 