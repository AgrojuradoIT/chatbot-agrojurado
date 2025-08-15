# 🤖 Chatbot WhatsApp - Agropecuaria Juradó S.A.S

Un sistema completo de chatbot para WhatsApp que permite la gestión de contactos, envío de mensajes, plantillas y comunicación en tiempo real con autenticación OAuth.

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
- **Autenticación OAuth**: Sistema de login seguro con JWT
- **Gestión de Media**: Subida y gestión de archivos multimedia
- **Estadísticas**: Dashboard con métricas del sistema

## ✨ Características

### 🔧 Backend (FastAPI)
- ✅ API REST completa para gestión de contactos y mensajes
- ✅ Sistema avanzado de plantillas de WhatsApp con media
- ✅ Webhook para mensajes entrantes con procesamiento automático
- ✅ WebSocket para comunicación en tiempo real
- ✅ Base de datos MySQL con SQLAlchemy
- ✅ Gestión de archivos multimedia (imágenes, documentos, audio)
- ✅ Sistema de estadísticas y métricas
- ✅ Importación masiva de contactos
- ✅ Gestión de plantillas archivadas
- ✅ Autenticación OAuth con JWT
- ✅ Sistema de permisos y middleware de autenticación

### 🎨 Frontend (React + TypeScript + Vite)
- ✅ Interfaz moderna y responsiva con diseño adaptativo
- ✅ Chat en tiempo real con WebSocket
- ✅ Panel de gestión de contactos con importación masiva
- ✅ Editor avanzado de plantillas con soporte multimedia
- ✅ Dashboard de estadísticas con gráficos interactivos (Recharts)
- ✅ Scroll infinito para mensajes
- ✅ Selector de medios para plantillas
- ✅ Gestión de estado con Context API
- ✅ Componentes reutilizables y modulares
- ✅ Sistema de autenticación con OAuth
- ✅ Importación de contactos desde Excel (XLSX)

### 🤖 Funcionalidades del Chatbot
- ✅ Respuestas automáticas inteligentes
- ✅ Menú interactivo con opciones dinámicas
- ✅ Gestión automática de contactos
- ✅ Plantillas personalizables con variables
- ✅ Historial completo de conversaciones
- ✅ Soporte para diferentes tipos de media
- ✅ Sistema de estados de mensajes
- ✅ Gestión de usuarios inactivos

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
                                │              │   OAuth/JWT     │
                                │              │   (Auth)        │
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
- Configuración OAuth (Laravel passport API, Tambien podrias usar autenticacion con google adaptando el proyecto.)

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
WHATSAPP_BUSINESS_ACCOUNT_ID=tu_business_account_id
WHATSAPP_VERIFY_TOKEN=Agrojurado2026

# Base de Datos
DB_HOST=localhost
DB_USER=root
DB_NAME=agrojura_web
DB_PASSWORD=tu_password
DB_PORT=3306

# OAuth Configuration
OAUTH_CLIENT_ID=tu_oauth_client_id
OAUTH_CLIENT_SECRET=tu_oauth_client_secret
OAUTH_REDIRECT_URI=http://localhost:5173/auth/callback
OAUTH_AUTH_URL=https://accounts.google.com/o/oauth2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_USER_URL=https://www.googleapis.com/oauth2/v2/userinfo

# JWT Configuration
JWT_SECRET_KEY=tu_jwt_secret_key_super_segura

# Configuración del Servidor
HOST=0.0.0.0
PORT=8000
```

### Configurar Webhook de WhatsApp

1. **Configurar en Meta Developers**:
   - URL: `https://tu-dominio.com/webhook`
   - Verify Token: `TU_TOKEN_VERIFICACION_AQUI`
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

