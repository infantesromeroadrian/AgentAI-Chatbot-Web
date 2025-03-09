let currentResponseElement = null;
let contactFormData = {};
let currentField = null;
let formActive = false;
let formFieldsCompleted = 0;
let totalFormFields = 5; // Nombre, email, teléfono, empresa, área de interés
let formFieldOrder = ['name', 'email', 'phone', 'company', 'interest']; // Orden de los campos
let currentFieldIndex = 0;
let formFields = [
    { id: 'name', label: 'Nombre completo', placeholder: 'Ej. Juan Pérez', required: true },
    { id: 'email', label: 'Correo electrónico', placeholder: 'Ej. juan@ejemplo.com', required: true },
    { id: 'phone', label: 'Número de teléfono', placeholder: 'Ej. 612345678', required: true },
    { id: 'company', label: 'Nombre de la empresa', placeholder: 'Ej. Empresa S.A.', required: true }
];

// Inicializar el chat con un mensaje de bienvenida
document.addEventListener('DOMContentLoaded', function() {
    addBotMessage("¡Hola! Soy el asistente virtual de Alisys. ¿En qué puedo ayudarte hoy?");
    
    // Limpiar el estado de la conversación al cargar la página
    sessionStorage.removeItem('conversation_completed');
    
    // Inicializar el chatbot
    checkConnectionStatus();
    
    // Manejar la tecla Enter en el input
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Si estamos en modo agentes, configurar el botón de información
    if (useAgents) {
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
});

function sendMessage(customMessage = null, hidden = false) {
    const userInput = document.getElementById('user-input');
    const message = customMessage || userInput.value.trim();
    
    if (!message) return;
    
    // Si la conversación ya ha sido completada, solo responder con un mensaje de despedida
    if (sessionStorage.getItem('conversation_completed') === 'true') {
        addUserMessage(message);
        addBotMessage("Gracias por tu mensaje. Un representante de Alisys ya ha recibido tus datos y se pondrá en contacto contigo en breve. Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**.");
        userInput.value = '';
        return;
    }
    
    // Si estamos en modo formulario, procesar el campo actual
    if (formActive && currentField) {
        // Guardar el valor del campo actual
        contactFormData[currentField] = message;
        formFieldsCompleted++;
        
        // Mostrar confirmación del campo con estilo destacado
        addBotMessage(`✅ Has ingresado: **${message}** como tu ${getFieldLabel(currentField)}`);
        
        // Determinar el siguiente campo a solicitar
        if (currentFieldIndex < formFieldOrder.length - 1) {
            currentFieldIndex++;
            const nextField = formFieldOrder[currentFieldIndex];
            currentField = nextField;
            
            // Solicitar el siguiente campo
            const fieldLabel = getFieldLabel(nextField);
            addBotMessage(`Por favor, ahora ingresa tu **${fieldLabel}**:`);
            
            // Cambiar el placeholder del input
            document.getElementById('user-input').placeholder = `Escribe tu ${fieldLabel} aquí...`;
            
            // Aplicar animación de resaltado al input
            document.getElementById('user-input').classList.add('highlight-input');
            setTimeout(() => {
                document.getElementById('user-input').classList.remove('highlight-input');
            }, 1500);
            
            // Enfocar el input
            document.getElementById('user-input').focus();
        } else {
            // Si hemos completado todos los campos, enviar el formulario automáticamente
            currentField = null;
            formActive = false;
            formFieldsCompleted = 0;
            currentFieldIndex = 0;
            
            // Restaurar placeholder
            document.getElementById('user-input').placeholder = "Escribe tu mensaje...";
            
            // Enviar el formulario
            submitContactForm();
        }
        
        userInput.value = '';
        return;
    }
    
    // Verificar si el mensaje contiene todos los datos del formulario
    const containsAllFormData = checkIfMessageContainsAllFormData(message);
    if (containsAllFormData) {
        addUserMessage(message);
        userInput.value = '';
        
        // Enviar el mensaje completo al servidor para procesamiento
        submitCompleteFormMessage(message);
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
    
    // Solo añadir al chat si no es un mensaje oculto
    if (!hidden) {
        document.getElementById('chat-container').appendChild(currentResponseElement);
    }
    
    // Usar streaming para la respuesta
    const eventSource = new EventSource(chatEndpoint + '?message=' + encodeURIComponent(message));
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
            
            // Mostrar el agente que respondió
            if (data.agent) {
                const agentId = data.agent;
                const agentInfo = agentsInfo[agentId] || { 
                    name: agentId.replace('Agent', ''), 
                    color: '#607D8B' 
                };
                
                const agentBadge = document.createElement('div');
                agentBadge.className = `agent-badge agent-${agentId}`;
                agentBadge.textContent = `Agente: ${agentInfo.name}`;
                agentBadge.style.backgroundColor = agentInfo.color + '20'; // Añadir transparencia
                agentBadge.style.borderColor = agentInfo.color;
                messageHeader.appendChild(agentBadge);
                
                // Verificar si es el agente de recopilación de datos
                const isDataCollectionAgent = checkIfDataCollectionAgent(data);
                
                // Solo añadir botones de selección si estamos en modo agentes y no es el agente de datos
                if (useAgents && !isDataCollectionAgent) {
                    // Añadir botones de selección de agente después de la respuesta
                    addAgentSelectionButtons(messageContent);
                }
            }
            
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
                
                // Reiniciar el índice del campo actual basado en el campo recibido
                currentFieldIndex = formFieldOrder.indexOf(data.field);
                if (currentFieldIndex === -1) currentFieldIndex = 0;
                
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
            // Obtener el nombre del usuario y el área de interés
            const userName = contactFormData.name ? contactFormData.name.split(' ')[0] : '';
            const interestArea = contactFormData.interest && contactFormData.interest !== 'No especificado' 
                ? contactFormData.interest 
                : 'soluciones tecnológicas';
            
            addBotMessage("### ¡Gracias, " + userName + ", por proporcionarnos tus datos de contacto! 🎉\n\n" +
                         "Hemos registrado correctamente la siguiente información:\n\n" +
                         "- **Nombre**: " + contactFormData.name + "\n" +
                         "- **Email**: " + contactFormData.email + "\n" +
                         "- **Teléfono**: " + contactFormData.phone + "\n" +
                         "- **Empresa**: " + contactFormData.company + "\n" +
                         "- **Área de interés**: " + contactFormData.interest + "\n\n" +
                         "Un especialista en **" + interestArea + "** se pondrá en contacto contigo **en las próximas 24-48 horas laborables**.\n\n" +
                         "Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**.\n\n" +
                         "¡Que tengas un excelente día!");
                         
            // Marcar la conversación como finalizada
            sessionStorage.setItem('conversation_completed', 'true');
        } else {
            addBotMessage("Lo siento, ha ocurrido un error al guardar tus datos: " + data.message);
        }
        // Limpiar datos del formulario
        contactFormData = {};
        currentField = null;
        formActive = false;
        formFieldsCompleted = 0;
        currentFieldIndex = 0;
        // Restaurar placeholder
        document.getElementById('user-input').placeholder = "Escribe tu mensaje...";
    })
    .catch(error => {
        addBotMessage("Error al enviar el formulario: " + error.message);
        // Limpiar datos del formulario
        contactFormData = {};
        currentField = null;
        formActive = false;
        formFieldsCompleted = 0;
        currentFieldIndex = 0;
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

// Función para hacer scroll al final del chat
function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Verificar estado de conexión al cargar
window.addEventListener('load', checkConnectionStatus);

function checkConnectionStatus() {
    fetch(healthEndpoint)
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

// Función para enviar un mensaje al servidor (utilizada por los botones de agente)
function sendChatRequest(message) {
    // Deshabilitar entrada mientras procesa
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
    document.getElementById('thinking').style.display = 'flex';
    document.getElementById('status-indicator').className = 'status-indicator status-thinking';
    document.getElementById('status').textContent = 'Generando respuesta...';
    
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
    
    // Añadir al chat
    document.getElementById('chat-container').appendChild(currentResponseElement);
    
    // Usar streaming para la respuesta
    const eventSource = new EventSource(chatEndpoint + '?message=' + encodeURIComponent(message));
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
            
            // Mostrar el agente que respondió
            if (data.agent) {
                const agentId = data.agent;
                const agentInfo = agentsInfo[agentId] || { 
                    name: agentId.replace('Agent', ''), 
                    color: '#607D8B' 
                };
                
                const agentBadge = document.createElement('div');
                agentBadge.className = `agent-badge agent-${agentId}`;
                agentBadge.textContent = `Agente: ${agentInfo.name}`;
                agentBadge.style.backgroundColor = agentInfo.color + '20'; // Añadir transparencia
                agentBadge.style.borderColor = agentInfo.color;
                messageHeader.appendChild(agentBadge);
                
                // Verificar si es el agente de recopilación de datos
                const isDataCollectionAgent = checkIfDataCollectionAgent(data);
                
                // Solo añadir botones de selección si estamos en modo agentes y no es el agente de datos
                if (useAgents && !isDataCollectionAgent) {
                    // Añadir botones de selección de agente después de la respuesta
                    addAgentSelectionButtons(messageContent);
                }
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

// Función para verificar si el mensaje contiene todos los datos del formulario
function checkIfMessageContainsAllFormData(message) {
    // Verificar si el mensaje contiene email y nombre al menos
    const containsEmail = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/.test(message);
    const containsName = /(mi nombre es|me llamo|soy|nombre:?) .+/.test(message);
    
    // Si contiene ambos, probablemente sea un mensaje con todos los datos
    return containsEmail && containsName && message.length > 50;
}

// Función para enviar un mensaje completo con todos los datos del formulario
function submitCompleteFormMessage(message) {
    // Mostrar mensaje de procesamiento
    addBotMessage("Procesando tus datos...");
    
    // Enviar el mensaje al servidor para extraer los datos
    fetch('/submit-contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Solicitar los datos guardados para mostrarlos en la confirmación
            fetch('/admin/get-last-lead', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(leadData => {
                if (leadData.success) {
                    // Obtener el nombre del usuario y el área de interés
                    const userName = leadData.lead.name ? leadData.lead.name.split(' ')[0] : '';
                    const interestArea = leadData.lead.interest && leadData.lead.interest !== 'No especificado' 
                        ? leadData.lead.interest 
                        : 'soluciones tecnológicas';
                    
                    addBotMessage("### ¡Gracias, " + userName + ", por proporcionarnos tus datos de contacto! 🎉\n\n" +
                                 "Hemos registrado correctamente tu información:\n\n" +
                                 "- **Nombre**: " + leadData.lead.name + "\n" +
                                 "- **Email**: " + leadData.lead.email + "\n" +
                                 "- **Teléfono**: " + leadData.lead.phone + "\n" +
                                 "- **Empresa**: " + leadData.lead.company + "\n\n" +
                                 "Un especialista en **" + interestArea + "** se pondrá en contacto contigo **en las próximas 24-48 horas laborables**.\n\n" +
                                 "Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**.\n\n" +
                                 "¡Que tengas un excelente día!");
                } else {
                    // Si no se puede obtener el lead, mostrar mensaje genérico
                    addBotMessage("### ¡Gracias por proporcionarnos tus datos de contacto! 🎉\n\n" +
                                 "Hemos registrado correctamente tu información.\n\n" +
                                 "Un especialista de Alisys se pondrá en contacto contigo **en las próximas 24-48 horas laborables**.\n\n" +
                                 "Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**.\n\n" +
                                 "¡Que tengas un excelente día!");
                }
                
                // Marcar la conversación como finalizada
                sessionStorage.setItem('conversation_completed', 'true');
            })
            .catch(error => {
                // En caso de error, mostrar mensaje genérico
                addBotMessage("### ¡Gracias por proporcionarnos tus datos de contacto! 🎉\n\n" +
                             "Hemos registrado correctamente tu información.\n\n" +
                             "Un representante de Alisys se pondrá en contacto contigo **en las próximas 24-48 horas laborables**.\n\n" +
                             "Si necesitas asistencia inmediata, puedes llamarnos al **+34 910 200 000**.\n\n" +
                             "¡Que tengas un excelente día!");
                
                // Marcar la conversación como finalizada
                sessionStorage.setItem('conversation_completed', 'true');
            });
        } else {
            addBotMessage("Lo siento, ha ocurrido un error al procesar tus datos: " + data.message + "\n\n" +
                         "Por favor, proporciona la información de forma más estructurada o contacta con nosotros directamente al **+34 910 200 000**.");
        }
    })
    .catch(error => {
        addBotMessage("Error al procesar el formulario: " + error.message);
    });
}

/**
 * Añade botones para seleccionar el agente con el que se desea continuar la conversación
 * @param {HTMLElement} container - El contenedor donde se añadirán los botones
 */
function addAgentSelectionButtons(container) {
    // Crear el contenedor para los botones
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'agent-selection-buttons';
    
    // Añadir título
    const title = document.createElement('div');
    title.className = 'agent-selection-title';
    title.textContent = '¿Con qué agente deseas continuar?';
    buttonsContainer.appendChild(title);
    
    // Usar la información de agentes definida en el HTML
    for (const [agentId, agentInfo] of Object.entries(agentsInfo)) {
        const button = document.createElement('button');
        button.className = `agent-button agent-button-${agentId}`;
        button.innerHTML = `<strong>${agentInfo.name}</strong><span>${agentInfo.description}</span>`;
        
        // Añadir evento de clic
        button.addEventListener('click', function() {
            // Enviar mensaje especial para cambiar de agente
            const message = `!cambiar_agente:${agentId}`;
            
            // Añadir mensaje del usuario (visible)
            const userMessageText = `Cambiar al agente: ${agentInfo.name}`;
            addUserMessage(userMessageText);
            
            // Enviar el mensaje al servidor
            sendChatRequest(message);
            
            // Limpiar el input y hacer scroll
            document.getElementById('user-input').value = '';
            scrollToBottom();
        });
        
        buttonsContainer.appendChild(button);
    }
    
    // Añadir los botones al contenedor
    container.appendChild(buttonsContainer);
}

// Función para mostrar el formulario visual
function showContactForm() {
    // Verificar si ya existe un formulario
    if (document.getElementById('contact-form-container')) {
        return;
    }
    
    // Crear contenedor del formulario
    const formContainer = document.createElement('div');
    formContainer.id = 'contact-form-container';
    formContainer.className = 'contact-form-container';
    
    // Crear título
    const formTitle = document.createElement('h3');
    formTitle.textContent = 'Formulario de contacto';
    formContainer.appendChild(formTitle);
    
    // Crear descripción
    const formDescription = document.createElement('p');
    formDescription.textContent = 'Por favor, completa los siguientes campos para que podamos contactarte:';
    formContainer.appendChild(formDescription);
    
    // Crear formulario
    const form = document.createElement('form');
    form.id = 'contact-form';
    form.className = 'contact-form';
    
    // Añadir campos al formulario
    formFields.forEach(field => {
        const fieldContainer = document.createElement('div');
        fieldContainer.className = 'form-field';
        
        const label = document.createElement('label');
        label.htmlFor = field.id;
        label.textContent = field.label + (field.required ? ' *' : '');
        fieldContainer.appendChild(label);
        
        const input = document.createElement('input');
        input.type = field.id === 'email' ? 'email' : 'text';
        input.id = field.id;
        input.name = field.id;
        input.placeholder = field.placeholder;
        input.required = field.required;
        
        // Si ya tenemos datos para este campo, rellenarlos
        if (contactFormData[field.id]) {
            input.value = contactFormData[field.id];
        }
        
        fieldContainer.appendChild(input);
        form.appendChild(fieldContainer);
    });
    
    // Añadir botón de envío
    const submitButton = document.createElement('button');
    submitButton.type = 'submit';
    submitButton.className = 'form-submit-button';
    submitButton.textContent = 'Enviar información';
    form.appendChild(submitButton);
    
    // Añadir evento de envío
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Recopilar datos del formulario
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
            contactFormData[key] = value;
        }
        
        // Construir mensaje con todos los datos
        const message = `Mi nombre es ${data.name}, correo ${data.email}, teléfono ${data.phone}, empresa ${data.company}`;
        
        // Añadir mensaje del usuario
        addUserMessage(message);
        
        // Enviar mensaje al servidor
        submitCompleteFormMessage(message);
        
        // Ocultar formulario
        formContainer.remove();
    });
    
    formContainer.appendChild(form);
    
    // Añadir formulario al chat
    document.getElementById('chat-container').appendChild(formContainer);
    
    // Hacer scroll hasta el formulario
    document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
}

// Modificar la función para detectar cuando mostrar el formulario
function checkIfDataCollectionAgent(data) {
    if (data.agent === 'DataCollectionAgent') {
        // Si es el agente de recopilación de datos, mostrar el formulario
        setTimeout(showContactForm, 1000); // Esperar 1 segundo para que se muestre el mensaje del agente
        return true;
    }
    return false;
} 