import { useState, useEffect } from 'react';
import './styles/App.css';
import ChatWindow from './components/ChatWindow';
import InputArea from './components/InputArea';
import ChatPanel from './components/ChatPanel';
import TemplatePanel from './components/TemplatePanel';
import ContactManager from './components/ContactManager';
import OperatorManager from './components/OperatorManager';
import StatisticsDashboard from './components/StatisticsDashboard';
import ReceiptsPanel from './components/ReceiptsPanel';
import LoginPage from './components/LoginPage';
import AuthCallback from './components/AuthCallback';
import { messageService } from './services/messageService';
import { websocketService, type WebSocketMessage } from './services/websocketService';
import { ContactProvider } from './contexts/ContactContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider, useNotifications } from './components/NotificationContainer';
import { ReceiptOperationProvider } from './contexts/ReceiptOperationContext';
import { ProtectedComponent } from './components/ProtectedComponent';
import { useConfirm } from './hooks/useConfirm';
import ConfirmDialog from './components/ConfirmDialog';
import Loader from './components/Loader';
import GlobalOperationIndicator from './components/GlobalOperationIndicator';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  status?: 'sending' | 'sent' | 'delivered' | 'error';
}

interface Chat {
  id: string;
  name: string;
  phone: string;
  lastMessage?: string;
  lastMessageTime?: Date;
  unreadCount?: number;
  isOnline?: boolean;
}

