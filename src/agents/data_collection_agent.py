"""
Agente de recopilación de datos para el chatbot de Alisys.
Este agente se encarga de solicitar y recopilar información de contacto
del usuario de manera estructurada.
"""
from typing import Dict, List, Any, Optional, Tuple, Generator
from .base_agent import BaseAgent
from data.data_manager import DataManager
import re
import logging

class DataCollectionAgent(BaseAgent):
    """
    Agente especializado en recopilar información de contacto del usuario.
    """
    
    def __init__(self):
        """
        Inicializa el agente de recopilación de datos.
        """
        super().__init__(
            name="DataCollectionAgent",
            description="Especialista en recopilar información de contacto del usuario"
        )
        self.data_manager = DataManager()
        self.required_fields = ["name", "email", "phone", "company"]
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determina si este agente puede manejar el mensaje actual.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            True si el agente puede manejar el mensaje, False en caso contrario
        """
        # Palabras clave relacionadas con contacto
        contact_keywords = [
            "contacto", "contactar", "llamar", "llamada", "email",
            "correo", "teléfono", "telefono", "celular", "móvil",
            "información de contacto", "datos de contacto", "formulario",
            "representante", "asesor", "comercial", "ventas", "cotización",
            "cotizar", "presupuesto", "información", "nombre", "empresa"
        ]
        
        # Frases que indican intención de contacto
        contact_phrases = [
            "me gustaría recibir una cotización",
            "quiero que me contacten",
            "necesito hablar con un representante",
            "me gustaría más información",
            "pueden contactarme",
            "me interesa contratar",
            "quisiera que me llamen",
            "necesito asesoría"
        ]
        
        # Verificar si el mensaje contiene alguna palabra clave de contacto
        message_lower = message.lower()
        
        # Verificar palabras clave
        for keyword in contact_keywords:
            if keyword in message_lower:
                return True
        
        # Verificar frases completas
        for phrase in contact_phrases:
            if phrase in message_lower:
                return True
        
        # Verificar si ya se ha mostrado el formulario pero no se ha completado
        if context.get('form_shown', False) and not context.get('form_completed', False):
            return True
            
        # Verificar si el mensaje contiene datos de contacto (nombre, email, teléfono)
        if self._contains_contact_data(message):
            return True
        
        # También manejar si el contexto indica que estamos en fase de recopilación de datos
        if context.get('current_agent') == self.name:
            return True
        
        # O si el agente anterior fue el de ventas o ingeniería y el usuario mostró interés
        previous_agent = context.get('previous_agent')
        if previous_agent in ["SalesAgent", "EngineerAgent"]:
            interest_keywords = ["interesado", "me interesa", "quiero", "deseo", "necesito", "contactar"]
            for keyword in interest_keywords:
                if keyword in message_lower:
                    return True
        
        # O si ya tenemos algunos datos de contacto pero faltan campos
        if context.get('user_info') and not self._has_all_required_fields(context.get('user_info', {})):
            return True
        
        return False
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        # Extraer información del usuario ya recopilada
        user_info = context.get('user_info', {})
        missing_fields = self._get_missing_fields(user_info)
        
        # Crear un resumen de la información ya recopilada para el prompt
        collected_info_summary = self._format_user_info(user_info)
        
        # Crear instrucciones específicas basadas en el estado actual
        specific_instructions = ""
        
        if not missing_fields:
            specific_instructions = """
Todos los datos han sido recopilados. Agradece al usuario y confirma que un representante se pondrá en contacto en 24-48 horas.
Muestra un resumen de toda la información recopilada para que el usuario pueda verificarla.
"""
        else:
            # Si es la primera interacción o hay múltiples campos faltantes
            if len(missing_fields) > 1:
                specific_instructions = f"""
Solicita TODOS los datos pendientes de una sola vez para agilizar el proceso. Los campos que necesitamos son: {', '.join(missing_fields)}.
Explica claramente que necesitas esta información para que un representante pueda contactar al usuario con una propuesta personalizada.
Sé amable pero directo, y menciona que esta información es confidencial y solo se utilizará para contactar al usuario.
"""
            # Si solo falta un campo
            else:
                field = missing_fields[0]
                if field == "name":
                    specific_instructions = "Solicita amablemente el nombre completo del usuario. Si ya te lo ha proporcionado antes, utiliza esa información y no vuelvas a pedirla."
                elif field == "email":
                    specific_instructions = "Solicita la dirección de correo electrónico del usuario. Explica que es necesaria para enviar información relevante."
                elif field == "phone":
                    specific_instructions = "Solicita el número de teléfono del usuario. Explica que es para que un representante pueda contactarle."
                elif field == "company":
                    specific_instructions = "Pregunta por el nombre de la empresa u organización del usuario."
        
        return f"""Eres un asistente de Alisys especializado en recopilar información de contacto.
