"""
Define las rutas específicas para el sistema de agentes del chatbot.
"""
import json
import traceback
from flask import request, jsonify, Response, stream_with_context, session, render_template, current_app
from agents.agent_manager import AgentManager
from agents.general_agent import GeneralAgent
from agents.sales_agent import SalesAgent
from agents.engineer_agent import EngineerAgent
from agents.data_collection_agent import DataCollectionAgent

# Inicializar el gestor de agentes y registrar los agentes
agent_manager = AgentManager()
agent_manager.register_agent(GeneralAgent())     # Primera prioridad para bienvenida e información general
agent_manager.register_agent(SalesAgent())       # Alta prioridad para ventas  
agent_manager.register_agent(EngineerAgent())    # Alta prioridad para consultas técnicas
agent_manager.register_agent(DataCollectionAgent()) # Última prioridad para recopilar datos

def register_agent_routes(app):
    """Registra las rutas específicas para el sistema de agentes"""
    
    @app.route('/agents')
    def agents_home():
        """Ruta principal para la interfaz que utiliza el sistema de agentes"""
        # Reiniciar el contexto del gestor de agentes
        agent_manager.reset()
        
        # Reiniciar variables de sesión
        session['message_count'] = 0
        session['form_shown'] = False
        session['form_active'] = False
        session['form_completed'] = False
        session['last_user_message'] = ''
        session['current_agent'] = None
        session['previous_agent'] = None
        session['user_info'] = {}
        session['project_info'] = {}
        
        # Renderizar la plantilla con un flag para indicar que estamos usando agentes
        return render_template('index.html', use_agents=True)
    
    @app.route('/agent/health', methods=['GET'])
    def agent_health():
        """Endpoint para verificar el estado de la conexión con LM Studio en modo agentes"""
        from services.lm_studio import check_lm_studio_connection
        
        lm_studio_connected = check_lm_studio_connection()
        
        return jsonify({
            "status": "ok",
            "lm_studio_connected": lm_studio_connected
        })
    
    @app.route('/agent/chat', methods=['POST'])
    def agent_chat():
        """Endpoint para chat con agentes (no streaming)"""
        data = request.json
        user_message = data.get('message', '')
        
        # Crear o actualizar el contexto para los agentes
        context = {
            'message_count': session.get('message_count', 0),
            'form_shown': session.get('form_shown', False),
            'form_active': session.get('form_active', False),
            'form_completed': session.get('form_completed', False),
            'last_user_message': session.get('last_user_message', ''),
            'current_agent': session.get('current_agent', None),
            'previous_agent': session.get('previous_agent', None),
            'user_info': session.get('user_info', {}),
            'project_info': session.get('project_info', {})
        }
        
        try:
            # Procesar el mensaje con el gestor de agentes
            response_text = ""
            for chunk in agent_manager.process_message(user_message, context):
                response_text += chunk
            
            # Actualizar la sesión con el contexto actualizado
            session['current_agent'] = context.get('current_agent')
            session['previous_agent'] = context.get('previous_agent')
            session['user_info'] = context.get('user_info', {})
            session['project_info'] = context.get('project_info', {})
            
            # Actualizar variables de formulario si fueron modificadas por los agentes
            if 'form_completed' in context:
                session['form_completed'] = context['form_completed']
            if 'form_shown' in context:
                session['form_shown'] = context['form_shown']
            if 'form_active' in context:
                session['form_active'] = context['form_active']
            
            return jsonify({
                "success": True,
                "response": response_text,
                "agent": context.get('current_agent', 'Unknown')
            })
            
        except Exception as e:
            print(f"Error al procesar mensaje con agentes: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e),
                "response": "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
            })
    
    @app.route('/agent/chat/stream', methods=['GET'])
    def agent_chat_stream():
        """Endpoint para chat con agentes (streaming)"""
        user_message = request.args.get('message', '')
        
        # Incrementar contador de mensajes
        message_count = session.get('message_count', 0) + 1
        session['message_count'] = message_count
        
        # Guardar el mensaje del usuario en la sesión
        session['last_user_message'] = user_message
        
        # Capturar valores de sesión actuales para usar en el generador
        form_shown = session.get('form_shown', False)
        form_active = session.get('form_active', False)
        form_completed = session.get('form_completed', False)
        current_agent_name = session.get('current_agent')
        previous_agent_name = session.get('previous_agent')
        user_info = session.get('user_info', {})
        project_info = session.get('project_info', {})
        messages = session.get('messages', [])
        
        # Verificar si es un mensaje especial para cambiar de agente
        if user_message.startswith('!cambiar_agente:'):
            try:
                # Extraer el nombre del agente
                agent_id = user_message.split(':', 1)[1].strip()
                
                # Actualizar el agente actual y anterior en la sesión
                session['previous_agent'] = current_agent_name
                session['current_agent'] = agent_id
                
                # Registrar el cambio de agente
                app.logger.info(f"Cambiando de agente: {previous_agent_name} -> {agent_id}")
                
                # Crear contexto para los agentes
                context = {
                    'message_count': message_count,
                    'form_shown': form_shown,
                    'form_active': form_active,
                    'form_completed': form_completed,
                    'last_user_message': user_message,
                    'current_agent': agent_id,
                    'previous_agent': previous_agent_name,
                    'user_info': user_info,
                    'project_info': project_info,
                    'messages': messages
                }
                
                # Mensaje de continuación para el nuevo agente
                continuation_message = "Por favor, continúa la conversación basándote en el contexto anterior."
                
                @stream_with_context
                def agent_change_response():
                    # Mensaje de confirmación
                    confirmation = f"Ahora estás hablando con el agente: {agent_id.replace('Agent', '')}"
                    for char in confirmation:
                        yield f"data: {json.dumps({'token': char})}\n\n"
                    
                    # Procesar un mensaje de continuación con el nuevo agente
                    try:
                        # Obtener la respuesta del nuevo agente
                        for chunk in agent_manager.process_message(continuation_message, context):
                            # Verificar que el chunk es una cadena de texto
                            if isinstance(chunk, str):
                                # Formatear la respuesta para SSE
                                yield f"data: {json.dumps({'token': chunk})}\n\n"
                            else:
                                # Si no es una cadena, continuar
                                continue
                    except Exception as e:
                        current_app.logger.error(f"Error al procesar mensaje de continuación: {str(e)}")
                    
                    # Marcar como completado y enviar el nombre del agente
                    yield f"data: {json.dumps({'done': True, 'agent': agent_id})}\n\n"
                
                return Response(agent_change_response(), mimetype='text/event-stream')
            except Exception as e:
                app.logger.error(f"Error al cambiar de agente: {str(e)}")
                return Response("data: {}\n\n", mimetype='text/event-stream')
        
        # Verificar si el mensaje de texto solicita cambiar de agente
        agent_keywords = {
            'técnico': 'EngineerAgent',
            'tecnico': 'EngineerAgent',
            'ingeniero': 'EngineerAgent',
            'ventas': 'SalesAgent',
            'comercial': 'SalesAgent',
            'precios': 'SalesAgent',
            'datos': 'DataCollectionAgent',
            'contacto': 'DataCollectionAgent',
            'general': 'GeneralAgent',
            'información': 'GeneralAgent',
            'informacion': 'GeneralAgent'
        }
        
        # Verificar si el mensaje contiene palabras clave para cambiar de agente
        for keyword, agent_id in agent_keywords.items():
            if keyword in user_message.lower() and f"cambiar a {keyword}" in user_message.lower():
                # Actualizar el agente actual y anterior en la sesión
                session['previous_agent'] = current_agent_name
                session['current_agent'] = agent_id
                
                # Registrar el cambio de agente
                app.logger.info(f"Cambiando de agente por palabra clave: {previous_agent_name} -> {agent_id}")
                
                # Crear contexto para los agentes
                context = {
                    'message_count': message_count,
                    'form_shown': form_shown,
                    'form_active': form_active,
                    'form_completed': form_completed,
                    'last_user_message': user_message,
                    'current_agent': agent_id,
                    'previous_agent': previous_agent_name,
                    'user_info': user_info,
                    'project_info': project_info,
                    'messages': messages
                }
                
                @stream_with_context
                def keyword_agent_change_response():
                    # Mensaje de confirmación
                    confirmation = f"Cambiando al agente: {agent_id.replace('Agent', '')}"
                    for char in confirmation:
                        yield f"data: {json.dumps({'token': char})}\n\n"
                    
                    # Procesar el mensaje con el gestor de agentes
                    try:
                        # Obtener la respuesta del gestor de agentes
                        for chunk in agent_manager.process_message(user_message, context):
                            # Verificar que el chunk es una cadena de texto
                            if isinstance(chunk, str):
                                # Formatear la respuesta para SSE
                                yield f"data: {json.dumps({'token': chunk})}\n\n"
                            else:
                                # Si no es una cadena, continuar
                                continue
                    except Exception as e:
                        current_app.logger.error(f"Error al procesar mensaje con cambio de agente por palabra clave: {str(e)}")
                    
                    # Marcar como completado y enviar el nombre del agente
                    yield f"data: {json.dumps({'done': True, 'agent': agent_id})}\n\n"
                
                return Response(keyword_agent_change_response(), mimetype='text/event-stream')
        
        # Si no es un mensaje para cambiar de agente, procesarlo normalmente
        # Crear contexto para los agentes
        context = {
            'message_count': message_count,
            'form_shown': form_shown,
            'form_active': form_active,
            'form_completed': form_completed,
            'last_user_message': user_message,
            'current_agent': current_agent_name,
            'previous_agent': previous_agent_name,
            'user_info': user_info,
            'project_info': project_info,
            'messages': messages
        }
        
        # Procesar el mensaje y obtener la respuesta
        # Capturar el resultado para actualizar la sesión después
        result_context = {}
        
        @stream_with_context
        def generate_response():
            nonlocal result_context
            try:
                # Procesar el mensaje con el gestor de agentes
                for chunk in agent_manager.process_message(user_message, context):
                    # Verificar que el chunk es una cadena de texto
                    if isinstance(chunk, str):
                        # Formatear la respuesta para SSE
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                    else:
                        # Si no es una cadena, continuar
                        continue
                
                # Guardar el contexto actualizado para usarlo después
                result_context = context.copy()
                
                # Marcar como completado y enviar el nombre del agente
                agent_id = context.get('current_agent', 'Unknown')
                yield f"data: {json.dumps({'done': True, 'agent': agent_id})}\n\n"
            except Exception as e:
                current_app.logger.error(f"Error al procesar mensaje: {str(e)}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        response = Response(generate_response(), mimetype='text/event-stream')
        
        # Configurar una función de cierre para actualizar la sesión después de que se complete la respuesta
        @response.call_on_close
        def on_close():
            # Actualizar la sesión con el contexto actualizado
            if result_context:
                with app.app_context():
                    with app.test_request_context():
                        session['current_agent'] = result_context.get('current_agent')
                        session['previous_agent'] = result_context.get('previous_agent')
                        session['user_info'] = result_context.get('user_info', {})
                        session['project_info'] = result_context.get('project_info', {})
                        
                        # Actualizar variables de formulario si fueron modificadas
                        if 'form_completed' in result_context:
                            session['form_completed'] = result_context['form_completed']
                        if 'form_shown' in result_context:
                            session['form_shown'] = result_context['form_shown']
                        if 'form_active' in result_context:
                            session['form_active'] = result_context['form_active']
        
        return response
    
    @app.route('/agent/reset', methods=['POST'])
    def agent_reset():
        """Endpoint para reiniciar el contexto de los agentes"""
        # Reiniciar el contexto del gestor de agentes
        agent_manager.reset()
        
        # Reiniciar variables de sesión
        session['message_count'] = 0
        session['form_shown'] = False
        session['form_active'] = False
        session['form_completed'] = False
        session['last_user_message'] = ''
        session['current_agent'] = None
        session['previous_agent'] = None
        session['user_info'] = {}
        session['project_info'] = {}
        
        return jsonify({
            "success": True,
            "message": "Contexto de agentes reiniciado correctamente"
        }) 