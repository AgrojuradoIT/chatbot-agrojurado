# 🤖 Chatbot WhatsApp - Agropecuaria Juradó S.A.S

Un sistema completo de chatbot para WhatsApp que permite la gestión de contactos, envío de mensajes, plantillas y comunicación en tiempo real con integración de IA.

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
- **Frontend**: Interfaz web moderna en React/TypeScript con Vite
- **Base de Datos**: MySQL con SQLAlchemy para almacenar contactos, mensajes y plantillas
- **WebSocket**: Comunicación en tiempo real entre frontend y backend
- **Integración WhatsApp**: Webhook para recibir y enviar mensajes automáticamente
- **IA Integrada**: Respuestas automáticas usando Google Gemini AI
- **Gestión de Media**: Subida y gestión de archivos multimedia

## ✨ Características

### 🔧 Backend (FastAPI)
- ✅ API REST completa para gestión de contactos y mensajes
- ✅ Sistema avanzado de plantillas de WhatsApp con media
- ✅ Webhook para mensajes entrantes con procesamiento automático
- ✅ Respuestas automáticas con IA (Google Gemini)
- ✅ WebSocket para comunicación en tiempo real
- ✅ Base de datos MySQL con SQLAlchemy y Alembic
- ✅ Gestión de archivos multimedia (imágenes, documentos, audio)
- ✅ Sistema de estadísticas y métricas
- ✅ Importación masiva de contactos
- ✅ Gestión de plantillas archivadas

### 🎨 Frontend (React + TypeScript + Vite)
- ✅ Interfaz moderna y responsiva con diseño adaptativo
- ✅ Chat en tiempo real con WebSocket
- ✅ Panel de gestión de contactos con importación masiva
- ✅ Editor avanzado de plantillas con soporte multimedia
- ✅ Dashboard de estadísticas con gráficos interactivos
- ✅ Scroll infinito para mensajes
- ✅ Selector de medios para plantillas
- ✅ Gestión de estado con Context API
- ✅ Componentes reutilizables y modulares

### 🤖 Funcionalidades del Chatbot
- ✅ Respuestas automáticas inteligentes con IA
- ✅ Menú interactivo con opciones dinámicas
- ✅ Gestión automática de contactos
- ✅ Plantillas personalizables con variables
- ✅ Historial completo de conversaciones
- ✅ Soporte para diferentes tipos de media
- ✅ Sistema de estados de mensajes

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Frontend      │    │   Backend       │
│   (Webhook)     │◄──►│   (React/Vite)  │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   WebSocket     │    │   MySQL DB      │
                       │   (Tiempo Real) │    │   (SQLAlchemy)  │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       ▼
                                │              ┌─────────────────┐
                                │              │   Google Gemini │
                                │              │   (IA)          │
                                │              └─────────────────┘
                                ▼
                       ┌─────────────────┐
                       │   Media Storage │
                       │   (Archivos)    │
                       └─────────────────┘
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Cuenta de WhatsApp Business API
- API Key de Google Gemini

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
cp env.example .env
# Editar .env con tus credenciales
```

### 3. Configurar la Base de Datos

```bash
# Ejecutar script de actualización de base de datos
python update_database.py
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
DB_HOST=localhost
DB_USER=root
DB_NAME=agrojura
DB_PASSWORD=tu_password
DB_PORT=3306

# Google Gemini AI
GOOGLE_API_KEY=tu_api_key_de_gemini

# Configuración del Servidor
HOST=0.0.0.0
PORT=8000
```

### Configurar Webhook de WhatsApp

1. **Configurar en Meta Developers**:
   - URL: `https://tu-dominio.com/webhook`
   - Verify Token: `TU_TOKEN_AQUI`
   - Suscribirse a eventos: `messages`, `message_deliveries`

2. **Verificar webhook**:
   ```bash
   curl "https://tu-dominio.com/webhook?hub.mode=subscribe&hub.challenge=CHALLENGE_ACCEPTED&hub.verify_token=Agrojurado2026"
   ```

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
- `POST /api/contacts/bulk` - Crear contactos masivamente
- `GET /api/contacts/{phone_number}` - Obtener contacto específico
- `PUT /api/contacts/{phone_number}` - Actualizar contacto
- `DELETE /api/contacts/{phone_number}` - Eliminar contacto

