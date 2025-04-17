"""
Clase base para todos los agentes del chatbot de Alisys.
Define la interfaz común y funcionalidad básica que todos los agentes deben implementar.
"""
from typing import Dict, Any, Generator, List, Optional
from abc import ABC, abstractmethod
import traceback
import logging
from services.lm_studio import LMStudioClient
from utils.intent_classifier import classify_intent, detect_agent_change_keywords, get_confidence_explanation

# Configurar logging
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del sistema.
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
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> float:
        """
        Determina si este agente puede manejar el mensaje actual y con qué nivel de confianza.
        Utiliza el clasificador de intenciones para analizar el mensaje y el contexto.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Nivel de confianza entre 0.0 y 1.0
        """
        # Verificar si hay una solicitud explícita de cambio de agente
        explicit_agent = detect_agent_change_keywords(message)
        if explicit_agent:
            # Si se solicita explícitamente este agente, máxima confianza
            if explicit_agent == self.name:
                logger.info(f"Solicitud explícita para cambiar al agente {self.name}")
                return 1.0
            # Si se solicita otro agente, mínima confianza
            return 0.0
        
        # Usar el clasificador de intenciones para obtener puntuaciones
        intent_scores = classify_intent(message, context)
        
        # Obtener la puntuación para este agente
        confidence = intent_scores.get(self.name, 0.1)
        
        # Registrar la explicación para debugging
        if logger.isEnabledFor(logging.DEBUG):
            explanation = get_confidence_explanation(intent_scores, self.name)
            logger.debug(explanation)
        
        # Implementaciones específicas pueden sobrescribir esta función
        # para ajustar la confianza basándose en criterios adicionales
        confidence = self._adjust_confidence(confidence, message, context)
        
        return confidence
    
    def _adjust_confidence(self, base_confidence: float, message: str, context: Dict[str, Any]) -> float:
        """
        Método que pueden sobrescribir las subclases para ajustar la confianza
        basándose en criterios específicos del agente.
        
        Args:
            base_confidence: Confianza base calculada por el clasificador
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Confianza ajustada
        """
        return base_confidence
    
    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        pass
    
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
        
        # Almacenar la respuesta completa para actualizar el contexto después
        full_response = ""
        
        # Generar la respuesta utilizando el LLM
        try:
            # Aplicar ajustes basados en el análisis de sentimiento
            adjusted_system_prompt = self._adjust_prompt_for_sentiment(system_prompt, context)
            
            for chunk in self._generate_response(adjusted_system_prompt, message):
                full_response += chunk
                yield chunk
            
            # Actualizar el contexto con la conversación
            self._update_conversation_history(message, full_response, context)
            
            # Actualizar el agente actual en el contexto
            context['current_agent'] = self.name
            
        except Exception as e:
            # En caso de error, registrar el error completo y devolver un mensaje genérico
            logger.error(f"Error en el agente {self.name}: {str(e)}")
            traceback.print_exc()
            error_message = f"Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
            yield error_message
    
    def _generate_response(self, system_prompt: str, message: str) -> Generator[str, None, None]:
        """
        Método auxiliar para generar la respuesta del LLM.
        
        Args:
            system_prompt: Prompt del sistema
            message: Mensaje del usuario
            
        Returns:
            Generador que produce la respuesta del modelo
        """
        return self.lm_client.generate_stream(system_prompt, message)
    
    def _update_conversation_history(self, user_message: str, assistant_response: str, context: Dict[str, Any]) -> None:
        """
        Actualiza el historial de conversación en el contexto.
        
        Args:
            user_message: Mensaje del usuario
            assistant_response: Respuesta completa del asistente
            context: Contexto a actualizar
        """
        if 'conversation_history' not in context:
            context['conversation_history'] = []
        
        # Añadir el mensaje del usuario
        context['conversation_history'].append({
            'role': 'user',
            'content': user_message
        })
        
        # Añadir la respuesta del asistente
        context['conversation_history'].append({
            'role': 'assistant',
            'content': assistant_response
        })
    
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

    def _adjust_prompt_for_sentiment(self, system_prompt: str, context: Dict[str, Any]) -> str:
        """
        Ajusta el prompt del sistema según el análisis de sentimiento del mensaje.
        
        Args:
            system_prompt: Prompt original del sistema
            context: Contexto de la conversación
            
        Returns:
            Prompt ajustado
        """
        # Verificar si hay análisis de sentimiento en el contexto
        if 'current_sentiment' not in context:
            return system_prompt
            
        sentiment = context['current_sentiment']
        
        # Obtener emoción dominante y polaridad
        dominant_emotion = sentiment.get('dominant_emotion')
        polarity = sentiment.get('polarity', 0)
        urgency = sentiment.get('urgency', 0)
        
        # Generar instrucciones adicionales basadas en el sentimiento
        sentiment_instructions = []
        
        if dominant_emotion:
            if dominant_emotion == 'alegria':
                sentiment_instructions.append("El usuario muestra un tono positivo. Mantén un tono animado y refuerza esta actitud positiva.")
            elif dominant_emotion == 'tristeza':
                sentiment_instructions.append("El usuario muestra un tono triste o decepcionado. Usa un tono empático y comprensivo.")
            elif dominant_emotion == 'enojo':
                sentiment_instructions.append("El usuario muestra frustración o enojo. Mantén la calma, no uses un tono defensivo y centra tu respuesta en soluciones concretas.")
            elif dominant_emotion == 'miedo':
                sentiment_instructions.append("El usuario muestra preocupación o ansiedad. Usa un tono tranquilizador y ofrece información clara y precisa.")
            elif dominant_emotion == 'confusión':
                sentiment_instructions.append("El usuario muestra confusión. Estructura tu respuesta de manera clara y simple, evitando términos técnicos innecesarios.")
        
        # Verificar polaridad
        if polarity < -0.5:
            sentiment_instructions.append("El usuario muestra una actitud muy negativa. Enfoca tu respuesta en ofrecer soluciones concretas y alternativas.")
        elif polarity > 0.5:
            sentiment_instructions.append("El usuario muestra una actitud muy positiva. Refuerza esta actitud en tu respuesta.")
        
        # Verificar urgencia
        if urgency > 0.7:
            sentiment_instructions.append("El usuario muestra urgencia en su consulta. Prioriza la eficiencia en tu respuesta y ofrece soluciones inmediatas cuando sea posible.")
        
        # Si no hay instrucciones específicas, no modificar el prompt
        if not sentiment_instructions:
            return system_prompt
        
        # Agregar instrucciones al prompt original
        sentiment_block = "\n\nINSTRUCCIONES ADICIONALES BASADAS EN EL SENTIMIENTO DEL USUARIO:\n"
        sentiment_block += "\n".join(f"- {instruction}" for instruction in sentiment_instructions)
        
        return system_prompt + sentiment_block 