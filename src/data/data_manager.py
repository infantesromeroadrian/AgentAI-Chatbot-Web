"""
Gestiona el almacenamiento y recuperación de datos para el chatbot.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# Importar el módulo de base de datos
from src.data.database import save_lead as db_save_lead, get_leads as db_get_leads

class DataManager:
    """Clase para gestionar datos del chatbot"""
    
    def __init__(self, data_dir="data", filename="leads.json"):
        """Inicializa el gestor de datos"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = os.path.join(data_dir, filename)
        self.leads = self._load_leads()
    
    def _load_leads(self) -> List[Dict]:
        """Carga los leads existentes del archivo JSON."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_lead(self, lead_data: Dict) -> bool:
        """
        Guarda un nuevo lead en el archivo JSON y en la base de datos SQLite.
        
        Args:
            lead_data (Dict): Datos del lead a guardar.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        try:
            # Añadir timestamp
            lead_data['timestamp'] = datetime.now().isoformat()
            
            # Guardar en el archivo JSON (mantener compatibilidad)
            self.leads.append(lead_data)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.leads, f, ensure_ascii=False, indent=2)
            
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
                db_save_lead(db_lead_data)
            except Exception as db_error:
                print(f"Error al guardar el lead en la base de datos: {str(db_error)}")
                # Continuar aunque falle la base de datos, ya que se guardó en JSON
            
            return True
        except Exception as e:
            print(f"Error al guardar el lead: {str(e)}")
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