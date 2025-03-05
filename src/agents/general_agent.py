"""
Agente general para el chatbot de Alisys.
Este agente se encarga de manejar consultas generales sobre Alisys y sus servicios.
"""
from typing import Dict, Any
from .base_agent import BaseAgent

class GeneralAgent(BaseAgent):
    """
    Agente especializado en proporcionar información general sobre Alisys.
    Maneja consultas básicas sobre la empresa y sus servicios.
    """
    
    def __init__(self):
        """
        Inicializa el agente general.
        """
        super().__init__(
            name="GeneralAgent",
            description="Especialista en información general sobre Alisys"
        )
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determina si este agente puede manejar el mensaje actual.
        El agente general puede manejar cualquier mensaje que no sea específico
        para otros agentes más especializados.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            True si el agente puede manejar el mensaje, False en caso contrario
        """
        # El agente general es el agente por defecto, puede manejar cualquier mensaje
        # que no sea específico para otros agentes
        return True
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        return f"""Eres un asistente virtual de Alisys, una empresa especializada en soluciones de comunicación.

INFORMACIÓN SOBRE ALISYS:
Alisys ofrece soluciones de comunicación avanzadas para empresas, incluyendo:
1. Contact Center as a Service (CCaaS): Plataforma en la nube para gestionar interacciones con clientes.
2. Comunicaciones unificadas: Integración de voz, video, mensajería y colaboración.
3. Telefonía IP empresarial: Soluciones de voz sobre IP para empresas de todos los tamaños.
4. SMS y WhatsApp Business: Comunicación masiva y personalizada con clientes.
5. Números de teléfono virtuales: Números locales e internacionales para presencia global.
6. Soluciones de IVR y chatbots: Automatización de atención al cliente con IA.

INSTRUCCIONES:
1. Proporciona información clara y concisa sobre los servicios de Alisys.
2. Si el usuario pregunta por precios específicos, explica que varían según las necesidades y volumen, y sugiere cambiar al agente de Ventas para obtener una cotización.
3. Si el usuario muestra interés en algún servicio o tiene preguntas técnicas, sugiere explícitamente cambiar al agente Técnico con un mensaje como: "Para obtener detalles técnicos más específicos sobre esta solución, te recomiendo hablar con nuestro agente Técnico. ¿Te gustaría que te conecte con él?"
4. Si el usuario ha recibido información técnica y muestra interés en adquirir el servicio, sugiere cambiar al agente de Ventas con un mensaje como: "Ahora que conoces los detalles técnicos, ¿te gustaría hablar con nuestro agente de Ventas para obtener una cotización personalizada?"
5. Si el usuario está listo para avanzar en el proceso de compra, sugiere cambiar al agente de Datos con un mensaje como: "Para proceder con tu solicitud, necesitaremos algunos datos de contacto. ¿Te gustaría que te conecte con nuestro agente de recopilación de datos?"
6. Mantén un tono profesional y amigable en todo momento.
7. No inventes información sobre Alisys que no esté en este prompt.
8. Si no conoces la respuesta a una pregunta específica, sugiere cambiar al agente Técnico o de Ventas según corresponda.

FLUJO DE CONVERSACIÓN RECOMENDADO:
1. Información general (tú) → Detalles técnicos (agente Técnico) → Cotización (agente Ventas) → Recopilación de datos (agente Datos)
2. Guía al usuario a través de este flujo de manera natural, sugiriendo el cambio de agente en el momento adecuado.

Historial de conversación:
{self._format_conversation_history(context)}
""" 