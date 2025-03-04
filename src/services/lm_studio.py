"""
Servicio para interactuar con LM Studio.
"""
import os
import json
import requests
from core.config import LM_STUDIO_URL, TIMEOUT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, SYSTEM_PROMPT

def check_lm_studio_connection():
    """Verifica la conexión con LM Studio"""
    try:
        response = requests.get(f"{LM_STUDIO_URL}/v1/models", timeout=3)
        return response.status_code == 200
    except:
        return False

def send_chat_request(message, stream=True, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS):
    """Envía una solicitud a LM Studio y devuelve la respuesta"""
    # Crear un sistema de mensajes que incluya la instrucción de solicitar datos
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\nDespués de proporcionar información sobre Alisys o sus servicios, SIEMPRE debes preguntar al usuario si desea ser contactado por un representante de Alisys. Si el usuario muestra interés, debes decir explícitamente: 'Para poder contactarte, necesitaría algunos datos. ¿Te gustaría proporcionar tu información de contacto?'"},
        {"role": "user", "content": message}
    ]
    
    if stream:
        return _send_streaming_request(messages, temperature, max_tokens)
    else:
        return _send_non_streaming_request(messages, temperature, max_tokens)

def _send_streaming_request(messages, temperature, max_tokens):
    """Envía una solicitud en modo streaming a LM Studio"""
    try:
        # Enviar solicitud a LM Studio con streaming activado
        response = requests.post(
            f"{LM_STUDIO_URL}/v1/chat/completions",
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
        response = requests.post(
            f"{LM_STUDIO_URL}/v1/chat/completions",
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