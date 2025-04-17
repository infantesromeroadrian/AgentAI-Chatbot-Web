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
        'GeneralAgent': 0.2,  # Mayor prioridad base para el agente general
        'SalesAgent': 0.1,
        'EngineerAgent': 0.1,
        'DataCollectionAgent': 0.05  # Menor prioridad base para el agente de datos
    }
    
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

def apply_context_adjustments(scores: Dict[str, float], message: str, context: Dict[str, Any]) -> Dict[str, float]:
    """
    Aplica ajustes a las puntuaciones basados en el contexto de la conversación.
    
    Args:
        scores: Puntuaciones actuales para cada tipo de agente
        message: Mensaje del usuario
        context: Contexto de la conversación
        
    Returns:
        Puntuaciones ajustadas
    """
    # Normalizar mensaje para búsquedas posteriores
    normalized_message = normalize_text(message)
    
    # Verificar el historial de mensajes
    message_count = context.get('message_count', 0)
    current_agent = context.get('current_agent')
    
    # Primeros mensajes: favorecer al agente general para presentaciones
    if message_count <= 2:
        scores['GeneralAgent'] += 0.1
    
    # Si hay un agente actual, darle algo de preferencia para mantener continuidad
    if current_agent and current_agent in scores:
        scores[current_agent] += 0.15
    
    # Si el formulario ha sido mostrado pero no completado, favorecer recolección de datos
    if context.get('form_shown', False) and not context.get('form_completed', False):
        scores['DataCollectionAgent'] += 0.2
    
    # Mensaje corto (como "sí", "ok", "no"): mantener el mismo agente
    if len(message) <= 5 and current_agent:
        scores[current_agent] += 0.3
    
    # Detectar preguntas directas (qué, cómo, cuándo, dónde, por qué)
    question_words = ['que', 'qué', 'como', 'cómo', 'cuando', 'cuándo', 
                      'donde', 'dónde', 'por que', 'por qué', 'cual', 'cuál']
    
    if any(normalize_text(question).strip() in normalized_message.split() for question in question_words):
        # Preguntas generales suelen manejarse mejor por el agente general
        scores['GeneralAgent'] += 0.1
    
    # Verificar información del usuario existente
    user_info = context.get('user_info', {})
    if user_info and not context.get('form_completed', False):
        # Si ya tenemos algunos datos pero no todos, favorecer recolección de datos
        scores['DataCollectionAgent'] += 0.15
        
    # Detectar términos de cotización para evitar que los maneje el DataCollectionAgent
    cotization_terms = ["cotizar", "cotización", "cotizacion", "presupuesto", 
                         "precio", "costo", "cuánto cuesta", "cuanto vale"]
    
    if any(term in normalized_message for term in cotization_terms):
        # Aumentar puntuación del SalesAgent
        scores['SalesAgent'] += 0.25
        # Reducir puntuación del DataCollectionAgent para estos casos
        scores['DataCollectionAgent'] -= 0.2
        logger.debug("Términos de cotización detectados, favoreciendo SalesAgent sobre DataCollectionAgent")
    
    # Si hay una mención explícita de "call center" o "contact center" junto a términos de precio
    if ('call center' in normalized_message or 'contact center' in normalized_message) and \
       any(term in normalized_message for term in cotization_terms):
        scores['SalesAgent'] += 0.3
        scores['DataCollectionAgent'] -= 0.15
        logger.debug("Consulta sobre precios de call center detectada, priorizando SalesAgent")
    
    return scores

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