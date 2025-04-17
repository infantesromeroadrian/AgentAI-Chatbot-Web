"""
Módulo principal del chatbot de Alisys.
Proporciona ejemplos de uso del sistema y punto de entrada principal.
"""
import logging
import argparse
import sys
import os
from typing import Dict, Any, Optional

from agents.agent_manager import AgentManager
from agents.general_agent import GeneralAgent
from agents.sales_agent import SalesAgent
from agents.engineer_agent import EngineerAgent
from agents.data_collection_agent import DataCollectionAgent
from utils.context_manager import ContextPersistenceManager
from utils.sentiment_analyzer import SentimentAnalyzer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_agent_manager() -> AgentManager:
    """
    Configura y devuelve un gestor de agentes completamente inicializado.
    
    Returns:
        Gestor de agentes configurado
    """
    # Crear gestor de agentes
    manager = AgentManager()
    
    # Registrar agentes disponibles - el orden determina la prioridad
    manager.register_agent(GeneralAgent())     # Primera prioridad para bienvenida e información general
    manager.register_agent(SalesAgent())       # Alta prioridad para ventas
    manager.register_agent(EngineerAgent())    # Alta prioridad para consultas técnicas
    manager.register_agent(DataCollectionAgent()) # Última prioridad para recopilar datos
    
    logger.info("Gestor de agentes configurado correctamente")
    return manager

def process_message(manager: AgentManager, message: str, user_id: str) -> str:
    """
    Procesa un mensaje de usuario y devuelve la respuesta completa.
    
    Args:
        manager: Gestor de agentes configurado
        message: Mensaje del usuario
        user_id: Identificador del usuario
        
    Returns:
        Respuesta completa del agente
    """
    # Asegurar que el user_id está en el contexto
    manager.context['user_id'] = user_id
    
    # Procesar mensaje
    full_response = ""
    for chunk in manager.process_message(message):
        full_response += chunk
        # En una aplicación real, aquí se enviaría cada chunk al frontend
        # para mostrar la respuesta de forma progresiva
    
    # Guardar contexto actualizado
    manager.save_session(user_id)
    
    return full_response

def example_sentiment_analysis():
    """
    Ejemplo de uso del analizador de sentimiento.
    """
    analyzer = SentimentAnalyzer()
    
    # Ejemplos de mensajes con diferentes sentimientos
    messages = [
        "Estoy muy contento con su servicio, funciona perfectamente",
        "No puedo creer que esto no funcione, es frustrante y una pérdida de tiempo",
        "Tengo dudas sobre cómo configurar la integración con mi CRM",
        "¿Es posible obtener un descuento para mi empresa?",
        "NECESITO AYUDA URGENTE!!! El sistema no responde!!!"
    ]
    
    print("\n=== EJEMPLO DE ANÁLISIS DE SENTIMIENTO ===\n")
    
    for message in messages:
        # Analizar sentimiento
        analysis = analyzer.analyze(message)
        
        # Obtener sugerencias para respuesta
        suggestions = analyzer.get_response_suggestion(analysis)
        
        # Mostrar resultados
        print(f"Mensaje: \"{message}\"")
        print(f"Emoción dominante: {analysis.get('dominant_emotion', 'No detectada')}")
        print(f"Polaridad: {analysis.get('polarity', 0):.2f}")
        print(f"Urgencia: {analysis.get('urgency', 0):.2f}")
        print(f"Tono sugerido: {suggestions.get('tone', 'neutral')}")
        print(f"Prioridad: {suggestions.get('priority', 'normal')}")
        if suggestions.get('focus'):
            print(f"Enfoque: {', '.join(suggestions.get('focus', []))}")
        print("-" * 50)