### Autenticación
- `GET /auth/login` - Iniciar proceso de login OAuth
- `GET /auth/callback` - Callback de OAuth
- `GET /auth/logout` - Cerrar sesión
- `GET /auth/user` - Obtener información del usuario actual

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
├── 📁 config/                    # Configuración del sistema
│   ├── __init__.py
│   ├── cors.py                   # Configuración CORS
│   └── settings.py               # Variables de entorno
├── 📁 dependencies/              # Dependencias compartidas
├── 📁 middleware/                # Middleware personalizado
│   ├── __init__.py
│   ├── auth.py                   # Middleware de autenticación
│   └── permissions.py            # Sistema de permisos
├── 📁 models/                    # Modelos de base de datos
│   ├── __init__.py
│   ├── auth_models.py            # Modelos de autenticación
│   ├── contact_models.py         # Modelos de contactos
│   ├── message_models.py         # Modelos de mensajes
│   ├── template_models.py        # Modelos de plantillas
│   └── whatsapp_models.py        # Modelos de WhatsApp
├── 📁 routers/                   # Rutas de la API
│   ├── __init__.py
│   ├── auth.py                   # Rutas de autenticación
│   ├── contacts.py               # Gestión de contactos
│   ├── messages.py               # Gestión de mensajes
│   ├── statistics.py             # Estadísticas
│   ├── templates.py              # Gestión de plantillas
│   ├── webhook.py                # Webhook de WhatsApp
│   └── websocket.py              # WebSocket
├── 📁 services/                  # Servicios del backend
│   ├── auth_service.py           # Servicio de autenticación
│   └── whatsapp_service.py       # Servicio de WhatsApp
├── 📁 static/                    # Archivos estáticos
│   ├── 📁 images/
│   └── 📁 uploads/               # Archivos subidos
├── 📁 utils/                     # Utilidades
│   ├── __init__.py
│   └── websocket_manager.py      # Gestor de WebSocket
├── 📁 frontend/                  # Aplicación React con Vite
│   ├── 📁 src/
│   │   ├── 📁 components/        # Componentes React
│   │   │   ├── AuthCallback.tsx  # Callback de autenticación
│   │   │   ├── ChatPanel.tsx     # Panel principal del chat
│   │   │   ├── ChatWindow.tsx    # Ventana de chat
│   │   │   ├── ContactManager.tsx # Gestión de contactos
│   │   │   ├── ContactImport.tsx # Importación masiva
│   │   │   ├── InfiniteScroll.tsx # Scroll infinito
│   │   │   ├── InputArea.tsx     # Área de entrada
│   │   │   ├── LoginPage.tsx     # Página de login
│   │   │   ├── MediaSelector.tsx # Selector de medios
│   │   │   ├── MessageStatus.tsx # Estados de mensajes
│   │   │   ├── ProtectedComponent.tsx # Componente protegido
│   │   │   ├── StatisticsDashboard.tsx # Dashboard de estadísticas
│   │   │   └── TemplatePanel.tsx # Editor de plantillas
│   │   ├── 📁 contexts/          # Context API
│   │   │   ├── AuthContext.tsx   # Contexto de autenticación
│   │   │   └── ContactContext.tsx # Contexto de contactos
│   │   ├── 📁 hooks/             # Custom hooks
│   │   │   └── usePermissions.ts # Hook de permisos
│   │   ├── 📁 services/          # Servicios de API
│   │   │   ├── contactService.ts # Servicio de contactos
│   │   │   ├── messageService.ts # Servicio de mensajes
│   │   │   ├── templateService.ts # Servicio de plantillas
│   │   │   └── websocketService.ts # Servicio WebSocket
│   │   ├── 📁 utils/             # Utilidades del frontend
│   │   │   └── auth.ts           # Utilidades de autenticación
│   │   ├── App.tsx               # Componente principal
│   │   ├── main.tsx              # Punto de entrada
│   │   └── index.css             # Estilos globales
│   ├── package.json              # Dependencias del frontend
│   ├── vite.config.ts            # Configuración de Vite
│   └── tsconfig.json             # Configuración de TypeScript
├── 📄 main.py                    # Aplicación principal FastAPI
├── 📄 database.py                # Configuración de base de datos
├── 📄 update_database.py         # Script de actualización de BD
├── 📄 requirements.txt           # Dependencias Python
├── 📄 env.example               # Ejemplo de variables de entorno
└── 📄 README.md                 # Este archivo
```

## 🛠️ Desarrollo

### Comandos de Desarrollo

```bash
# Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Build del frontend
cd frontend
npm run build
```

## 🚀 Despliegue

### Producción

1. **Instalar dependencias**:
   ```bash
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

4. **Actualizar base de datos**:
   ```bash
   python update_database.py
   ```

5. **Build del frontend**:
   ```bash
   cd frontend
   npm run build
   ```

6. **Configurar nginx** (opcional):
   ```nginx
   server {
       listen 80;
       server_name tu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Iniciar servicios**:
   ```bash
   # Backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 🔧 Solución de Problemas

### Problemas Comunes

- **Error de Conexión a Base de Datos**: Verificar credenciales en `.env` y ejecutar `python update_database.py`
- **Webhook no Funciona**: Verificar configuración en Meta Developers y `WHATSAPP_VERIFY_TOKEN`
- **Frontend no se Conecta**: Verificar CORS en `config/cors.py` y que el backend esté corriendo
- **Mensajes no se Envían**: Verificar `WHATSAPP_ACCESS_TOKEN` y permisos de WhatsApp Business
- **Media no se Sube**: Verificar permisos de escritura en `/static/uploads/`
- **Problemas de Autenticación**: Verificar configuración OAuth y `JWT_SECRET_KEY`

## 📞 Soporte

Para soporte técnico:
1. Verificar configuración de variables de entorno
2. Comprobar conectividad de servicios
3. Consultar documentación de WhatsApp Business API

## 📄 Licencia

Este proyecto es propiedad de **Agropecuaria Juradó S.A.S**.

---

**Desarrollado con ❤️ para Agropecuaria Juradó S.A.S** 