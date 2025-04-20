"""
Agente de ventas para el chatbot de Alisys.
Este agente se encarga de proporcionar información sobre precios, planes y
cotizaciones para los servicios de Alisys.
"""
from typing import Dict, List, Any, Optional, Generator
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class SalesAgent(BaseAgent):
    """
    Agente especializado en ventas y cotizaciones.
    """
    
    def __init__(self):
        """
        Inicializa el agente de ventas.
        """
        super().__init__(
            name="SalesAgent",
            description="Especialista en cotizaciones y precios de servicios"
        )
    
    def _adjust_confidence(self, base_confidence: float, message: str, context: Dict[str, Any]) -> float:
        """
        Ajusta la confianza del agente de ventas basado en criterios específicos.
        
        Args:
            base_confidence: Confianza base calculada por el clasificador
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Confianza ajustada
        """
        # Normalizar mensaje para búsquedas
        normalized_message = message.lower()
        
        # Si el mensaje contiene palabras muy específicas de ventas, aumentar aún más la confianza
        high_sales_indicators = [
            "cotización", "cotizar", "presupuesto", "cuánto cuesta", "cuanto vale",
            "descuento", "oferta", "promoción", "contrato", "presupuestar",
            "precio", "costo", "valor", "pagar", "interesado en cotizar"
        ]
        
        # Verificar palabras clave de alta prioridad
        for indicator in high_sales_indicators:
            if indicator in normalized_message:
                base_confidence += 0.25  # Aumentado de 0.15 a 0.25
                logger.info(f"Término de ventas crítico detectado en mensaje: '{indicator}'")
                break  # Aplicar solo una vez este bonus
        
        # Verificación aún más específica para términos relacionados con cotizaciones
        cotization_terms = ["cotizar", "cotización", "cotizacion", "presupuesto"]
        if any(term in normalized_message for term in cotization_terms):
            base_confidence += 0.25  # Bonus adicional para términos de cotización
            logger.info(f"Término explícito de cotización detectado en mensaje")
        
        # Si contiene la palabra 'call center' o 'contact center' y está relacionado con precio
        if ('call center' in normalized_message or 'contact center' in normalized_message) and \
           any(term in normalized_message for term in ['precio', 'costo', 'cotizar', 'cotización']):
            base_confidence += 0.3
            logger.info(f"Consulta sobre precios de call center detectada")
        
        # Si el agente anterior fue el ingeniero, es probable que ahora necesiten cotizar
        if context.get('previous_agent') == "EngineerAgent":
            base_confidence += 0.2
        
        # Si hay información técnica en el contexto pero aún no se ha hablado de precios
        if context.get('project_info') and not context.get('price_discussed', False):
            base_confidence += 0.15
        
        # Si hemos mostrado precios anteriormente, mantener a este agente como preferido
        if context.get('current_agent') == self.name:
            base_confidence += 0.15
        
        # Si el usuario pregunta por un plan específico que mencionamos antes
        plan_keywords = ["plan básico", "plan básico", "plan estándar", "plan premium"]
        if any(plan in normalized_message for plan in plan_keywords):
            base_confidence += 0.25
            
        # Penalizar si el mensaje parece ser solo para dejar datos sin pedir información de precios
        data_only_patterns = [
            "mis datos son", "mi correo es", "mi teléfono es", "mi telefono es",
            "mi nombre es", "mi empresa es", "pueden contactarme"
        ]
        if any(pattern in normalized_message for pattern in data_only_patterns) and \
           not any(term in normalized_message for term in high_sales_indicators):
            base_confidence -= 0.2
            logger.info(f"Mensaje parece ser solo para dejar datos, reduciendo confianza")
        
        return min(base_confidence, 1.0)  # Limitar a 1.0
    
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Genera el prompt específico para este agente.
        
        Args:
            context: Contexto de la conversación
            
        Returns:
            Prompt del sistema para el LLM
        """
        # Extraer información relevante del contexto
        project_info = context.get('project_info', {})
        
        # Marcar que hemos hablado de precios en el contexto
        context['price_discussed'] = True
        
        return f"""Eres un experto en ventas de Alisys, una empresa líder en soluciones tecnológicas innovadoras.
Tu objetivo es proporcionar cotizaciones precisas y persuasivas para los servicios de Alisys.

