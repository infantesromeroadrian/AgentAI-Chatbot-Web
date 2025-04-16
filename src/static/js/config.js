/**
 * config.js - Configuración global para el chatbot
 * Contiene constantes y configuraciones utilizadas en toda la aplicación
 */

// Variables globales para el estado de la aplicación
let currentResponseElement = null;

// Configuración de endpoints
const CONFIG = {
    // Endpoints de la API
    endpoints: {
        health: '/agent/health',
        chat: '/agent/chat/stream',
        submitContact: '/submit-contact',
        getLastLead: '/admin/get-last-lead'
    },
    
    // Configuración de timeouts
    timeouts: {
        connection: 30000, // 30 segundos
        reconnect: 5000    // 5 segundos
    },
    
    // Mensajes del sistema
    messages: {
        welcome: "¡Hola! Soy el asistente virtual de Alisys. ¿En qué puedo ayudarte hoy?",
        connectionError: "Error: No se pudo conectar con el servidor. Verifica tu conexión a internet.",
        timeoutError: "Error: La solicitud ha tardado demasiado tiempo. Por favor, intenta de nuevo.",
        serverError: "Error en el servidor. Por favor, intenta de nuevo.",
        formSuccess: "¡Gracias por proporcionarnos tus datos de contacto! Un representante se pondrá en contacto contigo pronto.",
        formError: "Lo siento, ha ocurrido un error al procesar tus datos. Por favor, intenta de nuevo."
    },
    
    // Configuración del formulario
    form: {
        fields: {
            'name': { 
                label: 'Nombre completo', 
                placeholder: 'Ej. Juan Pérez', 
                required: true,
                type: 'text'
            },
            'email': { 
                label: 'Correo electrónico', 
                placeholder: 'Ej. juan@ejemplo.com', 
                required: true,
                type: 'email'
            },
            'phone': { 
                label: 'Número de teléfono', 
                placeholder: 'Ej. 612345678', 
                required: true,
                type: 'tel'
            },
            'company': { 
                label: 'Nombre de la empresa', 
                placeholder: 'Ej. Empresa S.A.', 
                required: true,
                type: 'text'
            }
        }
    }
}; 