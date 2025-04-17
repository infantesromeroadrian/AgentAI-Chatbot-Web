"""
Módulo para persistencia de contexto en conversaciones.
Permite guardar y cargar el estado de las conversaciones para mantener
continuidad en sesiones largas o interrumpidas.
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class ContextPersistenceManager:
    """
    Gestor de persistencia para contextos de conversación.
    Permite guardar y recuperar contextos completos de conversación.
    """
    
    def __init__(self, storage_dir: str = "storage/contexts"):
        """
        Inicializa el gestor de persistencia.
        
        Args:
            storage_dir: Directorio para almacenar los archivos de contexto
        """
        self.storage_dir = storage_dir
        self._ensure_storage_dir_exists()
    
    def _ensure_storage_dir_exists(self) -> None:
        """
        Asegura que el directorio de almacenamiento exista.
        """
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
            logger.info(f"Creado directorio de almacenamiento: {self.storage_dir}")
    
    def save_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """
        Guarda el contexto de conversación para un usuario específico.
        
        Args:
            user_id: Identificador único del usuario
            context: Contexto de la conversación a guardar
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear una copia para no modificar el original
            context_to_save = context.copy()
            
            # Añadir metadatos de la persistencia
            context_to_save["_persistence_metadata"] = {
                "last_saved": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Generar nombre de archivo basado en el ID de usuario
            filename = f"{user_id}_{int(time.time())}.json"
            file_path = os.path.join(self.storage_dir, filename)
            
            # Guardar como JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(context_to_save, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Contexto guardado para usuario {user_id} en {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar contexto para usuario {user_id}: {str(e)}")
            return False
    
    def load_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga el contexto más reciente para un usuario específico.
        
        Args:
            user_id: Identificador único del usuario
            
        Returns:
            Contexto cargado o None si no se encuentra
        """
        try:
            # Buscar todos los archivos de contexto para este usuario
            user_files = []
            for filename in os.listdir(self.storage_dir):
                if filename.startswith(f"{user_id}_") and filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    user_files.append((file_path, os.path.getmtime(file_path)))
            
            # Si no hay archivos, retornar None
            if not user_files:
                logger.info(f"No se encontraron contextos guardados para usuario {user_id}")
                return None
            
            # Ordenar por fecha de modificación (más reciente primero)
            user_files.sort(key=lambda x: x[1], reverse=True)
            latest_file = user_files[0][0]
            
            # Cargar el archivo JSON
            with open(latest_file, 'r', encoding='utf-8') as f:
                context = json.load(f)
            
            logger.info(f"Contexto cargado para usuario {user_id} desde {latest_file}")
            return context
            
        except Exception as e:
            logger.error(f"Error al cargar contexto para usuario {user_id}: {str(e)}")
            return None
    
    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lista todas las sesiones guardadas para un usuario.
        
        Args:
            user_id: Identificador único del usuario
            
        Returns:
            Lista de metadatos de sesiones disponibles
        """
        sessions = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.startswith(f"{user_id}_") and filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    
                    # Extraer timestamp del nombre de archivo
                    timestamp = int(filename.split('_')[1].split('.')[0])
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                        
                    # Extraer información relevante
                    metadata = context.get("_persistence_metadata", {})
                    message_count = context.get("message_count", 0)
                    
                    sessions.append({
                        "session_id": filename,
                        "timestamp": timestamp,
                        "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                        "message_count": message_count,
                        "last_saved": metadata.get("last_saved", "Unknown"),
                        "file_path": file_path
                    })
            
            # Ordenar por fecha (más reciente primero)
            sessions.sort(key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error al listar sesiones para usuario {user_id}: {str(e)}")
        
        return sessions
    
    def delete_context(self, session_id: str) -> bool:
        """
        Elimina un archivo de contexto específico.
        
        Args:
            session_id: ID de la sesión a eliminar (nombre del archivo)
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            file_path = os.path.join(self.storage_dir, session_id)
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                logger.warning(f"Archivo de contexto no encontrado: {file_path}")
                return False
            
            # Eliminar archivo
            os.remove(file_path)
            logger.info(f"Contexto eliminado: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar contexto {session_id}: {str(e)}")
            return False 