"""
Agente de ventas para el chatbot de Alisys.
Este agente se encarga de proporcionar información sobre precios, planes y
cotizaciones para los servicios de Alisys.
"""
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

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
        # Si el mensaje contiene palabras muy específicas de ventas, aumentar aún más la confianza
        high_sales_indicators = [
            "cotización", "cotizar", "presupuesto", "cuánto cuesta", "cuanto vale",
            "descuento", "oferta", "promoción", "contrato", "presupuestar"
        ]
        
        # Verificar palabras clave de alta prioridad
        for indicator in high_sales_indicators:
            if indicator in message.lower():
                base_confidence += 0.15
                break  # Aplicar solo una vez este bonus
        
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
        if any(plan in message.lower() for plan in plan_keywords):
            base_confidence += 0.25
        
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