"""
Servicio para interactuar con LM Studio.
"""
import os
import json
import requests
from core.config import LM_STUDIO_URL, TIMEOUT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, SYSTEM_PROMPT
from typing import Dict, Any, Generator, List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_lm_studio_connection():
    """Verifica la conexión con LM Studio"""
    try:
        # Usar la misma lógica que en LMStudioClient para construir la URL
        base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        if base_url.endswith('/v1'):
            api_url = base_url
        else:
            api_url = f"{base_url}/v1"
            
        print(f"Verificando conexión con LM Studio en: {api_url}/models")
        
        response = requests.get(f"{api_url}/models", timeout=3)
        return response.status_code == 200
    except Exception as e:
        print(f"Error al verificar conexión con LM Studio: {str(e)}")
        return False

def send_chat_request(message, stream=True, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS):
    """Envía una solicitud a LM Studio y devuelve la respuesta"""
    # Crear un sistema de mensajes con instrucciones muy específicas
    system_prompt = """Eres un asistente especializado en Alisys, una empresa líder en soluciones tecnológicas innovadoras.
    
INSTRUCCIONES IMPORTANTES:

1. CUANDO EL USUARIO PREGUNTE SOBRE ALISYS O SUS SERVICIOS:
   - Proporciona información breve y relevante sobre los servicios de Alisys que podrían ayudar al usuario.
   - Mantén las respuestas concisas y enfocadas en lo que el usuario pregunta.
   - NO solicites datos de contacto en esta etapa inicial.

2. CUANDO EL USUARIO MUESTRE INTERÉS EXPLÍCITO EN ALGÚN SERVICIO:
   - Primero, explica brevemente por qué Alisys es una buena opción para su caso específico.
   - Luego, pregunta si desea ser contactado por un representante.
   - NUNCA asumas que el usuario ya ha proporcionado sus datos de contacto.
   - NUNCA menciones que "un representante ya ha recibido tus datos" a menos que el usuario haya completado el formulario.

3. CUANDO EL USUARIO ACEPTE SER CONTACTADO:
   - Solicita su nombre completo, correo electrónico, teléfono y empresa.
   - Usa un formato claro y directo para solicitar cada dato.
   - Después de obtener los datos, confirma que un representante se pondrá en contacto en 24-48 horas.

4. SI EL USUARIO PREGUNTA QUÉ INFORMACIÓN NECESITAS:
   - Solicita: nombre completo, correo electrónico, teléfono y empresa.
   - NO repitas información sobre Alisys en este punto.

IMPORTANTE: NUNCA digas "Un representante de Alisys ya ha recibido tus datos" a menos que el usuario haya proporcionado explícitamente su nombre y correo electrónico."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    if stream:
        return _send_streaming_request(messages, temperature, max_tokens)
    else:
        return _send_non_streaming_request(messages, temperature, max_tokens)

def _send_streaming_request(messages, temperature, max_tokens):
    """Envía una solicitud en modo streaming a LM Studio"""
    try:
        # Construir la URL correcta
        base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        if base_url.endswith('/v1'):
            api_url = base_url
        else:
            api_url = f"{base_url}/v1"
            
        # Enviar solicitud a LM Studio con streaming activado
        response = requests.post(
            f"{api_url}/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            },
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            yield f"data: {json.dumps({'error': f'Error de LM Studio: {response.status_code}'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        # Procesar la respuesta en streaming
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # Quitar 'data: '
                    if line == '[DONE]':
                        break
                    try:
                        data = json.loads(line)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                yield f"data: {json.dumps({'token': delta['content']})}\n\n"
                    except json.JSONDecodeError:
                        continue
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except requests.exceptions.Timeout:
        yield f"data: {json.dumps({'error': 'Tiempo de espera agotado al conectar con LM Studio.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

def _send_non_streaming_request(messages, temperature, max_tokens):
    """Envía una solicitud no streaming a LM Studio"""
    try:
        # Construir la URL correcta
        base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        if base_url.endswith('/v1'):
            api_url = base_url
        else:
            api_url = f"{base_url}/v1"
            
        response = requests.post(
            f"{api_url}/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            bot_response = response.json()["choices"][0]["message"]["content"]
            yield f"data: {json.dumps({'token': bot_response})}\n\n"
        else:
            yield f"data: {json.dumps({'error': f'No se pudo conectar con LM Studio. Código: {response.status_code}'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

class LMStudioClient:
    """
    Cliente para comunicarse con LM Studio y generar respuestas del chatbot.
    """
    
    def __init__(self):
        """
        Inicializa el cliente de LM Studio.
        """
        # Usar LM_STUDIO_URL en lugar de LM_STUDIO_API_URL
        base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        # Asegurarse de que la URL no termina con /v1 y añadirlo
        if base_url.endswith('/v1'):
            self.api_url = base_url
        else:
            self.api_url = f"{base_url}/v1"
        
        print(f"LMStudioClient inicializado con URL: {self.api_url}")
        
        self.model = os.getenv("LM_STUDIO_MODEL", "default")
        self.max_tokens = int(os.getenv("LM_STUDIO_MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("LM_STUDIO_TEMPERATURE", "0.7"))
    
    def generate(self, system_prompt: str, user_message: str) -> str:
        """
        Genera una respuesta completa para el mensaje del usuario.
        
        Args:
            system_prompt: Prompt del sistema que define el comportamiento del asistente
            user_message: Mensaje del usuario
            
        Returns:
            Respuesta generada por el modelo
        """
        try:
            # Preparar los mensajes para la API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Configurar los parámetros de la solicitud
            payload = {
                "messages": messages,
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            # Realizar la solicitud a la API
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            
            # Verificar si la solicitud fue exitosa
            response.raise_for_status()
            
            # Extraer la respuesta
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"Error al generar respuesta: {str(e)}")
            return "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
    
    def generate_stream(self, system_prompt: str, user_message: str) -> Generator[str, None, None]:
        """
        Genera una respuesta en modo streaming para el mensaje del usuario.
        
        Args:
            system_prompt: Prompt del sistema que define el comportamiento del asistente
            user_message: Mensaje del usuario
            
        Returns:
            Generador que produce fragmentos de la respuesta
        """
        try:
            # Preparar los mensajes para la API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Configurar los parámetros de la solicitud
            payload = {
                "messages": messages,
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True
            }
            
            # Realizar la solicitud a la API en modo streaming
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                stream=True
            )
            
            # Verificar si la solicitud fue exitosa
            response.raise_for_status()
            
            # Procesar la respuesta en streaming
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]  # Eliminar el prefijo 'data: '
                        if line == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            if chunk["choices"][0]["finish_reason"] is None:
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            print(f"Error al generar respuesta en streaming: {str(e)}")
            yield "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
    
    def get_default_system_prompt(self) -> str:
        """
        Obtiene el prompt del sistema por defecto.
        
        Returns:
            Prompt del sistema por defecto
        """
        return """Eres un asistente virtual de Alisys, una empresa especializada en soluciones de comunicación.

INFORMACIÓN SOBRE ALISYS:
Alisys ofrece soluciones de comunicación avanzadas para empresas, incluyendo:
1. Contact Center as a Service (CCaaS)
2. Comunicaciones unificadas
3. Telefonía IP empresarial
4. SMS y WhatsApp Business
5. Números de teléfono virtuales
6. Soluciones de IVR y chatbots

INSTRUCCIONES:
1. Proporciona información clara y concisa sobre los servicios de Alisys.
2. Si el usuario pregunta por precios específicos, explica que varían según las necesidades y volumen, y ofrece poner en contacto con un representante.
3. Si el usuario muestra interés en algún servicio, pregunta por sus necesidades específicas para entender mejor su caso de uso.
4. Si el usuario desea ser contactado, solicita su información de contacto (nombre, email, teléfono y empresa).
5. Mantén un tono profesional y amigable en todo momento.
6. No inventes información sobre Alisys que no esté en este prompt.
7. Si no conoces la respuesta a una pregunta específica, ofrece poner al usuario en contacto con un representante.

Recuerda que tu objetivo es proporcionar información útil y recopilar datos de contacto de usuarios interesados.""" 