INSTRUCCIONES:
1. Proporciona información clara sobre precios y planes de los servicios de Alisys.
2. Destaca el valor y los beneficios de los servicios, no solo el precio.
3. Adapta tus recomendaciones a las necesidades específicas del cliente.
4. Menciona ventajas competitivas de Alisys frente a otras alternativas.
5. Si no tienes información suficiente para una cotización precisa, solicita más detalles.
6. Ofrece diferentes opciones o planes cuando sea posible.
7. Menciona que estas cotizaciones son estimaciones iniciales y pueden ajustarse.
8. Después de proporcionar una cotización o cuando el usuario muestre interés en avanzar, sugiere explícitamente cambiar al agente de Datos con un mensaje como: "Para proceder con tu solicitud y que un representante pueda contactarte con una propuesta formal, necesitaremos algunos datos de contacto. ¿Te gustaría que te conecte con nuestro agente de recopilación de datos?"
9. Si el usuario solicita más información técnica, sugiere volver al agente Técnico.
10. Recuerda que tu función principal es proporcionar cotizaciones y cerrar ventas, no detalles técnicos profundos.

INFORMACIÓN ESPECÍFICA SOBRE COTIZACIONES PARA INTEGRACIÓN DE APIS EN CALL CENTERS:
- Cuando el usuario venga del agente técnico y haya consultado sobre integración de APIs para call centers, proporciona cotizaciones específicas como:

1. Plan Básico de Integración API para Call Centers:
   * Integración con un sistema CRM o ERP
   * Configuración de webhooks básicos
   * Soporte para APIs REST
   * Tiempo de implementación: 3-4 semanas
   * Costo estimado: $8,000-$12,000 USD

2. Plan Estándar de Integración API para Call Centers:
   * Integración con múltiples sistemas (CRM, ERP, etc.)
   * Configuración de webhooks y callbacks avanzados
   * Soporte para APIs REST y SOAP
   * Automatización de flujos de llamadas básicos
   * Tiempo de implementación: 4-6 semanas
   * Costo estimado: $15,000-$25,000 USD

3. Plan Premium de Integración API para Call Centers:
   * Integración completa con todos los sistemas necesarios
   * Soporte para REST, SOAP y WebSockets
   * Automatización avanzada de flujos de llamadas
   * Análisis de voz y sentiment analysis
   * Personalización completa según necesidades
   * Tiempo de implementación: 6-8 semanas
   * Costo estimado: $30,000-$50,000 USD

- Destaca que estos precios incluyen consultoría, implementación, pruebas y capacitación.
- Menciona que ofrecemos planes de mantenimiento mensual a partir de $1,500 USD dependiendo del alcance.

FLUJO DE CONVERSACIÓN RECOMENDADO:
1. Proporciona cotizaciones y opciones de precios → Sugiere cambiar al agente de Datos para finalizar el proceso y que un representante contacte al cliente.
2. Guía al usuario a través de este flujo de manera natural, sugiriendo el cambio de agente en el momento adecuado.

INFORMACIÓN DEL PROYECTO:
{self._format_project_info(project_info)}