Tu objetivo es obtener los datos necesarios para que un representante pueda contactar al usuario.

INSTRUCCIONES GENERALES:
1. Comienza explicando claramente que eres el agente de recopilación de datos y que tu objetivo es obtener la información necesaria para que un representante pueda contactar al usuario con una propuesta personalizada.
2. IMPORTANTE: Si es la primera interacción, solicita TODOS los datos pendientes de una sola vez (nombre, email, teléfono, empresa) para agilizar el proceso.
3. Si ya tienes algunos datos, confirma la información recibida y solicita solo los datos faltantes.
4. Mantén un tono profesional y respetuoso.
5. Explica brevemente por qué necesitas esta información.
6. Si el usuario se muestra reacio, no insistas y ofrece alternativas.
7. Una vez recopilados todos los datos, confirma la información completa.
8. Informa al usuario que un representante se pondrá en contacto en 24-48 horas.
9. CRÍTICO: No vuelvas a solicitar información que ya ha sido proporcionada.
10. Cuando hayas recopilado todos los datos necesarios, agradece al usuario y cierra la conversación con un mensaje claro de que el proceso ha sido completado exitosamente.

FLUJO DE CONVERSACIÓN:
1. Este es el último paso del proceso: Información general → Detalles técnicos → Cotización → Recopilación de datos (tú).
2. Tu objetivo es cerrar el ciclo de venta recopilando la información necesaria para que un representante pueda contactar al usuario.

INFORMACIÓN YA RECOPILADA:
{collected_info_summary}

INFORMACIÓN PENDIENTE:
{', '.join(missing_fields) if missing_fields else 'Toda la información ha sido recopilada.'}

INSTRUCCIÓN ESPECÍFICA PARA ESTE MENSAJE:
{specific_instructions}

ESTADO DE LA CONVERSACIÓN:
- Campos ya recopilados: {', '.join(user_info.keys()) if user_info else 'Ninguno'}
- Campos pendientes: {', '.join(missing_fields) if missing_fields else 'Ninguno, todos los datos han sido recopilados'}

