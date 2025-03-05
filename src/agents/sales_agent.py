"""
Agente de ventas para el chatbot de Alisys.
Este agente se encarga de proporcionar información sobre precios, planes y
cotizaciones para los servicios de Alisys.
"""
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class SalesAgent(BaseAgent):
    """
    Agente especializado en ventas y cotizaciones.
    """
    
    def __init__(self):
        """
        Inicializa el agente de ventas.
        """
        super().__init__(
            name="SalesAgent",
            description="Especialista en cotizaciones y precios de servicios"
        )
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determina si este agente puede manejar el mensaje actual.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            True si el agente puede manejar el mensaje, False en caso contrario
        """
        # Palabras clave relacionadas con ventas y precios
        sales_keywords = [
            "precio", "costo", "cotización", "cotizar", "presupuesto",
            "cuánto cuesta", "cuanto vale", "tarifa", "pagar", "inversión",
            "económico", "barato", "caro", "descuento", "oferta", "promoción",
            "plan", "paquete", "contratar", "adquirir", "comprar",
            "representante", "comercial", "ventas", "contactar", "contacto",
            "llamar", "llamada", "asesor", "asesoría", "consultor"
        ]
        
        # Frases completas que indican interés en ventas
        sales_phrases = [
            "me gustaría recibir una cotización",
            "quiero que me contacten",
            "necesito hablar con un representante",
            "me gustaría más información",
            "pueden contactarme",
            "me interesa contratar"
        ]
        
        # Verificar si el mensaje contiene alguna palabra clave de ventas
        message_lower = message.lower()
        
        # Verificar palabras clave
        for keyword in sales_keywords:
            if keyword in message_lower:
                return True
        
        # Verificar frases completas
        for phrase in sales_phrases:
            if phrase in message_lower:
                return True
        
        # También manejar si el contexto indica que estamos en fase de ventas
        if context.get('current_agent') == self.name:
            return True
        
        # O si el agente anterior fue el ingeniero y ahora necesitamos cotizar
        if context.get('previous_agent') == "EngineerAgent":
            return True
        
        return False
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        # Extraer información relevante del contexto
        project_info = context.get('project_info', {})
        
        return f"""Eres un experto en ventas de Alisys, una empresa líder en soluciones tecnológicas innovadoras.
Tu objetivo es proporcionar cotizaciones precisas y persuasivas para los servicios de Alisys.

INSTRUCCIONES:
1. Proporciona información clara sobre precios y planes de los servicios de Alisys.
2. Destaca el valor y los beneficios de los servicios, no solo el precio.
3. Adapta tus recomendaciones a las necesidades específicas del cliente.
4. Menciona ventajas competitivas de Alisys frente a otras alternativas.
5. Si no tienes información suficiente para una cotización precisa, solicita más detalles.
6. Ofrece diferentes opciones o planes cuando sea posible.
7. Menciona que estas cotizaciones son estimaciones iniciales y pueden ajustarse.
8. Después de proporcionar una cotización o cuando el usuario muestre interés en avanzar, sugiere explícitamente cambiar al agente de Datos con un mensaje como: "Para proceder con tu solicitud y que un representante pueda contactarte con una propuesta formal, necesitaremos algunos datos de contacto. ¿Te gustaría que te conecte con nuestro agente de recopilación de datos?"
9. Si el usuario solicita más información técnica, sugiere volver al agente Técnico.
10. Recuerda que tu función principal es proporcionar cotizaciones y cerrar ventas, no detalles técnicos profundos.

FLUJO DE CONVERSACIÓN RECOMENDADO:
1. Proporciona cotizaciones y opciones de precios → Sugiere cambiar al agente de Datos para finalizar el proceso y que un representante contacte al cliente.
2. Guía al usuario a través de este flujo de manera natural, sugiriendo el cambio de agente en el momento adecuado.

INFORMACIÓN DEL PROYECTO:
{self._format_project_info(project_info)}

Historial de conversación:
{self._format_conversation_history(context)}
"""
    
    def _format_project_info(self, project_info: Dict[str, Any]) -> str:
        """
        Formatea la información del proyecto para incluirla en el prompt.
        
        Args:
            project_info: Información del proyecto
            
        Returns:
            Información del proyecto formateada
        """
        if not project_info:
            return "No hay información específica del proyecto disponible."
        
        formatted_info = ""
        for key, value in project_info.items():
            formatted_key = key.replace('_', ' ').capitalize()
            formatted_info += f"- {formatted_key}: {value}\n"
        
        return formatted_info 