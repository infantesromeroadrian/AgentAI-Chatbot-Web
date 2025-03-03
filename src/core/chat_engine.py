"""
Motor principal del chatbot, maneja la lógica de procesamiento de mensajes.
"""
import os
import requests
import json
from typing import Dict, List, Optional
from requests.exceptions import Timeout, ConnectionError, RequestException
from services.lm_studio import send_chat_request, check_lm_studio_connection
from core.config import API_ENDPOINTS, SYSTEM_PROMPT, SUCCESS_CASES, LM_STUDIO_URL, TIMEOUT
from data.data_manager import DataManager

class ChatEngine:
    """Clase que maneja la lógica principal del chatbot"""
    
    def __init__(self, lm_studio_url=None):
        """Inicializa el motor del chatbot"""
        self.lm_studio_url = lm_studio_url or LM_STUDIO_URL
        self.timeout = TIMEOUT
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.data_manager = DataManager()
    
    def process_message(self, message, stream=True):
        """Procesa un mensaje del usuario y devuelve la respuesta"""
        self.add_message("user", message)
        return self.get_response(message, stream)
    
    def add_message(self, role: str, content: str) -> None:
        """Añade un mensaje al historial de conversación."""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_response(self, user_message: str, stream=True) -> Optional[str]:
        """Obtiene una respuesta del modelo de LM Studio."""
        try:
            if stream:
                return send_chat_request(user_message, stream=True)
            else:
                # Para respuestas no streaming
                response = requests.post(
                    API_ENDPOINTS["chat"],
                    json={
                        "messages": self.conversation_history,
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    bot_response = response.json()["choices"][0]["message"]["content"]
                    self.add_message("assistant", bot_response)
                    return bot_response
                else:
                    error_msg = f"Error al conectar con LM Studio. Código: {response.status_code}"
                    print(error_msg)
                    return None
                    
        except Timeout:
            error_msg = "Tiempo de espera agotado al conectar con LM Studio."
            print(error_msg)
            return None
        except ConnectionError:
            error_msg = "No se pudo conectar con LM Studio. Verifica que el servidor esté en ejecución."
            print(error_msg)
            return None
        except RequestException as e:
            error_msg = f"Error en la solicitud: {str(e)}"
            print(error_msg)
            return None
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            print(error_msg)
            return None
    
    def get_models(self):
        """Obtiene la lista de modelos disponibles en LM Studio"""
        try:
            response = requests.get(f"{self.lm_studio_url}/v1/models", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def clear_history(self) -> None:
        """Limpia el historial de conversación, manteniendo el prompt del sistema."""
        self.conversation_history = [self.conversation_history[0]]
    
    def save_conversation(self, user_id):
        """Guarda la conversación actual."""
        return self.data_manager.save_conversation(user_id, self.conversation_history) 