Historial de conversación:
{self._format_conversation_history(context)}
"""
    
    def _format_project_info(self, project_info: Dict[str, Any]) -> str:
        """
        Formatea la información del proyecto para incluirla en el prompt.
        
        Args:
            project_info: Información del proyecto
            
        Returns:
            Información del proyecto formateada
        """
        if not project_info:
            return "No hay información específica del proyecto disponible."
        
        formatted_info = ""
        for key, value in project_info.items():
            formatted_key = key.replace('_', ' ').capitalize()
            formatted_info += f"- {formatted_key}: {value}\n"
        
        return formatted_info 

    def can_handle(self, message: str, context: Dict[str, Any]) -> float:
        """
        Determina la confianza del agente para manejar el mensaje.
        
        Args:
            message: El mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Un valor entre 0 y 1 que indica la confianza
        """
        # Palabras clave relacionadas con ventas, costos y presupuestos
        sales_keywords = [
            'presupuesto', 'precio', 'costo', 'coste', 'inversión', 'inversion',
            'tarifa', 'cotización', 'cotizacion', 'propuesta', 'oferta',
            'comercial', 'contrato', 'plan', 'paquete', 'servicio',
            'comprar', 'adquirir', 'implementar', 'contratar', 'vender'
        ]
        
        # Inicializar con un valor base
        confidence = 0.1
        
        # Verificar si viene de análisis técnico - aumentar confianza significativamente
        if context.get('project_info', {}).get('has_file_analysis') and "presupuesto" in message.lower():
            confidence += 0.6
        
        # Aumentar confianza si hay términos de ventas
        message_lower = message.lower()
        for keyword in sales_keywords:
            if keyword in message_lower:
                confidence += 0.2
                # Evitar valores mayores a 1
                if confidence >= 1.0:
                    return 1.0
        
        # Si hay una pregunta específica sobre costos o precios
        cost_patterns = [
            'cuánto cuesta', 'cuanto cuesta', 'precio de', 'costo de', 'coste de',
            'qué precio', 'que precio', 'qué costo', 'que costo', 'valor de',
            'presupuesto para', 'cuánto vale', 'cuanto vale', 'tarifas', 'planes',
            'paquetes', 'opciones', 'comparación de precios', 'comparacion de precios',
            'descuento', 'oferta', 'promoción', 'promocion'
        ]
        
        for pattern in cost_patterns:
            if pattern in message_lower:
                confidence += 0.3
                # Evitar valores mayores a 1
                if confidence >= 1.0:
                    return 1.0
        
        # Verificar si hay términos relacionados con contratación o cierre de venta
        closing_patterns = [
            'contratar', 'contratación', 'contratacion', 'comprar', 'adquirir',
            'siguiente paso', 'proceso de compra', 'forma de pago', 'método de pago',
            'metodo de pago', 'facturación', 'facturacion', 'términos', 'terminos',
            'condiciones', 'contrato', 'acuerdo', 'cerrar', 'cierre'
        ]
        
        for pattern in closing_patterns:
            if pattern in message_lower:
                confidence += 0.3
                # Evitar valores mayores a 1
                if confidence >= 1.0:
                    return 1.0
                    
        return min(confidence, 1.0)

    def process(self, message: str, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Procesa un mensaje y genera una respuesta relacionada con ventas.
        
        Args:
            message: El mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Un generador que produce partes de la respuesta
        """
        # Verificar si tenemos análisis técnico para utilizarlo en la generación de presupuesto
        has_tech_analysis = context.get('project_info', {}).get('has_file_analysis', False)
        
        # Obtener mensajes previos para contexto
        messages = self._get_conversation_history(context)
        
        # Añadir el sistema prompt específico para este agente
        system_prompt = self._get_system_prompt(context)
        
        # Si tenemos análisis técnico, agregar información al sistema prompt
        if has_tech_analysis and "presupuesto" in message.lower():
            tech_analysis = context.get('project_info', {}).get('technical_analysis', {})
            tech_info = self._format_technical_analysis_for_sales(tech_analysis)
            
            system_prompt += f"\n\n{tech_info}"
            
            # Ajustar el mensaje del usuario para indicar que debe usar el análisis técnico
            if "presupuesto" in message.lower():
                message = f"Utilizando el análisis técnico anterior, por favor genera un presupuesto detallado para el proyecto. {message}"
        
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        # Generar la respuesta
        for response_chunk in self._call_llm(messages, context):
            yield response_chunk

    def _format_technical_analysis_for_sales(self, tech_analysis: Dict[str, str]) -> str:
        """
        Formatea el análisis técnico para el agente de ventas.
        
        Args:
            tech_analysis: Diccionario con información técnica relevante
            
        Returns:
            Texto formateado para incluir en el sistema prompt
        """
        if not tech_analysis:
            return ""
            
        result = "INFORMACIÓN TÉCNICA DEL PROYECTO PARA ELABORACIÓN DE PRESUPUESTO:\n\n"
        
        if tech_analysis.get("technologies"):
            result += "TECNOLOGÍAS A UTILIZAR:\n" + tech_analysis["technologies"] + "\n\n"
            
        if tech_analysis.get("timeline"):
            result += "ESTIMACIÓN DE TIEMPOS:\n" + tech_analysis["timeline"] + "\n\n"
            
        if tech_analysis.get("resources"):
            result += "RECURSOS NECESARIOS:\n" + tech_analysis["resources"] + "\n\n"
            
        if tech_analysis.get("challenges"):
            result += "DESAFÍOS TÉCNICOS:\n" + tech_analysis["challenges"] + "\n\n"
            
        if tech_analysis.get("budget_factors"):
            result += "FACTORES RELEVANTES PARA EL PRESUPUESTO:\n" + tech_analysis["budget_factors"] + "\n\n"
            
        result += "Usa esta información técnica detallada para elaborar un presupuesto preciso y completo que incluya todas las fases de desarrollo, recursos necesarios y consideraciones especiales basadas en los desafíos técnicos identificados."
        
        return result 