"""
Agente de ingeniería para el chatbot de Alisys.
Este agente se encarga de proporcionar estimaciones de tiempo y recomendaciones
técnicas para los proyectos.
"""
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

class EngineerAgent(BaseAgent):
    """
    Agente especializado en aspectos técnicos y estimaciones de proyectos.
    """
    
    def __init__(self):
        """
        Inicializa el agente de ingeniería.
        """
        super().__init__(
            name="EngineerAgent",
            description="Especialista en estimación de tiempos y tecnologías para proyectos"
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
        # Palabras clave relacionadas con aspectos técnicos
        tech_keywords = [
            "tecnología", "implementación", "desarrollo", "integración",
            "tiempo", "plazo", "duración", "estimación", "estimar",
            "técnico", "técnica", "arquitectura", "diseño", "requisitos",
            "funcionalidad", "características", "feature", "api", "apis",
            "cómo funciona", "cómo se implementa", "qué tecnología",
            "externa", "externas", "conectar", "conexión", "interfaz",
            "sistema", "plataforma", "software", "hardware", "infraestructura",
            "base de datos", "servidor", "cloud", "nube", "hosting",
            "programación", "código", "algoritmo", "automatización"
        ]
        
        # Frases técnicas completas
        tech_phrases = [
            "conectarme con apis",
            "integración con sistemas",
            "desarrollo de software",
            "implementación técnica",
            "arquitectura de sistema",
            "optimización de procesos",
            "automatización de tareas"
        ]
        
        # Verificar si el mensaje contiene alguna palabra clave técnica
        message_lower = message.lower()
        
        # Verificar palabras clave
        for keyword in tech_keywords:
            if keyword in message_lower:
                return True
        
        # Verificar frases completas
        for phrase in tech_phrases:
            if phrase in message_lower:
                return True
        
        # También manejar si el contexto indica que estamos en fase técnica
        if context.get('current_agent') == self.name:
            return True
        
        # O si el agente anterior fue el base y ahora necesitamos detalles técnicos
        if context.get('previous_agent') == "BaseAgent" and len(context.get('conversation_history', [])) >= 4:
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
        user_info = context.get('user_info', {})
        project_info = context.get('project_info', {})
        
        return f"""Eres un ingeniero experto de Alisys especializado en soluciones tecnológicas.
Tu objetivo es proporcionar estimaciones técnicas precisas y recomendaciones para proyectos.

INSTRUCCIONES:
1. Proporciona explicaciones técnicas claras y concisas sobre las soluciones de Alisys.
2. Estima tiempos de implementación basados en la complejidad del proyecto.
3. Recomienda tecnologías y enfoques específicos para las necesidades del cliente.
4. Explica las ventajas técnicas de las soluciones de Alisys.
5. Si no tienes suficiente información para una estimación precisa, solicita más detalles.
6. Proporciona rangos de tiempo realistas (por ejemplo, "3-4 semanas") en lugar de fechas exactas.
7. Menciona los factores que pueden afectar los tiempos de implementación.
8. Después de proporcionar información técnica detallada, sugiere al usuario hablar con el agente de Ventas para obtener una cotización personalizada con un mensaje como: "Ahora que conoces los detalles técnicos, ¿te gustaría hablar con nuestro agente de Ventas para obtener una cotización personalizada para tu proyecto?"
9. Si el usuario muestra interés en adquirir el servicio o solicita información de precios, sugiere explícitamente cambiar al agente de Ventas.
10. Recuerda que tu función principal es proporcionar información técnica, no cotizaciones o precios específicos.

INFORMACIÓN ESPECÍFICA SOBRE INTEGRACIÓN DE APIS PARA CALL CENTERS:
- Cuando el usuario pregunte sobre integración de APIs para call centers, proporciona información detallada sobre:
  * APIs específicas de Alisys para call centers (REST, SOAP, WebSockets)
  * Capacidades de integración con CRMs, ERPs y otras plataformas de gestión
  * Opciones de integración con sistemas de telefonía IP, VoIP y PBX
  * Automatización de flujos de llamadas mediante APIs
  * Integración con sistemas de análisis de voz y sentiment analysis
  * Opciones para webhooks y callbacks en tiempo real
  * Seguridad y autenticación en las integraciones de APIs
  * Ejemplos concretos de casos de uso para call centers

FLUJO DE CONVERSACIÓN RECOMENDADO:
1. Proporciona detalles técnicos y estimaciones de tiempo → Sugiere cambiar al agente de Ventas para cotización → El agente de Ventas sugerirá cambiar al agente de Datos para finalizar el proceso.
2. Guía al usuario a través de este flujo de manera natural, sugiriendo el cambio de agente en el momento adecuado.

INFORMACIÓN DEL USUARIO:
{self._format_user_info(user_info)}

INFORMACIÓN DEL PROYECTO:
{self._format_project_info(project_info)}

Historial de conversación:
{self._format_conversation_history(context)}
"""
    
    def _format_user_info(self, user_info: Dict[str, Any]) -> str:
        """
        Formatea la información del usuario para incluirla en el prompt.
        
        Args:
            user_info: Información del usuario
            
        Returns:
            Información del usuario formateada
        """
        if not user_info:
            return "No hay información específica del usuario disponible."
        
        formatted_info = ""
        for key, value in user_info.items():
            formatted_key = key.replace('_', ' ').capitalize()
            formatted_info += f"- {formatted_key}: {value}\n"
        
        return formatted_info
    
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