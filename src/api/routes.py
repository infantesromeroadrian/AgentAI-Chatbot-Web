"""
Define las rutas y endpoints de la API del chatbot.
"""
import json
import re
import traceback
from flask import request, jsonify, render_template, Response, stream_with_context, session
from services.lm_studio import send_chat_request, check_lm_studio_connection
from utils.alisys_info import get_alisys_info, generate_alisys_info_stream, generate_contact_form_stream
from data.data_manager import DataManager
from data.database import get_leads
from agents.agent_manager import AgentManager
from agents.general_agent import GeneralAgent
from agents.sales_agent import SalesAgent
from agents.engineer_agent import EngineerAgent
from agents.data_collection_agent import DataCollectionAgent

# Inicializar el gestor de datos
data_manager = DataManager()

# Inicializar el gestor de agentes
agent_manager = AgentManager()

# Registrar los agentes disponibles - El orden determina la prioridad
agent_manager.register_agent(GeneralAgent())     # Primera prioridad para bienvenida e información general
agent_manager.register_agent(SalesAgent())       # Alta prioridad para ventas
agent_manager.register_agent(EngineerAgent())    # Alta prioridad para consultas técnicas
agent_manager.register_agent(DataCollectionAgent()) # Última prioridad para recopilar datos

def register_routes(app):
    """Registra todas las rutas de la aplicación"""
    
    # Configurar la sesión
    app.secret_key = 'alisys_chatbot_secret_key'
    
    @app.route('/')
    def home():
        """Ruta principal que muestra la interfaz del chatbot"""
        # Reiniciar todas las variables de sesión para evitar problemas
        session['message_count'] = 0
        session['form_shown'] = False
        session['last_was_form'] = False
        session['form_active'] = False
        session['form_completed'] = False
        session['last_user_message'] = ''
        
        # Reiniciar el contexto del gestor de agentes
        agent_manager.reset()
        
        return render_template('index.html')
    
    @app.route('/health', methods=['GET'])
    def health():
        """Endpoint para verificar el estado de la conexión con LM Studio"""
        lm_studio_connected = check_lm_studio_connection()
        
        return jsonify({
            "status": "ok",
            "lm_studio_connected": lm_studio_connected
        })
    
    def _update_session_state(user_message):
        """Actualiza el estado de la sesión con el mensaje del usuario"""
        # Guardar el mensaje del usuario en la sesión para uso posterior
        session['last_user_message'] = user_message
        
        # Imprimir el estado actual de la sesión para depuración
        print(f"Estado de sesión: message_count={session.get('message_count', 0)}, form_shown={session.get('form_shown', False)}, form_active={session.get('form_active', False)}, form_completed={session.get('form_completed', False)}")
        
        # Si el último mensaje fue un formulario y recibimos una respuesta, no incrementamos el contador
        if not session.get('last_was_form', False):
            # Incrementar contador de mensajes
            if 'message_count' not in session:
                session['message_count'] = 0
            session['message_count'] += 1
        else:
            # Resetear el flag de último mensaje como formulario
            session['last_was_form'] = False
    
    def _handle_form_response():
        """Maneja la respuesta a un campo del formulario"""
        def simple_response():
            yield f"data: {json.dumps({'token': 'Procesando tu respuesta...'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return Response(
            stream_with_context(simple_response()), 
            content_type='text/event-stream'
        )
    
    def _handle_completed_form():
        """Maneja el caso cuando el formulario ya ha sido completado"""
        # Verificar si hay datos de contacto guardados
        leads = get_leads()
        
        # Verificar si hay leads y si el último lead tiene los datos mínimos
        valid_lead_exists = False
        if leads and len(leads) > 0:
            last_lead = leads[-1]
            if hasattr(last_lead, 'name') and hasattr(last_lead, 'email') and last_lead.name and last_lead.email:
                valid_lead_exists = True
        
        # Si no hay leads válidos, probablemente hubo un error o el formulario no se completó realmente
        if not valid_lead_exists:
            # Reiniciar variables de sesión
            session['form_completed'] = False
            session['form_shown'] = False
            session['form_active'] = False
            return None
        
        # Responder con un mensaje de despedida
        def farewell_response():
            response = "Gracias por tu mensaje. Un representante de Alisys ya ha recibido tus datos y se pondrá en contacto contigo en breve. Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**."
            yield f"data: {json.dumps({'token': response})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return Response(
            stream_with_context(farewell_response()), 
            content_type='text/event-stream'
        )
    
    def _build_agent_context():
        """Construye el contexto para los agentes a partir de la sesión"""
        return {
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
    
    def _process_with_agents(user_message, context):
        """Procesa el mensaje con el gestor de agentes"""
        try:
            # Obtener la respuesta del agente adecuado
            for chunk in agent_manager.process_message(user_message, context):
                # Formatear la respuesta para SSE
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            
            # Marcar como completado
            yield f"data: {json.dumps({'done': True})}\n\n"
            
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
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    @app.route('/chat/stream', methods=['GET'])
    def chat_stream():
        """Endpoint para streaming de respuestas del chatbot"""
        user_message = request.args.get('message', '')
        
        # Actualizar el estado de la sesión
        _update_session_state(user_message)
        
        # Verificar si es una respuesta a un campo del formulario
        if session.get('form_active', False):
            return _handle_form_response()
        
        # Verificar si el formulario ya ha sido completado
        if session.get('form_completed', False):
            form_response = _handle_completed_form()
            if form_response:
                return form_response
        
        # Crear o actualizar el contexto para los agentes
        context = _build_agent_context()
        
        # Usar el sistema de agentes para procesar el mensaje
        return Response(
            stream_with_context(_process_with_agents(user_message, context)), 
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
        print(f"Datos recibidos en submit-contact: {data}")
        
        # Si el usuario envió todos los datos en un solo mensaje, intentar extraerlos
        if len(data) == 1 and 'message' in data:
            message = data['message']
            print(f"Procesando mensaje único: {message}")
            
            # Extraer datos usando expresiones regulares
            extracted_data = {}
            
            # Patrones para extraer información
            name_patterns = [
                r'(?:mi nombre es|me llamo|soy) ([^,\.]+)',
                r'nombre:?\s*([^,\.]+)',
                r'nombre completo:?\s*([^,\.]+)'
            ]
            
            email_patterns = [
                r'(?:mi email|mi correo|email|correo) (?:es|:)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            
            phone_patterns = [
                r'(?:mi teléfono|mi telefono|teléfono|telefono|móvil|movil) (?:es|:)?\s*([+0-9\s]{7,})',
                r'(?:tlf|tel|phone):?\s*([+0-9\s]{7,})'
            ]
            
            company_patterns = [
                r'(?:mi empresa|empresa|compañía|compania) (?:es|:)?\s*([^,\.]+)',
                r'(?:trabajo en|trabajo para|laboro en) ([^,\.]+)'
            ]
            
            # Extraer nombre
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    extracted_data['name'] = match.group(1).strip()
                    break
            
            # Extraer email
            for pattern in email_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    extracted_data['email'] = match.group(1).strip()
                    break
            
            # Extraer teléfono
            for pattern in phone_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    extracted_data['phone'] = match.group(1).strip()
                    break
            
            # Extraer empresa
            for pattern in company_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    extracted_data['company'] = match.group(1).strip()
                    break
            
            # Si se extrajeron datos, usarlos
            if extracted_data:
                print(f"Datos extraídos del mensaje: {extracted_data}")
                data.update(extracted_data)
        
        # Validar datos mínimos
        if not data.get('name') or not data.get('email'):
            return jsonify({
                "success": False,
                "message": "El nombre y el correo electrónico son obligatorios."
            })
        
        # Extraer el mensaje de la conversación si está disponible
        # Esto puede ser útil para entender el contexto de la consulta
        user_message = session.get('last_user_message', '')
        if user_message and 'message' not in data:
            data['message'] = user_message
        
        # Guardar los datos
        try:
            # Asegurarse de que todos los campos necesarios estén presentes
            # Si no están, usar valores por defecto
            if not data.get('phone'):
                data['phone'] = 'No proporcionado'
            if not data.get('company'):
                data['company'] = 'No proporcionada'
            if not data.get('interest'):
                data['interest'] = 'No especificado'
            
            # Guardar el lead usando el data_manager (que ahora guarda en SQLite también)
            result = data_manager.save_lead(data)
            
            # Registrar en el log para depuración
            print(f"Lead guardado: {data}, resultado: {result}")
            
            # Marcar que el formulario ha sido completado
            session['form_completed'] = True
            session['form_active'] = False
            session['form_shown'] = True
            
            return jsonify({
                "success": True,
                "message": "Datos guardados correctamente. Pronto nos pondremos en contacto contigo."
            })
        except Exception as e:
            print(f"Error al guardar lead: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "message": f"Error al guardar los datos: {str(e)}"
            })
    
    @app.route('/admin/leads', methods=['GET'])
    def view_leads():
        """Endpoint para ver los leads guardados en la base de datos"""
        # Verificar autenticación básica (esto debería mejorarse en producción)
        auth = request.authorization
        if not auth or auth.username != 'admin' or auth.password != 'alisys2024':
            return Response(
                'Autenticación requerida', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        
        try:
            # Obtener leads de la base de datos
            leads = get_leads()
            
            # Convertir a formato JSON
            leads_data = []
            for lead in leads:
                leads_data.append({
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'phone': lead.phone,
                    'company': lead.company,
                    'interest': lead.interest,
                    'message': lead.message,
                    'created_at': lead.created_at.isoformat() if lead.created_at else None
                })
            
            # Renderizar plantilla HTML con los leads
            return render_template('leads.html', leads=leads_data)
        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Error al obtener los leads de la base de datos."
            })
    
    @app.route('/admin/get-last-lead', methods=['GET'])
    def get_last_lead():
        """Endpoint para obtener el último lead guardado"""
        try:
            # Obtener leads de la base de datos
            leads = get_leads()
            
            if not leads:
                # Si no hay leads, intentar obtener del JSON
                json_leads = data_manager.get_leads()
                if json_leads:
                    last_lead = json_leads[-1]
                    return jsonify({
                        "success": True,
                        "lead": {
                            "name": last_lead.get('name', ''),
                            "email": last_lead.get('email', ''),
                            "phone": last_lead.get('phone', 'No proporcionado'),
                            "company": last_lead.get('company', 'No proporcionada'),
                            "interest": last_lead.get('interest', 'No especificado')
                        }
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "No se encontraron leads"
                    })
            
            # Obtener el último lead (el más reciente)
            last_lead = leads[-1]
            
            # Convertir a formato JSON
            lead_data = {
                'id': last_lead.id,
                'name': last_lead.name,
                'email': last_lead.email,
                'phone': last_lead.phone,
                'company': last_lead.company,
                'interest': last_lead.interest,
                'message': last_lead.message,
                'created_at': last_lead.created_at.isoformat() if last_lead.created_at else None
            }
            
            return jsonify({
                "success": True,
                "lead": lead_data
            })
        except Exception as e:
            print(f"Error al obtener el último lead: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "message": f"Error al obtener el último lead: {str(e)}"
            }) 