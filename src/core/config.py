"""
Configuración del chatbot y la aplicación.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de LM Studio
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "phi-4")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))

# Configuración del chatbot
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500
SYSTEM_PROMPT = """Eres un asistente especializado en Alisys, una empresa líder en soluciones tecnológicas innovadoras. 
Tu conocimiento incluye:

SOLUCIONES PRINCIPALES:
1. Soluciones Cloud
   - Cloud Customer Experience
   - Centralita Virtual
   - Cloud Contact Center
   - Omnichannel Payments
   - Cloud CRM

2. Agentes Virtuales/IA
   - Gestión de citas
   - Gestión de reservas
   - Automatización de trámites
   - Encuestas
   - Red Inteligente Conversacional

3. Certificación/Blockchain
   - Sellado de tiempo
   - RGPD mediante blockchain
   - Certificación de comunicaciones

4. Robótica
   - Soluciones robóticas para procesos industriales
   - Automatización inteligente

SECTORES DE ACTUACIÓN:
1. Salud
2. Educación
3. Automoción
4. Administraciones Públicas

CASOS DE ÉXITO:
- Vodafone
- 060
- Sacyl
- Sodexo
- Carglass
- Fundación ONCE
- Vaughan
- Just Eat
- Bosch
- CAPSA
- Asamblea de Madrid
- W2M
- Naturgy

Debes proporcionar información precisa y estructurada, manteniendo un tono profesional y orientado a soluciones."""

# Configuración de la API
API_ENDPOINTS = {
    "chat": f"{LM_STUDIO_URL}/v1/chat/completions",
    "models": f"{LM_STUDIO_URL}/v1/models"
}

# Configuración de la aplicación
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Casos de éxito detallados
SUCCESS_CASES = {
    "vodafone": {
        "sector": "Telecomunicaciones",
        "solución": "Cloud Contact Center",
        "resultados": [
            "Reducción del 30% en tiempos de respuesta",
            "Mejora del 25% en satisfacción del cliente",
            "Optimización de recursos operativos"
        ]
    },
    "060": {
        "sector": "Administración Pública",
        "solución": "Agentes Virtuales",
        "resultados": [
            "Gestión de 450.000 peticiones mensuales",
            "Reducción del 40% en tiempos de espera",
            "Mejora en la eficiencia del servicio"
        ]
    },
    "sacyl": {
        "sector": "Salud",
        "solución": "Gestión de Citas",
        "resultados": [
            "Reducción del 35% en citas canceladas",
            "Optimización de agendas médicas",
            "Mejora en la experiencia del paciente"
        ]
    }
} 