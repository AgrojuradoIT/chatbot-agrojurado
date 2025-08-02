#!/usr/bin/env python3
"""
Script para actualizar la base de datos MySQL con las tablas necesarias.
Verifica qué tablas existen y crea/actualiza según sea necesario.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "agrojura")
DB_PORT = os.getenv("DB_PORT", "3306")

# URL de conexión
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_database_if_not_exists():
    """Crea la base de datos si no existe"""
    try:
        # Conectar sin especificar base de datos
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")
        
        with engine.connect() as conn:
            # Crear base de datos si no existe
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"✅ Base de datos '{DB_NAME}' verificada/creada exitosamente")
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear la base de datos: {e}")
        sys.exit(1)

def check_table_exists(engine, table_name):
    """Verifica si una tabla existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def get_table_columns(engine, table_name):
    """Obtiene las columnas de una tabla existente"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return {col['name']: col['type'] for col in columns}

def create_whatsapp_users_table(engine):
    """Crea o actualiza la tabla whatsapp_users"""
    table_name = "whatsapp_users"
    
    if not check_table_exists(engine, table_name):
        # Crear tabla nueva
        create_table_sql = """
        CREATE TABLE whatsapp_users (
            phone_number VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            inactivity_warning_sent BOOLEAN DEFAULT FALSE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print(f"✅ Tabla '{table_name}' creada exitosamente")
    else:
        # Verificar columnas existentes
        existing_columns = get_table_columns(engine, table_name)
        required_columns = {
            'phone_number': 'VARCHAR(50)',
            'name': 'VARCHAR(100)',
            'last_interaction': 'TIMESTAMP',
            'is_active': 'BOOLEAN',
            'inactivity_warning_sent': 'BOOLEAN'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"🔄 Actualizando tabla '{table_name}' con columnas faltantes...")
            with engine.connect() as conn:
                for col_name, col_type in missing_columns:
                    if col_name == 'inactivity_warning_sent':
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} BOOLEAN DEFAULT FALSE;"
                    elif col_name == 'is_active':
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} BOOLEAN DEFAULT TRUE;"
                    else:
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
                    
                    conn.execute(text(add_column_sql))
                conn.commit()
            print(f"✅ Tabla '{table_name}' actualizada exitosamente")
        else:
            print(f"✅ Tabla '{table_name}' ya existe y está actualizada")

def create_messages_table(engine):
    """Crea o actualiza la tabla messages"""
    table_name = "messages"
    
    if not check_table_exists(engine, table_name):
        # Crear tabla nueva
        create_table_sql = """
        CREATE TABLE messages (
            id VARCHAR(100) PRIMARY KEY,
            phone_number VARCHAR(50),
            sender VARCHAR(10),
            content VARCHAR(1000),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'sent',
            INDEX idx_phone_number (phone_number),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print(f"✅ Tabla '{table_name}' creada exitosamente")
    else:
        # Verificar columnas existentes
        existing_columns = get_table_columns(engine, table_name)
        required_columns = {
            'id': 'VARCHAR(100)',
            'phone_number': 'VARCHAR(50)',
            'sender': 'VARCHAR(10)',
            'content': 'VARCHAR(1000)',
            'timestamp': 'TIMESTAMP',
            'status': 'VARCHAR(20)'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"🔄 Actualizando tabla '{table_name}' con columnas faltantes...")
            with engine.connect() as conn:
                for col_name, col_type in missing_columns:
                    if col_name == 'status':
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} VARCHAR(20) DEFAULT 'sent';"
                    else:
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
                    
                    conn.execute(text(add_column_sql))
                conn.commit()
            print(f"✅ Tabla '{table_name}' actualizada exitosamente")
        else:
            print(f"✅ Tabla '{table_name}' ya existe y está actualizada")

def create_templates_table(engine):
    """Crea o actualiza la tabla templates"""
    table_name = "templates"
    
    if not check_table_exists(engine, table_name):
        # Crear tabla nueva
        create_table_sql = """
        CREATE TABLE templates (
            id VARCHAR(100) PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            content VARCHAR(1000) NOT NULL,
            category VARCHAR(50),
            status VARCHAR(50),
            rejected_reason VARCHAR(1000),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            footer VARCHAR(500),
            is_archived BOOLEAN DEFAULT FALSE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print(f"✅ Tabla '{table_name}' creada exitosamente")
    else:
        # Verificar columnas existentes
        existing_columns = get_table_columns(engine, table_name)
        required_columns = {
            'id': 'VARCHAR(100)',
            'name': 'VARCHAR(255)',
            'content': 'VARCHAR(1000)',
            'category': 'VARCHAR(50)',
            'status': 'VARCHAR(50)',
            'rejected_reason': 'VARCHAR(1000)',
            'created_at': 'TIMESTAMP',
            'footer': 'VARCHAR(500)',
            'is_archived': 'BOOLEAN'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"🔄 Actualizando tabla '{table_name}' con columnas faltantes...")
            with engine.connect() as conn:
                for col_name, col_type in missing_columns:
                    if col_name == 'is_archived':
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} BOOLEAN DEFAULT FALSE;"
                    else:
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
                    
                    conn.execute(text(add_column_sql))
                conn.commit()
            print(f"✅ Tabla '{table_name}' actualizada exitosamente")
        else:
            print(f"✅ Tabla '{table_name}' ya existe y está actualizada")

def main():
    """Función principal del script"""
    print("🔄 Iniciando actualización de la base de datos...")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"🌐 Host: {DB_HOST}:{DB_PORT}")
    print(f"👤 Usuario: {DB_USER}")
    print("-" * 50)
    
    try:
        # Crear base de datos si no existe
        create_database_if_not_exists()
        
        # Conectar a la base de datos específica
        engine = create_engine(DATABASE_URL)
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos establecida")
        
        # Crear/actualizar tablas
        create_whatsapp_users_table(engine)
        create_messages_table(engine)
        create_templates_table(engine)
        
        print("-" * 50)
        print("🎉 ¡Actualización de la base de datos completada exitosamente!")
        print("📋 Resumen:")
        print("   ✅ Base de datos verificada/creada")
        print("   ✅ Tabla 'whatsapp_users' verificada/creada")
        print("   ✅ Tabla 'messages' verificada/creada")
        print("   ✅ Tabla 'templates' verificada/creada")
        
    except SQLAlchemyError as e:
        print(f"❌ Error durante la actualización: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 