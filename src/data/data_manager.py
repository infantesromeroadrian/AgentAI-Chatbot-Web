"""
Gestiona el almacenamiento y recuperación de datos para el chatbot.
"""
import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

# Importar el módulo de base de datos
# Corregir la importación para que funcione tanto en desarrollo como en producción
try:
    # Intentar importación relativa (para desarrollo)
    from data.database import save_lead as db_save_lead, get_leads as db_get_leads
except ImportError:
    try:
        # Intentar importación absoluta (para producción en Docker)
        from src.data.database import save_lead as db_save_lead, get_leads as db_get_leads
    except ImportError:
        # Si ambas fallan, imprimir error detallado
        print("ERROR DE IMPORTACIÓN: No se pudo importar el módulo de base de datos")
        traceback.print_exc()
        # Definir funciones dummy para evitar errores
        def db_save_lead(data): 
            print(f"ADVERTENCIA: Usando función dummy para db_save_lead. Datos: {data}")
            return None
        def db_get_leads(): 
            print("ADVERTENCIA: Usando función dummy para db_get_leads")
            return []

# Interfaz para el repositorio de datos
class DataRepository(ABC):
    """Interfaz para repositorios de datos"""
    
    @abstractmethod
    def save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Guarda un lead en el repositorio"""
        pass
    
    @abstractmethod
    def get_leads(self) -> List[Dict[str, Any]]:
        """Obtiene todos los leads del repositorio"""
        pass
    
    @abstractmethod
    def save_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> str:
        """Guarda una conversación en el repositorio"""
        pass
    
    @abstractmethod
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Carga una conversación del repositorio"""
        pass

