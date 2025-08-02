import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def update_mysql_database():
    """Actualizar la base de datos MySQL para agregar el campo status a la tabla messages"""
    
    # Obtener configuración de la base de datos
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Contraseña vacía por defecto
    DB_NAME = os.getenv("DB_NAME", "agrojura_web")
    
    print(f"🔍 Configuración detectada:")
    print(f"  DB_HOST: {DB_HOST}")
    print(f"  DB_USER: {DB_USER}")
    print(f"  DB_NAME: {DB_NAME}")
    print(f"  DB_PASSWORD: {'***' if DB_PASSWORD else 'Vacía'}")
    
    try:
        print(f"\n🔄 Conectando a MySQL en {DB_HOST}...")
        
        # Conectar a MySQL
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("✅ Conexión exitosa a MySQL")
        
        cursor = connection.cursor()
        
        # Verificar si la tabla messages existe
        cursor.execute("SHOW TABLES LIKE 'messages'")
        if not cursor.fetchone():
            print("❌ La tabla 'messages' no existe")
            return
        
        # Verificar si la columna status ya existe
        cursor.execute("DESCRIBE messages")
        columns = [column[0] for column in cursor.fetchall()]
        
        print(f"📋 Columnas actuales: {columns}")
        
        if 'status' not in columns:
            print("🔄 Agregando columna 'status' a la tabla messages...")
            
            # Agregar la columna status
            cursor.execute("ALTER TABLE messages ADD COLUMN status VARCHAR(20) DEFAULT 'sent'")
            
            # Actualizar mensajes existentes
            cursor.execute("UPDATE messages SET status = 'delivered' WHERE sender = 'user'")
            cursor.execute("UPDATE messages SET status = 'sent' WHERE sender = 'bot'")
            
            connection.commit()
            print("✅ Columna 'status' agregada exitosamente")
        else:
            print("✅ La columna 'status' ya existe")
        
        # Mostrar estructura actualizada
        cursor.execute("DESCRIBE messages")
        columns = cursor.fetchall()
        print("\n📋 Estructura actual de la tabla messages:")
        for column in columns:
            print(f"  - {column[0]} ({column[1]})")
        
        # Mostrar algunos mensajes de ejemplo
        cursor.execute("SELECT id, sender, content, status FROM messages LIMIT 5")
        messages = cursor.fetchall()
        print(f"\n📝 Ejemplos de mensajes ({len(messages)} encontrados):")
        for msg in messages:
            print(f"  - ID: {msg[0]}, Sender: {msg[1]}, Status: {msg[3]}")
        
        cursor.close()
        connection.close()
        print("\n🎉 Base de datos MySQL actualizada correctamente")
        
    except mysql.connector.Error as e:
        print(f"❌ Error de MySQL: {e}")
        print("\n💡 Si el error es de autenticación, puedes:")
        print("1. Configurar la contraseña en un archivo .env")
        print("2. O ejecutar manualmente en MySQL:")
        print("   ALTER TABLE messages ADD COLUMN status VARCHAR(20) DEFAULT 'sent';")
        print("   UPDATE messages SET status = 'delivered' WHERE sender = 'user';")
        print("   UPDATE messages SET status = 'sent' WHERE sender = 'bot';")
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    update_mysql_database() 