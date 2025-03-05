# Alisys Web Bot

Un chatbot inteligente para el sitio web de Alisys que proporciona información sobre servicios y recopila datos de contacto de clientes potenciales.

## Características

- Sistema de agentes especializados para manejar diferentes tipos de consultas
- Recopilación inteligente de datos de contacto
- Almacenamiento de leads en base de datos SQLite
- Interfaz web responsive
- Streaming de respuestas para una experiencia fluida

## Estructura del Proyecto

```
Alisys-Web-Bot/
├── src/
│   ├── agents/                 # Sistema de agentes inteligentes
│   │   ├── agent_manager.py    # Gestor de agentes
│   │   ├── base_agent.py       # Clase base para todos los agentes
│   │   ├── general_agent.py    # Agente para consultas generales
│   │   ├── sales_agent.py      # Agente especializado en ventas
│   │   ├── engineer_agent.py   # Agente especializado en aspectos técnicos
│   │   └── data_collection_agent.py  # Agente para recopilar datos de contacto
│   ├── api/                    # Endpoints de la API
│   │   ├── routes.py           # Rutas principales
│   │   └── agent_routes.py     # Rutas específicas para el sistema de agentes
│   ├── data/                   # Gestión de datos
│   │   ├── data_manager.py     # Gestor de datos
│   │   └── database.py         # Configuración de la base de datos
│   ├── services/               # Servicios externos
│   │   └── lm_studio.py        # Cliente para LM Studio
│   ├── static/                 # Archivos estáticos
│   │   ├── css/                # Estilos CSS
│   │   ├── js/                 # Scripts JavaScript
│   │   └── img/                # Imágenes
│   ├── templates/              # Plantillas HTML
│   │   ├── index.html          # Página principal
│   │   └── leads.html          # Panel de administración de leads
│   ├── utils/                  # Utilidades
│   │   └── alisys_info.py      # Información sobre Alisys
│   └── app.py                  # Punto de entrada de la aplicación
├── .env                        # Variables de entorno
├── requirements.txt            # Dependencias
└── README.md                   # Documentación
```

## Requisitos

- Python 3.8+
- Flask
- SQLAlchemy
- LM Studio (para el modelo de lenguaje)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/alisys/alisys-web-bot.git
   cd alisys-web-bot
   ```

2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con los valores adecuados
   ```

## Uso

1. Iniciar LM Studio y cargar un modelo compatible con la API de OpenAI.

2. Iniciar la aplicación:
   ```bash
   python src/app.py
   ```

3. Acceder a la aplicación en el navegador:
   ```
   http://localhost:8000
   ```

4. Para acceder al panel de administración de leads:
   ```
   http://localhost:8000/admin/leads
   ```
   Credenciales por defecto: admin / alisys2024

## Sistema de Agentes

El chatbot utiliza un sistema de agentes especializados para manejar diferentes tipos de consultas:

- **GeneralAgent**: Maneja consultas generales sobre Alisys y sus servicios.
- **SalesAgent**: Especializado en proporcionar información sobre precios y cotizaciones.
- **EngineerAgent**: Proporciona estimaciones de tiempo y recomendaciones técnicas.
- **DataCollectionAgent**: Se encarga de recopilar información de contacto del usuario.

El **AgentManager** coordina estos agentes, seleccionando el más adecuado para cada mensaje del usuario.

## Licencia

Propiedad de Alisys. Todos los derechos reservados.