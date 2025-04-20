"""
Define las rutas específicas para el sistema de agentes del chatbot.
"""
import json
import traceback
import re
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
        
        # Verificar si este mensaje es una solicitud de análisis de archivo
        is_file_analysis = user_message.startswith('ANALYSIS_REQUEST:')
        
        # Obtener información sobre el agente actual explícitamente enviada desde el cliente
        client_current_agent = request.args.get('current_agent')
        
        # Verificar si hay contenido de archivo en la sesión
        file_content = session.get('project_file_content')
        file_name = session.get('project_file_name')
        
        # Si es una solicitud de análisis y no hay archivo en sesión, extraer el contenido
        if is_file_analysis and not file_content:
            # Extraer contenido del archivo
            try:
                # Separar el contenido del archivo
                file_marker_index = user_message.find("cargado con el siguiente contenido:")
                if file_marker_index > 0:
                    file_content = user_message[file_marker_index + len("cargado con el siguiente contenido:"):].strip()
                    
                    # Extraer nombre del archivo si está presente
                    file_name_match = re.search(r"Archivo de proyecto '([^']+)'", user_message)
                    if file_name_match:
                        file_name = file_name_match.group(1)
                    else:
                        file_name = "documento_proyecto.txt"
                    
                    # Guardar en sesión
                    session['project_file_content'] = file_content
                    session['project_file_name'] = file_name
            except Exception as e:
                app.logger.error(f"Error al extraer contenido del archivo: {str(e)}")
        
        # Verificar inmediatamente si es un mensaje sobre call center con IA - ALTA PRIORIDAD
        force_engineer = False
        force_sales = False
        message_lower = user_message.lower()
        
        # Si es una solicitud de análisis, forzar el uso del EngineerAgent
        if is_file_analysis:
            app.logger.info(f"¡ALTA PRIORIDAD! Solicitud de análisis de archivo para EngineerAgent")
            client_current_agent = 'EngineerAgent'
            force_engineer = True
            
            # Modificar el mensaje para incluir instrucciones específicas
            if file_content and file_name:
                user_message = f"Analiza el siguiente documento de proyecto llamado '{file_name}' y proporciona una estimación detallada del tiempo y recursos necesarios para implementarlo. El documento contiene:\n\n{file_content}\n\nConsideraciones importantes: Menciona tecnologías específicas, identifica posibles desafíos técnicos, estima tiempos de desarrollo, y prepara información que el agente de ventas pueda usar para generar un presupuesto."
        
        # Obtener el agente actual de la sesión
        session_agent = session.get('current_agent')
        
        # Mantener agente para mensajes cortos (como "si", "no", etc.) - para continuidad
        is_short_message = len(message_lower.split()) <= 2
        if is_short_message and session_agent:
            app.logger.info(f"Mensaje corto detectado. Manteniendo agente actual: {session_agent}")
            client_current_agent = session_agent
        
        # Patrones muy específicos que siempre deben ir al agente técnico
        call_center_ai_exact_patterns = [
            'call center con agentes de ai', 
            'call center con ia',
            'call center que gestiona llamadas',
            'call center con agentes', 
            'pasarlo a agentes de ai',
            'me proyecto es', 
            'mi proyecto es',
            'proyecto de call center'
        ]
        
        # Si hay una coincidencia exacta, forzar el agente técnico inmediatamente
        if any(pattern in message_lower for pattern in call_center_ai_exact_patterns):
            app.logger.info(f"¡ALTA PRIORIDAD! Coincidencia exacta para EngineerAgent: {user_message}")
            client_current_agent = 'EngineerAgent'
            force_engineer = True
        
        # Patrones específicos para el agente de ventas
        sales_exact_patterns = [
            'presupuesto', 
            'cotización', 
            'cotizacion', 
            'precio', 
            'costo', 
            'pasame con el agente de ventas',
            'hablar con ventas',
            'quiero una cotización',
            'quiero un presupuesto'
        ]
        
        # Si hay patrones de ventas, forzar el agente de ventas
        if any(pattern in message_lower for pattern in sales_exact_patterns):
            app.logger.info(f"¡ALTA PRIORIDAD! Coincidencia para SalesAgent: {user_message}")
            client_current_agent = 'SalesAgent'
            force_sales = True
            
        # Buscar combinaciones específicas de palabras clave
        if ('call center' in message_lower or 'centro de llamadas' in message_lower or 'contact center' in message_lower):
            if ('ai' in message_lower or 'ia' in message_lower or 'inteligencia' in message_lower or 
                'agentes' in message_lower or 'automatizar' in message_lower or 'automático' in message_lower):
                app.logger.info(f"¡ALTA PRIORIDAD! Coincidencia de keywords para EngineerAgent: {user_message}")
                client_current_agent = 'EngineerAgent'
                force_engineer = True
        
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
        
        # Si la última vez el usuario explícitamente pidió el agente de ventas y ahora envía un mensaje corto
        # forzar que se mantenga en el agente de ventas
        last_message = session.get('last_user_message', '').lower()
        if session_agent == 'SalesAgent' and is_short_message:
            app.logger.info(f"Manteniendo SalesAgent para mensaje corto después de solicitud explícita")
            client_current_agent = 'SalesAgent'
            force_sales = True
        
        # Si el cliente envió información sobre el agente actual, actualizamos la sesión
        if client_current_agent:
            current_agent_name = client_current_agent
            session['current_agent'] = client_current_agent
            app.logger.info(f"Cliente solicitó o se forzó el agente: {client_current_agent}")
        
        previous_agent_name = session.get('previous_agent')
        user_info = session.get('user_info', {})
        project_info = session.get('project_info', {})
        messages = session.get('messages', [])
        
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
            'messages': messages,
            'force_engineer': force_engineer,  # Nuevo parámetro para forzar el agente técnico
            'force_sales': force_sales         # Nuevo parámetro para forzar el agente de ventas
        }
        
        # Verificar si es un mensaje especial para cambiar de agente
        if user_message.startswith('!cambiar_agente:'):
            try:
                # Extraer el nombre del agente
                agent_id = user_message.split(':', 1)[1].strip()
                
                # Actualizar el agente actual y anterior en la sesión
                session['previous_agent'] = current_agent_name
                session['current_agent'] = agent_id
                
                # Actualizar el contexto
                context['current_agent'] = agent_id
                context['previous_agent'] = current_agent_name
                
                # Si se cambia a SalesAgent, establecer flag
                if agent_id == 'SalesAgent':
                    context['force_sales'] = True
                
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
            if keyword in user_message.lower() and (f"cambiar a {keyword}" in user_message.lower() or 
                                                     f"pasame con {keyword}" in user_message.lower() or
                                                     f"pasar a {keyword}" in user_message.lower() or
                                                     f"hablar con {keyword}" in user_message.lower()):
                # Actualizar el agente actual y anterior
                session['previous_agent'] = current_agent_name
                session['current_agent'] = agent_id
                
                # Actualizar el contexto
                context['current_agent'] = agent_id
                context['previous_agent'] = current_agent_name
                
                # Si se cambia a SalesAgent, establecer flag
                if agent_id == 'SalesAgent':
                    context['force_sales'] = True
                
                # Registrar el cambio de agente
                app.logger.info(f"Cambiando de agente por palabra clave: {previous_agent_name} -> {agent_id}")
                
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
        
        # Verificar si es un proyecto de call center con IA
        call_center_ai_keywords = [
            'call center', 'centro de llamadas', 'contact center', 'gestiona llamadas', 
            'mi proyecto es', 'pasarlo a agentes de ai', 'agentes de ai',
            'agentes virtuales', 'ia', 'ai', 'inteligencia artificial'
        ]
        
        # Si el mensaje contiene palabras clave de call center con IA, forzar el uso del EngineerAgent
        if any(keyword in message_lower for keyword in call_center_ai_keywords):
            if ('proyecto' in message_lower and any(kw in message_lower for kw in ['call center', 'ai', 'ia'])) or \
               ('mi proyecto' in message_lower) or \
               ('me proyecto' in message_lower) or \
               ('call center' in message_lower and any(kw in message_lower for kw in ['ai', 'ia', 'inteligencia', 'agentes'])):
                # Forzar el uso del EngineerAgent
                context['current_agent'] = 'EngineerAgent'
                context['force_engineer'] = True
                session['current_agent'] = 'EngineerAgent'
                app.logger.info("Forzando EngineerAgent en el contexto para proyecto de call center con IA")
        
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
                        # Asegurar que el agente técnico persista para call center AI
                        if force_engineer or result_context.get('force_engineer', False):
                            result_context['current_agent'] = 'EngineerAgent'
                        
                        # Asegurar que el agente de ventas persista cuando se ha solicitado
                        if force_sales or result_context.get('force_sales', False):
                            result_context['current_agent'] = 'SalesAgent'
                            
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