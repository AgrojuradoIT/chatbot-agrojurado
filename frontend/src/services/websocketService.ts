export interface WebSocketMessage {
  type: 'new_message' | 'template_updated' | 'contact_updated' | 'stats_updated';
  message?: {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: string;
    phone_number: string;
    status?: 'sending' | 'sent' | 'delivered' | 'error';
  };
  data?: {
    template_id?: string;
    contact_phone?: string;
    action?: 'created' | 'updated' | 'deleted';
  };
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 2000;
  private onMessageCallback: ((message: WebSocketMessage) => void) | null = null;
  private connectionTimeout: number | null = null;
  private isConnecting = false;
  private isDisconnecting = false;
  private currentContact: string | null = null;

  connect() {
    // Si ya estamos conectados, no hacer nada
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('✅ Ya conectado al WebSocket general');
      return;
    }

    // Si estamos conectando, cancelar
    if (this.isConnecting) {
      console.log('⏳ Ya conectando, cancelando...');
      return;
    }

    // Limpiar timeout anterior
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }

    // Debounce para evitar reconexiones rápidas
    this.connectionTimeout = setTimeout(() => {
      this._connect();
    }, 300);
  }

  private _connect() {
    if (this.isConnecting) return;
    
    this.isConnecting = true;
    console.log('🔌 Iniciando conexión WebSocket general');

    // Si hay una conexión activa, cerrarla primero
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('🔄 Cerrando conexión anterior...');
      this.isDisconnecting = true;
      this.ws.close();
      
      // Esperar un poco antes de conectar la nueva
      setTimeout(() => {
        this._createConnection();
      }, 500);
    } else {
      this._createConnection();
    }
  }

  private _createConnection() {
    // Conectar al WebSocket general (sin número específico)
    this.ws = new WebSocket(`ws://localhost:8000/ws`);

    this.ws.onopen = () => {
      console.log('✅ WebSocket general conectado');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
      this.isDisconnecting = false;
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        // Manejar diferentes tipos de mensajes
        if (data.type === 'new_message' && data.message) {
          console.log('📨 Mensaje recibido para:', data.message.phone_number);
          
          // Solo procesar mensajes del contacto actual
          if (this.currentContact && data.message.phone_number === this.currentContact) {
            if (this.onMessageCallback) {
              this.onMessageCallback(data);
            }
          } else {
            console.log('📭 Mensaje ignorado - contacto diferente:', data.message.phone_number);
          }
        } else if (data.type === 'template_updated' || data.type === 'contact_updated' || data.type === 'stats_updated') {
          console.log('🔄 Actualización recibida:', data.type, data.data);
          // Procesar actualizaciones globales
          if (this.onMessageCallback) {
            this.onMessageCallback(data);
          }
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket desconectado:', event.code, event.reason);
      this.isConnecting = false;
      
      // Solo intentar reconectar si no fue una desconexión manual
      if (!this.isDisconnecting && event.code !== 1000) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this.isConnecting = false;
    };
  }

  private attemptReconnect() {
    if (this.isDisconnecting) {
      console.log('🛑 No reconectando - desconexión manual');
      return;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Intentando reconectar... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (!this.isDisconnecting) {
          this._connect();
        }
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.log('❌ Máximo número de intentos de reconexión alcanzado');
    }
  }

  // Cambiar contacto activo (sin reconectar)
  setCurrentContact(phoneNumber: string) {
    console.log('👤 Cambiando contacto activo a:', phoneNumber);
    this.currentContact = phoneNumber;
  }

  onMessage(callback: (message: WebSocketMessage) => void) {
    this.onMessageCallback = callback;
  }

  disconnect() {
    console.log('🛑 Desconectando WebSocket manualmente');
    this.isDisconnecting = true;
    this.currentContact = null;
    this.reconnectAttempts = 0;
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }
}

export const websocketService = new WebSocketService(); 