# 🚀 Guía Rápida - Chatbot WhatsApp Agropecuaria Juradó

## ⚡ Inicio Rápido en 5 Minutos

### 1. 📋 Prerrequisitos
- Python 3.8+ instalado
- Node.js 16+ instalado
- MySQL 8.0+ instalado
- Cuenta de WhatsApp Business API

### 2. 🛠️ Instalación Express

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd chatbot-agrojurado

# 2. Configurar backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar base de datos
mysql -u root -p
CREATE DATABASE agrojura_web;
exit

# 4. Configurar variables de entorno
cp env.example .env
# Editar .env con tus credenciales

# 5. Inicializar base de datos
python init_db.py

# 6. Configurar frontend
cd frontend
npm install
```

### 3. 🚀 Iniciar el Sistema

```bash
# Terminal 1: Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 4. 🌐 Acceder al Sistema
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Backend**: http://localhost:8000

## 📱 Configuración del Webhook

### 1. Configurar ngrok (para pruebas)
```bash
# Instalar ngrok
# Descargar desde: https://ngrok.com/download

# Autenticar
ngrok authtoken TU_TOKEN

# Iniciar túnel
ngrok http 8000
```

### 2. Configurar Webhook en Meta
1. Ve a: https://developers.facebook.com/apps/
2. Selecciona tu aplicación de WhatsApp
3. WhatsApp > Configuración > Webhooks
4. Configura:
   - **URL**: `https://TU_URL_NGROK/webhook`
   - **Token**: `Agrojurado2026`
5. Suscríbete al evento: `messages`

### 3. Probar Webhook
```bash
python test_webhook.py
```

## 🎯 Primeros Pasos

### 1. Crear tu Primera Plantilla
1. Ve al panel de plantillas en la interfaz web
2. Haz clic en "Crear Plantilla"
3. Completa los campos:
   - **Nombre**: "Bienvenida"
   - **Categoría**: "marketing"
   - **Idioma**: "es"
   - **Contenido**: "¡Hola! Bienvenido a Agropecuaria Juradó"

### 2. Enviar tu Primer Mensaje
1. Ve al panel de contactos
2. Selecciona un contacto
3. Escribe un mensaje en el chat
4. Haz clic en "Enviar"

### 3. Probar Respuestas Automáticas
1. Envía un mensaje de WhatsApp al número configurado
2. Verifica que se guarde automáticamente el contacto
3. Comprueba que llegue la respuesta automática

## 🔧 Configuración Básica

### Variables de Entorno Esenciales
```env
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_VERIFY_TOKEN=Agrojurado2026

# Base de Datos
DATABASE_URL=mysql://usuario:password@localhost/agrojura_web

# Google Gemini AI
GOOGLE_API_KEY=tu_api_key_de_gemini
```

### Comandos Útiles
```bash
# Verificar conexión a BD
python -c "from database import SessionLocal; db = SessionLocal(); print('✅ Conexión exitosa')"

# Probar webhook
python test_webhook.py

# Ver templates
python test_whatsapp_templates.py

# Enviar mensaje de prueba
python test_send_template.py
```

## 🎮 Uso Básico

### Gestión de Contactos
1. **Ver Contactos**: Panel lateral izquierdo
2. **Buscar Contacto**: Barra de búsqueda
3. **Editar Contacto**: Haz clic en el contacto
4. **Eliminar Contacto**: Opción en menú contextual

### Envío de Mensajes
1. **Seleccionar Contacto**: Haz clic en un contacto
2. **Escribir Mensaje**: Área de texto en la parte inferior
3. **Enviar**: Botón de envío o Enter
4. **Ver Estado**: Indicadores de envío/entrega/lectura

### Gestión de Plantillas
1. **Crear Plantilla**: Panel de plantillas
2. **Editar Plantilla**: Haz clic en la plantilla
3. **Enviar Masivamente**: Selecciona contactos y plantilla
4. **Archivar**: Opción en menú contextual

## 🔍 Solución de Problemas Rápidos

### ❌ Error: "No se puede conectar a la base de datos"
```bash
# Verificar MySQL
sudo systemctl status mysql

# Verificar credenciales
mysql -u usuario -p agrojura_web
```

### ❌ Error: "Webhook no funciona"
1. Verificar que ngrok esté corriendo
2. Comprobar URL en Meta Developers
3. Revisar logs del servidor
4. Ejecutar: `python test_webhook.py`

### ❌ Error: "Frontend no se conecta al backend"
1. Verificar que el backend esté corriendo en puerto 8000
2. Comprobar CORS en `main.py`
3. Revisar configuración de WebSocket

### ❌ Error: "No se envían mensajes"
1. Verificar `WHATSAPP_ACCESS_TOKEN`
2. Comprobar `WHATSAPP_PHONE_NUMBER_ID`
3. Revisar logs de la API de WhatsApp

## 📊 Monitoreo Básico

### Ver Logs del Sistema
```bash
# Logs del backend
tail -f logs/app.log

# Logs de uvicorn
uvicorn main:app --log-level debug

# Logs de MySQL
sudo tail -f /var/log/mysql/error.log
```

### Verificar Estado del Sistema
```bash
# Verificar endpoints
curl http://localhost:8000/

# Verificar base de datos
python -c "from database import SessionLocal; db = SessionLocal(); print('✅ BD OK')"

# Verificar WebSocket
# Abrir herramientas de desarrollo del navegador
# Ir a la pestaña Network > WS
```

## 🚀 Despliegue Rápido

### Para Producción
```bash
# 1. Configurar servidor
sudo apt update
sudo apt install python3 python3-pip nodejs npm mysql-server nginx

# 2. Configurar base de datos
mysql -u root -p
CREATE DATABASE agrojura_web;
CREATE USER 'agrojurado'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON agrojura_web.* TO 'agrojurado'@'localhost';

# 3. Configurar variables de entorno
nano .env
# Editar con credenciales de producción

# 4. Inicializar sistema
python init_db.py

# 5. Construir frontend
cd frontend
npm run build

# 6. Configurar nginx
sudo nano /etc/nginx/sites-available/chatbot
# Configurar proxy al backend y servir frontend

# 7. Iniciar servicios
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 📞 Soporte Rápido

### Comandos de Diagnóstico
```bash
# Estado general del sistema
python -c "
from database import SessionLocal
from services.whatsapp_service import get_whatsapp_templates
try:
    db = SessionLocal()
    print('✅ Base de datos: OK')
    templates = get_whatsapp_templates()
    print('✅ WhatsApp API: OK')
    print(f'📱 Templates disponibles: {len(templates)}')
except Exception as e:
    print(f'❌ Error: {e}')
"

# Verificar configuración
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('🔧 Configuración:')
print(f'WHATSAPP_ACCESS_TOKEN: {'✅' if os.getenv('WHATSAPP_ACCESS_TOKEN') else '❌'}')
print(f'WHATSAPP_PHONE_NUMBER_ID: {'✅' if os.getenv('WHATSAPP_PHONE_NUMBER_ID') else '❌'}')
print(f'DATABASE_URL: {'✅' if os.getenv('DATABASE_URL') else '❌'}')
print(f'GOOGLE_API_KEY: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}')
"
```

### Contacto de Emergencia
Si tienes problemas críticos:
1. Revisar logs del sistema
2. Verificar conectividad de red
3. Comprobar credenciales de API
4. Reiniciar servicios si es necesario

---

**¡Con esta guía rápida deberías tener el sistema funcionando en menos de 10 minutos! 🚀** 