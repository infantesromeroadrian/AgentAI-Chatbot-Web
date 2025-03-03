"""
Punto de entrada principal para la aplicación del chatbot web.
"""
import os
from flask import Flask
from dotenv import load_dotenv

# Importar rutas de la API
from api.routes import register_routes

# Cargar variables de entorno
load_dotenv()

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)
    
    # Registrar rutas
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True) 