### Gestión de Mensajes
- `GET /api/messages/{phone_number}` - Obtener mensajes de un contacto
- `GET /api/messages/{phone_number}/older` - Obtener mensajes más antiguos
- `GET /api/messages/{phone_number}/recent` - Mensajes recientes
- `POST /api/messages/send` - Enviar mensaje
- `GET /api/debug/messages/{phone_number}` - Debug de mensajes

### Gestión de Plantillas
- `GET /api/templates` - Obtener plantillas activas
- `GET /api/templates/archived` - Obtener plantillas archivadas
- `POST /api/templates` - Crear plantilla
- `POST /api/templates/with-media` - Crear plantilla con media
- `DELETE /api/templates/{template_id}` - Eliminar plantilla
- `POST /api/templates/{template_id}/archive` - Archivar plantilla
- `POST /api/templates/{template_id}/unarchive` - Desarchivar plantilla
- `POST /api/templates/send` - Enviar plantilla a contactos
- `POST /api/templates/send-with-media` - Enviar plantilla con media

### Gestión de Media
- `POST /api/media/upload` - Subir archivo multimedia
- `POST /api/media/upload-base64` - Subir media desde base64

### Estadísticas
- `GET /api/statistics` - Obtener estadísticas del sistema

### WebSocket
- `WS /ws/{phone_number}` - WebSocket para contacto específico
- `WS /ws` - WebSocket general

### Webhook
- `GET /webhook` - Verificación del webhook
- `POST /webhook` - Recibir mensajes de WhatsApp

## 📁 Estructura del Proyecto

```
chatbot-agrojurado/
├── 📁 frontend/                 # Aplicación React con Vite
│   ├── 📁 src/
│   │   ├── 📁 components/      # Componentes React
│   │   │   ├── ChatPanel.tsx   # Panel principal del chat
│   │   │   ├── ChatWindow.tsx  # Ventana de chat
│   │   │   ├── ContactManager.tsx # Gestión de contactos
│   │   │   ├── ContactImport.tsx # Importación masiva
│   │   │   ├── TemplatePanel.tsx # Editor de plantillas
│   │   │   ├── MediaSelector.tsx # Selector de medios
│   │   │   ├── StatisticsDashboard.tsx # Dashboard de estadísticas
│   │   │   ├── MessageStatus.tsx # Estados de mensajes
│   │   │   ├── InputArea.tsx   # Área de entrada
│   │   │   └── InfiniteScroll.tsx # Scroll infinito
│   │   ├── 📁 services/        # Servicios de API
│   │   │   ├── contactService.ts
│   │   │   ├── messageService.ts
│   │   │   ├── templateService.ts
│   │   │   └── websocketService.ts
│   │   ├── 📁 contexts/        # Context API
│   │   │   └── ContactContext.tsx
│   │   ├── 📁 hooks/          # Custom hooks
│   │   └── 📁 config/         # Configuración
│   ├── package.json
│   └── vite.config.ts
├── 📁 models/                  # Modelos de base de datos
│   └── whatsapp_models.py
├── 📁 services/                # Servicios del backend
│   ├── whatsapp_service.py     # Servicio de WhatsApp
│   └── gemini_service.py      # Servicio de IA
├── 📁 static/                  # Archivos estáticos
│   ├── 📁 images/
│   └── 📁 uploads/
├── 📄 main.py                  # Aplicación principal FastAPI
├── 📄 database.py              # Configuración de base de datos
├── 📄 update_database.py       # Script de actualización de BD
├── 📄 requirements.txt         # Dependencias Python
└── 📄 env.example             # Ejemplo de variables de entorno
```

## 🛠️ Desarrollo

### Scripts Útiles

