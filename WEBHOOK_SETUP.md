# Configuración del Webhook de WhatsApp

## 🎯 Objetivo
Este documento explica cómo configurar el webhook de WhatsApp para que:
- ✅ Guarde automáticamente los contactos cuando reciban mensajes
- ✅ Responda automáticamente con el menú de opciones

## 🚀 Configuración Paso a Paso

### 1. Verificar que el servidor esté corriendo
```bash
# En la terminal principal
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Configurar ngrok para pruebas locales (Opcional pero recomendado)

#### Instalar ngrok
1. Descarga ngrok desde: https://ngrok.com/download
2. Regístrate en ngrok.com y obtén tu token de autenticación
3. Configura ngrok:
```bash
ngrok authtoken TU_TOKEN_AQUI
```

#### Iniciar ngrok
```bash
ngrok http 8000
```

Copia la URL HTTPS generada (ejemplo: `https://abcd1234.ngrok.io`)

### 3. Configurar el Webhook en Meta Developers

1. Ve a: https://developers.facebook.com/apps/
2. Selecciona tu aplicación de WhatsApp
3. Ve a "WhatsApp" > "Configuración"
4. En "Webhooks", haz clic en "Editar"
5. Configura:
   - **URL de devolución de llamada**: `https://TU_URL/webhook`
   - **Token de verificación**: `Agrojurado2026`
6. Suscríbete al evento: `messages`

### 4. Probar el webhook

#### Opción 1: Usar el script de prueba
```bash
python test_webhook.py
```

#### Opción 2: Enviar mensaje real
1. Envía un mensaje de WhatsApp al número configurado
2. Verifica los logs del servidor
3. Verifica que el contacto se guarde en la base de datos

### 5. Verificar la base de datos

#### Ver contactos guardados
```sql
-- Conectarte a MySQL
mysql -u root -p agrojura_web

-- Ver todos los contactos
SELECT * FROM whatsapp_users ORDER BY last_interaction DESC;

-- Ver últimos 10 contactos
SELECT phone_number, name, last_interaction FROM whatsapp_users ORDER BY last_interaction DESC LIMIT 10;
```

## 🔧 Solución de Problemas

### Problema: "No me funciona"

#### Verifica estos puntos:

1. **Variables de entorno**:
   ```bash
   # Verifica que las variables estén configuradas
   echo $WHATSAPP_ACCESS_TOKEN
   echo $WHATSAPP_PHONE_NUMBER_ID
   echo $WHATSAPP_VERIFY_TOKEN
   ```

2. **Logs del servidor**:
   - Mira los logs de uvicorn para errores
   - Busca mensajes como "📱 Mensaje recibido de..."

3. **Webhook verificado**:
   - En Meta Developers, el webhook debe mostrarse como "Verificado"

4. **Base de datos**:
   - Asegúrate de que la tabla `whatsapp_users` exista
   - Verifica permisos de escritura

### Problema: No se guardan los mensajes

#### Solución:
1. **Verifica la conexión a la base de datos**:
   ```python
   # Ejecuta esto en Python para probar
   from database import SessionLocal
   from services.whatsapp_service import create_or_update_whatsapp_user
   
   db = SessionLocal()
   create_or_update_whatsapp_user(db, "573001234567", "Test User")
   print("Usuario guardado exitosamente")
   ```

2. **Verifica el endpoint del webhook**:
   ```bash
   curl -X POST http://localhost:8000/webhook \
     -H "Content-Type: application/json" \
     -d @test_payload.json
   ```

## 📱 Cómo funciona

Cuando un usuario envía un mensaje:

1. WhatsApp envía el mensaje al webhook configurado
2. El webhook procesa:
   - Guarda/actualiza el contacto en `whatsapp_users`
   - Responde automáticamente con el menú
   - Actualiza la fecha de última interacción

### Respuestas automáticas:
- **"hola" o "menu"**: Muestra el menú completo
- **"1" o "contacto"**: Números de contacto
- **"4" o "datos"**: Tratamiento de datos personales
- **"5" o "cancelar"**: Cancela la suscripción

## 🧪 Script de prueba incluido

El archivo `test_webhook.py` permite probar el webhook sin necesidad de enviar mensajes reales.

```bash
# Ejecutar prueba
python test_webhook.py
```

## 📞 Contacto de soporte

Si tienes problemas adicionales:
1. Verifica los logs del servidor
2. Asegúrate de que el webhook esté verificado en Meta
3. Comprueba la conexión a la base de datos