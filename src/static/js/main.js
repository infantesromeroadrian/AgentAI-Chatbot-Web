let currentResponseElement = null;
let contactFormData = {};
let currentField = null;
let formActive = false;
let formFieldsCompleted = 0;
let totalFormFields = 5; // Nombre, email, teléfono, empresa, área de interés

// Inicializar el chat con un mensaje de bienvenida
document.addEventListener('DOMContentLoaded', function() {
    addBotMessage("¡Hola! Soy el asistente virtual de Alisys. ¿En qué puedo ayudarte hoy?");
});

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;
    
    // Si estamos en modo formulario, procesar el campo actual
    if (formActive && currentField) {
        contactFormData[currentField] = message;
        formFieldsCompleted++;
        
        // Mostrar confirmación del campo con estilo destacado
        addBotMessage(`✅ Has ingresado: **${message}**`);
        
        // Limpiar el campo actual
        currentField = null;
        
        // Restaurar placeholder
        document.getElementById('user-input').placeholder = "Escribe tu mensaje...";
        userInput.value = '';
        
        // Si hemos completado todos los campos, enviar el formulario automáticamente
        if (formFieldsCompleted >= totalFormFields) {
            submitContactForm();
            formActive = false;
            formFieldsCompleted = 0;
        }
        return;
    }
    
    // Deshabilitar entrada mientras procesa
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('thinking').style.display = 'flex';
    document.getElementById('status-indicator').className = 'status-indicator status-thinking';
    document.getElementById('status').textContent = 'Generando respuesta...';
    
    // Mostrar mensaje del usuario
    addUserMessage(message);
    userInput.value = '';
    
    // Preparar para respuesta del bot
    currentResponseElement = document.createElement('div');
    currentResponseElement.className = 'message bot-message';
    
    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar bot-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    messageHeader.appendChild(avatar);
    currentResponseElement.appendChild(messageHeader);
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content markdown';
    currentResponseElement.appendChild(messageContent);
    
    document.getElementById('chat-container').appendChild(currentResponseElement);
    
    // Usar streaming para la respuesta
    const eventSource = new EventSource('/chat/stream?message=' + encodeURIComponent(message));
    let fullResponse = '';
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.done) {
            // Finalizar streaming
            eventSource.close();
            document.getElementById('thinking').style.display = 'none';
            document.getElementById('status-indicator').className = 'status-indicator status-connected';
            document.getElementById('status').textContent = 'Conectado';
            document.getElementById('user-input').disabled = false;
            document.getElementById('send-button').disabled = false;
            document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
            
            // Renderizar markdown completo al final
            messageContent.innerHTML = marked.parse(fullResponse);
            
            // Si es un formulario completado, enviar los datos
            if (data.form && Object.keys(contactFormData).length > 0) {
                formActive = false;
                submitContactForm();
            }
        } else if (data.error) {
            // Mostrar error
            messageContent.textContent = 'Error: ' + data.error;
            currentResponseElement.className = 'message error-message';
            eventSource.close();
            document.getElementById('thinking').style.display = 'none';
            document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
            document.getElementById('status').textContent = 'Error';
            document.getElementById('user-input').disabled = false;
            document.getElementById('send-button').disabled = false;
        } else if (data.token) {
            // Agregar token a la respuesta
            fullResponse += data.token;
            // Actualizar con renderizado parcial de markdown
            messageContent.innerHTML = marked.parse(fullResponse);
            document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
            
            // Si hay un campo de formulario, guardarlo y destacarlo visualmente
            if (data.field) {
                formActive = true;
                currentField = data.field;
                
                // Cambiar el placeholder del input con instrucción clara
                const fieldLabel = getFieldLabel(currentField);
                document.getElementById('user-input').placeholder = `Escribe tu ${fieldLabel} aquí...`;
                
                // Aplicar animación de resaltado al input
                document.getElementById('user-input').classList.add('highlight-input');
                setTimeout(() => {
                    document.getElementById('user-input').classList.remove('highlight-input');
                }, 1500);
                
                // Enfocar el input
                document.getElementById('user-input').focus();
                
                // Mostrar mensaje de ayuda destacado
                const helpMessage = document.createElement('div');
                helpMessage.className = 'form-help-message';
                helpMessage.innerHTML = `<i class="fas fa-info-circle"></i> Por favor, escribe tu <strong>${fieldLabel}</strong> y presiona Enter`;
                messageContent.appendChild(helpMessage);
            }
        }
    };
    
    eventSource.onerror = function() {
        eventSource.close();
        if (messageContent.textContent === '') {
            messageContent.textContent = 'Error: No se pudo conectar con el servidor.';
            currentResponseElement.className = 'message error-message';
        }
        document.getElementById('thinking').style.display = 'none';
        document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
        document.getElementById('status').textContent = 'Error de conexión';
        document.getElementById('user-input').disabled = false;
        document.getElementById('send-button').disabled = false;
    };
}

function getFieldLabel(field) {
    const labels = {
        'name': 'nombre completo',
        'email': 'correo electrónico',
        'phone': 'teléfono',
        'company': 'empresa',
        'interest': 'área de interés'
    };
    return labels[field] || field;
}

function submitContactForm() {
    // Mostrar mensaje de envío
    addBotMessage("Enviando tus datos...");
    
    // Enviar datos al servidor
    fetch('/submit-contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(contactFormData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addBotMessage("¡Gracias! Tus datos han sido guardados correctamente. Un representante de Alisys se pondrá en contacto contigo pronto.");
        } else {
            addBotMessage("Lo siento, ha ocurrido un error al guardar tus datos: " + data.message);
        }
        // Limpiar datos del formulario
        contactFormData = {};
        currentField = null;
        formActive = false;
        // Restaurar placeholder
        document.getElementById('user-input').placeholder = "Escribe tu mensaje...";
    })
    .catch(error => {
        addBotMessage("Error al enviar el formulario: " + error.message);
        // Limpiar datos del formulario
        contactFormData = {};
        currentField = null;
        formActive = false;
        // Restaurar placeholder
        document.getElementById('user-input').placeholder = "Escribe tu mensaje...";
    });
}

function addUserMessage(text) {
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
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addBotMessage(text) {
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
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Manejar envío con Enter
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Verificar estado de conexión al cargar
window.addEventListener('load', checkConnectionStatus);

function checkConnectionStatus() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (data.lm_studio_connected) {
                document.getElementById('status-indicator').className = 'status-indicator status-connected';
                document.getElementById('status').textContent = 'Conectado';
            } else {
                document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
                document.getElementById('status').textContent = 'LM Studio no conectado';
            }
        })
        .catch(() => {
            document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
            document.getElementById('status').textContent = 'Error de conexión';
        });
} 