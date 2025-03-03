"""
Define las rutas y endpoints de la API del chatbot.
"""
import json
from flask import request, jsonify, render_template, Response, stream_with_context
from services.lm_studio import send_chat_request, check_lm_studio_connection
from utils.alisys_info import get_alisys_info, generate_alisys_info_stream

def register_routes(app):
    """Registra todas las rutas de la aplicación"""
    
    @app.route('/')
    def home():
        """Ruta principal que muestra la interfaz del chatbot"""
        return render_template('index.html')
    
    @app.route('/health', methods=['GET'])
    def health():
        """Endpoint para verificar el estado de la conexión con LM Studio"""
        lm_studio_connected = check_lm_studio_connection()
        
        return jsonify({
            "status": "ok",
            "lm_studio_connected": lm_studio_connected
        })
    
    @app.route('/chat/stream', methods=['GET'])
    def chat_stream():
        """Endpoint para streaming de respuestas del chatbot"""
        user_message = request.args.get('message', '').lower()
        
        # Respuestas rápidas para preguntas sobre Alisys
        if 'alisys' in user_message and ('qué es' in user_message or 'que es' in user_message 
                                        or 'info' in user_message or 'información' in user_message 
                                        or 'hablame' in user_message):
            return Response(
                stream_with_context(generate_alisys_info_stream()), 
                content_type='text/event-stream'
            )
        
        # Para otras preguntas, usar LM Studio
        return Response(
            stream_with_context(send_chat_request(user_message)), 
            content_type='text/event-stream'
        )
    
    @app.route('/chat', methods=['POST'])
    def chat():
        """Endpoint para respuestas no streaming (compatibilidad)"""
        data = request.json
        user_message = data.get('message', '')
        
        for response in send_chat_request(user_message, stream=False):
            response_data = json.loads(response.replace('data: ', ''))
            if 'error' in response_data:
                return jsonify({
                    "error": response_data['error'],
                    "response": "Lo siento, ocurrió un error al procesar tu mensaje."
                })
            elif 'token' in response_data:
                return jsonify({"response": response_data['token']})
        
        return jsonify({
            "error": "No se recibió respuesta",
            "response": "Lo siento, no pude procesar tu mensaje."
        }) 