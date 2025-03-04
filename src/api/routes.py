"""
Define las rutas y endpoints de la API del chatbot.
"""
import json
from flask import request, jsonify, render_template, Response, stream_with_context, session
from services.lm_studio import send_chat_request, check_lm_studio_connection
from utils.alisys_info import get_alisys_info, generate_alisys_info_stream, generate_contact_form_stream
from data.data_manager import DataManager

# Inicializar el gestor de datos
data_manager = DataManager()

def register_routes(app):
    """Registra todas las rutas de la aplicación"""
    
    # Configurar la sesión
    app.secret_key = 'alisys_chatbot_secret_key'
    
    @app.route('/')
    def home():
        """Ruta principal que muestra la interfaz del chatbot"""
        # Inicializar contador de mensajes en la sesión
        if 'message_count' not in session:
            session['message_count'] = 0
        if 'form_shown' not in session:
            session['form_shown'] = False
        if 'last_was_form' not in session:
            session['last_was_form'] = False
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
        
        # Si el último mensaje fue un formulario y recibimos una respuesta, no incrementamos el contador
        if not session.get('last_was_form', False):
            # Incrementar contador de mensajes
            if 'message_count' not in session:
                session['message_count'] = 0
            session['message_count'] += 1
        else:
            # Resetear el flag de último mensaje como formulario
            session['last_was_form'] = False
        
        # Respuestas rápidas para preguntas sobre Alisys
        if 'alisys' in user_message and ('qué es' in user_message or 'que es' in user_message 
                                        or 'info' in user_message or 'información' in user_message 
                                        or 'hablame' in user_message):
            # Después de mostrar la información, mostraremos el formulario
            session['form_shown'] = True
            session['last_was_form'] = True
            
            def combined_stream():
                # Primero enviamos la información de Alisys
                for chunk in generate_alisys_info_stream():
                    yield chunk
                
                # Luego enviamos el formulario de contacto
                for chunk in generate_contact_form_stream():
                    yield chunk
            
            return Response(
                stream_with_context(combined_stream()), 
                content_type='text/event-stream'
            )
        
        # Detectar si el usuario muestra interés o acepta proporcionar información de contacto
        interest_keywords = ['interesado', 'interesada', 'me interesa', 'quiero saber', 'más información', 
                            'contactar', 'contacto', 'ok', 'sí', 'si', 'claro', 'por supuesto', 'adelante',
                            'contactarme', 'llamarme', 'información de contacto', 'mis datos', 'proporcionar',
                            'formulario', 'datos', 'gustaría', 'quiero']
        
        shows_interest = any(keyword in user_message for keyword in interest_keywords)
        
        # Si el usuario muestra interés o menciona algo relacionado con proporcionar información, mostrar el formulario directamente
        if shows_interest and not session.get('form_shown', False):
            session['form_shown'] = True
            session['last_was_form'] = True
            return Response(
                stream_with_context(generate_contact_form_stream()),
                content_type='text/event-stream'
            )
        
        # Capturar respuestas del LLM para detectar cuando sugiere proporcionar información de contacto
        def capture_and_check_response():
            full_response = ""
            contact_keywords = ['contacto', 'información de contacto', 'datos', 'proporcionar', 'contactarte', 
                               'representante', '¿te gustaría', 'información personal', 'email', 'correo', 'teléfono']
            
            # Obtener respuesta del LLM
            for chunk in send_chat_request(user_message):
                yield chunk
                
                # Extraer el token si existe
                try:
                    data = json.loads(chunk.replace('data: ', ''))
                    if 'token' in data:
                        full_response += data['token']
                        
                        # Si la respuesta del LLM sugiere proporcionar información de contacto y no se ha mostrado el formulario
                        if any(keyword in full_response.lower() for keyword in contact_keywords) and not session.get('form_shown', False):
                            # Marcar que el formulario se mostrará
                            session['form_shown'] = True
                            session['last_was_form'] = True
                            
                            # Después de que termine la respuesta actual, mostrar el formulario
                            if 'done' in data and data['done']:
                                for form_chunk in generate_contact_form_stream():
                                    yield form_chunk
                except:
                    pass
        
        # Mostrar formulario después de cada respuesta sustancial si no se ha mostrado antes
        if session['message_count'] >= 2 and not session.get('form_shown', False):
            # Marcar que el formulario se ha mostrado
            session['form_shown'] = True
            session['last_was_form'] = True
            
            def response_with_form():
                # Primero enviamos la respuesta normal
                for chunk in send_chat_request(user_message):
                    yield chunk
                
                # Luego enviamos el formulario de contacto
                for chunk in generate_contact_form_stream():
                    yield chunk
            
            return Response(
                stream_with_context(response_with_form()),
                content_type='text/event-stream'
            )
        
        # Para otras preguntas, usar LM Studio normalmente y capturar la respuesta para detectar sugerencias de contacto
        return Response(
            stream_with_context(capture_and_check_response()), 
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
    
    @app.route('/submit-contact', methods=['POST'])
    def submit_contact():
        """Endpoint para guardar los datos del formulario de contacto"""
        data = request.json
        
        # Validar datos mínimos
        if not data.get('name') or not data.get('email'):
            return jsonify({
                "success": False,
                "message": "El nombre y el correo electrónico son obligatorios."
            })
        
        # Guardar los datos
        try:
            data_manager.save_lead(data)
            return jsonify({
                "success": True,
                "message": "Datos guardados correctamente. Pronto nos pondremos en contacto contigo."
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Error al guardar los datos: {str(e)}"
            }) 