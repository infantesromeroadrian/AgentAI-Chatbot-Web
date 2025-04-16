/**
 * api.js - Módulo para manejar las comunicaciones con la API
 * Contiene funciones para enviar y recibir datos del servidor
 */

const API = {
    /**
     * Verifica el estado de conexión con el servidor
     * @returns {Promise<boolean>} - Promesa que se resuelve con el estado de la conexión
     */
    checkConnectionStatus: function() {
        console.log("Verificando estado de conexión...");
        console.log("Endpoint:", CONFIG.endpoints.health);
        
        return fetch(CONFIG.endpoints.health)
            .then(response => {
                console.log("Respuesta recibida:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Datos de estado:", data);
                
                if (data.lm_studio_connected) {
                    UI.updateConnectionStatus(true, 'Conectado');
                    return true;
                } else {
                    UI.updateConnectionStatus(false, 'LM Studio no conectado');
                    
                    // Mostrar información de diagnóstico si está disponible
                    if (data.diagnostics) {
                        console.log("Diagnóstico de conexión:", data.diagnostics);
                        
                        // Mostrar mensaje de error con información de diagnóstico
                        let errorMsg = "Error: No se pudo conectar con LM Studio. Por favor, asegúrate de que LM Studio esté en ejecución en tu máquina local en el puerto 1234.";
                        
                        if (data.diagnostics) {
                            errorMsg += `\n\nInformación de diagnóstico:\n- URL configurada: ${data.diagnostics.lm_studio_url}\n- Timeout: ${data.diagnostics.timeout}s`;
                        }
                        
                        UI.addBotMessage(errorMsg);
                    }
                    
                    return false;
                }
            })
            .catch(error => {
                console.error("Error al verificar conexión:", error);
                UI.updateConnectionStatus(false, 'Error de conexión');
                return false;
            });
    },

    /**
     * Envía un mensaje al servidor y procesa la respuesta en streaming
     * @param {string} message - Mensaje a enviar
     */
    sendChatRequest: function(message) {
        console.log("Enviando mensaje al servidor:", message);
        console.log("Endpoint:", CONFIG.endpoints.chat);
        
        // Crear un nuevo elemento para la respuesta del bot
        currentResponseElement = UI.addBotMessageElement();
        
        // Configurar un timeout para la solicitud
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeouts.connection);
        
        // Enviar la solicitud al servidor
        fetch(CONFIG.endpoints.chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
            signal: controller.signal
        })
        .then(response => {
            console.log("Respuesta recibida:", response.status);
            if (!response.ok) {
                throw new Error(`Error en la respuesta del servidor: ${response.status}`);
            }
            
            // Configurar un lector para procesar la respuesta en streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            // Función para procesar los chunks de datos
            function processChunk({ done, value }) {
                if (done) {
                    console.log("Procesamiento completado");
                    UI.hideLoadingIndicator();
                    clearTimeout(timeoutId); // Limpiar el timeout
                    return;
                }
                
                // Decodificar el chunk y añadirlo al buffer
                const chunk = decoder.decode(value, { stream: true });
                console.log("Chunk recibido:", chunk);
                buffer += chunk;
                
                // Procesar las líneas completas en el buffer
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Guardar la última línea incompleta
                
                // Procesar cada línea
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            console.log("Datos procesados:", data);
                            
                            // Procesar el token
                            if (data.token) {
                                UI.appendToResponse(data.token);
                            }
                            
                            // Verificar si la respuesta está completa
                            if (data.done) {
                                console.log("Respuesta completa");
                                UI.hideLoadingIndicator();
                                clearTimeout(timeoutId); // Limpiar el timeout
                                
                                // Actualizar el agente actual si se proporciona
                                if (data.agent && typeof AGENTS !== 'undefined') {
                                    AGENTS.updateCurrentAgent(data.agent);
                                }
                                
                                // Verificar si hay un error
                                if (data.error) {
                                    UI.showErrorMessage(CONFIG.messages.serverError);
                                }
                                
                                // Verificar si es un formulario
                                if (data.field && typeof FORM !== 'undefined') {
                                    FORM.activateField(data.field);
                                }
                            }
                        } catch (e) {
                            console.error('Error al procesar la respuesta:', e, line.substring(6));
                        }
                    }
                }
                
                // Continuar leyendo
                return reader.read().then(processChunk);
            }
            
            // Iniciar la lectura
            return reader.read().then(processChunk);
        })
        .catch(error => {
            console.error('Error en la solicitud:', error);
            UI.hideLoadingIndicator();
            clearTimeout(timeoutId); // Limpiar el timeout
            
            // Mostrar mensaje de error específico según el tipo de error
            if (error.name === 'AbortError') {
                UI.showErrorMessage(CONFIG.messages.timeoutError);
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                UI.showErrorMessage(CONFIG.messages.connectionError);
            } else {
                UI.showErrorMessage("Error: " + error.message);
            }
            
            // Reintentar la conexión después de un error
            setTimeout(this.checkConnectionStatus, CONFIG.timeouts.reconnect);
        });
    },

    /**
     * Envía los datos del formulario al servidor
     * @param {Object} formData - Datos del formulario
     * @returns {Promise} - Promesa que se resuelve con la respuesta del servidor
     */
    submitContactForm: function(formData) {
        return fetch(CONFIG.endpoints.submitContact, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json());
    },

    /**
     * Obtiene el último lead guardado
     * @returns {Promise} - Promesa que se resuelve con la respuesta del servidor
     */
    getLastLead: function() {
        return fetch(CONFIG.endpoints.getLastLead, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json());
    }
}; 