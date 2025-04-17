"""
Gestor de agentes para el chatbot de Alisys.
Se encarga de seleccionar el agente adecuado para cada mensaje y coordinar
la interacción entre ellos.
"""
from typing import Dict, List, Any, Optional, Generator, Tuple
import traceback
import logging
import uuid
from .base_agent import BaseAgent
from utils.intent_classifier import get_confidence_explanation, detect_agent_change_keywords
from utils.context_manager import ContextPersistenceManager
from utils.sentiment_analyzer import SentimentAnalyzer

# Configurar logging
logger = logging.getLogger(__name__)

class AgentManager:
    """
    Gestor de agentes que coordina la selección y ejecución de agentes.
    """
    
    def __init__(self):
        """
        Inicializa el gestor de agentes.
        """
        self.agents = []
        self.current_agent = None
        self.context = {
            'conversation_history': [],
            'messages': [],
            'user_info': {},
            'project_info': {},
            'current_agent': None,
            'previous_agent': None,
            'agent_selection_history': [],  # Historial de selecciones de agentes
            'sentiment_history': [],        # Historial de análisis de sentimiento
            'session_id': str(uuid.uuid4())  # ID único para la sesión
        }
        
        # Inicializar componentes
        self.context_manager = ContextPersistenceManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        logger.info(f"AgentManager inicializado. Session ID: {self.context['session_id']}")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Registra un nuevo agente en el sistema.
        
        Args:
            agent: El agente a registrar
        """
        self.agents.append(agent)
        logger.info(f"Agente registrado: {agent.name} - {agent.description}")
    
    def select_agent(self, message: str, context: Dict[str, Any] = None) -> Optional[BaseAgent]:
        """
        Selecciona el agente más adecuado para manejar el mensaje.
        
        Args:
            message: El mensaje del usuario
            context: Contexto para la selección (opcional)
            
        Returns:
            El agente seleccionado o None si no hay agentes disponibles
        """
        # Usar el contexto proporcionado o el interno
        working_context = context if context is not None else self.context
        
        # Si no hay agentes registrados, devolver None
        if not self.agents:
            logger.warning("No hay agentes registrados para seleccionar")
            return None
        
        # Si solo hay un agente, devolverlo
        if len(self.agents) == 1:
            logger.info(f"Solo hay un agente disponible: {self.agents[0].name}")
            return self.agents[0]
        
        # Verificar si hay una solicitud explícita de cambio de agente
        # Esta es la prioridad más alta, siempre debe respetarse
        explicit_agent_name = detect_agent_change_keywords(message)
        if explicit_agent_name:
            agent = self._get_agent_by_name(explicit_agent_name)
            if agent:
                logger.info(f"Cambio explícito de agente solicitado: {explicit_agent_name}")
                self._update_agent_selection(agent, 1.0, working_context, "Solicitud explícita del usuario")
                return agent
            else:
                logger.warning(f"Se solicitó el agente {explicit_agent_name} pero no está disponible")
                # Si se solicitó un agente que no existe, continuar con el proceso normal
        
        # Para respuestas cortas como "sí", "no", etc., mantener el agente actual
        if len(message.strip()) <= 5:
            current_agent_name = working_context.get('current_agent')
            current_agent = self._get_agent_by_name(current_agent_name)
            if current_agent:
                logger.info(f"Mensaje corto, manteniendo agente actual: {current_agent.name}")
                self._update_agent_selection(current_agent, 0.8, working_context, "Mensaje corto")
                return current_agent
        
        # Intentar obtener agente por nombre específico en el contexto
        current_agent_name = working_context.get('current_agent')
        if current_agent_name:
            current_agent = self._get_agent_by_name(current_agent_name)
            # Verificar si el agente actual puede seguir manejando el mensaje
            if current_agent:
                confidence = current_agent.can_handle(message, working_context)
                if confidence >= 0.5:  # Umbral para mantener el mismo agente
                    logger.info(f"Manteniendo el agente actual: {current_agent.name} con confianza {confidence:.2f}")
                    self._update_agent_selection(current_agent, confidence, working_context, "Continuidad de conversación")
                    return current_agent
        
        # Seleccionar el mejor agente basado en confianza
        best_agent, best_confidence = self._select_agent_with_highest_confidence(message, working_context)
        
        if best_agent and best_confidence > 0.3:  # Umbral mínimo de confianza
            logger.info(f"Mejor agente seleccionado: {best_agent.name} con confianza {best_confidence:.2f}")
            self._update_agent_selection(best_agent, best_confidence, working_context, "Mayor confianza")
            return best_agent
        
        # Si ningún agente supera el umbral, usar el agente de fallback
        fallback = self._get_fallback_agent()
        logger.info(f"Usando agente de fallback: {fallback.name}")
        self._update_agent_selection(fallback, 0.2, working_context, "Fallback por baja confianza")
        return fallback
    
    def _update_agent_selection(self, agent: BaseAgent, confidence: float, context: Dict[str, Any], reason: str) -> None:
        """
        Actualiza el contexto con la selección de agente y registra la información.
        
        Args:
            agent: Agente seleccionado
            confidence: Nivel de confianza
            context: Contexto a actualizar
            reason: Razón de la selección
        """
        # Actualizar el agente actual y anterior en el contexto
        context['previous_agent'] = context.get('current_agent')
        context['current_agent'] = agent.name
        
        # Registrar la selección en el historial
        if 'agent_selection_history' not in context:
            context['agent_selection_history'] = []
            
        context['agent_selection_history'].append({
            'agent': agent.name,
            'confidence': confidence,
            'reason': reason,
            'message_count': context.get('message_count', 0)
        })
        
        # Actualizar el agente actual en el gestor
        self.current_agent = agent
    
    def _get_agent_by_name(self, agent_name: Optional[str]) -> Optional[BaseAgent]:
        """
        Busca un agente por su nombre.
        
        Args:
            agent_name: Nombre del agente a buscar
            
        Returns:
            El agente si se encuentra, None en caso contrario
        """
        if not agent_name:
            return None
            
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        
        logger.warning(f"No se encontró el agente con nombre: {agent_name}")
        return None
    
    def _select_agent_with_highest_confidence(self, message: str, context: Dict[str, Any]) -> Tuple[Optional[BaseAgent], float]:
        """
        Selecciona el agente con mayor confianza para el mensaje.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Tupla con el mejor agente y su nivel de confianza
        """
        best_agent = None
        best_confidence = 0.0
        
        # Recopilar confianzas para debugging
        all_confidences = {}
        
        for agent in self.agents:
            # Obtener confianza del agente para este mensaje
            confidence = agent.can_handle(message, context)
            all_confidences[agent.name] = confidence
            
            # Actualizar si este es el mejor hasta ahora
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent
        
        # Registrar todas las confianzas para debugging
        if logger.isEnabledFor(logging.DEBUG):
            confidence_str = ", ".join([f"{name}: {conf:.2f}" for name, conf in sorted(
                all_confidences.items(), key=lambda x: x[1], reverse=True)])
            logger.debug(f"Confianzas de agentes: {confidence_str}")
        
        return best_agent, best_confidence
    
    def _get_fallback_agent(self) -> BaseAgent:
        """
        Obtiene el agente de respaldo cuando ninguno tiene confianza suficiente.
        Por defecto, el GeneralAgent es el agente de respaldo.
        
        Returns:
            Agente de respaldo
        """
        # Buscar GeneralAgent por nombre
        for agent in self.agents:
            if agent.name == "GeneralAgent":
                return agent
        
        # Si no hay GeneralAgent, usar el último agente registrado
        return self.agents[-1]
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Generator[str, None, None]:
        """
        Procesa un mensaje seleccionando el agente adecuado.
        
        Args:
            message: El mensaje del usuario
            context: Contexto externo para el procesamiento (opcional)
            
        Returns:
            Un generador que produce la respuesta del agente
        """
        # Actualizar contexto y añadir el mensaje
        working_context = self._prepare_context(message, context)
        
        # Obtener el agente adecuado
        agent = self.select_agent(message, working_context)
        
        if not agent:
            # Si no hay agente disponible, devolver un mensaje de error
            error_message = "No hay agentes disponibles para procesar tu mensaje."
            logger.error("No se encontró ningún agente para procesar el mensaje")
            yield error_message
            
            # Añadir el mensaje de error al historial
            working_context['messages'].append({
                'role': 'assistant',
                'content': error_message
            })
            
            return
        
        # Registrar el cambio de agente
        logger.info(f"Procesando mensaje con el agente: {agent.name}")
        
        # Procesar el mensaje y capturar la respuesta
        response = yield from self._process_with_agent(agent, message, working_context)
        
        # Actualizar el contexto compartido
        self._update_shared_context(working_context)
        
        return response
    
    def _prepare_context(self, message: str, external_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepara y unifica el contexto para el procesamiento.
        
        Args:
            message: El mensaje del usuario
            external_context: Contexto externo opcional
            
        Returns:
            El contexto unificado
        """
        # Usar el contexto proporcionado o el interno
        if external_context is not None:
            # Actualizar el contexto interno con valores del externo
            self.context.update({
                'current_agent': external_context.get('current_agent', self.context.get('current_agent')),
                'previous_agent': external_context.get('previous_agent', self.context.get('previous_agent')),
                'user_info': external_context.get('user_info', self.context.get('user_info', {})),
                'project_info': external_context.get('project_info', self.context.get('project_info', {})),
                'messages': external_context.get('messages', self.context.get('messages', []))
            })
            # Usar el contexto externo para el procesamiento
            working_context = external_context
            
            # Asegurar que el contexto externo tiene un session_id
            if 'session_id' not in working_context:
                working_context['session_id'] = self.context.get('session_id', str(uuid.uuid4()))
        else:
            working_context = self.context
        
        # Inicializar el historial de mensajes si no existe
        if 'messages' not in working_context:
            working_context['messages'] = []
        
        # Actualizar contador de mensajes (importante para la selección de agente)
        if 'message_count' not in working_context:
            working_context['message_count'] = 0
        working_context['message_count'] += 1
        
        # Analizar sentimiento del mensaje
        sentiment_analysis = self.sentiment_analyzer.analyze(message)
        
        # Almacenar análisis de sentimiento en el historial
        if 'sentiment_history' not in working_context:
            working_context['sentiment_history'] = []
            
        working_context['sentiment_history'].append({
            'message': message,
            'analysis': sentiment_analysis,
            'message_index': working_context['message_count']
        })
        
        # Almacenar el análisis actual para uso inmediato
        working_context['current_sentiment'] = sentiment_analysis
        
        # Añadir el mensaje del usuario al historial
        working_context['messages'].append({
            'role': 'user',
            'content': message,
            'sentiment': sentiment_analysis
        })
        
        # Registrar información del contexto para debugging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Contexto preparado: mensaje #{working_context['message_count']}, " +
                        f"agente actual: {working_context.get('current_agent')}, " +
                        f"emoción dominante: {sentiment_analysis.get('dominant_emotion')}")
        
        return working_context
    
    def _process_with_agent(self, agent: BaseAgent, message: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Procesa el mensaje con un agente específico.
        
        Args:
            agent: El agente a utilizar
            message: El mensaje del usuario
            context: Contexto de procesamiento
            
        Returns:
            Un generador con la respuesta del agente
        """
        try:
            # Procesar el mensaje con el agente
            full_response = ""
            for chunk in agent.process(message, context):
                full_response += chunk
                yield chunk
            
            # Añadir la respuesta al historial de mensajes
            context['messages'].append({
                'role': 'assistant',
                'content': full_response
            })
            
            # Guardar el contexto actualizado para persistencia
            user_id = context.get('user_id', 'anonymous')
            self.context_manager.save_context(user_id, context)
            logger.info(f"Contexto guardado para usuario {user_id} después de la respuesta")
            
            return full_response
        except Exception as e:
            # En caso de error, registrar y devolver un mensaje genérico
            logger.error(f"Error al procesar mensaje con el agente {agent.name}: {str(e)}")
            traceback.print_exc()
            
            error_message = "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
            yield error_message
            
            # Añadir el mensaje de error al historial
            context['messages'].append({
                'role': 'assistant',
                'content': error_message
            })
            
            return error_message
    
    def _update_shared_context(self, context: Dict[str, Any]) -> None:
        """
        Actualiza el contexto interno con información compartida entre agentes.
        
        Args:
            context: El contexto actualizado por el agente
        """
        # Actualizar información del usuario
        if 'user_info' in context:
            self.context['user_info'].update(context['user_info'])
        
        # Actualizar información del proyecto
        if 'project_info' in context:
            self.context['project_info'].update(context['project_info'])
        
        # Actualizar historial de selección de agentes
        if 'agent_selection_history' in context:
            self.context['agent_selection_history'] = context['agent_selection_history']
    
    def load_session(self, user_id: str) -> bool:
        """
        Carga una sesión anterior para un usuario específico.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            # Cargar el contexto desde el almacenamiento
            loaded_context = self.context_manager.load_context(user_id)
            
            if not loaded_context:
                logger.warning(f"No se encontró contexto para el usuario {user_id}")
                return False
            
            # Actualizar el contexto interno con los datos cargados
            self.context.update(loaded_context)
            
            # Restaurar el agente actual si está disponible
            current_agent_name = self.context.get('current_agent')
            if current_agent_name:
                self.current_agent = self._get_agent_by_name(current_agent_name)
            
            logger.info(f"Sesión cargada para usuario {user_id}, {len(self.context.get('messages', []))} mensajes recuperados")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar sesión para usuario {user_id}: {str(e)}")
            return False
    
    def save_session(self, user_id: str) -> bool:
        """
        Guarda explícitamente la sesión actual para un usuario.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Actualizar el ID de usuario en el contexto
            self.context['user_id'] = user_id
            
            # Guardar el contexto actual
            result = self.context_manager.save_context(user_id, self.context)
            
            if result:
                logger.info(f"Sesión guardada explícitamente para usuario {user_id}")
            else:
                logger.warning(f"No se pudo guardar la sesión para usuario {user_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al guardar sesión para usuario {user_id}: {str(e)}")
            return False
    
    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lista todas las sesiones disponibles para un usuario.
        
        Args:
            user_id: Identificador del usuario
            
        Returns:
            Lista de metadatos de sesiones
        """
        return self.context_manager.list_user_sessions(user_id)

    def reset(self) -> None:
        """
        Reinicia el estado del gestor de agentes.
        """
        # Guardar el user_id para mantener referencia
        user_id = self.context.get('user_id', 'anonymous')
        
        # Reiniciar el contexto
        self.current_agent = None
        self.context = {
            'conversation_history': [],
            'messages': [],
            'user_info': {},
            'project_info': {},
            'current_agent': None,
            'previous_agent': None,
            'agent_selection_history': [],
            'sentiment_history': [],
            'session_id': str(uuid.uuid4()),
            'user_id': user_id  # Mantener el ID de usuario
        }
        
        logger.info(f"AgentManager reiniciado. Nueva session ID: {self.context['session_id']}") 