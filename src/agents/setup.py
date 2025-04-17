"""
Configuración e inicialización del sistema de agentes.
"""
import logging
from typing import Dict, Any

from .agent_manager import AgentManager
from .welcome_agent import WelcomeAgent
from .sales_agent import SalesAgent
from .engineer_agent import EngineerAgent
from .data_collection_agent import DataCollectionAgent

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_agent_system() -> AgentManager:
    """
    Configura e inicializa el sistema de agentes.
    
    Returns:
        Una instancia configurada de AgentManager con todos los agentes registrados
    """
    logger.info("Inicializando el sistema de agentes...")
    
    # Crear el gestor de agentes
    agent_manager = AgentManager()
    
    # Crear instancias de los agentes
    welcome_agent = WelcomeAgent()
    sales_agent = SalesAgent()
    engineer_agent = EngineerAgent()
    data_collection_agent = DataCollectionAgent()
    
    # Registrar los agentes en el gestor
    # El orden de registro es importante, ya que determina el orden de prioridad
    # Los agentes se evalúan en el orden en que se registran
    # El primero que puede manejar el mensaje es el que se selecciona
    agent_manager.register_agent(welcome_agent)    # Primera prioridad para bienvenida y preguntas generales
    agent_manager.register_agent(sales_agent)      # Alta prioridad para ventas
    agent_manager.register_agent(engineer_agent)   # Alta prioridad para consultas técnicas
    agent_manager.register_agent(data_collection_agent)  # Última prioridad para recopilar datos
    
    logger.info("Sistema de agentes inicializado correctamente")
    
    return agent_manager

def create_context() -> Dict[str, Any]:
    """
    Crea un contexto inicial para la conversación.
    
    Returns:
        Un diccionario con el contexto inicial
    """
    return {
        "conversation_history": [],
        "current_agent": None,
        "previous_agent": None,
        "message_count": 0,
        "data_collection_active": False,
        "data_collection_completed": False,
        "user_name": None,
        "user_email": None,
        "user_phone": None,
        "user_company": None,
        "mentioned_services": [],
        "interest_level": 0  # 0-10 escala de interés
    }

# Singleton para el gestor de agentes
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """
    Obtiene la instancia del gestor de agentes, creándola si no existe.
    
    Returns:
        La instancia del gestor de agentes
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = setup_agent_system()
    return _agent_manager 