// Componente principal del dashboard (protegido)
function Dashboard() {
  const { user, logout, isLoggingOut } = useAuth();
  const { confirm, confirmDialog } = useConfirm();
  const { showNotification } = useNotifications();
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [selectedChats, setSelectedChats] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'templates' | 'contacts' | 'operators' | 'statistics' | 'comprobantes'>('chat');

  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [hasMoreOlder, setHasMoreOlder] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Cache de mensajes por contacto
  const [messageCache, setMessageCache] = useState<Record<string, {
    messages: Message[];
    hasMore: boolean;
    lastLoaded: Date;
  }>>({});

  // Configurar WebSocket listener global para manejar mensajes
  useEffect(() => {
    websocketService.connect();
    
    const removeListener = websocketService.onMessage((wsMessage: WebSocketMessage) => {
      if (wsMessage.message && wsMessage.type === 'new_message') {
        const messagePhoneNumber = wsMessage.message.phone_number;
        
        console.log('📨 Mensaje recibido de:', messagePhoneNumber, 'Chat actual:', selectedChat?.phone);
        
        const newMessage: Message = {
          id: wsMessage.message.id || `ws_${Date.now()}`,
          text: wsMessage.message.text,
          sender: wsMessage.message.sender === 'user' ? 'bot' : 'user',
          timestamp: new Date(wsMessage.message.timestamp || Date.now()),
          status: wsMessage.message.status || 'sent' // Agregar status para mensajes nuevos
        };
        
        // 1. SIEMPRE actualizar el caché si existe
        if (messageCache[messagePhoneNumber]) {
          const currentCache = messageCache[messagePhoneNumber];
          const exists = currentCache.messages.some(msg => msg.id === newMessage.id);
          
          if (!exists) {
            console.log('📝 Actualizando caché para:', messagePhoneNumber);
            const updatedCacheMessages = [...currentCache.messages, newMessage];
            setCachedMessages(messagePhoneNumber, updatedCacheMessages, currentCache.hasMore);
          }
        }
        
        // 2. Si es el chat actual, también actualizar la vista
        if (selectedChat && messagePhoneNumber === selectedChat.phone) {
          console.log('✅ Actualizando vista del chat actual');
          setMessages(prev => {
            const exists = prev.some(msg => msg.id === newMessage.id);
            if (exists) {
              console.log('⚠️ Mensaje duplicado ignorado en vista');
              return prev;
            }
            return [...prev, newMessage];
          });
          
          // Auto-scroll si está cerca del final
          setTimeout(() => {
            if (isNearBottom()) {
              scrollToBottom();
            }
          }, 50);
        }
      }
      
      // Manejar actualizaciones de contactos
      if (wsMessage.type === 'contact_updated') {
        console.log('👥 Contacto actualizado:', wsMessage.data?.contact_phone, 'Acción:', wsMessage.data?.action);
        // El contexto de contactos se encargará de actualizar automáticamente
      }
    });

    return () => {
      removeListener();
      websocketService.disconnect();
    };
  }, [selectedChat?.phone, messageCache]); // Dependencias necesarias

  // Scroll automático solo cuando se selecciona un nuevo chat
  useEffect(() => {
    if (selectedChat && !isLoadingMessages) {
      // Solo hacer scroll automático cuando se selecciona un chat nuevo
      // NO cuando llegan mensajes nuevos (eso se maneja en el WebSocket listener)
      requestAnimationFrame(() => {
        setTimeout(() => {
          scrollToBottom();
        }, 50);
      });
    }
  }, [selectedChat?.id]); // Solo cuando cambia el chat seleccionado

  const handleSendMessage = async (text: string) => {
    if (!selectedChat) {
      console.error('No hay chat seleccionado');
      return;
    }

    // Crear ID único para el mensaje
    const messageId = `user_${selectedChat.phone}_${Date.now()}`;
    
    // Agregar mensaje del usuario inmediatamente (optimistic update)
    const newMessage: Message = {
      id: messageId,
      text,
      sender: 'user', // Este es el mensaje que TÚ envías
      timestamp: new Date(),
      status: 'sending' // Estado inicial: enviando
    };
    
    console.log(' Enviando mensaje:', messageId);
    setMessages(prev => [...prev, newMessage]);

    try {
      // Enviar mensaje real a WhatsApp
      const success = await messageService.sendMessage(selectedChat.phone, text);
      
      if (!success) {
        // Actualizar estado a error
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, status: 'error' as const }
            : msg
        ));
        
        // Mostrar notificación de error usando el sistema de notificaciones
        showNotification({
          type: 'error',
          title: 'Error al Enviar',
          message: 'No se pudo enviar el mensaje. Intenta nuevamente.'
        });
      } else {
        // Actualizar estado a enviado
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, status: 'sent' as const }
            : msg
        ));
        console.log(' Mensaje enviado exitosamente:', messageId);
      }
      // Si es exitoso, el WebSocket se encargará de mostrar el mensaje confirmado
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      
      // Actualizar estado a error
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, status: 'error' as const }
          : msg
      ));
      
      // Mostrar notificación de error usando el sistema de notificaciones
      showNotification({
        type: 'error',
        title: 'Error al Enviar',
        message: 'No se pudo enviar el mensaje. Intenta nuevamente.'
      });
    }
  };

  const getCachedMessages = (phoneNumber: string) => {
    return messageCache[phoneNumber]?.messages || [];
  };

  const scrollToBottom = () => {
    const chatContainer = document.querySelector('.infinite-scroll-container');
    if (chatContainer) {
      console.log(' Haciendo scroll al final');
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  };

  const isNearBottom = () => {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainer;
      return scrollHeight - scrollTop - clientHeight < 100;
    }
    return true;
  };

  const setCachedMessages = (phoneNumber: string, messages: Message[], hasMore: boolean) => {
    setMessageCache(prev => ({
      ...prev,
      [phoneNumber]: {
        messages,
        hasMore,
        lastLoaded: new Date()
      }
    }));
  };

  const handleSelectChat = async (chat: Chat) => {
    console.log(' Seleccionando chat:', chat.name, chat.phone);
    
    // Actualizar chat seleccionado
    setSelectedChat(chat);
    
    // Verificar si hay mensajes en caché
    const cachedMessages = getCachedMessages(chat.phone);
    
    if (cachedMessages.length > 0) {
      console.log(' Usando mensajes en caché:', cachedMessages.length);
      setMessages(cachedMessages);
      setHasMoreOlder(messageCache[chat.phone]?.hasMore || false);
      
      // Scroll al final será manejado por useEffect cuando cambien los mensajes
      
      return;
    }
    
    // Si no hay caché, cargar mensajes
    setIsLoadingMessages(true);
    // Limpiar mensajes del chat anterior para evitar confusión
    setMessages([]);
    setHasMoreOlder(false);
    
    try {
      console.log(' Cargando mensajes para:', chat.phone);
      
      const response = await messageService.getMessages(chat.phone, 1, 50);
      
      if (response && response.messages) {
        console.log(' Mensajes cargados:', response.messages.length);
        
        const formattedMessages = response.messages.map(msg => ({
          id: msg.id,
          text: msg.text,
          sender: (msg.sender === 'user' ? 'bot' : 'user') as 'user' | 'bot',
          timestamp: new Date(msg.timestamp),
          status: msg.status || 'sent' // Agregar status, por defecto 'sent' para mensajes existentes
        }));
        
        // El backend ya envía los mensajes en orden cronológico correcto (antiguos primero, recientes después)
        const sortedMessages = formattedMessages;
        
        // Limpiar mensajes anteriores y establecer los nuevos
        setMessages(sortedMessages);
        setHasMoreOlder(response.pagination.has_next);
        
        // Guardar en caché
        setCachedMessages(chat.phone, sortedMessages, response.pagination.has_next);
        
        // Conectar WebSocket
        websocketService.connect();
        
        // Scroll al final será manejado por useEffect cuando cambien los mensajes
        
      } else {
        console.log(' No se pudieron cargar los mensajes');
        setMessages([]);
        setHasMoreOlder(false);
      }
    } catch (error) {
      console.error(' Error cargando mensajes:', error);
      setMessages([]);
      setHasMoreOlder(false);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const handleToggleChatSelection = (chatId: string) => {
    setSelectedChats(prev => 
      prev.includes(chatId) 
        ? prev.filter(id => id !== chatId)
        : [...prev, chatId]
    );
  };

  const handleSendTemplate = (templateId: string, contactIds: string[]) => {
    // Implementar envío de plantilla
    console.log('Enviando plantilla:', templateId, 'a contactos:', contactIds);
  };

  const handleContactUpdate = () => {
    // Esta función se llama cuando se crean/actualizan/eliminan contactos manualmente
    // El WebSocket se encargará de las actualizaciones automáticas
    console.log('Contactos actualizados manualmente');
  };

  const handleSelectContactFromManager = (contact: any) => {
    const chat: Chat = {
      id: contact.phone_number,
      name: contact.name || contact.phone_number,
      phone: contact.phone_number,
      lastMessage: contact.last_message,
      lastMessageTime: contact.last_interaction ? new Date(contact.last_interaction) : undefined,
      isOnline: contact.is_active
    };
    
    handleSelectChat(chat);
    setActiveTab('chat');
  };

  const handleLoadMore = async () => {
    if (!selectedChat || isLoadingMore || !hasMoreOlder) {
      return;
    }
    
    console.log(' Cargando más mensajes antiguos...');
    setIsLoadingMore(true);
    
    try {
      const currentPage = Math.floor(messages.length / 50) + 1;
      const response = await messageService.getMessages(selectedChat.phone, currentPage + 1, 50);
      
      if (!response || !response.messages) {
        console.log(' No hay más mensajes para cargar');
        setHasMoreOlder(false);
        return;
      }
      
      const formattedMessages = response.messages.map(msg => ({
        id: msg.id,
        text: msg.text,
        sender: (msg.sender === 'user' ? 'bot' : 'user') as 'user' | 'bot',
        timestamp: new Date(msg.timestamp)
      }));
      
      // El backend ya envía los mensajes en orden cronológico correcto
      const sortedOlderMessages = formattedMessages;
      
      console.log('Mensajes más antiguos cargados:', sortedOlderMessages.length);
      
      // Agregar mensajes antiguos al inicio, evitando duplicados
      const existingIds = new Set(messages.map(msg => msg.id));
      const newMessages = sortedOlderMessages.filter(msg => !existingIds.has(msg.id));
      const updatedMessages = [...newMessages, ...messages];
      
      console.log(` Agregando ${newMessages.length} mensajes nuevos de ${formattedMessages.length} cargados`);
      
      setMessages(updatedMessages);
      setHasMoreOlder(response.pagination.has_next);
      
      // Actualizar cache
      if (selectedChat) {
        setCachedMessages(selectedChat.phone, updatedMessages, response.pagination.has_next);
      }
      
      console.log(' Mensajes antiguos cargados, posición mantenida');
    } catch (error) {
      console.error(' Error al cargar más mensajes:', error);
      // Si hay error, asumir que no hay más mensajes
      setHasMoreOlder(false);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleLogout = async () => {
    const confirmed = await confirm({
      title: 'Cerrar Sesión',
      message: '¿Estás seguro de que quieres cerrar tu sesión? Tendrás que volver a iniciar sesión para acceder al sistema.',
      confirmText: 'Cerrar Sesión',
      cancelText: 'Cancelar',
      type: 'logout'
    });

    if (confirmed) {
    logout();
    }
  };

  return (
    <ContactProvider>
      <div className="App">
        {/* Indicador global de operación */}
        <GlobalOperationIndicator />
        
        <div className="tab-navigation">
          <div className="app-title">
            <h1>Chatbot Agrojurado</h1>
          </div>
          
          <div className="tab-buttons">
            <ProtectedComponent permissions={['chatbot.messages.view', 'chatbot.messages.send.individual', 'chatbot.messages.send.massive']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
              >
                CHAT
              </button>
            </ProtectedComponent>
            <ProtectedComponent permissions={['chatbot.templates.create', 'chatbot.templates.edit', 'chatbot.templates.delete', 'chatbot.templates.use']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
                onClick={() => setActiveTab('templates')}
              >
                PLANTILLAS
              </button>
            </ProtectedComponent>
            <ProtectedComponent permissions={['chatbot.contacts.view', 'chatbot.contacts.manage']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'contacts' ? 'active' : ''}`}
                onClick={() => setActiveTab('contacts')}
              >
                CONTACTOS
              </button>
            </ProtectedComponent>
            <ProtectedComponent permissions={['chatbot.operators.view', 'chatbot.operators.manage']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'operators' ? 'active' : ''}`}
                onClick={() => setActiveTab('operators')}
              >
                OPERARIOS
              </button>
            </ProtectedComponent>
            <ProtectedComponent permissions={['chatbot.statistics.view', 'chatbot.statistics.manage']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'statistics' ? 'active' : ''}`}
                onClick={() => setActiveTab('statistics')}
              >
                ESTADÍSTICAS
              </button>
            </ProtectedComponent>
            <ProtectedComponent permissions={['chatbot.comprobantes.view', 'chatbot.comprobantes.manage']} hideWhenNoAccess={true}>
              <button 
                className={`tab-btn ${activeTab === 'comprobantes' ? 'active' : ''}`}
                onClick={() => setActiveTab('comprobantes')}
              >
                COMPROBANTES
              </button>
            </ProtectedComponent>
          </div>
          
          <div className="header-actions">
            <div className="user-info">
              <div className="user-details">
                <div className="user-avatar">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                  </svg>
                </div>
                <span className="user-name">{user?.name}</span>
                <button 
                  className="logout-icon-btn" 
                  onClick={handleLogout} 
                  title="Cerrar Sesión"
                  disabled={isLoggingOut}
                >
                  {isLoggingOut ? (
                    <Loader size={14} color="#8696a0" />
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="currentColor"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>
            
            <button 
              className="mobile-menu-btn"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Menú de navegación"
            >
              <div className={`hamburger ${isMobileMenuOpen ? 'active' : ''}`}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </button>
          </div>
          
                      {/* Menú móvil */}
            <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
              <div className="mobile-menu-content">
              <div className="mobile-user-info">
                <div className="mobile-user-details">
                  <div className="mobile-user-avatar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                    </svg>
                  </div>
                  <span className="mobile-user-name">{user?.name}</span>
                </div>
              </div>
              
              <div className="mobile-menu-separator"></div>
              
              <ProtectedComponent permissions={['chatbot.messages.view', 'chatbot.messages.send.individual', 'chatbot.messages.send.massive']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('chat');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  CHAT
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.templates.create', 'chatbot.templates.edit', 'chatbot.templates.delete', 'chatbot.templates.use']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('templates');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  PLANTILLAS
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.contacts.view', 'chatbot.contacts.manage']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'contacts' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('contacts');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  CONTACTOS
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.operators.view', 'chatbot.operators.manage']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'operators' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('operators');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  OPERARIOS
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.statistics.view', 'chatbot.statistics.manage']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'statistics' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('statistics');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  ESTADÍSTICAS
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.comprobantes.view', 'chatbot.comprobantes.manage']} hideWhenNoAccess={true}>
                <button 
                  className={`mobile-tab-btn ${activeTab === 'comprobantes' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('comprobantes');
                    setIsMobileMenuOpen(false);
                  }}
                >
                  COMPROBANTES
                </button>
              </ProtectedComponent>
              
              <button 
                className="mobile-logout-btn"
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  handleLogout();
                }}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? (
                  <>
                    <Loader size={14} color="#ffffff" />
                    <span>Cerrando Sesión...</span>
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="currentColor"/>
                    </svg>
                    <span>Cerrar Sesión</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
        <div className="App-content">
          {/* Panel de chats siempre visible excepto en estadísticas, operarios y comprobantes */}
          {activeTab !== 'statistics' && activeTab !== 'operators' && activeTab !== 'comprobantes' && (
            <ChatPanel
              selectedChat={selectedChat}
              onSelectChat={handleSelectChat}
              selectedChats={selectedChats}
              onToggleSelection={handleToggleChatSelection}
              multiSelect={false}
            />
          )}
          
          {/* Chat y área de entrada siempre visible excepto en estadísticas, operarios y comprobantes */}
          {activeTab !== 'statistics' && activeTab !== 'operators' && activeTab !== 'comprobantes' && (
            <div className="chat-section">
              {selectedChat ? (
                <>
                  <ChatWindow 
                    messages={messages} 
                    isLoading={isLoadingMessages}
                    onLoadMore={handleLoadMore}
                    hasMore={hasMoreOlder}
                    isLoadingMore={isLoadingMore}
                    selectedChat={selectedChat}
                  />
                  <ProtectedComponent permissions={['chatbot.messages.send.individual']} fallback={<div className="no-permission-input">No tienes permisos para enviar mensajes</div>}>
                    <InputArea onSendMessage={handleSendMessage} />
                  </ProtectedComponent>
                </>
              ) : (
                <div className="no-chat-selected">
                  <div className="no-chat-content">
                    <div className="no-chat-icon">
                      <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#00a884" fillOpacity="0.1"/>
                        <path d="M12 8v8m-4-4h8" stroke="#00a884" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <h2>Inicia una conversación</h2>
                    <p>Selecciona un chat, plantilla o contacto de la lista para empezar.</p>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Paneles adicionales según la pestaña activa */}
          {activeTab === 'templates' && (
            <ProtectedComponent permissions={['chatbot.templates.create', 'chatbot.templates.edit', 'chatbot.templates.delete', 'chatbot.templates.use']} fallback={<div className="no-permission">No tienes permisos para acceder a las plantillas</div>}>
              <TemplatePanel
                onSendTemplate={handleSendTemplate}
              />
            </ProtectedComponent>
          )}
          
          {activeTab === 'contacts' && (
            <ProtectedComponent permissions={['chatbot.contacts.view', 'chatbot.contacts.manage']} fallback={<div className="no-permission">No tienes permisos para acceder a los contactos</div>}>
              <ContactManager
                onContactUpdate={handleContactUpdate}
                onSelectChat={handleSelectContactFromManager}
              />
            </ProtectedComponent>
          )}
          
          {activeTab === 'operators' && (
            <ProtectedComponent permissions={['chatbot.operators.view', 'chatbot.operators.manage']} fallback={<div className="no-permission">No tienes permisos para acceder a los operarios</div>}>
              <OperatorManager
                onOperatorUpdate={handleContactUpdate}
              />
            </ProtectedComponent>
          )}
          
          {activeTab === 'statistics' && (
            <ProtectedComponent permissions={['chatbot.statistics.view', 'chatbot.statistics.manage']} fallback={<div className="no-permission">No tienes permisos para acceder a las estadísticas</div>}>
              <StatisticsDashboard
                isVisible={true}
              />
            </ProtectedComponent>
          )}
          
          {activeTab === 'comprobantes' && (
            <ProtectedComponent permissions={['chatbot.comprobantes.view', 'chatbot.comprobantes.manage']} fallback={<div className="no-permission">No tienes permisos para acceder a los comprobantes</div>}>
              <ReceiptsPanel
                onClose={() => setActiveTab('chat')}
              />
            </ProtectedComponent>
          )}
        </div>
        
        {/* Diálogo de confirmación */}
        {confirmDialog && (
          <ConfirmDialog
            isOpen={confirmDialog.isOpen}
            title={confirmDialog.title}
            message={confirmDialog.message}
            confirmText={confirmDialog.confirmText}
            cancelText={confirmDialog.cancelText}
            type={confirmDialog.type}
            onConfirm={confirmDialog.onConfirm}
            onCancel={confirmDialog.onCancel}
          />
        )}
      </div>
    </ContactProvider>
  );
}

// Componente principal de la aplicación
function App() {
  const isCallback = window.location.pathname === '/auth/callback';
  
  if (isCallback) {
    return (
      <AuthProvider>
        <AuthCallback />
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <NotificationProvider>
        <ReceiptOperationProvider>
          <AppContent />
        </ReceiptOperationProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}

// Componente que maneja el estado de autenticación
function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-content">
          <div className="loading-logo"></div>
          <h2 className="loading-title">Chatbot Agrojurado</h2>
          <Loader size={50} />
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <Dashboard />;
}

export default App
