# Arquitectura Interactiva de Alisys Web Bot

## Diagrama de Componentes

```mermaid
graph TD
    subgraph "Interfaz de Usuario"
        UI[Frontend Web] --> |HTTP Requests| API[API REST]
    end
    
    subgraph "API Layer"
        API --> Routes[Rutas API]
        Routes --> AgentRoutes[Rutas de Agentes]
        Routes --> StandardRoutes[Rutas Estándar]
    end
    
    subgraph "Sistema de Agentes"
        AgentManager[Gestor de Agentes] --> GeneralAgent[Agente General]
        AgentManager --> SalesAgent[Agente de Ventas]
        AgentManager --> EngineerAgent[Agente Técnico]
        AgentManager --> DataCollectionAgent[Agente de Recolección de Datos]
        AgentManager --> WelcomeAgent[Agente de Bienvenida]
    end
    
    subgraph "Servicios"
        LMStudioClient[Cliente LM Studio] --> |API OpenAI Compatible| LLM[Modelo de Lenguaje]
    end
    
    subgraph "Utilidades"
        ContextManager[Gestor de Contexto]
        SentimentAnalyzer[Analizador de Sentimiento]
        IntentClassifier[Clasificador de Intenciones]
    end
    
    subgraph "Almacenamiento"
        Database[Base de Datos SQLite] --> DataManager[Gestor de Datos]
        ContextStorage[Almacenamiento de Contexto]
    end
    
    Routes --> |Routing| AgentManager
    AgentManager --> |Analiza Mensaje| IntentClassifier
    AgentManager --> |Analiza Sentimiento| SentimentAnalyzer
    AgentManager --> |Almacena Contexto| ContextManager
    ContextManager --> |Persiste Datos| ContextStorage
    DataCollectionAgent --> |Almacena Leads| DataManager
    DataManager --> |CRUD Operations| Database
    GeneralAgent --> |Genera Respuestas| LMStudioClient
    SalesAgent --> |Genera Respuestas| LMStudioClient
    EngineerAgent --> |Genera Respuestas| LMStudioClient
    DataCollectionAgent --> |Genera Respuestas| LMStudioClient
    WelcomeAgent --> |Genera Respuestas| LMStudioClient
```

## Flujo de Procesamiento de Mensajes

```mermaid
sequenceDiagram
    participant Usuario
    participant API
    participant AgentManager
    participant Agentes
    participant LMStudio
    
    Usuario->>API: Envía mensaje
    API->>AgentManager: process_message(mensaje, contexto)
    AgentManager->>AgentManager: Analiza sentimiento del mensaje
    AgentManager->>AgentManager: Selecciona el agente apropiado
    AgentManager->>Agentes: Delega el mensaje al agente seleccionado
    Agentes->>Agentes: Genera prompt del sistema
    Agentes->>LMStudio: Realiza consulta al modelo de lenguaje
    LMStudio-->>Agentes: Devuelve respuesta generada
    Agentes-->>AgentManager: Devuelve chunks de respuesta
    AgentManager-->>API: Streaming de respuesta
    API-->>Usuario: Muestra respuesta progresivamente
    AgentManager->>AgentManager: Actualiza contexto de conversación
```

## Jerarquía de Clases del Sistema de Agentes

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +name: string
        +description: string
        +lm_client: LMStudioClient
        +can_handle(message, context): float
        +process(message, context): Generator
        +get_system_prompt(context): string
        -_adjust_confidence(confidence, message, context): float
        -_generate_response(system_prompt, message): Generator
        -_update_conversation_history(user_message, assistant_response, context): void
        -_format_conversation_history(context): string
        -_adjust_prompt_for_sentiment(system_prompt, context): string
    }
    
    class AgentManager {
        +agents: List[BaseAgent]
        +current_agent: BaseAgent
        +context: Dict
        +context_manager: ContextPersistenceManager
        +sentiment_analyzer: SentimentAnalyzer
        +register_agent(agent): void
        +select_agent(message, context): BaseAgent
        +process_message(message, context): Generator
        +load_session(user_id): bool
        +save_session(user_id): bool
        +reset(): void
        -_update_agent_selection(agent, confidence, context, reason): void
        -_get_agent_by_name(agent_name): BaseAgent
        -_select_agent_with_highest_confidence(message, context): Tuple
        -_get_fallback_agent(): BaseAgent
        -_prepare_context(message, external_context): Dict
        -_process_with_agent(agent, message, context): Generator
        -_update_shared_context(context): void
    }
    
    class GeneralAgent {
        +get_system_prompt(context): string
        +_adjust_confidence(base_confidence, message, context): float
    }
    
    class SalesAgent {
        +get_system_prompt(context): string
        +_adjust_confidence(base_confidence, message, context): float
    }
    
    class EngineerAgent {
        +get_system_prompt(context): string
        +_adjust_confidence(base_confidence, message, context): float
    }
    
    class DataCollectionAgent {
        +get_system_prompt(context): string
        +_adjust_confidence(base_confidence, message, context): float
        -_detect_contact_information(message, context): Dict
        -_should_collect_data(message, context): bool
        -_process_form_input(message, context): string
    }
    
    class WelcomeAgent {
        +get_system_prompt(context): string
        +_adjust_confidence(base_confidence, message, context): float
    }
    
    BaseAgent <|-- GeneralAgent
    BaseAgent <|-- SalesAgent
    BaseAgent <|-- EngineerAgent
    BaseAgent <|-- DataCollectionAgent
    BaseAgent <|-- WelcomeAgent
    AgentManager --> BaseAgent
