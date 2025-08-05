# 🎨 Frontend - Chatbot WhatsApp Agropecuaria Juradó

Interfaz web moderna para administrar el chatbot de WhatsApp de Agropecuaria Juradó S.A.S.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
npm install

# Iniciar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# Vista previa de producción
npm run preview
```

## 📋 Características

### 🎯 Funcionalidades Principales
- ✅ **Chat en Tiempo Real**: Comunicación instantánea con contactos
- ✅ **Gestión de Contactos**: Crear, editar y eliminar contactos
- ✅ **Panel de Plantillas**: Administrar plantillas de WhatsApp
- ✅ **Scroll Infinito**: Carga automática de mensajes antiguos
- ✅ **Diseño Responsivo**: Adaptable a diferentes dispositivos

### 🛠️ Tecnologías Utilizadas
- **React 19**: Framework principal
- **TypeScript**: Tipado estático
- **Vite**: Build tool rápido
- **WebSocket**: Comunicación en tiempo real
- **CSS Modules**: Estilos modulares

## 📁 Estructura del Proyecto

```
frontend/
├── 📁 src/
│   ├── 📁 components/          # Componentes React
│   │   ├── ChatWindow.tsx      # Ventana principal del chat
│   │   ├── ContactsPanel.tsx   # Panel de contactos
│   │   ├── TemplatePanel.tsx   # Panel de plantillas
│   │   ├── InputArea.tsx       # Área de entrada de mensajes
│   │   ├── MessageStatus.tsx   # Estado de mensajes
│   │   └── InfiniteScroll.tsx  # Scroll infinito
│   ├── 📁 services/            # Servicios de API
│   │   ├── websocketService.ts # WebSocket
│   │   ├── contactService.ts   # Gestión de contactos
│   │   ├── messageService.ts   # Gestión de mensajes
│   │   └── templateService.ts  # Gestión de plantillas
│   ├── 📁 hooks/              # Custom hooks
│   ├── 📁 config/             # Configuraciones
│   ├── App.tsx                # Componente principal
│   └── main.tsx               # Punto de entrada
├── 📁 public/                 # Archivos estáticos
├── package.json               # Dependencias
└── vite.config.ts            # Configuración de Vite
```

## 🎮 Uso

### Desarrollo
```bash
# Iniciar servidor de desarrollo
npm run dev

# El frontend estará disponible en:
# http://localhost:5173
```

### Producción
```bash
# Construir aplicación
npm run build

# Vista previa de producción
npm run preview
```

## 🔧 Configuración

### Variables de Entorno
Crear archivo `.env` en la carpeta `frontend/`:

```env
# URL del backend
VITE_API_URL=http://localhost:8000

# URL del WebSocket
VITE_WS_URL=ws://localhost:8000
```

### Configuración de Vite
El archivo `vite.config.ts` está configurado para:
- Proxy automático al backend
- Hot Module Replacement (HMR)
- Build optimizado para producción

## 📡 Integración con Backend

### WebSocket
El frontend se conecta al backend mediante WebSocket para:
- Recibir mensajes en tiempo real
- Actualizar estado de mensajes
- Notificaciones de nuevos contactos

### API REST
Los servicios en `src/services/` manejan:
- **contactService.ts**: CRUD de contactos
- **messageService.ts**: Envío y recepción de mensajes
- **templateService.ts**: Gestión de plantillas
- **websocketService.ts**: Conexión WebSocket

## 🎨 Componentes Principales

### ChatWindow.tsx
- Ventana principal del chat
- Maneja la conversación con un contacto específico
- Integra InputArea y MessageStatus

### ContactsPanel.tsx
- Lista de contactos disponibles
- Búsqueda y filtrado
- Selección de contacto activo

### TemplatePanel.tsx
- Gestión de plantillas de WhatsApp
- Crear, editar y eliminar plantillas
- Envío masivo de plantillas

### InputArea.tsx
- Área de entrada de mensajes
- Soporte para texto y archivos
- Integración con servicios de mensajería

## 🚀 Despliegue

### Build para Producción
```bash
npm run build
```

Los archivos generados estarán en `dist/` y pueden ser servidos por cualquier servidor web estático.

### Nginx (Recomendado)
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔍 Debugging

### Herramientas de Desarrollo
- **React DevTools**: Para inspeccionar componentes
- **Network Tab**: Para ver llamadas a la API
- **Console**: Para logs y errores

### Logs Útiles
```javascript
// En el navegador
console.log('WebSocket conectado');
console.log('Mensaje recibido:', message);
console.log('Error de conexión:', error);
```

## 📞 Soporte

Para problemas específicos del frontend:

1. **Verificar conexión al backend**: Asegurar que el backend esté corriendo
2. **Revisar WebSocket**: Comprobar conexión en tiempo real
3. **Verificar CORS**: El backend debe permitir requests del frontend
4. **Revisar logs**: Usar herramientas de desarrollo del navegador

---

**Frontend del Chatbot WhatsApp - Agropecuaria Juradó S.A.S**
