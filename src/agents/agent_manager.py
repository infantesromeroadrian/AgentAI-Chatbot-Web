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
        # Inicializar contexto si no existe
        if context is None:
            context = {}
        
        # Detección rápida de preguntas sobre servicios o información general
        message_lower = message.lower()
        service_info_patterns = [
            'qué servicios', 'que servicios', 'qué ofrece', 'que ofrece',
            'qué hace', 'que hace', 'información sobre', 'informacion sobre',
            'cuáles son', 'cuales son', 'qué es', 'que es'
        ]
        
        # Si es una pregunta sobre servicios, forzar el uso del GeneralAgent
        is_service_question = any(pattern in message_lower for pattern in service_info_patterns)
        if is_service_question:
            for agent in self.agents:
                if agent.__class__.__name__ == 'GeneralAgent':
                    logger.info("Pregunta sobre servicios detectada, utilizando GeneralAgent")
                    return agent
        
        # Verificar si hay una solicitud explícita de cambio de agente
        explicit_agent = detect_agent_change_keywords(message)
        if explicit_agent:
            for agent in self.agents:
                if agent.__class__.__name__ == explicit_agent:
                    logger.info(f"Cambio explícito al agente: {explicit_agent}")
                    # Actualizar el historial con el cambio de agente
                    if 'history' in context:
                        context['history'].append({
                            'message': message,
                            'agent': explicit_agent,
                            'confidence': 1.0,
                            'reason': 'Selección explícita del usuario'
                        })
                    return agent
        
        # Calcular puntuaciones de confianza para cada agente
        agent_scores = {}
        for agent in self.agents:
            agent_name = agent.__class__.__name__
            confidence = agent.can_handle(message, context)
            agent_scores[agent_name] = confidence
            logger.debug(f"Agente {agent_name}: puntuación {confidence}")
        
        # Encontrar el agente con la mayor puntuación
        max_confidence = -1
        selected_agent = None
        selected_agent_name = None
        
        # Umbrales específicos por agente (ajustados para mayor consistencia)
        thresholds = {
            'DataCollectionAgent': 0.55,  # Umbral reducido para el agente de recopilación de datos
            'SalesAgent': 0.5,           # Umbrales reducidos
            'EngineerAgent': 0.5,
            'GeneralAgent': 0.4          # El GeneralAgent puede tener un umbral más bajo
        }
        
        for agent in self.agents:
            agent_name = agent.__class__.__name__
            confidence = agent_scores.get(agent_name, 0)
            
            # Obtener umbral específico o usar valor predeterminado
            threshold = thresholds.get(agent_name, 0.5)
            
            if confidence > max_confidence and confidence >= threshold:
                max_confidence = confidence
                selected_agent = agent
                selected_agent_name = agent_name
        
        # Si ningún agente supera su umbral, usar el agente de respaldo (GeneralAgent)
        if not selected_agent:
            logger.info("Ningún agente supera el umbral. Usando agente de respaldo.")
            for agent in self.agents:
                if agent.__class__.__name__ == 'GeneralAgent':
                    selected_agent = agent
                    selected_agent_name = 'GeneralAgent'
                    break
        
        # Registrar la selección para el historial
        if 'history' in context and selected_agent_name:
            context['history'].append({
                'message': message,
                'agent': selected_agent_name,
                'confidence': max_confidence,
                'reason': 'Selección automática por puntuación'
            })
        
        logger.info(f"Agente seleccionado: {selected_agent_name} con confianza {max_confidence}")
        return selected_agent
    
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
        
        # Verificar si se debe forzar el uso del EngineerAgent (nuevo)
        if working_context.get('force_engineer', False):
            # Buscar directamente el EngineerAgent
            logger.info("Forzando el uso del EngineerAgent por flag force_engineer")
            agent = next((a for a in self.agents if a.__class__.__name__ == 'EngineerAgent'), None)
            # Actualizar contexto
            if agent:
                working_context['current_agent'] = 'EngineerAgent'
            # Si no se encuentra el EngineerAgent, usar el flujo normal
            if not agent:
                logger.warning("No se encontró EngineerAgent a pesar de force_engineer=True")
                agent = self.select_agent(message, working_context)
        # Verificar si se debe forzar el uso del SalesAgent
        elif working_context.get('force_sales', False):
            # Buscar directamente el SalesAgent
            logger.info("Forzando el uso del SalesAgent por flag force_sales")
            agent = next((a for a in self.agents if a.__class__.__name__ == 'SalesAgent'), None)
            # Actualizar contexto
            if agent:
                working_context['current_agent'] = 'SalesAgent'
            # Si no se encuentra el SalesAgent, usar el flujo normal
            if not agent:
                logger.warning("No se encontró SalesAgent a pesar de force_sales=True")
                agent = self.select_agent(message, working_context)
        else:
            # Verificar si estamos en una conversación técnica en progreso
            tech_keywords = [
                'proyecto', 'implementar', 'desarrollar', 'integrar', 'call center', 'centro de llamadas',
                'ai', 'ia', 'inteligencia artificial', 'automatizar', 'automatización', 'automatizacion',
                'sistema', 'solución', 'solucion', 'migrar', 'migración', 'migracion', 'plataforma'
            ]
            
            # Palabras clave más específicas para proyectos de call center con IA
            call_center_ai_keywords = [
                'call center', 'centro de llamadas', 'contact center', 'gestiona llamadas', 
                'gestionar llamadas', 'mi proyecto es', 'pasarlo a agentes de ai', 
                'agentes virtuales', 'ia', 'ai', 'inteligencia artificial', 'bot', 'chatbot'
            ]
            
            message_lower = message.lower()
            
            # Obtener el agente actual del contexto
            current_agent_name = working_context.get('current_agent')
            
            # Verificar si estamos en casos que requieren forzar EngineerAgent
            force_engineer_agent = False
            
            # Caso 1: Ya estamos en una conversación técnica con EngineerAgent
            if current_agent_name == 'EngineerAgent' and any(keyword in message_lower for keyword in tech_keywords):
                force_engineer_agent = True
                logger.info("Manteniendo EngineerAgent para conversación técnica en curso")
            
            # Caso 2: Mensaje contiene palabras clave específicas de proyectos de call center con IA
            if any(keyword in message_lower for keyword in call_center_ai_keywords):
                # Verificar si hay combinaciones de palabras clave que indiquen claramente un proyecto técnico
                if ('proyecto' in message_lower and any(kw in message_lower for kw in ['call center', 'ai', 'ia'])) or \
                   ('mi proyecto' in message_lower) or \
                   ('call center' in message_lower and any(kw in message_lower for kw in ['ai', 'ia', 'inteligencia'])):
                    force_engineer_agent = True
                    logger.info("Forzando EngineerAgent para proyecto de call center con IA")
            
            # Obtener el agente adecuado
            if force_engineer_agent:
                # Forzar el uso del EngineerAgent
                agent = next((a for a in self.agents if a.__class__.__name__ == 'EngineerAgent'), None)
                if agent:
                    # Actualizar explícitamente el agente actual en el contexto
                    working_context['current_agent'] = 'EngineerAgent'
                else:
                    # Usar selección normal si no se encuentra el EngineerAgent
                    agent = self.select_agent(message, working_context)
            else:
                # Verificar si estamos en una conversación de ventas con mensajes cortos
                sales_keywords = ['precio', 'costo', 'presupuesto', 'cotización', 'cotizacion']
                is_sales_conversation = (
                    current_agent_name == 'SalesAgent' and
                    (len(message.split()) <= 3 or any(keyword in message.lower() for keyword in sales_keywords))
                )
                
                if is_sales_conversation:
                    # Mantener el agente de ventas para mensajes cortos o relacionados con ventas
                    agent = next((a for a in self.agents if a.__class__.__name__ == 'SalesAgent'), None)
                    logger.info("Manteniendo SalesAgent para mensaje corto o relacionado con ventas")
                else:
                    # Utilizar la selección normal basada en confianza
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
            # Actualizar el agente actual en el contexto
            context['current_agent'] = agent.__class__.__name__
            
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