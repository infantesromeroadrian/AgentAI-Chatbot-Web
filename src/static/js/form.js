/**
 * form.js - Módulo para manejar el formulario de contacto
 * Contiene funciones para activar campos, validar y enviar el formulario
 */

const FORM = {
    // Estado del formulario
    active: false,
    currentField: null,
    formData: {},
    
    /**
     * Activa un campo específico del formulario
     * @param {string} field - Nombre del campo a activar
     */
    activateField: function(field) {
        if (!field || !CONFIG.form.fields[field]) return;
        
        console.log("Activando campo:", field);
        this.active = true;
        this.currentField = field;
        
        // Mostrar el formulario si no está visible
        document.getElementById('contact-form-container').style.display = 'block';
        
        // Actualizar la etiqueta del campo
        const fieldConfig = CONFIG.form.fields[field];
        document.getElementById('form-field-label').textContent = fieldConfig.label;
        
        // Configurar el tipo de entrada
        const input = document.getElementById('form-field-input');
        input.type = fieldConfig.type || 'text';
        input.placeholder = fieldConfig.placeholder || '';
        input.value = this.formData[field] || '';
        input.focus();
        
        // Mostrar mensaje de ayuda si existe
        const helpText = document.getElementById('form-field-help');
        helpText.textContent = fieldConfig.help || '';
        helpText.style.display = fieldConfig.help ? 'block' : 'none';
    },
    
    /**
     * Valida el valor del campo actual
     * @param {string} value - Valor a validar
     * @returns {boolean} - Verdadero si el valor es válido
     */
    validateField: function(value) {
        if (!this.currentField) return false;
        
        const fieldConfig = CONFIG.form.fields[this.currentField];
        
        // Validar según el tipo de campo
        if (fieldConfig.required && !value.trim()) {
            UI.showFormError('Este campo es obligatorio');
            return false;
        }
        
        if (this.currentField === 'email' && value.trim()) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                UI.showFormError('Por favor, introduce un email válido');
                return false;
            }
        }
        
        if (this.currentField === 'phone' && value.trim()) {
            const phoneRegex = /^[0-9+\s()-]{6,20}$/;
            if (!phoneRegex.test(value)) {
                UI.showFormError('Por favor, introduce un número de teléfono válido');
                return false;
            }
        }
        
        return true;
    },
    
    /**
     * Guarda el valor del campo actual y avanza al siguiente
     * @param {string} value - Valor a guardar
     */
    submitField: function(value) {
        if (!this.currentField) return;
        
        // Validar el campo
        if (!this.validateField(value)) return;
        
        // Guardar el valor
        this.formData[this.currentField] = value;
        console.log("Datos del formulario actualizados:", this.formData);
        
        // Determinar el siguiente campo
        const nextField = this.getNextField();
        
        // Si no hay más campos, enviar el formulario
        if (!nextField) {
            this.submitForm();
            return;
        }
        
        // Activar el siguiente campo
        this.activateField(nextField);
    },
    
    /**
     * Determina el siguiente campo a mostrar
     * @returns {string|null} - Nombre del siguiente campo o null si no hay más
     */
    getNextField: function() {
        const fields = Object.keys(CONFIG.form.fields);
        const currentIndex = fields.indexOf(this.currentField);
        
        if (currentIndex < 0 || currentIndex >= fields.length - 1) {
            return null;
        }
        
        return fields[currentIndex + 1];
    },
    
    /**
     * Envía el formulario completo al servidor
     */
    submitForm: function() {
        console.log("Enviando formulario:", this.formData);
        
        // Mostrar indicador de carga
        UI.showLoadingIndicator();
        
        // Ocultar el formulario
        document.getElementById('contact-form-container').style.display = 'none';
        
        // Enviar los datos al servidor
        API.submitContactForm(this.formData)
            .then(response => {
                console.log("Respuesta del servidor:", response);
                UI.hideLoadingIndicator();
                
                if (response.success) {
                    // Mostrar mensaje de éxito
                    UI.addBotMessage(CONFIG.messages.formSuccess);
                    
                    // Reiniciar el formulario
                    this.resetForm();
                } else {
                    // Mostrar mensaje de error
                    UI.showFormError(response.error || CONFIG.messages.formError);
                }
            })
            .catch(error => {
                console.error("Error al enviar formulario:", error);
                UI.hideLoadingIndicator();
                UI.showFormError(CONFIG.messages.formError);
            });
    },
    
    /**
     * Reinicia el estado del formulario
     */
    resetForm: function() {
        this.active = false;
        this.currentField = null;
        this.formData = {};
        
        // Limpiar el campo de entrada
        document.getElementById('form-field-input').value = '';
    },
    
    /**
     * Inicializa los eventos relacionados con el formulario
     */
    init: function() {
        console.log("Inicializando módulo de formulario...");
        
        // Verificar si existen los elementos del formulario
        const submitButton = document.getElementById('form-submit-button');
        const fieldInput = document.getElementById('form-field-input');
        
        if (!submitButton || !fieldInput) {
            console.error("No se encontraron los elementos del formulario");
            return;
        }
        
        // Configurar el evento para enviar el campo
        submitButton.addEventListener('click', () => {
            const value = fieldInput.value;
            this.submitField(value);
        });
        
        // Configurar el evento para enviar el campo con Enter
        fieldInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const value = e.target.value;
                this.submitField(value);
            }
        });
    }
}; 