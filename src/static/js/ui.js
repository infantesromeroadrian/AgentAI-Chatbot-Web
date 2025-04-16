/**
 * ui.js - Módulo para manejar la interfaz de usuario
 * Contiene funciones para manipular el DOM y mostrar mensajes
 */

const UI = {
    /**
     * Muestra el indicador de carga
     */
    showLoadingIndicator: function() {
        document.getElementById('user-input').disabled = true;
        document.getElementById('send-button').disabled = true;
        document.getElementById('thinking').style.display = 'flex';
        document.getElementById('status-indicator').className = 'status-indicator status-thinking';
        document.getElementById('status').textContent = 'Generando respuesta...';
    },

    /**
     * Oculta el indicador de carga
     */
    hideLoadingIndicator: function() {
        document.getElementById('thinking').style.display = 'none';
        document.getElementById('status-indicator').className = 'status-indicator status-connected';
        document.getElementById('status').textContent = 'Conectado';
        document.getElementById('user-input').disabled = false;
        document.getElementById('send-button').disabled = false;
        document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
    },

    /**
     * Añade un mensaje del usuario al chat
     * @param {string} text - Texto del mensaje
     */
    addUserMessage: function(text) {
        const chatContainer = document.getElementById('chat-container');
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        
        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar user-avatar';
        avatar.innerHTML = '<i class="fas fa-user"></i>';
        
        messageHeader.appendChild(avatar);
        messageElement.appendChild(messageHeader);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        messageElement.appendChild(messageContent);
        
        chatContainer.appendChild(messageElement);
        this.scrollToBottom();
    },

    /**
     * Añade un mensaje del bot al chat
     * @param {string} text - Texto del mensaje (puede contener markdown)
     */
    addBotMessage: function(text) {
        const chatContainer = document.getElementById('chat-container');
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        
        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar bot-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        messageHeader.appendChild(avatar);
        messageElement.appendChild(messageHeader);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content markdown';
        messageContent.innerHTML = marked.parse(text);
        messageElement.appendChild(messageContent);
        
        chatContainer.appendChild(messageElement);
        this.scrollToBottom();
        
        return messageElement;
    },

    /**
     * Añade un elemento de mensaje del bot al chat
     * @returns {HTMLElement} El elemento creado
     */
    addBotMessageElement: function() {
        const element = document.createElement('div');
        element.className = 'message bot-message';
        
        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar bot-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        messageHeader.appendChild(avatar);
        element.appendChild(messageHeader);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content markdown';
        element.appendChild(messageContent);
        
        // Añadir al chat
        document.getElementById('chat-container').appendChild(element);
        
        return element;
    },

    /**
     * Añade texto a la respuesta actual
     * @param {string} text - Texto a añadir
     */
    appendToResponse: function(text) {
        if (!currentResponseElement) return;
        
        const messageContent = currentResponseElement.querySelector('.message-content');
        if (!messageContent) return;
        
        // Añadir el texto y renderizar markdown
        const currentText = messageContent.getAttribute('data-text') || '';
        const newText = currentText + text;
        messageContent.setAttribute('data-text', newText);
        messageContent.innerHTML = marked.parse(newText);
        
        // Scroll al final
        this.scrollToBottom();
    },

    /**
     * Muestra un mensaje de error
     * @param {string} message - Mensaje de error
     */
    showErrorMessage: function(message) {
        if (!currentResponseElement) return;
        
        const messageContent = currentResponseElement.querySelector('.message-content');
        if (!messageContent) return;
        
        messageContent.textContent = message;
        currentResponseElement.className = 'message error-message';
    },

    /**
     * Muestra un mensaje de error en el formulario
     * @param {string} message - Mensaje de error
     */
    showFormError: function(message) {
        const errorElement = document.getElementById('form-field-error');
        if (!errorElement) return;
        
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Ocultar el mensaje después de 3 segundos
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 3000);
    },

    /**
     * Muestra un modal con contenido personalizado
     * @param {string} content - Contenido HTML del modal
     * @param {string} title - Título del modal
     */
    showModal: function(content, title) {
        const modal = document.getElementById('agent-info-modal');
        const modalContent = document.getElementById('agent-info-content');
        
        if (!modal || !modalContent) return;
        
        // Actualizar el contenido del modal
        modalContent.innerHTML = content;
        
        // Actualizar el título si se proporciona
        if (title) {
            const modalTitle = modal.querySelector('h2');
            if (modalTitle) {
                modalTitle.textContent = title;
            }
        }
        
        // Mostrar el modal
        modal.style.display = 'flex';
    },

    /**
     * Actualiza el estado de conexión en la interfaz
     * @param {boolean} connected - Estado de la conexión
     * @param {string} message - Mensaje a mostrar
     */
    updateConnectionStatus: function(connected, message) {
        if (connected) {
            document.getElementById('status-indicator').className = 'status-indicator status-connected';
            document.getElementById('status').textContent = 'Conectado';
            document.getElementById('user-input').disabled = false;
            document.getElementById('send-button').disabled = false;
        } else {
            document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
            document.getElementById('status').textContent = message || 'Error de conexión';
            document.getElementById('user-input').disabled = true;
            document.getElementById('send-button').disabled = true;
        }
    },

    /**
     * Hace scroll hasta el final del chat
     */
    scrollToBottom: function() {
        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    },

    /**
     * Inicializa los eventos de la interfaz
     */
    initEvents: function() {
        // Manejar la tecla Enter en el input
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                APP.sendMessage();
            }
        });
        
        // Configurar el botón de enviar
        document.getElementById('send-button').addEventListener('click', function() {
            APP.sendMessage();
        });
        
        // Configurar el botón de información de agentes
        const infoButton = document.getElementById('agent-info-button');
        const infoModal = document.getElementById('agent-info-modal');
        const closeButton = document.getElementById('agent-info-close');
        
        if (infoButton && infoModal && closeButton) {
            // Mostrar el modal al hacer clic en el botón de información
            infoButton.addEventListener('click', function() {
                infoModal.style.display = 'flex';
            });
            
            // Cerrar el modal al hacer clic en el botón de cierre
            closeButton.addEventListener('click', function() {
                infoModal.style.display = 'none';
            });
            
            // Cerrar el modal al hacer clic fuera del contenido
            infoModal.addEventListener('click', function(event) {
                if (event.target === infoModal) {
                    infoModal.style.display = 'none';
                }
            });
        }
    }
}; 