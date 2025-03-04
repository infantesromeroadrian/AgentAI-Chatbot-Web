"""
Información sobre Alisys y funciones relacionadas.
"""
import json

def get_alisys_info():
    """Devuelve información estructurada sobre Alisys"""
    return {
        "nombre": "Alisys Digital S.L.U.",
        "descripcion": "Empresa especializada en soluciones tecnológicas para mejorar la relación con clientes y optimizar procesos empresariales.",
        "areas_principales": [
            {
                "nombre": "Soluciones Cloud",
                "descripcion": "Optimiza las comunicaciones, mejora la satisfacción y reduce los costes de IT con soluciones de customer care, marketing y ventas en la nube.",
                "servicios": ["Cloud Customer Experience", "Centralita Virtual", "Cloud Contact Center", "Omnichannel Payments", "Cloud CRM"]
            },
            {
                "nombre": "Agentes Virtuales/IA",
                "descripcion": "Disminuye los costes hasta un 30% y mejora la atención automatizando las conversaciones con inteligencia artificial y agentes virtuales.",
                "servicios": ["Gestión de citas", "Gestión de reservas", "Automatización info/trámites", "Encuestas", "Red Inteligente Conversacional"]
            },
            {
                "nombre": "Certificación/Blockchain",
                "descripcion": "Aumenta la transparencia de las operaciones e incrementa la confianza en las comunicaciones a través de la certificación digital.",
                "servicios": ["Sellado de tiempo", "RGPD mediante blockchain", "Certificación de comunicaciones"]
            },
            {
                "nombre": "Robótica",
                "descripcion": "Crea una experiencia de usuario única y emocional y optimiza los procesos en tu empresa gracias a las soluciones de robótica de Alisys."
            }
        ],
        "sectores": ["Salud", "Educación", "Automoción", "Administraciones Públicas"],
        "casos_exito": ["Vodafone", "060", "Sacyl", "Sodexo", "Carglass", "Fundación ONCE", "Vaughan", "Just Eat", "Bosch", "CAPSA", "Asamblea de Madrid", "Naturgy"],
        "ubicaciones": ["Madrid", "Gijón", "Barcelona", "Bogotá"],
        "contacto": "+34 910 200 000"
    }

def generate_alisys_info_stream():
    """Genera un stream con información sobre Alisys"""
    info = get_alisys_info()
    
    # Respuesta estructurada
    response = f"## Alisys Digital S.L.U.\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"Empresa especializada en tecnologías para mejorar la relación con clientes y optimizar procesos empresariales.\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Áreas principales:\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    for area in info['areas_principales']:
        response = f"**{area['nombre']}**: {area['descripcion']}\n\n"
        yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Sectores donde opera:\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"* " + "\n* ".join(info['sectores']) + "\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Clientes destacados:\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"* " + "\n* ".join(info['casos_exito'][:6]) + "\n* Entre otros\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Presencia internacional:\n{', '.join(info['ubicaciones'])}\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Contacto:\n{info['contacto']}\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"*Fuente: [Sitio web oficial de Alisys](https://alisys.net/es/)*"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    yield f"data: {json.dumps({'done': True})}\n\n"

def generate_contact_form_stream():
    """Genera un stream con un formulario de contacto"""
    
    response = f"## ¡Gracias por tu interés en Alisys!\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"Para que un representante de Alisys pueda contactarte y ofrecerte una solución personalizada, necesitamos algunos datos de contacto.\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"### Por favor, completa el siguiente formulario:\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    response = f"**1. Nombre completo**: (Escribe tu nombre y apellidos)\n\n"
    yield f"data: {json.dumps({'token': response, 'field': 'name'})}\n\n"
    
    response = f"**2. Correo electrónico**: (Escribe tu email de contacto)\n\n"
    yield f"data: {json.dumps({'token': response, 'field': 'email'})}\n\n"
    
    response = f"**3. Teléfono**: (Escribe tu número de teléfono para contacto directo)\n\n"
    yield f"data: {json.dumps({'token': response, 'field': 'phone'})}\n\n"
    
    response = f"**4. Empresa**: (Escribe el nombre de tu empresa u organización)\n\n"
    yield f"data: {json.dumps({'token': response, 'field': 'company'})}\n\n"
    
    response = f"**5. Área de interés**:\n* Soluciones Cloud\n* Agentes Virtuales/IA\n* Certificación/Blockchain\n* Robótica\n\n(Indica cuál de estas áreas te interesa más)\n\n"
    yield f"data: {json.dumps({'token': response, 'field': 'interest'})}\n\n"
    
    response = f"**¡Muchas gracias!** Un representante de Alisys se pondrá en contacto contigo lo antes posible para ayudarte con tus necesidades específicas.\n\n"
    yield f"data: {json.dumps({'token': response})}\n\n"
    
    yield f"data: {json.dumps({'done': True, 'form': True})}\n\n" 