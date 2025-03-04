#!/usr/bin/env python
"""
Script para verificar el contenido de la base de datos SQLite.
"""
import sqlite3
import os
import json

# Ruta a la base de datos
db_path = 'data/leads_alisys_bot.db'

print(f"Verificando base de datos en: {os.path.abspath(db_path)}")
print("-" * 50)

# Verificar si el archivo existe
if not os.path.exists(db_path):
    print(f"ERROR: El archivo de base de datos no existe en {db_path}")
    exit(1)

try:
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener información sobre las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Tablas encontradas: {[table[0] for table in tables]}")
    print("-" * 50)
    
    # Verificar si existe la tabla leads
    if ('leads',) not in tables:
        print("ERROR: La tabla 'leads' no existe en la base de datos")
        exit(1)
    
    # Obtener estructura de la tabla leads
    cursor.execute("PRAGMA table_info(leads);")
    columns = cursor.fetchall()
    
    print("Estructura de la tabla 'leads':")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    print("-" * 50)
    
    # Ejecutar consulta para obtener todos los leads
    cursor.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    
    print(f"Total de leads encontrados: {len(rows)}")
    print("-" * 50)
    
    # Mostrar resultados
    if rows:
        for i, row in enumerate(rows):
            print(f"Lead #{i+1}:")
            for j, col in enumerate(columns):
                print(f"  {col[1]}: {row[j]}")
            print("-" * 30)
    else:
        print("No se encontraron leads en la base de datos.")
    
    # Cerrar conexión
    conn.close()
    
    # También verificar el archivo JSON
    json_path = 'data/leads.json'
    print(f"\nVerificando archivo JSON en: {os.path.abspath(json_path)}")
    print("-" * 50)
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                leads_json = json.load(f)
                print(f"Total de leads en JSON: {len(leads_json)}")
                for i, lead in enumerate(leads_json):
                    print(f"Lead JSON #{i+1}:")
                    for key, value in lead.items():
                        print(f"  {key}: {value}")
                    print("-" * 30)
            except json.JSONDecodeError:
                print("ERROR: El archivo JSON no tiene un formato válido")
    else:
        print(f"ERROR: El archivo JSON no existe en {json_path}")
    
except sqlite3.Error as e:
    print(f"ERROR de SQLite: {e}")
except Exception as e:
    print(f"ERROR general: {e}") 