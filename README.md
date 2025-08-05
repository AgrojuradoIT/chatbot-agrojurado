# 🤖 Chatbot WhatsApp - Agropecuaria Juradó S.A.S

Un sistema completo de chatbot para WhatsApp que permite la gestión de contactos, envío de mensajes, plantillas y comunicación en tiempo real.

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Características](#-características)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Desarrollo](#-desarrollo)
- [Despliegue](#-despliegue)
- [Solución de Problemas](#-solución-de-problemas)

## 🎯 Descripción del Proyecto

Este proyecto es un sistema completo de chatbot para WhatsApp desarrollado para **Agropecuaria Juradó S.A.S**. El sistema incluye:

- **Backend**: API REST con FastAPI para gestionar mensajes, contactos y plantillas
- **Frontend**: Interfaz web en React/TypeScript para administrar el chatbot
- **Base de Datos**: MySQL para almacenar contactos, mensajes y plantillas
- **WebSocket**: Comunicación en tiempo real entre frontend y backend
- **Integración WhatsApp**: Webhook para recibir y enviar mensajes automáticamente

## ✨ Características

### 🔧 Backend (FastAPI)
- ✅ API REST completa para gestión de contactos
- ✅ Sistema de plantillas de WhatsApp
- ✅ Webhook para mensajes entrantes
- ✅ Respuestas automáticas con IA (Gemini)
- ✅ WebSocket para comunicación en tiempo real
- ✅ Base de datos MySQL con SQLAlchemy

### 🎨 Frontend (React + TypeScript)
- ✅ Interfaz moderna y responsiva
- ✅ Chat en tiempo real con WebSocket
- ✅ Gestión de contactos
- ✅ Panel de plantillas
- ✅ Scroll infinito para mensajes
- ✅ Diseño adaptativo

### 🤖 Funcionalidades del Chatbot
- ✅ Respuestas automáticas a mensajes
- ✅ Menú interactivo con opciones
- ✅ Gestión de contactos automática
- ✅ Plantillas personalizables
- ✅ Historial de conversaciones

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Frontend      │    │   Backend       │
│   (Webhook)     │◄──►│   (React)       │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   WebSocket     │    │   MySQL DB      │
                       │   (Tiempo Real) │    │   (Datos)       │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Cuenta de WhatsApp Business API

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd chatbot-agrojurado
```

### 2. Configurar el Backend

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Configurar la Base de Datos

```bash
# Crear base de datos
mysql -u root -p
CREATE DATABASE agrojura_web;

# Ejecutar migraciones
python init_db.py
```

### 4. Configurar el Frontend

```bash
cd frontend
npm install
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_VERIFY_TOKEN=Agrojurado2026

# Base de Datos
DATABASE_URL=mysql://usuario:password@localhost/agrojura_web

# Google Gemini AI
GOOGLE_API_KEY=tu_api_key_de_gemini

# Configuración del Servidor
HOST=0.0.0.0
PORT=8000
```

### Configurar Webhook de WhatsApp

Ver el archivo [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) para instrucciones detalladas.

## 🎮 Uso

### Iniciar el Backend

```bash
# Desde la raíz del proyecto
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Iniciar el Frontend

```bash
# Desde la carpeta frontend
cd frontend
npm run dev
```

### Acceder a la Aplicación

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Backend**: http://localhost:8000

## 📡 API Endpoints

### Gestión de Contactos
- `GET /api/contacts` - Obtener todos los contactos
- `POST /api/contacts` - Crear nuevo contacto
- `GET /api/contacts/{phone_number}` - Obtener contacto específico
- `PUT /api/contacts/{phone_number}` - Actualizar contacto
- `DELETE /api/contacts/{phone_number}` - Eliminar contacto

### Gestión de Mensajes
- `GET /api/messages/{phone_number}` - Obtener mensajes de un contacto
- `POST /api/messages/send` - Enviar mensaje
- `GET /api/messages/{phone_number}/recent` - Mensajes recientes

### Gestión de Plantillas
- `GET /api/templates` - Obtener plantillas
- `POST /api/templates` - Crear plantilla
- `DELETE /api/templates/{template_id}` - Eliminar plantilla
- `POST /api/templates/send` - Enviar plantilla a contactos

### WebSocket
- `WS /ws/{phone_number}` - WebSocket para contacto específico
- `WS /ws` - WebSocket general

### Webhook
- `GET /webhook` - Verificación del webhook
- `POST /webhook` - Recibir mensajes de WhatsApp

## 📁 Estructura del Proyecto

```
chatbot-agrojurado/
├── 📁 frontend/                 # Aplicación React
│   ├── 📁 src/
│   │   ├── 📁 components/      # Componentes React
│   │   ├── 📁 services/        # Servicios de API
│   │   └── 📁 hooks/          # Custom hooks
│   ├── package.json
│   └── README.md
├── 📁 models/                  # Modelos de base de datos
│   └── whatsapp_models.py
├── 📁 services/                # Servicios del backend
│   ├── whatsapp_service.py
│   └── gemini_service.py
├── 📄 main.py                  # Aplicación principal FastAPI
├── 📄 database.py              # Configuración de base de datos
├── 📄 requirements.txt         # Dependencias Python
├── 📄 init_db.py              # Inicialización de BD
└── 📄 WEBHOOK_SETUP.md        # Configuración del webhook
```

## 🛠️ Desarrollo

### Scripts Útiles

```bash
# Probar webhook
python test_webhook.py

# Verificar templates
python test_whatsapp_templates.py

# Probar envío de mensajes
python test_send_template.py

# Verificar conexión a BD
python test_contacts_api.py
```

### Comandos de Desarrollo

```bash
# Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Linting
cd frontend
npm run lint

# Build
cd frontend
npm run build
```

## 🚀 Despliegue

### Producción

1. **Configurar servidor**:
   ```bash
   # Instalar dependencias del sistema
   sudo apt update
   sudo apt install python3 python3-pip nodejs npm mysql-server
   ```

2. **Configurar base de datos**:
   ```bash
   mysql -u root -p
   CREATE DATABASE agrojura_web;
   CREATE USER 'agrojurado'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON agrojura_web.* TO 'agrojurado'@'localhost';
   ```

3. **Configurar variables de entorno**:
   ```bash
   # Editar .env con credenciales de producción
   nano .env
   ```

4. **Iniciar servicios**:
   ```bash
   # Backend con systemd
   sudo systemctl enable chatbot-backend
   sudo systemctl start chatbot-backend

   # Frontend (build estático)
   cd frontend
   npm run build
   # Servir con nginx
   ```

### Docker (Opcional)

```dockerfile
# Dockerfile para el backend
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar conexión
python -c "from database import SessionLocal; db = SessionLocal(); print('Conexión exitosa')"
```

#### 2. Webhook no Funciona
- Verificar que el webhook esté verificado en Meta Developers
- Comprobar que la URL sea accesible desde internet
- Revisar logs del servidor

#### 3. Frontend no se Conecta al Backend
- Verificar CORS en `main.py`
- Comprobar que el backend esté corriendo en puerto 8000
- Revisar configuración de WebSocket

#### 4. Mensajes no se Envían
- Verificar `WHATSAPP_ACCESS_TOKEN`
- Comprobar `WHATSAPP_PHONE_NUMBER_ID`
- Revisar logs de la API de WhatsApp

### Logs Útiles

```bash
# Ver logs del backend
tail -f logs/app.log

# Ver logs de uvicorn
uvicorn main:app --log-level debug

# Ver logs de MySQL
sudo tail -f /var/log/mysql/error.log
```

## 📞 Soporte

Para soporte técnico o preguntas:

1. **Revisar logs** del servidor y frontend
2. **Verificar configuración** de variables de entorno
3. **Comprobar conectividad** de red y servicios
4. **Consultar documentación** de WhatsApp Business API

## 📄 Licencia

Este proyecto es propiedad de **Agropecuaria Juradó S.A.S**.

---

**Desarrollado con ❤️ para Agropecuaria Juradó S.A.S** 