Historial de conversación:
{self._format_conversation_history(context)}
"""
    
    def process(self, message: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Procesa un mensaje del usuario y actualiza el contexto.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Generador que produce la respuesta del agente
        """
        # Inicializar user_info si no existe
        if 'user_info' not in context:
            context['user_info'] = {}
        
        # Verificar si el usuario indica que ya proporcionó información
        if self._check_previous_info_confirmation(message):
            context['confirmed_previous_info'] = True
            logging.info("Usuario ha confirmado que ya proporcionó información anteriormente")
        
        # Extraer información de contacto del mensaje
        updated_info = self._extract_contact_info(message, context)
        
        # Actualizar el contexto con la nueva información
        if updated_info:
            context['user_info'].update(updated_info)
            logging.info(f"Información actualizada: {updated_info}")
            
            # Verificar si se han recopilado todos los datos necesarios
            missing_fields = self._get_missing_fields(context['user_info'])
            if not missing_fields:
                # Guardar la información del lead
                self._save_lead(context['user_info'], context)
                logging.info("Todos los datos han sido recopilados y guardados")
                context['data_collection_complete'] = True
        
        # Generar el prompt del sistema
        system_prompt = self.get_system_prompt(context)
        
        # Obtener respuesta del LLM en modo streaming
        for chunk in self.lm_client.generate_stream(
            system_prompt=system_prompt,
            user_message=message
        ):
            yield chunk
            
        # Actualizar el contexto con el agente actual
        context['current_agent'] = self.name
    
    def _extract_contact_info(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae información de contacto del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Diccionario con la información extraída
        """
        # Inicializar el diccionario para almacenar la información extraída
        extracted_info = {}
        
        # Registrar el mensaje para depuración
        logging.info(f"Procesando mensaje para extracción de datos: '{message}'")
        logging.info(f"Contexto actual: {context.get('user_info', {})}")
        
        # Inicializar user_info si no existe
        if 'user_info' not in context:
            context['user_info'] = {}
        
        # Verificar si el usuario indica que ya proporcionó información
        confirmation_patterns = [
            r"ya (te|les?) (di|dije|proporcion[eé]|envi[eé]|mand[eé]) (mi|el) (nombre|correo|email|teléfono|telefono|celular|móvil|empresa|compañía)",
            r"ya lo (di|dije|proporcion[eé]|envi[eé]|mand[eé])",
            r"(te|les?) (di|dije|proporcion[eé]|envi[eé]|mand[eé]) (mi|el) (nombre|correo|email|teléfono|telefono|celular|móvil|empresa|compañía)",
            r"(es|son) los (mismos|que te di|que les di)",
            r"(ya|antes) (te|les?) (lo|los) (di|dije|proporcion[eé]|envi[eé]|mand[eé])"
        ]
        
        for pattern in confirmation_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                logging.info(f"Usuario indica que ya proporcionó información: '{message}'")
                context['confirmed_previous_info'] = True
                break
        
        # Verificar si el mensaje contiene múltiples datos (mensaje completo)
        # Si contiene al menos un correo electrónico y menciona la palabra "nombre", "teléfono" o "empresa"
        contains_multiple_data = (
            re.search(r"[\w\.-]+@[\w\.-]+\.\w+", message) and 
            re.search(r"(nombre|telefono|teléfono|empresa|compañía|compania)", message, re.IGNORECASE)
        )
        
        if contains_multiple_data:
            logging.info("Mensaje detectado como conteniendo múltiples datos")
        
        # Extraer nombre completo - Mejorado para detectar nombres simples
        if 'name' not in context['user_info'] or not context['user_info']['name']:
            # Primero intentar con patrones específicos
            name_patterns = [
                r"(?:mi nombre es|me llamo|soy) ([A-Za-zÀ-ÖØ-öø-ÿ\s]+?)(?:,|\.|y|mi|correo|email|telefono|teléfono|empresa|compañía|$)",
                r"([A-Za-zÀ-ÖØ-öø-ÿ\s]+?) (?:es mi nombre|me llamo)",
                r"nombre:?\s*([A-Za-zÀ-ÖØ-öø-ÿ\s]+?)(?:,|\.|y|mi|correo|email|telefono|teléfono|empresa|compañía|$)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 2:  # Evitar coincidencias demasiado cortas
                        extracted_info['name'] = name
                        logging.info(f"Nombre extraído con patrón específico: {name}")
                        break
            
            # Si no se encontró con patrones específicos, intentar con un enfoque más simple
            if 'name' not in extracted_info and not contains_multiple_data:
                # Si el mensaje es corto y parece un nombre (sin caracteres especiales)
                if len(message.split()) <= 4 and re.match(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$', message.strip()):
                    name = message.strip()
                    if len(name) > 2:
                        extracted_info['name'] = name
                        logging.info(f"Nombre extraído como mensaje simple: {name}")
        
        # Extraer correo electrónico - Mejorado para detectar emails simples
        if 'email' not in context['user_info'] or not context['user_info']['email']:
            # Patrón simple para correos electrónicos
            email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
            email_matches = re.findall(email_pattern, message)
            
            if email_matches:
                email = email_matches[0]
                extracted_info['email'] = email
                logging.info(f"Email extraído: {email}")
            # Si el mensaje es solo un email
            elif re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', message.strip()):
                email = message.strip()
                extracted_info['email'] = email
                logging.info(f"Email extraído como mensaje simple: {email}")
        
        # Extraer número de teléfono - Mejorado para detectar números simples
        if 'phone' not in context['user_info'] or not context['user_info']['phone']:
            # Patrones para números de teléfono
            phone_patterns = [
                r"(?:mi teléfono|mi telefono|mi número|mi celular|mi móvil|teléfono|telefono) (?:es)? (\+?[\d\s\(\)\-\.]{7,20})",
                r"(\+?[\d\s\(\)\-\.]{7,20}) (?:es mi teléfono|es mi telefono|es mi número|es mi celular|es mi móvil)",
                r"(?:teléfono|telefono):?\s*(\+?[\d\s\(\)\-\.]{7,20})"
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    phone = match.group(1).strip()
                    # Verificar que sea un número de teléfono válido (al menos 7 dígitos)
                    digits = re.sub(r'\D', '', phone)
                    if len(digits) >= 7:
                        extracted_info['phone'] = phone
                        logging.info(f"Teléfono extraído con patrón específico: {phone}")
                        break
            
            # Si no se encontró con patrones específicos, buscar números en el mensaje
            if 'phone' not in extracted_info:
                # Buscar secuencias de dígitos que parezcan números de teléfono
                phone_matches = re.findall(r'(\d{7,15})', message.replace(" ", ""))
                for match in phone_matches:
                    if len(match) >= 7 and len(match) <= 15:
                        extracted_info['phone'] = match
                        logging.info(f"Teléfono extraído de secuencia de dígitos: {match}")
                        break
                
                # Si el mensaje es solo un número de teléfono
                if 'phone' not in extracted_info and not contains_multiple_data:
                    digits = re.sub(r'\D', '', message)
                    if len(digits) >= 7 and len(digits) <= 15:
                        extracted_info['phone'] = message.strip()
                        logging.info(f"Teléfono extraído como mensaje simple: {message.strip()}")
        
        # Extraer nombre de la empresa - Mejorado para detectar nombres de empresa simples
        if 'company' not in context['user_info'] or not context['user_info']['company']:
            company_patterns = [
                r"(?:mi empresa|mi compañía|mi compania|mi organización|trabajo para|trabajo en) (?:es|se llama)? ([A-Za-zÀ-ÖØ-öø-ÿ\s\&\.\,]+?)(?:,|\.|y|$)",
                r"([A-Za-zÀ-ÖØ-öø-ÿ\s\&\.\,]+?) (?:es mi empresa|es mi compañía|es mi compania|es mi organización)",
                r"(?:empresa|compañía|compania):?\s*([A-Za-zÀ-ÖØ-öø-ÿ\s\&\.\,]+?)(?:,|\.|y|$)"
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if len(company) > 2:  # Evitar coincidencias demasiado cortas
                        extracted_info['company'] = company
                        logging.info(f"Empresa extraída con patrón específico: {company}")
                        break
            
            # Si no se encontró con patrones específicos y el mensaje contiene múltiples datos
            if 'company' not in extracted_info and contains_multiple_data:
                # Buscar la última palabra o frase que no sea un email o número
                words = message.split()
                for i in range(len(words) - 1, -1, -1):
                    if not re.match(r'[\w\.-]+@[\w\.-]+\.\w+', words[i]) and not re.match(r'\d+', words[i]):
                        potential_company = words[i]
                        if len(potential_company) > 2:
                            extracted_info['company'] = potential_company
                            logging.info(f"Empresa extraída de palabras finales: {potential_company}")
                            break
            
            # Si el mensaje es corto y no se ha identificado como nombre, email o teléfono
            if 'company' not in extracted_info and not contains_multiple_data:
                if 'name' not in extracted_info and 'phone' not in extracted_info and 'email' not in extracted_info:
                    if len(message.split()) <= 5:
                        company = message.strip()
                        if len(company) > 2:
                            extracted_info['company'] = company
                            logging.info(f"Empresa extraída como mensaje simple: {company}")
        
        # Actualizar el contexto con la información extraída
        if extracted_info:
            context['user_info'].update(extracted_info)
            logging.info(f"Información del usuario actualizada: {context.get('user_info', {})}")
            logging.info(f"Campos faltantes: {self._get_missing_fields(context.get('user_info', {}))}")
        
        return extracted_info
    
    def _has_all_required_fields(self, user_info: Dict[str, Any]) -> bool:
        """
        Verifica si tenemos toda la información requerida.
        
        Args:
            user_info: Información del usuario
            
        Returns:
            True si tenemos todos los campos requeridos, False en caso contrario
        """
        # Verificar cada campo requerido
        for field in self.required_fields:
            if field not in user_info or not user_info[field]:
                return False
        return True
    
    def _get_missing_fields(self, user_info: Dict[str, Any]) -> List[str]:
        """
        Obtiene la lista de campos que faltan por recopilar.
        
        Args:
            user_info: Información del usuario
            
        Returns:
            Lista de campos faltantes
        """
        missing = []
        for field in self.required_fields:
            if field not in user_info or not user_info[field]:
                missing.append(field)
        return missing
    
    def _format_user_info(self, user_info: Dict[str, str]) -> str:
        """
        Formatea la información del usuario para incluirla en el prompt.
        
        Args:
            user_info: Diccionario con la información del usuario
            
        Returns:
            Texto formateado con la información del usuario
        """
        if not user_info:
            return "No se ha recopilado información todavía."
        
        formatted_info = []
        field_names = {
            "name": "Nombre",
            "email": "Correo electrónico",
            "phone": "Teléfono",
            "company": "Empresa"
        }
        
        for field, value in user_info.items():
            if field in field_names and value:
                formatted_info.append(f"- {field_names[field]}: {value}")
        
        if formatted_info:
            return "\n".join(formatted_info)
        else:
            return "No se ha recopilado información válida todavía."
    
    def _save_lead(self, user_info: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Guarda la información del usuario como un lead.
        
        Args:
            user_info: Información del usuario
            context: Contexto de la conversación
        """
        # Extraer información relevante
        lead_data = {
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'phone': user_info.get('phone', ''),
            'company': user_info.get('company', ''),
            'interest': context.get('project_info', {}).get('interest', '')
        }
        
        # Guardar el lead
        self.data_manager.save_lead(lead_data)
        
        # Marcar que el formulario ha sido completado en el contexto
        context['form_completed'] = True
    
    def _contains_contact_data(self, message: str) -> bool:
        """
        Verifica si el mensaje contiene datos de contacto como nombre, email o teléfono.
        
        Args:
            message: El mensaje del usuario
            
        Returns:
            True si el mensaje contiene datos de contacto, False en caso contrario
        """
        # Patrones para detectar emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Patrones para detectar números de teléfono
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{3,4}'
        
        # Verificar si el mensaje contiene un email
        if re.search(email_pattern, message):
            return True
        
        # Verificar si el mensaje contiene un número de teléfono
        if re.search(phone_pattern, message):
            return True
        
        # Verificar si el mensaje contiene palabras que indican que se está proporcionando un nombre
        name_indicators = ["me llamo", "mi nombre es", "soy", "nombre:", "nombre ", "llamo"]
        message_lower = message.lower()
        for indicator in name_indicators:
            if indicator in message_lower:
                return True
        
        # Verificar si el mensaje es potencialmente un nombre (2-4 palabras, sin ser una respuesta común)
        if 1 <= len(message.split()) <= 4:
            common_responses = ["si", "no", "ok", "okay", "vale", "bien", "gracias", "hola", 
                               "adios", "hasta luego", "por favor", "claro", "perfecto"]
            if message_lower.strip() not in common_responses:
                # Verificar que al menos una palabra comience con mayúscula (posible nombre propio)
                words = message.split()
                for word in words:
                    if word and word[0].isupper():
                        return True
        
        return False
    
    def _format_conversation_history(self, context: Dict[str, Any]) -> str:
        """
        Formatea el historial de conversación para incluirlo en el prompt.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Texto formateado con el historial de conversación
        """
        messages = context.get('messages', [])
        if not messages:
            return "No hay historial de conversación disponible."
        
        # Limitar a las últimas 5 interacciones para mantener el contexto relevante
        recent_messages = messages[-10:]
        
        formatted_history = []
        for msg in recent_messages:
            role = "Usuario" if msg.get('role') == 'user' else "Asistente"
            content = msg.get('content', '')
            formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history)

    def _check_previous_info_confirmation(self, message: str) -> bool:
        """
        Verifica si el usuario ha confirmado que ya proporcionó información anteriormente.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            True si el usuario ha confirmado que ya proporcionó información anteriormente, False en caso contrario
        """
        # Manejar confirmaciones como "sí, ya lo proporcioné"
        confirmation_patterns = [
            r"s[ií],?\s+ya\s+(lo|te\s+lo)?\s+(he\s+)?(proporcionad[oa]|dad[oa]|dicho|mencionad[oa])",
            r"ya\s+(lo|te\s+lo)?\s+(he\s+)?(proporcionad[oa]|dad[oa]|dicho|mencionad[oa])",
            r"ya\s+(lo|te\s+lo)?\s+sabes",
            r"ya\s+te\s+(lo)?\s+dije"
        ]
        
        for pattern in confirmation_patterns:
            if re.search(pattern, message.lower()):
                return True
        return False 