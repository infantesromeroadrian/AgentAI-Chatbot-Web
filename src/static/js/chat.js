/**
 * chat.js - Módulo para manejar la funcionalidad del chat
 * Contiene funciones para procesar mensajes y gestionar la conversación
 */

const CHAT = {
    // Estado de la conversación
    messageCount: 0,
    conversationCompleted: false,
    
    /**
     * Verifica si un mensaje contiene todos los datos del formulario
     * @param {string} message - Mensaje a verificar
     * @returns {boolean} - Verdadero si el mensaje contiene todos los datos
     */
    checkIfMessageContainsAllFormData: function(message) {
        // Verificar si el mensaje contiene nombre, email y teléfono
        const nameRegex = /(?:me llamo|soy|nombre[:]?\s+es|nombre[:]?)[^\n.]*?([A-Za-zÀ-ÖØ-öø-ÿ\s]{2,})/i;
        const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/i;
        const phoneRegex = /(?:teléfono|telefono|tel|móvil|movil|celular|número|numero)[^\n.]*?([0-9+\s()-]{6,})/i;
        const companyRegex = /(?:empresa|compañía|compania|organización|organizacion|trabajo)[^\n.]*?([A-Za-zÀ-ÖØ-öø-ÿ\s]{2,})/i;
        
        // Extraer los datos del mensaje
        const nameMatch = message.match(nameRegex);
        const emailMatch = message.match(emailRegex);
        const phoneMatch = message.match(phoneRegex);
        const companyMatch = message.match(companyRegex);
        
        // Verificar si se encontraron al menos nombre, email y teléfono
        if (nameMatch && emailMatch && phoneMatch) {
            // Extraer los valores
            const name = nameMatch[1].trim();
            const email = emailMatch[0].trim();
            const phone = phoneMatch[1].trim();
            const company = companyMatch ? companyMatch[1].trim() : '';
            
            // Guardar los datos en el formulario
            FORM.formData = {
                name: name,
                email: email,
                phone: phone,
                company: company
            };
            
            return true;
        }
        
        return false;
    },
    
    /**
     * Verifica si un agente es el de recopilación de datos
     * @param {Object} data - Datos de la respuesta
     * @returns {boolean} - Verdadero si es el agente de recopilación de datos
     */
    checkIfDataCollectionAgent: function(data) {
        return data.agent === 'DataCollectionAgent';
    },
    
    /**
     * Añade botones de selección de agente
     * @param {HTMLElement} container - Contenedor donde añadir los botones
     */
    addAgentSelectionButtons: function(container) {
        // Crear contenedor para los botones
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'agent-selection-buttons';
        
        // Añadir título
        const title = document.createElement('div');
        title.className = 'agent-selection-title';
        title.textContent = '¿Quieres hablar con un agente específico?';
        buttonsContainer.appendChild(title);
        
        // Añadir botones para cada agente
        const agents = [
            { id: 'general', name: 'General', prompt: 'Quiero hablar con el agente general' },
            { id: 'sales', name: 'Ventas', prompt: 'Quiero hablar con el agente de ventas' },
            { id: 'engineer', name: 'Técnico', prompt: 'Quiero hablar con el agente técnico' },
            { id: 'data', name: 'Contacto', prompt: 'Quiero dejar mis datos de contacto' }
        ];
        
        agents.forEach(agent => {
            const button = document.createElement('button');
            button.className = 'agent-button';
            button.textContent = agent.name;
            button.addEventListener('click', () => {
                // Enviar mensaje para cambiar de agente
                const message = agent.prompt;
                
                // Añadir mensaje del usuario
                UI.addUserMessage(message);
                
                // Limpiar el input y hacer scroll
                document.getElementById('user-input').value = '';
                
                // Enviar el mensaje al servidor
                API.sendChatRequest(message);
            });
            buttonsContainer.appendChild(button);
        });
        
        // Añadir los botones al contenedor
        container.appendChild(buttonsContainer);
    },
    
    /**
     * Incrementa el contador de mensajes
     */
    incrementMessageCount: function() {
        this.messageCount++;
    },
    
    /**
     * Marca la conversación como completada
     */
    markConversationAsCompleted: function() {
        this.conversationCompleted = true;
        sessionStorage.setItem('conversation_completed', 'true');
    },
    
    /**
     * Reinicia el estado de la conversación
     */
    resetConversation: function() {
        this.messageCount = 0;
        this.conversationCompleted = false;
        sessionStorage.removeItem('conversation_completed');
    },
    
    /**
     * Inicializa el módulo de chat
     */
    init: function() {
        console.log("Inicializando módulo de chat...");
        
        // Verificar si hay una conversación completada en sessionStorage
        this.conversationCompleted = sessionStorage.getItem('conversation_completed') === 'true';
        
        // Limpiar el estado de la conversación al cargar la página
        if (!this.conversationCompleted) {
            sessionStorage.removeItem('conversation_completed');
        }
    }
}; 