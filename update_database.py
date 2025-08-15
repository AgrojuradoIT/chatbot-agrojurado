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

# Verificar variables de entorno requeridas
required_env_vars = ["DB_HOST", "DB_USER", "DB_NAME"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Error: Variables de entorno faltantes: {', '.join(missing_vars)}")
    print("Por favor, configura estas variables en tu archivo .env:")
    print("   DB_HOST=localhost")
    print("   DB_USER=root")
    print("   DB_NAME=agrojura")
    print("   DB_PASSWORD= (puede estar vacío para desarrollo local)")
    print("   DB_PORT=3306 (opcional, por defecto 3306)")
    sys.exit(1)

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # Puerto por defecto es útil mantener

# URL de conexión (maneja contraseña vacía para desarrollo local)
if DB_PASSWORD:
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_dependencies():
    """Verifica que las dependencias necesarias estén instaladas"""
    try:
        import mysql.connector
        print("✅ mysql-connector-python está instalado")
    except ImportError:
        print("❌ Error: mysql-connector-python no está instalado")
        print("Instala con: pip install mysql-connector-python")
        sys.exit(1)

def create_database_if_not_exists():
    """Crea la base de datos si no existe"""
    try:
        # Conectar sin especificar base de datos (maneja contraseña vacía)
        if DB_PASSWORD:
            engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")
        else:
            engine = create_engine(f"mysql+mysqlconnector://{DB_USER}@{DB_HOST}:{DB_PORT}")
    
        with engine.connect() as conn:
            # Crear base de datos si no existe
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"✅ Base de datos '{DB_NAME}' verificada/creada exitosamente")
            
    except SQLAlchemyError as e:
        print(f"❌ Error al crear la base de datos: {e}")
        print("💡 Sugerencias:")
        print("   - Verifica que MySQL esté ejecutándose")
        print("   - Verifica que el usuario tenga permisos")
        print("   - Para desarrollo local, puedes usar contraseña vacía")
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

def create_indexes(engine, table_name):
    """Crea índices adicionales para mejorar el rendimiento"""
    try:
        with engine.connect() as conn:
            if table_name == "messages":
                # Índices para búsquedas por sender y status
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_sender ON {table_name} (sender);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_status ON {table_name} (status);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_phone_sender ON {table_name} (phone_number, sender);"))
            elif table_name == "templates":
                # Índices para búsquedas por categoría y estado
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_category ON {table_name} (category);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_status ON {table_name} (status);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_archived ON {table_name} (is_archived);"))
                # Nuevos índices para plantillas con medios
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_media_type ON {table_name} (media_type);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_has_media ON {table_name} (media_id, image_url);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_template_type ON {table_name} (media_type, is_archived);"))
            elif table_name == "whatsapp_users":
                # Índices para búsquedas por estado activo
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_active ON {table_name} (is_active);"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_last_interaction ON {table_name} (last_interaction);"))
            
            conn.commit()
            print(f"✅ Índices adicionales creados para '{table_name}'")
    except SQLAlchemyError as e:
        print(f"⚠️ Advertencia: No se pudieron crear algunos índices para '{table_name}': {e}")

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
        
        # Crear índices adicionales
        create_indexes(engine, table_name)
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
        
        # Crear índices adicionales
        create_indexes(engine, table_name)

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
        
        # Crear índices adicionales
        create_indexes(engine, table_name)
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
        
        # Crear índices adicionales
        create_indexes(engine, table_name)

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
            is_archived BOOLEAN DEFAULT FALSE,
            header_text VARCHAR(500),
            media_type VARCHAR(20),
            media_id VARCHAR(100),
            image_url VARCHAR(500)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print(f"✅ Tabla '{table_name}' creada exitosamente")
        
        # Crear índices adicionales
        create_indexes(engine, table_name)
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
            'is_archived': 'BOOLEAN',
            # Nuevas columnas para plantillas con medios
            'header_text': 'VARCHAR(500)',
            'media_type': 'VARCHAR(20)',
            'media_id': 'VARCHAR(100)',
            'image_url': 'VARCHAR(500)'
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
                    elif col_name in ['header_text', 'media_type', 'media_id', 'image_url']:
                        # Nuevas columnas para medios
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} NULL;"
                    else:
                        add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
                    
                    conn.execute(text(add_column_sql))
                conn.commit()
            print(f"✅ Tabla '{table_name}' actualizada exitosamente")
            
            # Mostrar información sobre las nuevas columnas agregadas
            new_media_columns = [col for col in missing_columns if col[0] in ['header_text', 'media_type', 'media_id', 'image_url']]
            if new_media_columns:
                print("📸 Nuevas columnas para plantillas con medios:")
                for col_name, col_type in new_media_columns:
                    print(f"   - {col_name}: {col_type}")
        else:
            print(f"✅ Tabla '{table_name}' ya existe y está actualizada")
        
        # Crear índices adicionales
        create_indexes(engine, table_name)

def main():
    """Función principal del script"""
    print("🔄 Iniciando actualización de la base de datos...")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"🌐 Host: {DB_HOST}:{DB_PORT}")
    print(f"👤 Usuario: {DB_USER}")
    print(f"🔐 Contraseña: {'Configurada' if DB_PASSWORD else 'Vacía (desarrollo local)'}")
    print("-" * 50)
    
    try:
        # Verificar dependencias
        check_dependencies()
        
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
        print("   ✅ Dependencias verificadas")
        print("   ✅ Base de datos verificada/creada")
        print("   ✅ Tabla 'whatsapp_users' verificada/creada")
        print("   ✅ Tabla 'messages' verificada/creada")
        print("   ✅ Tabla 'templates' verificada/creada")
        print("   ✅ Índices adicionales creados")
        print("📸 Nuevas funcionalidades para plantillas con medios:")
        print("   - header_text: Texto del encabezado de la plantilla")
        print("   - media_type: Tipo de medio (IMAGE, VIDEO, DOCUMENT)")
        print("   - media_id: ID del medio subido a WhatsApp")
        print("   - image_url: URL de imagen para plantillas con URL")
        
    except SQLAlchemyError as e:
        print(f"❌ Error durante la actualización: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 