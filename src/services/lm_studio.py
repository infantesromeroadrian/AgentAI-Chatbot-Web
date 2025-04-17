"""
Servicio para interactuar con LM Studio.
"""
import os
import json
import requests
import traceback
from typing import Dict, Any, Generator, List, Optional
from dotenv import load_dotenv
from core.config import LM_STUDIO_URL, TIMEOUT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, SYSTEM_PROMPT

# Cargar variables de entorno
load_dotenv()

class LMStudioClient:
    """
    Cliente para comunicarse con LM Studio y generar respuestas del chatbot.
    """
    
    def __init__(self):
        """
        Inicializa el cliente de LM Studio.
        """
        # Construir la URL correcta
        base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
        # Asegurarse de que la URL tenga el formato correcto
        self.api_url = self._normalize_url(base_url)
        
        print(f"LMStudioClient inicializado con URL: {self.api_url}")
        
        self.model = os.getenv("LM_STUDIO_MODEL", "default")
        self.max_tokens = int(os.getenv("LM_STUDIO_MAX_TOKENS", "1024"))
        self.temperature = float(os.getenv("LM_STUDIO_TEMPERATURE", "0.7"))
        self.timeout = int(os.getenv("TIMEOUT", "30"))
    
    def _normalize_url(self, base_url: str) -> str:
        """
        Normaliza la URL base para asegurar que tiene el formato correcto.
        
        Args:
            base_url: URL base para la API
            
        Returns:
            URL normalizada
        """
        if base_url.endswith('/v1'):
            return base_url
        else:
            return f"{base_url}/v1"
    
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
            messages = self._prepare_messages(system_prompt, user_message)
            
            # Enviar la solicitud a la API
            response = self._send_request(messages, stream=False)
            
            # Extraer la respuesta
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content']
            else:
                return "Lo siento, no pude generar una respuesta. Por favor, inténtalo de nuevo."
                
        except Exception as e:
            print(f"Error al generar respuesta: {str(e)}")
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def generate_stream(self, system_prompt: str, user_message: str) -> Generator[str, None, None]:
        """
        Genera una respuesta en modo streaming para el mensaje del usuario.
        
        Args:
            system_prompt: Prompt del sistema que define el comportamiento del asistente
            user_message: Mensaje del usuario
            
        Returns:
            Generador que produce la respuesta por fragmentos
        """
        try:
            # Preparar los mensajes para la API
            messages = self._prepare_messages(system_prompt, user_message)
            
            # Enviar la solicitud en modo streaming
            for chunk in self._send_streaming_request(messages):
                yield chunk
                
        except requests.exceptions.Timeout:
            print("Timeout al conectar con LM Studio")
            yield "Lo siento, se agotó el tiempo de espera al conectar con el modelo. Por favor, inténtalo de nuevo."
        except Exception as e:
            print(f"Error al generar respuesta streaming: {str(e)}")
            traceback.print_exc()
            yield f"Error: {str(e)}"
    
    def _prepare_messages(self, system_prompt: str, user_message: str) -> List[Dict[str, str]]:
        """
        Prepara los mensajes en el formato esperado por la API.
        
        Args:
            system_prompt: Prompt del sistema
            user_message: Mensaje del usuario
            
        Returns:
            Lista de mensajes formateada
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    
    def _send_request(self, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """
        Envía una solicitud a la API de LM Studio.
        
        Args:
            messages: Lista de mensajes
            stream: Indica si se debe usar streaming
            
        Returns:
            Respuesta de la API
        """
        payload = {
            "messages": messages,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": stream
        }
        
        response = requests.post(
            f"{self.api_url}/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Error en la API de LM Studio: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _send_streaming_request(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Envía una solicitud en modo streaming a la API de LM Studio.
        
        Args:
            messages: Lista de mensajes
            
        Returns:
            Generador que produce la respuesta por fragmentos
        """
        payload = {
            "messages": messages,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }
        
        response = requests.post(
            f"{self.api_url}/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Error en la API de LM Studio: {response.status_code}")
        
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
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    def get_default_system_prompt(self) -> str:
        """
        Obtiene el prompt del sistema por defecto.
        
        Returns:
            Prompt del sistema por defecto
        """
        return SYSTEM_PROMPT

# Funciones auxiliares para retrocompatibilidad
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
    """
    Envía una solicitud a LM Studio y devuelve la respuesta.
    Función de compatibilidad con el código antiguo.
    """
    client = LMStudioClient()
    system_prompt = client.get_default_system_prompt()
    
    if stream:
        for chunk in client.generate_stream(system_prompt, message):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    else:
        response = client.generate(system_prompt, message)
        yield f"data: {json.dumps({'token': response})}\n\n" 