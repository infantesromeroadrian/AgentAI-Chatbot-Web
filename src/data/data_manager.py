"""
Gestiona el almacenamiento y recuperación de datos para el chatbot.
"""
import os
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional

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

class DataManager:
    """Clase para gestionar datos del chatbot"""
    
    def __init__(self, data_dir="data", filename="leads.json"):
        """Inicializa el gestor de datos"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = os.path.join(data_dir, filename)
        self.leads = self._load_leads()
        print(f"DataManager inicializado. Ruta de archivo: {self.filepath}")
        print(f"Leads cargados: {len(self.leads)}")
    
    def _load_leads(self) -> List[Dict]:
        """Carga los leads existentes del archivo JSON."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Archivo no encontrado: {self.filepath}. Creando lista vacía.")
            return []
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON en {self.filepath}. Creando lista vacía.")
            return []
    
    def save_lead(self, lead_data: Dict) -> bool:
        """
        Guarda un nuevo lead en el archivo JSON y en la base de datos SQLite.
        
        Args:
            lead_data (Dict): Datos del lead a guardar.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        print(f"Intentando guardar lead: {lead_data}")
        
        try:
            # Añadir timestamp
            lead_data['timestamp'] = datetime.now().isoformat()
            
            # Guardar en el archivo JSON (mantener compatibilidad)
            self.leads.append(lead_data)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.leads, f, ensure_ascii=False, indent=2)
            print(f"Lead guardado en JSON. Total de leads: {len(self.leads)}")
            
            # Guardar en la base de datos SQLite
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
                print(f"Intentando guardar en SQLite: {db_lead_data}")
                result = db_save_lead(db_lead_data)
                print(f"Resultado de guardar en SQLite: {result}")
            except Exception as db_error:
                print(f"Error al guardar el lead en la base de datos: {str(db_error)}")
                traceback.print_exc()
                # Continuar aunque falle la base de datos, ya que se guardó en JSON
            
            return True
        except Exception as e:
            print(f"Error al guardar el lead: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_leads(self) -> List[Dict]:
        """Retorna todos los leads guardados."""
        return self.leads
    
    def save_conversation(self, user_id, messages):
        """Guarda una conversación en el sistema de archivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_dir}/conversation_{user_id}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "user_id": user_id,
                "timestamp": timestamp,
                "messages": messages
            }, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def load_conversation(self, filename):
        """Carga una conversación desde el sistema de archivos"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None 