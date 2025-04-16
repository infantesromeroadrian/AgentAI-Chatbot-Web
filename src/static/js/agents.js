/**
 * agents.js - Módulo para manejar la información de los agentes
 * Contiene funciones para actualizar y mostrar información sobre los agentes
 */

const AGENTS = {
    // Información del agente actual
    current: null,
    
    /**
     * Actualiza la información del agente actual
     * @param {Object|string} agent - Información del agente o ID del agente
     */
    updateCurrentAgent: function(agent) {
        if (!agent) return;
        
        console.log("Actualizando agente actual:", agent);
        
        // Si agent es un string, convertirlo a un objeto
        if (typeof agent === 'string') {
            agent = {
                id: agent,
                name: this.getAgentNameFromId(agent),
                description: this.getAgentDescriptionFromId(agent)
            };
        }
        
        this.current = agent;
        
        // Actualizar la interfaz con la información del agente
        document.getElementById('agent-name').textContent = agent.name || 'Desconocido';
        document.getElementById('agent-description').textContent = agent.description || 'Sin descripción';
        
        // Mostrar el botón de información del agente
        document.getElementById('agent-info-button').style.display = 'flex';
    },
    
    /**
     * Obtiene el nombre del agente a partir de su ID
     * @param {string} agentId - ID del agente
     * @returns {string} - Nombre del agente
     */
    getAgentNameFromId: function(agentId) {
        const agentNames = {
            'GeneralAgent': 'Agente General',
            'SalesAgent': 'Agente de Ventas',
            'EngineerAgent': 'Agente Técnico',
            'DataCollectionAgent': 'Agente de Contacto'
        };
        
        return agentNames[agentId] || agentId;
    },
    
    /**
     * Obtiene la descripción del agente a partir de su ID
     * @param {string} agentId - ID del agente
     * @returns {string} - Descripción del agente
     */
    getAgentDescriptionFromId: function(agentId) {
        const agentDescriptions = {
            'GeneralAgent': 'Proporciona información general sobre Alisys',
            'SalesAgent': 'Especialista en productos, servicios y precios',
            'EngineerAgent': 'Especialista en aspectos técnicos y soluciones',
            'DataCollectionAgent': 'Recopila tus datos de contacto'
        };
        
        return agentDescriptions[agentId] || '';
    },
    
    /**
     * Muestra la información del agente actual
     */
    showAgentInfo: function() {
        if (!this.current) return;
        
        // Obtener información adicional según el tipo de agente
        let additionalInfo = '';
        
        switch (this.current.id) {
            case 'GeneralAgent':
                additionalInfo = `
                    <h4>Capacidades:</h4>
                    <ul>
                        <li>Proporcionar información general sobre Alisys</li>
                        <li>Responder preguntas sobre la empresa</li>
                        <li>Dirigirte al agente adecuado según tus necesidades</li>
                    </ul>
                `;
                break;
            case 'SalesAgent':
                additionalInfo = `
                    <h4>Capacidades:</h4>
                    <ul>
                        <li>Informar sobre productos y servicios</li>
                        <li>Proporcionar información sobre precios</li>
                        <li>Explicar las ventajas competitivas de Alisys</li>
                    </ul>
                `;
                break;
            case 'EngineerAgent':
                additionalInfo = `
                    <h4>Capacidades:</h4>
                    <ul>
                        <li>Resolver dudas técnicas</li>
                        <li>Explicar el funcionamiento de los servicios</li>
                        <li>Proporcionar información sobre integraciones y APIs</li>
                    </ul>
                `;
                break;
            case 'DataCollectionAgent':
                additionalInfo = `
                    <h4>Capacidades:</h4>
                    <ul>
                        <li>Recopilar tus datos de contacto</li>
                        <li>Registrar tu interés en productos específicos</li>
                        <li>Facilitar que un representante se ponga en contacto contigo</li>
                    </ul>
                `;
                break;
        }
        
        // Crear el contenido del modal
        const modalContent = `
            <div class="agent-info-modal">
                <h3>${this.current.name || 'Agente'}</h3>
                <p>${this.current.description || 'Sin descripción'}</p>
                ${additionalInfo}
            </div>
        `;
        
        // Mostrar el modal
        UI.showModal(modalContent, 'Información del Agente');
    },
    
    /**
     * Inicializa los eventos relacionados con los agentes
     */
    init: function() {
        console.log("Inicializando módulo de agentes...");
        
        // Configurar el evento para mostrar la información del agente
        const infoButton = document.getElementById('agent-info-button');
        if (infoButton) {
            infoButton.addEventListener('click', () => {
                this.showAgentInfo();
            });
        } else {
            console.error("No se encontró el botón de información del agente");
        }
    }
}; 