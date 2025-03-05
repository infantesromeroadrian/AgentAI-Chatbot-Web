"""
Punto de entrada principal para la aplicación del chatbot web.
"""
import os
from flask import Flask
from dotenv import load_dotenv

# Importar rutas de la API
from api.routes import register_routes
from api.agent_routes import register_agent_routes

# Cargar variables de entorno
load_dotenv()

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)
    
    # Configurar la clave secreta para las sesiones
    app.secret_key = os.getenv('SECRET_KEY', 'alisys_chatbot_secret_key')
    
    # Registrar rutas tradicionales
    register_routes(app)
    
    # Registrar rutas basadas en agentes (experimentales)
    register_agent_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True) 