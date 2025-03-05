"""
Define las rutas específicas para el sistema de agentes del chatbot.
"""
import json
import traceback
from flask import request, jsonify, Response, stream_with_context, session, render_template
from agents.agent_manager import AgentManager
from agents.general_agent import GeneralAgent
from agents.sales_agent import SalesAgent
from agents.engineer_agent import EngineerAgent
from agents.data_collection_agent import DataCollectionAgent

# Inicializar el gestor de agentes para las rutas específicas
agent_manager = AgentManager()

# Registrar los agentes disponibles
agent_manager.register_agent(GeneralAgent())
agent_manager.register_agent(SalesAgent())
agent_manager.register_agent(EngineerAgent())
agent_manager.register_agent(DataCollectionAgent())

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
        if 'message_count' not in session:
            session['message_count'] = 0
        session['message_count'] += 1
        
        # Guardar el mensaje del usuario en la sesión
        session['last_user_message'] = user_message
        
        # Verificar si es un mensaje especial para cambiar de agente
        if user_message.startswith('!cambiar_agente:'):
            try:
                # Extraer el nombre del agente
                agent_id = user_message.split(':', 1)[1].strip()
                
                # Actualizar el agente actual y anterior en la sesión
                session['previous_agent'] = session.get('current_agent')
                session['current_agent'] = agent_id
                
                # Registrar el cambio de agente
                app.logger.info(f"Cambiando de agente: {session.get('previous_agent')} -> {agent_id}")
                
                # Crear o actualizar el contexto para los agentes
                context = {
                    'message_count': session.get('message_count', 0),
                    'form_shown': session.get('form_shown', False),
                    'form_active': session.get('form_active', False),
                    'form_completed': session.get('form_completed', False),
                    'last_user_message': session.get('last_user_message', ''),
                    'current_agent': agent_id,
                    'previous_agent': session.get('previous_agent', None),
                    'user_info': session.get('user_info', {}),
                    'project_info': session.get('project_info', {}),
                    'messages': session.get('messages', [])
                }
                
                # Mensaje de continuación para el nuevo agente
                continuation_message = "Por favor, continúa la conversación basándote en el contexto anterior."
                
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
                                app.logger.warning(f"Chunk no es una cadena: {type(chunk)}")
                                continue
                        
                        # Actualizar la sesión con el contexto actualizado
                        session['current_agent'] = context.get('current_agent')
                        session['previous_agent'] = context.get('previous_agent')
                        session['user_info'] = context.get('user_info', {})
                        session['project_info'] = context.get('project_info', {})
                        session['messages'] = context.get('messages', [])
                    except Exception as e:
                        app.logger.error(f"Error al procesar mensaje de continuación: {str(e)}")
                    
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
        
        # Verificar si el mensaje contiene una solicitud de cambio de agente
        if user_message.lower().startswith(('con el agente', 'hablar con', 'cambiar a', 'quiero hablar con')):
            for keyword, agent_id in agent_keywords.items():
                if keyword in user_message.lower():
                    # Actualizar el agente actual y anterior en la sesión
                    session['previous_agent'] = session.get('current_agent')
                    session['current_agent'] = agent_id
                    
                    # Registrar el cambio de agente
                    app.logger.info(f"Cambiando de agente por texto: {session.get('previous_agent')} -> {agent_id}")
                    
                    # Crear o actualizar el contexto para los agentes
                    context = {
                        'message_count': session.get('message_count', 0),
                        'form_shown': session.get('form_shown', False),
                        'form_active': session.get('form_active', False),
                        'form_completed': session.get('form_completed', False),
                        'last_user_message': session.get('last_user_message', ''),
                        'current_agent': agent_id,
                        'previous_agent': session.get('previous_agent', None),
                        'user_info': session.get('user_info', {}),
                        'project_info': session.get('project_info', {}),
                        'messages': session.get('messages', [])
                    }
                    
                    # Mensaje de continuación para el nuevo agente
                    continuation_message = "Por favor, continúa la conversación basándote en el contexto anterior."
                    
                    def agent_change_text_response():
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
                                    app.logger.warning(f"Chunk no es una cadena: {type(chunk)}")
                                    continue
                            
                            # Actualizar la sesión con el contexto actualizado
                            session['current_agent'] = context.get('current_agent')
                            session['previous_agent'] = context.get('previous_agent')
                            session['user_info'] = context.get('user_info', {})
                            session['project_info'] = context.get('project_info', {})
                            session['messages'] = context.get('messages', [])
                        except Exception as e:
                            app.logger.error(f"Error al procesar mensaje de continuación: {str(e)}")
                        
                        # Marcar como completado y enviar el nombre del agente
                        yield f"data: {json.dumps({'done': True, 'agent': agent_id})}\n\n"
                    
                    return Response(agent_change_text_response(), mimetype='text/event-stream')
        
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
            'project_info': session.get('project_info', {}),
            'messages': session.get('messages', [])
        }
        
        # Registrar el agente actual antes de procesar
        app.logger.info(f"Procesando mensaje con agente: {context.get('current_agent')}")
        
        def process_with_agents():
            try:
                # Obtener la respuesta del agente adecuado
                for chunk in agent_manager.process_message(user_message, context):
                    # Verificar que el chunk es una cadena de texto
                    if isinstance(chunk, str):
                        # Formatear la respuesta para SSE
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                    else:
                        # Si no es una cadena, convertirla a cadena
                        app.logger.warning(f"Chunk no es una cadena: {type(chunk)}")
                        continue
                
                # Obtener el nombre del agente actual
                agent_name = context.get('current_agent', 'GeneralAgent')
                
                # Registrar el agente que respondió
                app.logger.info(f"Respuesta generada por el agente: {agent_name}")
                
                # Marcar como completado y enviar el nombre del agente
                yield f"data: {json.dumps({'done': True, 'agent': agent_name})}\n\n"
                
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
                
            except Exception as e:
                print(f"Error al procesar mensaje con agentes: {str(e)}")
                traceback.print_exc()
                yield f"data: {json.dumps({'token': 'Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo.'})}\n\n"
                yield f"data: {json.dumps({'done': True, 'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(process_with_agents()), 
            content_type='text/event-stream'
        )
    
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
            "message": "Contexto de agentes reiniciado correctamente."
        }) 