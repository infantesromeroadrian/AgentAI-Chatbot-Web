"""
Módulo para gestionar la base de datos SQLite.
"""
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Crear la ruta para la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'leads_alisys_bot.db')
DB_DIR = os.path.dirname(DB_PATH)

# Asegurarse de que el directorio data existe
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Crear el motor de la base de datos
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
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
Base.metadata.create_all(engine)

# Crear una sesión para interactuar con la base de datos
Session = sessionmaker(bind=engine)

def save_lead(data):
    """Guarda un lead en la base de datos.
    
    Args:
        data (dict): Diccionario con los datos del lead.
        
    Returns:
        Lead: El objeto Lead creado.
    """
    session = Session()
    try:
        lead = Lead(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            company=data.get('company', ''),
            interest=data.get('interest', ''),
            message=data.get('message', '')
        )
        session.add(lead)
        session.commit()
        return lead
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_leads():
    """Obtiene todos los leads de la base de datos.
    
    Returns:
        list: Lista de objetos Lead.
    """
    session = Session()
    try:
        leads = session.query(Lead).all()
        return leads
    finally:
        session.close()

def get_lead_by_id(lead_id):
    """Obtiene un lead por su ID.
    
    Args:
        lead_id (int): ID del lead.
        
    Returns:
        Lead: El objeto Lead encontrado o None.
    """
    session = Session()
    try:
        lead = session.query(Lead).filter(Lead.id == lead_id).first()
        return lead
    finally:
        session.close() 