# Implementación de repositorio con almacenamiento en archivo JSON
class JsonFileRepository(DataRepository):
    """Repositorio que almacena datos en archivos JSON"""
    
    def __init__(self, data_dir: str = "data", leads_filename: str = "leads.json"):
        """Inicializa el repositorio JSON"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.leads_filepath = os.path.join(data_dir, leads_filename)
        self.leads = self._load_leads()
        print(f"JsonFileRepository inicializado. Ruta de archivo: {self.leads_filepath}")
        print(f"Leads cargados: {len(self.leads)}")
    
    def _load_leads(self) -> List[Dict[str, Any]]:
        """Carga los leads existentes del archivo JSON."""
        try:
            with open(self.leads_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Archivo no encontrado: {self.leads_filepath}. Creando lista vacía.")
            return []
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON en {self.leads_filepath}. Creando lista vacía.")
            return []
    
    def save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Guarda un lead en el archivo JSON"""
        try:
            # Añadir timestamp
            lead_data['timestamp'] = datetime.now().isoformat()
            
            # Guardar en el archivo JSON
            self.leads.append(lead_data)
            with open(self.leads_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.leads, f, ensure_ascii=False, indent=2)
            print(f"Lead guardado en JSON. Total de leads: {len(self.leads)}")
            return True
        except Exception as e:
            print(f"Error al guardar el lead en JSON: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_leads(self) -> List[Dict[str, Any]]:
        """Retorna todos los leads guardados en JSON."""
        return self.leads
    
    def save_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> str:
        """Guarda una conversación en un archivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversation_id = f"{user_id}_{timestamp}"
        filename = os.path.join(self.data_dir, f"conversation_{conversation_id}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "user_id": user_id,
                    "timestamp": timestamp,
                    "messages": messages
                }, f, ensure_ascii=False, indent=2)
            return conversation_id
        except Exception as e:
            print(f"Error al guardar conversación: {str(e)}")
            traceback.print_exc()
            return ""
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Carga una conversación desde un archivo JSON"""
        filename = os.path.join(self.data_dir, f"conversation_{conversation_id}.json")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Conversación no encontrada: {filename}")
            return None
        except json.JSONDecodeError:
            print(f"Error al decodificar conversación: {filename}")
            return None

# Implementación de repositorio con almacenamiento en base de datos SQLite
class SqliteRepository(DataRepository):
    """Repositorio que almacena datos en base de datos SQLite"""
    
    def save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Guarda un lead en la base de datos SQLite"""
        try:
            # Mapear los campos del formulario a los campos de la base de datos
            db_lead_data = {
                'name': lead_data.get('name', ''),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'company': lead_data.get('company', ''),
                'interest': lead_data.get('interest', ''),
                'message': lead_data.get('message', '')
            }
            print(f"Guardando lead en SQLite: {db_lead_data}")
            result = db_save_lead(db_lead_data)
            return result is not None
        except Exception as e:
            print(f"Error al guardar el lead en SQLite: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_leads(self) -> List[Dict[str, Any]]:
        """Obtiene todos los leads de la base de datos SQLite"""
        try:
            db_leads = db_get_leads()
            # Convertir los objetos SQLAlchemy a diccionarios
            leads = []
            for lead in db_leads:
                leads.append({
                    'id': lead.id,
                    'name': lead.name,
                    'email': lead.email,
                    'phone': lead.phone,
                    'company': lead.company,
                    'interest': lead.interest,
                    'message': lead.message,
                    'created_at': lead.created_at.isoformat() if lead.created_at else None
                })
            return leads
        except Exception as e:
            print(f"Error al obtener leads de SQLite: {str(e)}")
            traceback.print_exc()
            return []
    
    def save_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        SQLite no está configurado para almacenar conversaciones, 
        así que esta implementación no hace nada.
        """
        print("SQLite no implementa guardado de conversaciones")
        return ""
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        SQLite no está configurado para almacenar conversaciones,
        así que esta implementación no hace nada.
        """
        print("SQLite no implementa carga de conversaciones")
        return None

# Gestor de datos principal que combina múltiples repositorios
class DataManager:
    """Clase para gestionar datos del chatbot usando múltiples repositorios"""
    
    def __init__(self, data_dir: str = "data", filename: str = "leads.json"):
        """Inicializa el gestor de datos con repositorios configurados"""
        # Inicializar repositorios
        self.json_repository = JsonFileRepository(data_dir, filename)
        self.db_repository = SqliteRepository()
        print("DataManager inicializado con múltiples repositorios")
    
    def save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """
        Guarda un lead en todos los repositorios disponibles.
        
        Args:
            lead_data (Dict): Datos del lead a guardar.
            
        Returns:
            bool: True si se guardó correctamente en al menos un repositorio.
        """
        print(f"Intentando guardar lead: {lead_data}")
        
        # Guardar en JSON
        json_success = self.json_repository.save_lead(lead_data)
        
        # Guardar en SQLite
        db_success = self.db_repository.save_lead(lead_data)
        
        # Devolver éxito si al menos un repositorio funcionó
        return json_success or db_success
    
    def get_leads(self) -> List[Dict[str, Any]]:
        """
        Retorna los leads guardados, prefiriendo los de la base de datos.
        
        Returns:
            List[Dict]: Lista de leads.
        """
        # Intentar obtener desde SQLite primero
        db_leads = self.db_repository.get_leads()
        if db_leads:
            return db_leads
        
        # Si no hay leads en la base de datos, usar JSON
        return self.json_repository.get_leads()
    
    def save_conversation(self, user_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        Guarda una conversación utilizando el repositorio JSON.
        
        Args:
            user_id: Identificador del usuario
            messages: Lista de mensajes de la conversación
            
        Returns:
            str: Identificador de la conversación guardada
        """
        return self.json_repository.save_conversation(user_id, messages)
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga una conversación utilizando el repositorio JSON.
        
        Args:
            conversation_id: Identificador de la conversación
            
        Returns:
            Optional[Dict]: Datos de la conversación o None si no se encuentra
        """
        return self.json_repository.load_conversation(conversation_id) 