"""
Agente de bienvenida que saluda y hace preguntas generales.
"""
from typing import Dict, Any
import re
from .base_agent import BaseAgent

class WelcomeAgent(BaseAgent):
    """
    Agente que maneja los saludos iniciales y preguntas generales.
    Este es el agente por defecto que se activa al inicio de una conversación.
    """
    
    def __init__(self):
        """Inicializa el agente de bienvenida."""
        super().__init__(
            name="WelcomeAgent",
            description="Agente que saluda y hace preguntas generales para entender las necesidades del usuario"
        )
        
        # Patrones para detectar saludos
        self.greeting_patterns = [
            r'\bhola\b',
            r'\bbuenos días\b',
            r'\bbuenas tardes\b',
            r'\bbuenas noches\b',
            r'\bhey\b',
            r'\bsaludos\b',
            r'\bqué tal\b',
            r'\bcómo estás\b',
            r'\bqué hay\b',
        ]
        
        # Patrones para detectar preguntas generales
        self.general_question_patterns = [
            r'\bqué (es|son|hace|hacen)\b',
            r'\bcómo funciona\b',
            r'\bme puedes ayudar\b',
            r'\bpuedes ayudarme\b',
            r'\bnecesito ayuda\b',
            r'\bquiero saber\b',
            r'\bme gustaría saber\b',
            r'\bme interesa\b',
            r'\bquiero información\b',
        ]
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> float:
        """
        Determina si este agente puede manejar el mensaje actual.
        
        Args:
            message: El mensaje del usuario
            context: El contexto de la conversación
            
        Returns:
            Un valor de confianza entre 0 y 1
        """
        message_lower = message.lower()
        
        # Si es el primer mensaje o hay pocos mensajes, este agente tiene alta prioridad
        message_count = len(context.get('conversation_history', []))
        if message_count < 3:
            return 0.9
        
        # Detectar saludos
        for pattern in self.greeting_patterns:
            if re.search(pattern, message_lower):
                return 0.8
        
        # Detectar preguntas generales
        for pattern in self.general_question_patterns:
            if re.search(pattern, message_lower):
                return 0.7
        
        # Este agente puede manejar cualquier mensaje, pero con baja prioridad
        return 0.3
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt de sistema para este agente.
        
        Args:
            context: El contexto de la conversación
            
        Returns:
            El prompt de sistema
        """
        # Determinar si es el inicio de la conversación
        is_conversation_start = len(context.get('conversation_history', [])) < 3
        
        if is_conversation_start:
            # Prompt para el inicio de la conversación
            return """Eres un asistente virtual de Alisys, una empresa líder en soluciones tecnológicas innovadoras.

INSTRUCCIONES PARA EL INICIO DE LA CONVERSACIÓN:

1. Saluda al usuario de manera amigable y profesional.
2. Preséntate como el asistente virtual de Alisys.
3. Haz preguntas abiertas para entender las necesidades específicas del usuario.
4. Muestra interés genuino en ayudar al usuario a encontrar la solución adecuada.
5. No proporciones información detallada sobre servicios específicos todavía.
6. No solicites información de contacto en esta etapa inicial.

Tu objetivo es establecer una conversación fluida y entender qué busca el usuario para poder dirigirlo al agente especializado adecuado.

INFORMACIÓN BÁSICA SOBRE ALISYS:
- Alisys es una empresa especializada en soluciones tecnológicas innovadoras.
- Ofrece servicios en áreas como Cloud, IA, Blockchain y Robótica.
- Trabaja con diversos sectores como Salud, Educación, Automoción y Administraciones Públicas.

Recuerda mantener un tono conversacional, amigable y profesional en todo momento."""
        else:
            # Prompt para preguntas generales durante la conversación
            return """Eres un asistente virtual de Alisys, una empresa líder en soluciones tecnológicas innovadoras.

INSTRUCCIONES PARA PREGUNTAS GENERALES:

1. Responde de manera clara y concisa a las preguntas del usuario.
2. Proporciona información general sobre Alisys y sus servicios.
3. Si el usuario muestra interés en un área específica, proporciona información básica.
4. No entres en detalles técnicos profundos o especificaciones de precios.
5. Si el usuario necesita información más específica, indica que puedes conectarlo con un especialista.
6. Mantén un tono conversacional y amigable.

INFORMACIÓN SOBRE ALISYS:
- Alisys es una empresa especializada en soluciones tecnológicas innovadoras.
- Ofrece servicios en áreas como Cloud, IA, Blockchain y Robótica.
- Trabaja con diversos sectores como Salud, Educación, Automoción y Administraciones Públicas.
- Casos de éxito incluyen Vodafone, 060, Sacyl, Sodexo, Carglass, entre otros.

Recuerda mantener un tono conversacional, amigable y profesional en todo momento.""" 