```

## Arquitectura de Servicios y Utilidades

```mermaid
classDiagram
    class LMStudioClient {
        +api_base: string
        +api_key: string
        +model: string
        +generate_stream(system_prompt, user_message): Generator
        +generate(system_prompt, user_message): string
        +check_connection(): bool
    }
    
    class ContextPersistenceManager {
        +storage_dir: string
        +save_context(user_id, context): bool
        +load_context(user_id): Dict
        +list_user_sessions(user_id): List[Dict]
        -_get_user_storage_path(user_id): string
        -_get_session_file_path(user_id, session_id): string
    }
    
    class SentimentAnalyzer {
        +analyze(message): Dict
        +get_response_suggestion(analysis): Dict
        -_detect_emotions(message): Dict
        -_calculate_polarity(message): float
        -_detect_urgency(message): float
    }
    
    class IntentClassifier {
        +classify_intent(message, context): Dict
        +detect_agent_change_keywords(message): string
        +get_confidence_explanation(scores, agent_name): string
    }
    
    class DataManager {
        +save_lead(lead_data): bool
        +get_leads(): List[Lead]
        +get_lead_by_id(lead_id): Lead
        +update_lead(lead_id, updated_data): bool
    }
```

## Descripción de los Componentes Principales

### Sistema de Agentes

- **AgentManager**: Coordina el sistema de agentes, seleccionando el más adecuado para cada mensaje y gestionando el contexto de la conversación.
- **BaseAgent**: Clase abstracta que define la interfaz común para todos los agentes.
- **GeneralAgent**: Maneja consultas generales sobre Alisys y sus servicios.
- **SalesAgent**: Especializado en proporcionar información sobre precios y cotizaciones.
- **EngineerAgent**: Proporciona estimaciones de tiempo y recomendaciones técnicas.
- **DataCollectionAgent**: Se encarga de recopilar información de contacto del usuario.
- **WelcomeAgent**: Da la bienvenida a los usuarios y proporciona información inicial.

### Servicios

- **LMStudioClient**: Cliente que se conecta a LM Studio para generar respuestas utilizando un modelo de lenguaje compatible con la API de OpenAI.

### Utilidades

- **ContextPersistenceManager**: Gestiona la persistencia del contexto de conversación entre sesiones.
- **SentimentAnalyzer**: Analiza el sentimiento del mensaje del usuario para adaptar la respuesta.
- **IntentClassifier**: Clasifica la intención del mensaje para seleccionar el agente adecuado.

### Almacenamiento

- **DataManager**: Gestiona el almacenamiento y recuperación de datos de leads.
- **Database**: Base de datos SQLite para almacenar leads y otra información.

### API Layer

- **Routes**: Define las rutas y endpoints de la API del chatbot.
- **AgentRoutes**: Rutas específicas para el sistema de agentes.

### Interfaz de Usuario

- **Frontend Web**: Interfaz web responsive que permite a los usuarios interactuar con el chatbot.

## Flujos de Usuario

1. **Consulta General**:
   - Usuario envía una pregunta sobre servicios de Alisys
   - GeneralAgent proporciona información detallada

2. **Consulta de Precios**:
   - Usuario pregunta por precios o cotizaciones
   - SalesAgent proporciona información sobre precios y opciones

3. **Consulta Técnica**:
   - Usuario pregunta aspectos técnicos de implementación
   - EngineerAgent proporciona información técnica detallada

4. **Recopilación de Datos**:
   - Después de mostrar interés, el DataCollectionAgent solicita información de contacto
   - Se guardan los datos en la base de datos para seguimiento 