```bash
# Actualizar base de datos
python update_database.py

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

### Nuevas Funcionalidades

#### 🎨 Frontend Mejorado
- **Componentes Modulares**: Cada funcionalidad tiene su propio componente
- **Context API**: Gestión de estado global para contactos
- **WebSocket Real-time**: Comunicación instantánea
- **Media Management**: Subida y gestión de archivos multimedia
- **Statistics Dashboard**: Gráficos interactivos con Recharts
- **Infinite Scroll**: Carga eficiente de mensajes
- **Template Editor**: Editor avanzado de plantillas

#### 🔧 Backend Avanzado
- **Media Upload**: Soporte para subida de archivos
- **Bulk Operations**: Operaciones masivas para contactos
- **Template Management**: Sistema completo de plantillas
- **Statistics API**: Métricas y estadísticas del sistema
- **WebSocket Manager**: Gestión avanzada de conexiones
- **AI Integration**: Integración con Google Gemini

## 🚀 Despliegue

### Producción

1. **Configurar servidor**:
   ```bash
   # Instalar dependencias del sistema
   sudo apt update
   sudo apt install python3 python3-pip nodejs npm mysql-server nginx
   ```

2. **Configurar base de datos**:
   ```bash
   mysql -u root -p
   CREATE DATABASE agrojura;
   CREATE USER 'agrojurado'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON agrojura.* TO 'agrojurado'@'localhost';
   ```

3. **Configurar variables de entorno**:
   ```bash
   # Editar .env con credenciales de producción
   nano .env
   ```

4. **Actualizar base de datos**:
   ```bash
   python update_database.py
   ```

5. **Build del frontend**:
   ```bash
   cd frontend
   npm run build
   ```

6. **Configurar nginx**:
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static/ {
           alias /path/to/chatbot-agrojurado/static/;
       }
   }
   ```

7. **Iniciar servicios**:
   ```bash
   # Backend con systemd
   sudo systemctl enable chatbot-backend
   sudo systemctl start chatbot-backend
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

# Actualizar base de datos
python update_database.py
```

#### 2. Webhook no Funciona
- Verificar que el webhook esté verificado en Meta Developers
- Comprobar que la URL sea accesible desde internet
- Revisar logs del servidor
- Verificar `WHATSAPP_VERIFY_TOKEN`

#### 3. Frontend no se Conecta al Backend
- Verificar CORS en `main.py`
- Comprobar que el backend esté corriendo en puerto 8000
- Revisar configuración de WebSocket
- Verificar variables de entorno

#### 4. Mensajes no se Envían
- Verificar `WHATSAPP_ACCESS_TOKEN`
- Comprobar `WHATSAPP_PHONE_NUMBER_ID`
- Revisar logs de la API de WhatsApp
- Verificar permisos de la cuenta de WhatsApp Business

#### 5. Media no se Sube
- Verificar permisos de escritura en `/static/uploads/`
- Comprobar límites de tamaño de archivo
- Revisar configuración de `python-multipart`

### Logs Útiles

```bash
# Ver logs del backend
tail -f logs/app.log

# Ver logs de uvicorn
uvicorn main:app --log-level debug

# Ver logs de MySQL
sudo tail -f /var/log/mysql/error.log

# Ver logs del frontend
cd frontend && npm run dev
```

### Verificación de Servicios

```bash
# Verificar que todos los servicios estén corriendo
ps aux | grep -E "(uvicorn|node|mysql)"

# Verificar puertos
netstat -tlnp | grep -E "(8000|5173|3306)"

# Verificar variables de entorno
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Variables cargadas:', bool(os.getenv('WHATSAPP_ACCESS_TOKEN')))"
```

## 📞 Soporte

Para soporte técnico o preguntas:

1. **Revisar logs** del servidor y frontend
2. **Verificar configuración** de variables de entorno
3. **Comprobar conectividad** de red y servicios
4. **Consultar documentación** de WhatsApp Business API
5. **Verificar base de datos** con `update_database.py`

## 📄 Licencia

Este proyecto es propiedad de **Agropecuaria Juradó S.A.S**.

---

**Desarrollado con ❤️ para Agropecuaria Juradó S.A.S** 