def example_context_persistence():
    """
    Ejemplo de uso de persistencia de contexto.
    """
    ctx_manager = ContextPersistenceManager()
    
    # Crear un contexto de ejemplo
    user_id = "usuario_ejemplo"
    context = {
        "messages": [
            {"role": "user", "content": "Hola, necesito información sobre vuestros servicios"},
            {"role": "assistant", "content": "Claro, te puedo ayudar con eso. ¿Qué tipo de servicio te interesa?"}
        ],
        "user_info": {
            "company": "Empresa Ejemplo",
            "email": "contacto@ejemplo.com"
        },
        "current_agent": "GeneralAgent",
        "message_count": 2
    }
    
    print("\n=== EJEMPLO DE PERSISTENCIA DE CONTEXTO ===\n")
    
    # Guardar contexto
    saved = ctx_manager.save_context(user_id, context)
    print(f"Contexto guardado: {saved}")
    
    # Listar sesiones disponibles
    sessions = ctx_manager.list_user_sessions(user_id)
    print(f"Sesiones disponibles: {len(sessions)}")
    
    if sessions:
        print(f"Última sesión: {sessions[0]['datetime']}")
    
    # Cargar contexto
    loaded_context = ctx_manager.load_context(user_id)
    if loaded_context:
        print(f"Contexto cargado con {len(loaded_context.get('messages', []))} mensajes")
        print(f"Agente actual: {loaded_context.get('current_agent')}")
    
    print("-" * 50)

def example_conversation_with_persistence():
    """
    Ejemplo de conversación con persistencia entre sesiones.
    """
    user_id = "usuario_demo"
    manager = setup_agent_manager()
    
    print("\n=== EJEMPLO DE CONVERSACIÓN CON PERSISTENCIA ===\n")
    
    # Intentar cargar sesión anterior
    session_loaded = manager.load_session(user_id)
    if session_loaded:
        print("Sesión anterior cargada. Continuando conversación...\n")
    else:
        print("Iniciando nueva conversación...\n")
    
    # Simulación de conversación
    messages = [
        "Hola, me gustaría información sobre vuestros servicios",
        "Me interesa el servicio de Contact Center, ¿qué opciones tienen?",
        "¿Y cuál sería el precio aproximado para una empresa de 50 empleados?"
    ]
    
    for i, message in enumerate(messages):
        print(f"Usuario: {message}")
        response = process_message(manager, message, user_id)
        print(f"Asistente ({manager.current_agent.name}): {response}\n")
        
        # Mostrar información de sentimiento
        if 'current_sentiment' in manager.context:
            sentiment = manager.context['current_sentiment']
            print(f"[Análisis interno] Emoción: {sentiment.get('dominant_emotion', 'No detectada')}, " + 
                  f"Polaridad: {sentiment.get('polarity', 0):.2f}\n")
    
    # Guardar sesión explícitamente al finalizar
    manager.save_session(user_id)
    print("Sesión guardada. ID:", manager.context.get('session_id'))
    print("-" * 50)

def main():
    """
    Función principal que ejecuta ejemplos de uso del sistema.
    """
    # Crear directorio de almacenamiento si no existe
    os.makedirs("storage/contexts", exist_ok=True)
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Ejemplos de uso del chatbot de Alisys")
    parser.add_argument('--sentiment', action='store_true', help='Ejecutar ejemplo de análisis de sentimiento')
    parser.add_argument('--persistence', action='store_true', help='Ejecutar ejemplo de persistencia de contexto')
    parser.add_argument('--conversation', action='store_true', help='Ejecutar ejemplo de conversación con persistencia')
    parser.add_argument('--all', action='store_true', help='Ejecutar todos los ejemplos')
    
    args = parser.parse_args()
    
    # Si no se especifican argumentos, mostrar ayuda
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Ejecutar ejemplos según los argumentos
    if args.all or args.sentiment:
        example_sentiment_analysis()
    
    if args.all or args.persistence:
        example_context_persistence()
    
    if args.all or args.conversation:
        example_conversation_with_persistence()

if __name__ == "__main__":
    main() 