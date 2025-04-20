"""
Define las rutas y endpoints de la API del chatbot.
"""
import json
import re
import traceback
import os
import tempfile
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
from datetime import datetime

# Importar librería para procesar PDFs
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("PyPDF2 no está instalado. El soporte para PDFs está deshabilitado.")

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
        # Reiniciar variables de proyecto y archivo
        session['project_file_content'] = None
        session['project_file_name'] = None
        session['project_estimate'] = None
        
        # Reiniciar el contexto del gestor de agentes
        agent_manager.reset()
        
        return render_template('index.html')
    
    @app.route('/process-pdf', methods=['POST'])
    def process_pdf():
        """Endpoint para procesar archivos PDF y extraer su texto"""
        if not PDF_SUPPORT:
            return jsonify({
                "success": False,
                "error": "El soporte para PDFs no está disponible en el servidor"
            })
        
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No se ha proporcionado ningún archivo"
            })
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Nombre de archivo vacío"
            })
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                "success": False,
                "error": "El archivo debe ser un PDF"
            })
        
        try:
            # Guardar el archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                file.save(temp.name)
                temp_filename = temp.name
            
            # Procesar el PDF
            text = extract_text_from_pdf(temp_filename)
            
            # Eliminar el archivo temporal
            os.unlink(temp_filename)
            
            # Añadir el contenido del archivo a la sesión para uso posterior
            session['project_file_content'] = text
            session['project_file_name'] = file.filename
            
            return jsonify({
                "success": True,
                "text": text
            })
        except Exception as e:
            print(f"Error al procesar PDF: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/process-txt', methods=['POST'])
    def process_txt():
        """Endpoint para procesar archivos de texto"""
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No se ha proporcionado ningún archivo"
            })
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "Nombre de archivo vacío"
            })
        
        if not file.filename.lower().endswith('.txt'):
            return jsonify({
                "success": False,
                "error": "El archivo debe ser un TXT"
            })
        
        try:
            # Leer el contenido del archivo
            text = file.read().decode('utf-8', errors='ignore')
            
            # Añadir el contenido del archivo a la sesión para uso posterior
            session['project_file_content'] = text
            session['project_file_name'] = file.filename
            
            return jsonify({
                "success": True,
                "text": text
            })
        except Exception as e:
            print(f"Error al procesar TXT: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/project/estimate', methods=['POST'])
    def save_project_estimate():
        """Endpoint para guardar la estimación del proyecto"""
        data = request.json
        
        if not data or 'estimate' not in data:
            return jsonify({
                "success": False,
                "error": "No se ha proporcionado una estimación"
            })
        
        try:
            # Guardar la estimación en la sesión
            session['project_estimate'] = data['estimate']
            
            return jsonify({
                "success": True,
                "message": "Estimación guardada correctamente"
            })
        except Exception as e:
            print(f"Error al guardar estimación: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @app.route('/project/info', methods=['GET'])
    def get_project_info():
        """Endpoint para obtener la información del proyecto"""
        try:
            project_info = {
                "file_name": session.get('project_file_name'),
                "file_content": session.get('project_file_content'),
                "estimate": session.get('project_estimate')
            }
            
            return jsonify({
                "success": True,
                "project_info": project_info
            })
        except Exception as e:
            print(f"Error al obtener información del proyecto: {str(e)}")
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    def extract_text_from_pdf(file_path):
        """Extrae texto de un archivo PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    
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
            'project_info': session.get('project_info', {}),
            'project_file_content': session.get('project_file_content'),
            'project_file_name': session.get('project_file_name'),
            'project_estimate': session.get('project_estimate')
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
            
            # Guardar la estimación del proyecto si fue generada
            if 'project_estimate' in context and context['project_estimate']:
                session['project_estimate'] = context['project_estimate']
            
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
        
        # Si hay una estimación de proyecto, añadirla a los datos
        project_estimate = session.get('project_estimate')
        if project_estimate:
            data['project_estimate'] = project_estimate
        
        # Si hay un archivo de proyecto, añadir su nombre
        project_file_name = session.get('project_file_name')
        if project_file_name:
            data['project_file_name'] = project_file_name
        
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
                    'created_at': lead.created_at.isoformat() if lead.created_at else None,
                    'project_estimate': getattr(lead, 'project_estimate', None),
                    'project_file_name': getattr(lead, 'project_file_name', None)
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
                            "interest": last_lead.get('interest', 'No especificado'),
                            "project_estimate": last_lead.get('project_estimate', 'No disponible'),
                            "project_file_name": last_lead.get('project_file_name', 'No disponible')
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
                'created_at': last_lead.created_at.isoformat() if last_lead.created_at else None,
                'project_estimate': getattr(last_lead, 'project_estimate', None),
                'project_file_name': getattr(last_lead, 'project_file_name', None)
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
    
    @app.route('/admin/project-summaries', methods=['GET'])
    def project_summaries():
        """Endpoint para ver los resúmenes de proyectos generados"""
        # Verificar autenticación básica
        auth = request.authorization
        if not auth or auth.username != 'admin' or auth.password != 'alisys2024':
            return Response(
                'Autenticación requerida', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        
        try:
            # Obtener todos los archivos de resumen de proyectos
            data_dir = "data"
            summaries = []
            
            # Buscar archivos de resumen en formato TXT
            for filename in os.listdir(data_dir):
                if filename.startswith("client_summary_") and filename.endswith(".txt"):
                    file_path = os.path.join(data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            summary_text = f.read()
                        
                        # Extraer el email del nombre del archivo
                        email = filename.replace("client_summary_", "").replace(".txt", "").replace("_at_", "@")
                        
                        # Obtener la fecha de modificación del archivo
                        modified_time = os.path.getmtime(file_path)
                        modified_date = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                        
                        summaries.append({
                            'email': email,
                            'filename': filename,
                            'modified_date': modified_date,
                            'summary': summary_text
                        })
                    except Exception as e:
                        print(f"Error al leer el archivo {filename}: {str(e)}")
            
            # Buscar archivos de resumen en formato JSON
            for filename in os.listdir(data_dir):
                if filename.startswith("client_summary_") and filename.endswith(".json"):
                    file_path = os.path.join(data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)
                        
                        # Extraer el email del nombre del archivo
                        email = filename.replace("client_summary_", "").replace(".json", "").replace("_at_", "@")
                        
                        # Obtener la fecha de modificación del archivo
                        modified_time = os.path.getmtime(file_path)
                        modified_date = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Verificar si ya existe un resumen en formato TXT para este cliente
                        existing_summary = next((s for s in summaries if s['email'] == email), None)
                        
                        if not existing_summary:
                            # Generar un resumen en texto a partir de los datos JSON
                            client_info = summary_data.get('client_info', {})
                            project_info = summary_data.get('project_info', {})
                            technical_analysis = summary_data.get('technical_analysis', {})
                            
                            summary_text = f"""
RESUMEN DE LEAD - {modified_date}

INFORMACIÓN DEL CLIENTE:
- Nombre: {client_info.get('name', 'No proporcionado')}
- Email: {client_info.get('email', 'No proporcionado')}
- Teléfono: {client_info.get('phone', 'No proporcionado')}
- Empresa: {client_info.get('company', 'No proporcionada')}
- Interés: {client_info.get('interest', 'No especificado')}

RESUMEN DEL PROYECTO:
"""
                            
                            # Añadir detalles sobre el archivo subido si existe
                            if project_info.get('has_uploaded_file'):
                                summary_text += f"- Cliente subió archivo: {project_info.get('file_name')}\n"
                            
                            # Añadir análisis técnico si existe
                            if technical_analysis:
                                summary_text += f"""
ANÁLISIS TÉCNICO:
- Complejidad: {technical_analysis.get('complejidad', 'No determinada')}
- Tecnologías recomendadas: {', '.join(technical_analysis.get('tecnologias_recomendadas', ['No determinadas']))}
- Tiempo estimado: {technical_analysis.get('tiempo_estimado', 'No determinado')}
- Desarrolladores recomendados: {technical_analysis.get('num_desarrolladores', 'No determinado')}
- Presupuesto estimado: {technical_analysis.get('costo_total', 'No determinado')} {technical_analysis.get('moneda', 'EUR')}
"""
                            
                            # Añadir resumen de la conversación
                            if project_info.get('conversation_summary'):
                                summary_text += f"\nRESUMEN DE LA CONVERSACIÓN:\n{project_info.get('conversation_summary')[:500]}...\n"
                            
                            summaries.append({
                                'email': email,
                                'filename': filename,
                                'modified_date': modified_date,
                                'summary': summary_text,
                                'json_data': summary_data
                            })
                    except Exception as e:
                        print(f"Error al leer el archivo JSON {filename}: {str(e)}")
            
            # Ordenar los resúmenes por fecha de modificación (más reciente primero)
            summaries.sort(key=lambda x: x['modified_date'], reverse=True)
            
            # Renderizar plantilla HTML con los resúmenes
            return render_template('project_summaries.html', summaries=summaries)
        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Error al obtener los resúmenes de proyectos."
            }) 