"""
Clase base para todos los agentes del chatbot de Alisys.
Define la interfaz común y funcionalidad básica que todos los agentes deben implementar.
"""
from typing import Dict, Any, Generator, List, Optional
from services.lm_studio import LMStudioClient

class BaseAgent:
    """
    Clase base para todos los agentes del sistema.
    Proporciona la estructura común y métodos que todos los agentes deben implementar.
    """
    
    def __init__(self, name: str, description: str):
        """
        Inicializa un nuevo agente.
        
        Args:
            name: Nombre único del agente
            description: Descripción breve de la función del agente
        """
        self.name = name
        self.description = description
        self.lm_client = LMStudioClient()
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determina si este agente puede manejar el mensaje actual.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            True si el agente puede manejar el mensaje, False en caso contrario
        """
        # Implementación por defecto, los agentes concretos deben sobrescribir este método
        return False
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        # Implementación por defecto, los agentes concretos deben sobrescribir este método
        return f"""Eres un asistente de Alisys, una empresa especializada en soluciones de comunicación.
Tu objetivo es proporcionar información clara y precisa sobre los servicios de Alisys.

Historial de conversación:
{self._format_conversation_history(context)}
"""
    
    def process(self, message: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Procesa el mensaje del usuario y genera una respuesta.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Generador que produce la respuesta del agente
        """
        # Obtener el prompt del sistema
        system_prompt = self.get_system_prompt(context)
        
        # Generar la respuesta utilizando el LLM
        try:
            for chunk in self.lm_client.generate_stream(system_prompt, message):
                yield chunk
            
            # Actualizar el contexto con la respuesta generada
            if 'conversation_history' not in context:
                context['conversation_history'] = []
            
            # Añadir la respuesta al historial de conversación
            context['conversation_history'].append({
                'role': 'assistant',
                'content': message  # En una implementación real, esto sería la respuesta completa
            })
            
            # Actualizar el agente actual en el contexto
            context['current_agent'] = self.name
            
        except Exception as e:
            # En caso de error, devolver un mensaje genérico
            error_message = f"Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
            yield error_message
    
    def _format_conversation_history(self, context: Dict[str, Any]) -> str:
        """
        Formatea el historial de conversación para incluirlo en el prompt.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Historial de conversación formateado
        """
        history = context.get('conversation_history', [])
        if not history:
            return "No hay historial de conversación disponible."
        
        formatted_history = ""
        for i, message in enumerate(history[-5:]):  # Mostrar solo los últimos 5 mensajes
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            formatted_history += f"{role.capitalize()}: {content}\n"
        
        return formatted_history 