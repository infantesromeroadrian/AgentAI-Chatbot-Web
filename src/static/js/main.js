let currentResponseElement = null;

// Inicializar el chat con un mensaje de bienvenida
document.addEventListener('DOMContentLoaded', function() {
    addBotMessage("¡Hola! Soy el asistente virtual de Alisys. ¿En qué puedo ayudarte hoy?");
});

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;
    
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