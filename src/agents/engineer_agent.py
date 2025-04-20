"""
Agente especializado en consultas técnicas y de ingeniería.
"""
import json
import re
from services.lm_studio import send_chat_request

class EngineerAgent:
    """Agente especializado en consultas técnicas y de ingeniería"""
    
    def __init__(self):
        self.name = "EngineerAgent"
        self.description = "Especialista en consultas técnicas y de ingeniería."
        self.confidence_threshold = 0.7
        # Palabras clave que este agente puede manejar
        self.keywords = [
            "desarrollo", "programación", "código", "software", "aplicación", 
            "app", "móvil", "web", "arquitectura", "cloud", "nube", "servidor",
            "infraestructura", "técnico", "tecnología", "implementación",
            "integración", "api", "backend", "frontend", "fullstack", "proyecto",
            "requisitos", "estimación", "presupuesto", "tiempo", "plazo",
            "funcionalidad", "característica", "feature", "herramienta",
            "tecnología", "plataforma", "lenguaje", "framework", "biblioteca",
            "library", "seguridad", "escalabilidad", "rendimiento", "performance",
            "optimización", "deployment", "despliegue", "devops", "ci/cd",
            "testing", "pruebas", "calidad", "mantenimiento", "soporte",
            "consultoría", "asesoría", "recomendación", "experiencia", "mejora",
            "actualización", "migración", "modernización", "transformación",
            "innovación", "automatización", "monitorización", "backup", "respaldo",
            "disaster recovery", "recuperación", "continuidad", "disponibilidad",
            "alta disponibilidad", "balanceo", "carga", "virtualización",
            "contenedor", "docker", "kubernetes", "aws", "azure", "gcp", "google",
            "microsoft", "amazon", "hosting", "iaas", "paas", "saas", "microservicios",
            "soa", "base de datos", "database", "sql", "nosql", "almacenamiento",
            "storage", "cache", "memoria", "cpu", "procesamiento", "computación",
            "gpu", "machine learning", "ml", "ai", "artificial intelligence", 
            "big data", "análisis", "analytics", "etl", "extracción", "transformación",
            "carga", "datos", "data", "información", "knowledge", "conocimiento",
            "modelo", "predicción", "forecast", "insight", "visualización",
            "dashboard", "kpi", "métrica", "indicador", "diagrama", "gráfico",
            "chart", "informe", "reporte", "report", "estadística", "tendencia",
            "decisión", "business intelligence", "bi", "internet of things",
            "iot", "dispositivo", "sensor", "actuador", "embebido", "embedded",
            "firmware", "hardware", "pcb", "arduino", "raspberry", "prototipo",
            "mvp", "producto", "viable", "mínimo", "funcional", "usabilidad",
            "ux", "ui", "diseño", "interface", "interfaz", "experiencia",
            "usuario", "accesibilidad", "responsive", "adaptable", "móvil",
            "tablet", "desktop", "navegador", "browser", "chrome", "firefox",
            "safari", "edge", "ie", "explorer", "compatibilidad", "estándar",
            "w3c", "html", "css", "javascript", "js", "typescript", "ts",
            "react", "angular", "vue", "svelte", "jquery", "bootstrap", "material",
            "tailwind", "webpack", "babel", "node", "express", "nestjs", "next",
            "nuxt", "gatsby", "php", "laravel", "symfony", "wordpress", "drupal",
            "joomla", "magento", "shopify", "woocommerce", "ecommerce", "tienda",
            "online", "shop", "carro", "compra", "pago", "payment", "gateway",
            "stripe", "paypal", "tarjeta", "crédito", "débito", "transferencia",
            "banco", "factura", "invoice", "fiscal", "legal", "compliance",
            "regulación", "gdpr", "lopd", "protección", "privacidad", "cookie",
            "seguridad", "certificado", "ssl", "tls", "https", "encriptación",
            "cifrado", "hash", "password", "contraseña", "autenticación",
            "authentication", "autorización", "authorization", "oauth", "jwt",
            "token", "session", "sesión", "login", "logout", "signup", "signin",
            "registro", "cuenta", "perfil", "role", "rol", "permiso", "permission",
            "admin", "usuario", "user", "miembro", "member", "cliente", "customer",
            "proveedor", "vendor", "partner", "socio", "stakeholder", "interesado",
            "comunicación", "asíncrono", "síncrono", "tiempo real", "websocket",
            "http", "rest", "soap", "grpc", "graphql", "webhook", "callback",
            "notificación", "push", "email", "sms", "whatsapp", "telegram", "chat",
            "bot", "chatbot", "asistente", "virtual", "mensaje", "message",
            "comunicado", "anuncio", "news", "noticia", "evento", "event",
            "calendario", "schedule", "agenda", "cita", "appointment", "reunión",
            "meeting", "conferencia", "webinar", "seminario", "curso", "training",
            "formación", "capacitación", "entrenamiento", "educación", "aprende",
            "learn", "tutorial", "guía", "documentación", "manual", "referencia",
            "api", "sdk", "kit", "desarrollo"
        ]
        # Conocimientos técnicos específicos de este agente
        self.technical_knowledge = {
            "lenguajes": ["Python", "JavaScript", "TypeScript", "Java", "C#", "PHP", "Ruby", "Go", "Swift", "Kotlin"],
            "frameworks_frontend": ["React", "Angular", "Vue", "Svelte", "Next.js", "Nuxt.js", "Gatsby"],
            "frameworks_backend": ["Express", "Django", "Flask", "Spring Boot", "Laravel", "Ruby on Rails", "ASP.NET Core"],
            "bases_de_datos": ["MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server", "Redis", "Elasticsearch"],
            "cloud": ["AWS", "Azure", "Google Cloud", "DigitalOcean", "Heroku", "Netlify", "Vercel"],
            "devops": ["Docker", "Kubernetes", "Jenkins", "GitHub Actions", "GitLab CI/CD", "Travis CI", "CircleCI"],
            "testing": ["Jest", "Mocha", "Selenium", "Cypress", "PyTest", "JUnit", "PHPUnit"],
            "seguridad": ["JWT", "OAuth", "HTTPS", "SSL/TLS", "Encriptación", "Autenticación de dos factores", "OWASP Top 10"],
            "metodologias": ["Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "TDD", "BDD"]
        }
    
    def evaluate_confidence(self, message, context):
        """
        Evalúa la confianza de este agente para responder al mensaje.
        
        Args:
            message (str): El mensaje del usuario
            context (dict): El contexto de la conversación
            
        Returns:
            float: Nivel de confianza entre 0 y 1
        """
        # Normalizar mensaje a minúsculas para comparación
        normalized_message = message.lower()
        
        # Si ya se identificó como ingeniero en mensajes anteriores, mantener alta confianza
        if context.get('current_agent') == self.name:
            # Verificar si el usuario quiere hablar con otro agente
            if any(word in normalized_message for word in ["hablar con ventas", "hablar con comercial", "contactar ventas"]):
                return 0.3  # Baja confianza para permitir que otro agente tome el control
            return 0.85  # Alta confianza para mantener la conversación
        
        # Inicializar puntuación base
        confidence = 0.0
        
        # Verificar las palabras clave en el mensaje
        for keyword in self.keywords:
            if keyword.lower() in normalized_message:
                confidence += 0.1
                # Limitar a un máximo razonable por keywords
                if confidence >= 0.6:
                    break
        
        # Análisis adicional para detectar consultas técnicas
        # Preguntas sobre tecnologías específicas
        if any(tech.lower() in normalized_message for tech in sum(self.technical_knowledge.values(), [])):
            confidence += 0.2
        
        # Consultas sobre desarrollo o implementación
        if re.search(r'(cómo|como) (desarrollar|implementar|crear|hacer|programar)', normalized_message):
            confidence += 0.15
        
        # Consultas sobre estimar o presupuestar proyectos
        if re.search(r'(estimar|presupuesto|costo|coste|precio|cuánto cuesta|cuanto cuesta|valor)', normalized_message):
            confidence += 0.15

        # Consultas sobre requisitos técnicos
        if re.search(r'(requisitos|especificaciones|features|funcionalidades|tecnología)', normalized_message):
            confidence += 0.15
        
        # Análisis de archivos de proyecto subidos
        if context.get('project_file_content') is not None:
            confidence += 0.3  # Alta confianza si hay un archivo de proyecto
        
        # Permitir transición hacia el agente de ventas para presupuestos
        if re.search(r'(presupuesto final|contratar|comenzar proyecto|iniciar proyecto|precio final)', normalized_message) and confidence > 0.4:
            # Confidence alta pero no tanto como para bloquear al agente de ventas
            return 0.75
        
        # Limitar la confianza máxima
        return min(confidence, 0.95)
    
    def analyze_project_requirements(self, file_content, file_name=None):
        """
        Analiza los requisitos del proyecto a partir del contenido del archivo
        
        Args:
            file_content (str): Contenido del archivo de requisitos
            file_name (str, optional): Nombre del archivo
            
        Returns:
            dict: Análisis del proyecto con campos como complejidad, tecnologías, etc.
        """
        # Crear un prompt para analizar los requisitos del proyecto
        prompt = f"""Por favor, analiza los siguientes requisitos de proyecto y proporciona una estimación en formato JSON:

REQUISITOS DEL PROYECTO:
{file_content}

Extrae la siguiente información en formato JSON:
1. "complejidad": un valor entre 1 (muy simple) y 5 (muy complejo)
2. "tecnologias_recomendadas": un array de tecnologías recomendadas
3. "tiempo_estimado": tiempo estimado en semanas o meses
4. "num_desarrolladores": número recomendado de desarrolladores
5. "riesgos_principales": array de posibles riesgos técnicos
6. "resumen": resumen breve del proyecto (máximo 3 párrafos)
7. "desglose_tareas": array de tareas principales con sus estimaciones individuales

FORMATO DE RESPUESTA (solo JSON):
{{
  "complejidad": 3,
  "tecnologias_recomendadas": ["React", "Node.js", "MongoDB"],
  "tiempo_estimado": "8 semanas",
  "num_desarrolladores": 2,
  "riesgos_principales": ["Integración con sistema legacy", "Seguridad de datos sensibles"],
  "resumen": "Proyecto de desarrollo de...",
  "desglose_tareas": [
    {{"tarea": "Diseño de arquitectura", "tiempo": "1 semana"}},
    {{"tarea": "Desarrollo frontend", "tiempo": "3 semanas"}},
    {{"tarea": "Desarrollo backend", "tiempo": "3 semanas"}},
    {{"tarea": "Pruebas y despliegue", "tiempo": "1 semana"}}
  ]
}}

Responde SOLO con el JSON, sin texto adicional."""
        
        try:
            # Enviar solicitud para analizar requisitos
            analysis_json = ""
            for chunk in send_chat_request(prompt, stream=True):
                chunk_data = json.loads(chunk.replace('data: ', ''))
                if 'token' in chunk_data:
                    analysis_json += chunk_data['token']
            
            # Convertir respuesta a diccionario
            analysis = json.loads(analysis_json)
            
            # Añadir nombre del archivo si está disponible
            if file_name:
                analysis['archivo_origen'] = file_name
            
            return analysis
        except Exception as e:
            print(f"Error al analizar requisitos: {str(e)}")
            # Devolver un análisis básico en caso de error
            return {
                "complejidad": 3,
                "tecnologias_recomendadas": ["No se pudo determinar"],
                "tiempo_estimado": "No se pudo estimar",
                "num_desarrolladores": 2,
                "riesgos_principales": ["No se pudieron determinar"],
                "resumen": "No se pudo analizar el contenido del archivo",
                "desglose_tareas": [],
                "error": str(e)
            }
    
    def generate_budget_estimate(self, project_analysis):
        """
        Genera una estimación de presupuesto basada en el análisis del proyecto
        
        Args:
            project_analysis (dict): Análisis del proyecto
            
        Returns:
            dict: Estimación de presupuesto
        """
        try:
            # Calcular tarifas base según complejidad
            complejidad = project_analysis.get('complejidad', 3)
            tarifa_desarrollador = 350 + (complejidad * 50)  # Tarifa diaria base ajustada por complejidad
            
            # Estimar duración en días (convertir desde semanas/meses)
            tiempo_estimado = project_analysis.get('tiempo_estimado', '8 semanas')
            dias_estimados = 0
            
            if 'semana' in tiempo_estimado.lower():
                semanas = int(re.search(r'(\d+)', tiempo_estimado).group(1))
                dias_estimados = semanas * 5  # 5 días laborables por semana
            elif 'mes' in tiempo_estimado.lower():
                meses = int(re.search(r'(\d+)', tiempo_estimado).group(1))
                dias_estimados = meses * 20  # 20 días laborables por mes
            else:
                # Si no se puede determinar, usar valor por defecto
                dias_estimados = 40  # 8 semanas * 5 días
            
            # Calcular número de desarrolladores
            num_desarrolladores = project_analysis.get('num_desarrolladores', 2)
            
            # Calcular costo base de desarrollo
            costo_desarrollo = dias_estimados * tarifa_desarrollador * num_desarrolladores
            
            # Ajustar por complejidad y riesgos
            factor_riesgo = 1.0 + (0.05 * len(project_analysis.get('riesgos_principales', [])))
            costo_ajustado = costo_desarrollo * factor_riesgo
            
            # Añadir costos adicionales
            costo_gestion_proyecto = costo_ajustado * 0.15  # 15% para gestión de proyecto
            costo_qa_testing = costo_ajustado * 0.2  # 20% para QA y testing
            costo_infraestructura = 1500 * complejidad  # Costo base de infraestructura
            
            # Calcular total
            costo_total = costo_ajustado + costo_gestion_proyecto + costo_qa_testing + costo_infraestructura
            
            # Redondear a miles
            costo_total = round(costo_total / 1000) * 1000
            
            # Crear desglose de presupuesto
            presupuesto = {
                "costo_total": costo_total,
                "moneda": "EUR",
                "desglose": {
                    "desarrollo": round(costo_ajustado),
                    "gestion_proyecto": round(costo_gestion_proyecto),
                    "qa_testing": round(costo_qa_testing),
                    "infraestructura": round(costo_infraestructura)
                },
                "duracion_estimada": tiempo_estimado,
                "equipo_recomendado": {
                    "desarrolladores": num_desarrolladores,
                    "qa_testers": max(1, round(num_desarrolladores / 2)),
                    "project_manager": 1
                },
                "tecnologias": project_analysis.get('tecnologias_recomendadas', []),
                "notas": "Esta estimación es preliminar y puede variar según los requisitos detallados y el alcance final del proyecto."
            }
            
            return presupuesto
        except Exception as e:
            print(f"Error al generar presupuesto: {str(e)}")
            # Devolver un presupuesto básico en caso de error
            return {
                "costo_total": 50000,
                "moneda": "EUR",
                "desglose": {
                    "desarrollo": 35000,
                    "gestion_proyecto": 7500,
                    "qa_testing": 5000,
                    "infraestructura": 2500
                },
                "duracion_estimada": "No determinada",
                "equipo_recomendado": {
                    "desarrolladores": 2,
                    "qa_testers": 1,
                    "project_manager": 1
                },
                "tecnologias": ["No determinadas"],
                "notas": "Esta es una estimación por defecto debido a un error en el cálculo. Para una estimación precisa, por favor proporcione más detalles del proyecto."
            }
    
    def process_message(self, message, context):
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            message (str): El mensaje del usuario
            context (dict): El contexto de la conversación
            
        Returns:
            str: La respuesta generada
        """
        # Actualizar el contexto para indicar que este agente está activo
        context['current_agent'] = self.name
        if 'previous_agent' not in context or context['previous_agent'] != self.name:
            context['previous_agent'] = context.get('current_agent')
        
        # Analizar si hay un archivo de proyecto en el contexto
        if context.get('project_file_content') and not context.get('project_analysis'):
            # Analizar el archivo de requisitos
            project_analysis = self.analyze_project_requirements(
                context['project_file_content'],
                context.get('project_file_name')
            )
            
            # Generar estimación de presupuesto
            budget_estimate = self.generate_budget_estimate(project_analysis)
            
            # Guardar análisis y estimación en el contexto
            context['project_analysis'] = project_analysis
            context['project_estimate'] = budget_estimate
            
            # Indicar que tenemos un análisis del proyecto para formular una mejor respuesta
            has_new_analysis = True
        else:
            has_new_analysis = False
        
        # Verificar si hay una solicitud específica de presupuesto
        is_budget_request = re.search(r'(presupuesto|precio|costo|cuánto cuesta|cuanto cuesta)', message.lower())
        
        # Construir el prompt para el agente
        prompt = f"""Eres un ingeniero técnico especializado en Alisys, experto en desarrollo de software, inteligencia artificial, infraestructura y soluciones técnicas. 
Tu objetivo es responder de manera precisa y profesional las consultas técnicas, explicando conceptos y ofreciendo soluciones.

CONTEXTO ACTUAL:
- Mensaje del usuario: "{message}"
- Número de mensajes: {context.get('message_count', 0)}
"""
        
        # Añadir información sobre el archivo de proyecto si existe
        if context.get('project_file_content'):
            prompt += f"""
- El usuario ha subido un archivo de proyecto: {context.get('project_file_name', 'documento de requisitos')}
"""

        # Añadir análisis del proyecto si existe
        if context.get('project_analysis'):
            analysis = context['project_analysis']
            prompt += f"""
ANÁLISIS DEL PROYECTO:
- Complejidad: {analysis.get('complejidad', 'No determinada')} (escala 1-5)
- Tecnologías recomendadas: {', '.join(analysis.get('tecnologias_recomendadas', ['No determinadas']))}
- Tiempo estimado: {analysis.get('tiempo_estimado', 'No determinado')}
- Desarrolladores recomendados: {analysis.get('num_desarrolladores', 'No determinado')}
- Riesgos principales: {', '.join(analysis.get('riesgos_principales', ['No determinados']))}
- Resumen: {analysis.get('resumen', 'No disponible')}
"""
        
        # Añadir estimación de presupuesto si existe
        if context.get('project_estimate'):
            budget = context['project_estimate']
            prompt += f"""
ESTIMACIÓN DE PRESUPUESTO:
- Costo total estimado: {budget.get('costo_total', 0):,} {budget.get('moneda', 'EUR')}
- Duración estimada: {budget.get('duracion_estimada', 'No determinada')}
- Equipo recomendado: {budget.get('equipo_recomendado', {}).get('desarrolladores', 0)} desarrolladores, {budget.get('equipo_recomendado', {}).get('qa_testers', 0)} QA testers, {budget.get('equipo_recomendado', {}).get('project_manager', 0)} project manager
"""
        
        # Instrucciones específicas basadas en la situación
        if has_new_analysis:
            prompt += """
INSTRUCCIONES ESPECÍFICAS:
Has analizado el documento de requisitos del proyecto. Proporciona un resumen del análisis y de la estimación preliminar.
Menciona que este es un análisis inicial y que para un presupuesto detallado, el departamento de ventas puede proporcionar una propuesta formal.
Si el usuario está interesado en proceder, ofrece transferirlo al agente de ventas para discutir los siguientes pasos.
"""
        elif is_budget_request and context.get('project_estimate'):
            prompt += """
INSTRUCCIONES ESPECÍFICAS:
El usuario está preguntando sobre el presupuesto. Presenta la estimación que ya has calculado.
Menciona que esta es una estimación preliminar y que para un presupuesto formal y detallado, deberías hablar con el departamento de ventas.
Pregunta si desea que le transfieras al agente de ventas para discutir los detalles comerciales.
"""
        elif is_budget_request and not context.get('project_file_content'):
            prompt += """
INSTRUCCIONES ESPECÍFICAS:
El usuario está preguntando sobre presupuesto pero no ha proporcionado requisitos de proyecto.
Explica que para dar una estimación precisa, necesitas más información sobre el proyecto.
Sugiere que suba un documento con los requisitos o que describa el proyecto con más detalle.
Menciona que tenemos una funcionalidad para cargar archivos PDF o TXT con los requisitos del proyecto para un análisis más preciso.
"""
        else:
            prompt += """
INSTRUCCIONES ESPECÍFICAS:
Responde a la consulta técnica del usuario con profesionalidad y precisión.
Si el usuario pregunta por estimaciones o presupuestos, recomiéndale subir un documento con los requisitos para un análisis más detallado.
Si detectas que el usuario necesita hablar con ventas, ofrece transferirlo al agente correspondiente.
"""
        
        prompt += """
IMPORTANTE:
- Sé conciso pero informativo. Evita respuestas excesivamente largas.
- Utiliza lenguaje técnico profesional pero comprensible.
- Mantén un tono asertivo y seguro, propio de un experto técnico.
- Si no conoces la respuesta, indícalo claramente en lugar de inventar.
- Si el usuario pregunta por integraciones o servicios específicos de Alisys, menciona que Alisys ofrece soluciones a medida en esas áreas y que puede hablar con un agente de ventas para más detalles.

Responde directamente como el ingeniero técnico sin mencionar estas instrucciones.
"""
        
        # Enviar la solicitud al modelo y devolver la respuesta
        for chunk in send_chat_request(prompt, stream=True):
            chunk_data = json.loads(chunk.replace('data: ', ''))
            if 'token' in chunk_data:
                yield chunk_data['token'] 