"""
Módulo para gestionar la base de datos SQLite.
"""
import os
import sys
import traceback
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Imprimir información de depuración
print("Inicializando módulo de base de datos...")
print(f"Directorio actual: {os.getcwd()}")

# Crear la ruta para la base de datos
# Intentar diferentes rutas para manejar tanto desarrollo como producción
possible_paths = [
    # Ruta relativa desde el directorio actual
    os.path.join('data', 'leads_alisys_bot.db'),
    # Ruta absoluta basada en la ubicación del script
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'leads_alisys_bot.db'),
    # Ruta absoluta para Docker
    '/app/data/leads_alisys_bot.db'
]

# Probar cada ruta y usar la primera que funcione
DB_PATH = None
for path in possible_paths:
    dir_path = os.path.dirname(path)
    if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
        DB_PATH = path
        print(f"Usando ruta de base de datos: {DB_PATH}")
        break

if DB_PATH is None:
    # Si ninguna ruta funciona, usar una ruta por defecto
    DB_PATH = os.path.join('data', 'leads_alisys_bot.db')
    print(f"ADVERTENCIA: No se encontró una ruta válida. Usando ruta por defecto: {DB_PATH}")

DB_DIR = os.path.dirname(DB_PATH)

# Asegurarse de que el directorio data existe
try:
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"Directorio creado: {DB_DIR}")
except Exception as e:
    print(f"Error al crear directorio {DB_DIR}: {str(e)}")
    traceback.print_exc()

# Crear el motor de la base de datos
try:
    print(f"Creando motor de base de datos para: sqlite:///{DB_PATH}")
    engine = create_engine(f'sqlite:///{DB_PATH}', echo=True)
    Base = declarative_base()
except Exception as e:
    print(f"Error al crear motor de base de datos: {str(e)}")
    traceback.print_exc()
    # Crear un motor en memoria como fallback
    print("Usando base de datos en memoria como fallback")
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base = declarative_base()

# Definir el modelo de datos para los leads
class Lead(Base):
    """Modelo para almacenar los leads capturados por el chatbot."""
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    company = Column(String(100))
    interest = Column(String(100))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Lead(name='{self.name}', email='{self.email}')>"

# Crear las tablas en la base de datos
try:
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente")
except Exception as e:
    print(f"Error al crear tablas: {str(e)}")
    traceback.print_exc()

# Crear una sesión para interactuar con la base de datos
Session = sessionmaker(bind=engine)

def save_lead(data):
    """Guarda un lead en la base de datos.
    
    Args:
        data (dict): Diccionario con los datos del lead.
        
    Returns:
        Lead: El objeto Lead creado.
    """
    print(f"Función save_lead llamada con datos: {data}")
    session = Session()
    try:
        # Validar datos mínimos
        if not data.get('name') or not data.get('email'):
            raise ValueError("El nombre y el email son obligatorios")
        
        lead = Lead(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            interest=data.get('interest', ''),
            message=data.get('message', '')
        )
        print(f"Objeto Lead creado: {lead}")
        session.add(lead)
        session.commit()
        print(f"Lead guardado con ID: {lead.id}")
        return lead
    except Exception as e:
        session.rollback()
        print(f"Error al guardar lead: {str(e)}")
        traceback.print_exc()
        raise e
    finally:
        session.close()

def get_leads():
    """Obtiene todos los leads de la base de datos.
    
    Returns:
        list: Lista de objetos Lead.
    """
    print("Función get_leads llamada")
    session = Session()
    try:
        leads = session.query(Lead).all()
        print(f"Leads obtenidos: {len(leads)}")
        return leads
    except Exception as e:
        print(f"Error al obtener leads: {str(e)}")
        traceback.print_exc()
        return []
    finally:
        session.close()

def get_lead_by_id(lead_id):
    """Obtiene un lead por su ID.
    
    Args:
        lead_id (int): ID del lead.
        
    Returns:
        Lead: El objeto Lead encontrado o None.
    """
    print(f"Función get_lead_by_id llamada con ID: {lead_id}")
    session = Session()
    try:
        lead = session.query(Lead).filter(Lead.id == lead_id).first()
        print(f"Lead obtenido: {lead}")
        return lead
    except Exception as e:
        print(f"Error al obtener lead por ID: {str(e)}")
        traceback.print_exc()
        return None
    finally:
        session.close() 