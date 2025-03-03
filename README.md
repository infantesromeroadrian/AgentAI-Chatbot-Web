# Alisys Web Bot

<div align="center">
  <img src="https://alisys.net/wp-content/uploads/2022/05/logo-alisys-1.svg" alt="Alisys Logo" width="300"/>
  <br>
  <h3>Chatbot web inteligente con integración de LM Studio</h3>
</div>

## 📋 Descripción

Alisys Web Bot es una solución de chatbot avanzada diseñada para proporcionar información sobre Alisys, sus servicios y soluciones tecnológicas. Utiliza modelos de lenguaje de LM Studio para generar respuestas contextuales y precisas en tiempo real.

Este proyecto implementa una arquitectura modular que facilita el mantenimiento y la escalabilidad, con una interfaz web moderna y responsive que ofrece una experiencia de usuario óptima.

## ✨ Características principales

- **Interfaz web moderna y responsive**: Diseño limpio y adaptable a diferentes dispositivos
- **Respuestas en streaming**: Generación de texto en tiempo real para una experiencia más fluida
- **Integración con LM Studio**: Aprovecha modelos de lenguaje avanzados para respuestas inteligentes
- **Arquitectura modular**: Código organizado en componentes reutilizables
- **Soporte para Markdown**: Respuestas formateadas para mejor legibilidad
- **Información estructurada sobre Alisys**: Datos precisos sobre servicios, soluciones y casos de éxito
- **Contenedorización con Docker**: Facilita el despliegue y la escalabilidad

## 🏗️ Arquitectura del proyecto

El proyecto sigue una arquitectura modular con separación clara de responsabilidades:

src/
├── api/ # Endpoints y rutas de la API
│ ├── init.py
│ └── routes.py
├── core/ # Lógica principal del chatbot
│ ├── init.py
│ ├── chat_engine.py # Motor de procesamiento de mensajes
│ └── config.py # Configuración centralizada
├── data/ # Gestión de datos
│ ├── init.py
│ └── data_manager.py # Persistencia de conversaciones
├── services/ # Servicios externos
│ ├── init.py
│ └── lm_studio.py # Integración con LM Studio
├── templates/ # Plantillas HTML
│ └── index.html # Interfaz principal del chatbot
├── static/ # Archivos estáticos
│ ├── css/
│ │ └── style.css # Estilos de la interfaz
│ └── js/
│ └── main.js # Lógica del cliente
├── utils/ # Utilidades
│ ├── init.py
│ └── alisys_info.py # Información sobre Alisys
└── app.py # Punto de entrada principal




## 🚀 Instalación y ejecución

### Requisitos previos

- Python 3.10 o superior
- LM Studio ejecutándose localmente o en un servidor accesible
- Docker y Docker Compose (opcional, para despliegue con contenedores)

### Método 1: Instalación con Python

1. Clona este repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/Alisys-Web-Bot.git
   cd Alisys-Web-Bot
   ```

2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno (opcional):
   ```bash
   # Linux/macOS
   export LM_STUDIO_URL=http://localhost:1234
   
   # Windows (PowerShell)
   $env:LM_STUDIO_URL = "http://localhost:1234"
   ```

4. Ejecuta la aplicación:
   ```bash
   python src/app.py
   ```

5. Accede a la interfaz web en tu navegador:
   ```
   http://localhost:8000
   ```

### Método 2: Instalación con Docker

1. Clona este repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/Alisys-Web-Bot.git
   cd Alisys-Web-Bot
   ```

2. Construye y ejecuta el contenedor:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. Accede a la interfaz web en tu navegador:
   ```
   http://localhost:8000
   ```

### Entorno de desarrollo

Para desarrollo con recarga en caliente de cambios:

```bash
docker-compose -f docker-compose.dev.yml up
```

## ⚙️ Configuración

### Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `LM_STUDIO_URL` | URL de la API de LM Studio | `http://localhost:1234` |
| `LM_STUDIO_MODEL` | Modelo a utilizar | `phi-4` |
| `TIMEOUT` | Tiempo máximo de espera para respuestas (segundos) | `30` |
| `PORT` | Puerto para la aplicación web | `8000` |
| `HOST` | Host para la aplicación web | `0.0.0.0` |
| `DEBUG` | Modo de depuración | `True` |

### Configuración de LM Studio

1. Descarga e instala [LM Studio](https://lmstudio.ai/)
2. Carga un modelo compatible (recomendado: Phi-3, Mistral, Llama 3)
3. Inicia el servidor local en el puerto 1234
4. Asegúrate de que la API esté accesible desde `http://localhost:1234`

## 🔧 Desarrollo

### Estructura de directorios

- **api/**: Contiene las rutas y endpoints de la API Flask
- **core/**: Implementa la lógica principal del chatbot
- **data/**: Gestiona el almacenamiento y recuperación de datos
- **services/**: Integra servicios externos como LM Studio
- **templates/**: Contiene las plantillas HTML para la interfaz
- **static/**: Almacena archivos CSS, JavaScript e imágenes
- **utils/**: Proporciona utilidades y funciones auxiliares

### Flujo de trabajo recomendado

1. Crea una rama para tu nueva funcionalidad:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. Realiza tus cambios y pruébalos localmente
3. Ejecuta las pruebas (si están disponibles):
   ```bash
   pytest
   ```

4. Realiza un commit de tus cambios:
   ```bash
   git add .
   git commit -m "Añade nueva funcionalidad"
   ```

5. Sube tus cambios y crea un Pull Request:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```

## 📝 Guía de uso

1. **Inicio**: Al abrir la aplicación, serás recibido por el chatbot con un mensaje de bienvenida.

2. **Consultas sobre Alisys**: Puedes preguntar sobre:
   - Soluciones y servicios de Alisys
   - Sectores donde opera la empresa
   - Casos de éxito y clientes destacados
   - Información de contacto

3. **Ejemplos de preguntas**:
   - "¿Qué es Alisys?"
   - "¿Qué soluciones ofrece Alisys para el sector salud?"
   - "Cuéntame sobre los casos de éxito de Alisys"
   - "¿Qué servicios de IA proporciona Alisys?"

## 🛠️ Solución de problemas

### Problemas comunes

| Problema | Posible solución |
|----------|------------------|
| Error de conexión con LM Studio | Verifica que LM Studio esté ejecutándose y accesible en la URL configurada |
| Respuestas lentas | Ajusta el valor de `TIMEOUT` o considera usar un modelo más ligero |
| Error al construir la imagen Docker | Asegúrate de tener los permisos necesarios y suficiente espacio en disco |

### Logs

Los logs de la aplicación se pueden consultar:

- **Ejecución directa**: En la consola donde se ejecuta la aplicación
- **Docker**: Usando `docker-compose logs -f alisys-bot`

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios y haz commit (`git commit -m 'Add amazing feature'`)
4. Sube tus cambios (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo [especificar licencia] - consulta el archivo LICENSE para más detalles.

## 📞 Contacto

Para preguntas o soporte, contacta con:
- [Adrian Infantes]
- [infantesromeroadrian@gmail.com]