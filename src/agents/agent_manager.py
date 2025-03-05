"""
Gestor de agentes para el chatbot de Alisys.
Se encarga de seleccionar el agente adecuado para cada mensaje y coordinar
la interacción entre ellos.
"""
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

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
            'user_info': {},
            'project_info': {},
            'current_agent': None,
            'previous_agent': None
        }
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Registra un nuevo agente en el sistema.
        
        Args:
            agent: El agente a registrar
        """
        self.agents.append(agent)
    
    def select_agent(self, message: str, context: Dict[str, Any] = None) -> BaseAgent:
        """
        Selecciona el agente más adecuado para manejar el mensaje.
        
        Args:
            message: El mensaje del usuario
            context: Contexto para la selección (opcional)
            
        Returns:
            El agente seleccionado
        """
        # Usar el contexto proporcionado o el interno
        working_context = context if context is not None else self.context
        
        # Si no hay agentes registrados, devolver None
        if not self.agents:
            return None
        
        # Si solo hay un agente, devolverlo
        if len(self.agents) == 1:
            return self.agents[0]
        
        # Verificar si hay un agente específico en el contexto
        specified_agent_name = working_context.get('current_agent')
        
        if specified_agent_name:
            # Buscar el agente por nombre
            for agent in self.agents:
                if agent.name == specified_agent_name:
                    # Actualizar el agente actual
                    self.current_agent = agent
                    return agent
        
        # Si hay un agente actual y puede seguir manejando el mensaje, mantenerlo
        if self.current_agent and self.current_agent.can_handle(message, working_context):
            # Actualizar el contexto
            working_context['current_agent'] = self.current_agent.name
            return self.current_agent
        
        # Buscar el agente con mayor confianza para manejar el mensaje
        best_agent = None
        best_confidence = 0.0
        
        for agent in self.agents:
            # Verificar si el agente puede manejar el mensaje
            can_handle = agent.can_handle(message, working_context)
            
            # Si el agente puede manejar el mensaje, calcular su confianza
            if can_handle:
                # Si can_handle devuelve un booleano, convertirlo a un valor de confianza
                confidence = 1.0 if isinstance(can_handle, bool) else float(can_handle)
                
                # Si este agente tiene mayor confianza que el mejor hasta ahora, actualizarlo
                if confidence > best_confidence:
                    best_agent = agent
                    best_confidence = confidence
        
        # Si se encontró un agente adecuado, actualizarlo como el agente actual
        if best_agent:
            # Actualizar el agente actual y el anterior en el contexto
            working_context['previous_agent'] = working_context.get('current_agent')
            working_context['current_agent'] = best_agent.name
            self.current_agent = best_agent
            return best_agent
        
        # Si ningún agente puede manejar el mensaje, usar el último como fallback
        self.current_agent = self.agents[-1]  # Usar el último agente (WelcomeAgent) como fallback
        working_context['current_agent'] = self.current_agent.name
        return self.current_agent
    
    def process_message(self, message: str, context: Dict[str, Any] = None):
        """
        Procesa un mensaje seleccionando el agente adecuado.
        
        Args:
            message: El mensaje del usuario
            context: Contexto externo para el procesamiento (opcional)
            
        Returns:
            Un generador que produce la respuesta del agente
        """
        # Usar el contexto proporcionado o el interno
        if context is not None:
            # Actualizar el contexto interno con valores del externo
            self.context.update({
                'current_agent': context.get('current_agent', self.context.get('current_agent')),
                'previous_agent': context.get('previous_agent', self.context.get('previous_agent')),
                'user_info': context.get('user_info', self.context.get('user_info', {})),
                'project_info': context.get('project_info', self.context.get('project_info', {})),
                'messages': context.get('messages', self.context.get('messages', []))
            })
            # Usar el contexto externo para el procesamiento
            working_context = context
        else:
            working_context = self.context
        
        # Inicializar el historial de mensajes si no existe
        if 'messages' not in working_context:
            working_context['messages'] = []
        
        # Añadir el mensaje del usuario al historial
        working_context['messages'].append({
            'role': 'user',
            'content': message
        })
        
        # Verificar si hay un agente específico en el contexto
        specified_agent_name = working_context.get('current_agent')
        
        if specified_agent_name:
            # Buscar el agente por nombre
            specified_agent = None
            for agent in self.agents:
                if agent.name == specified_agent_name:
                    specified_agent = agent
                    break
            
            # Si se encontró el agente especificado, usarlo
            if specified_agent:
                self.current_agent = specified_agent
                
                # Procesar el mensaje con el agente especificado
                response_generator = specified_agent.process(message, working_context)
                
                # Capturar la respuesta completa para añadirla al historial
                full_response = ""
                for chunk in response_generator:
                    full_response += chunk
                    yield chunk
                
                # Añadir la respuesta al historial de mensajes
                working_context['messages'].append({
                    'role': 'assistant',
                    'content': full_response
                })
                
                return
        
        # Si no hay un agente específico o no se encontró, seleccionar uno
        agent = self.select_agent(message, working_context)
        
        if not agent:
            # Si no hay agente disponible, devolver un mensaje de error
            error_message = "No hay agentes disponibles para procesar tu mensaje."
            yield error_message
            
            # Añadir el mensaje de error al historial
            working_context['messages'].append({
                'role': 'assistant',
                'content': error_message
            })
            
            return
        
        # Procesar el mensaje con el agente seleccionado
        response_generator = agent.process(message, working_context)
        
        # Capturar la respuesta completa para añadirla al historial
        full_response = ""
        for chunk in response_generator:
            full_response += chunk
            yield chunk
        
        # Añadir la respuesta al historial de mensajes
        working_context['messages'].append({
            'role': 'assistant',
            'content': full_response
        })
    
    def reset(self) -> None:
        """
        Reinicia el estado del gestor de agentes.
        """
        self.current_agent = None
        self.context = {
            'conversation_history': [],
            'messages': [],
            'user_info': {},
            'project_info': {},
            'current_agent': None,
            'previous_agent': None
        } 