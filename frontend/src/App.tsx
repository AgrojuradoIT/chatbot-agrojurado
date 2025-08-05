import { useState, useEffect } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';
import InputArea from './components/InputArea';
import ChatPanel from './components/ChatPanel';
import TemplatePanel from './components/TemplatePanel';
import ContactManager from './components/ContactManager';
import StatisticsDashboard from './components/StatisticsDashboard';
import { messageService } from './services/messageService';
import { websocketService } from './services/websocketService';
import { ContactProvider } from './contexts/ContactContext';

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

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [selectedChats, setSelectedChats] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'templates' | 'contacts' | 'statistics'>('chat');

  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [hasMoreOlder, setHasMoreOlder] = useState(true);


  
  // Cache de mensajes por contacto
  const [messageCache, setMessageCache] = useState<Record<string, {
    messages: Message[];
    hasMore: boolean;
    lastLoaded: Date;
  }>>({});

  // Limpiar WebSocket cuando el componente se desmonte
  useEffect(() => {
    return () => {
      websocketService.disconnect();
    };
  }, []);

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
    
    console.log('📤 Enviando mensaje:', messageId);
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
        
        // Mostrar mensaje de error
        const errorMessage: Message = {
          id: `error_${Date.now()}`,
          text: 'Error al enviar el mensaje. Intenta nuevamente.',
          sender: 'bot',
          timestamp: new Date(),
          status: 'error'
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        // Actualizar estado a enviado
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, status: 'sent' as const }
            : msg
        ));
        console.log('✅ Mensaje enviado exitosamente:', messageId);
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
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        text: 'Error al enviar el mensaje. Intenta nuevamente.',
        sender: 'bot',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const getCachedMessages = (phoneNumber: string) => {
    return messageCache[phoneNumber];
  };



  const scrollToBottom = () => {
    const container = document.querySelector('.infinite-scroll-container');
    if (container) {
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
        console.log('📜 Scroll al final ejecutado');
      });
    }
  };

  const isNearTop = () => {
    const container = document.querySelector('.infinite-scroll-container');
    if (container) {
      return container.scrollTop < 200;
    }
    return false;
  };

  const isNearBottom = () => {
    const container = document.querySelector('.infinite-scroll-container');
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container as HTMLElement;
      return scrollTop + clientHeight >= scrollHeight - 100;
    }
    return true;
  };

  const setCachedMessages = (phoneNumber: string, messages: Message[], hasMore: boolean) => {
    setMessageCache(prev => {
      // Limpiar cache antiguo (más de 1 hora)
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
      const cleanedCache = Object.fromEntries(
        Object.entries(prev).filter(([_, data]) => 
          data.lastLoaded > oneHourAgo
        )
      );
      
      // Eliminar duplicados antes de guardar
      const uniqueMessages = messages.filter((message, index, self) => 
        index === self.findIndex(m => m.id === message.id)
      );
      
      return {
        ...cleanedCache,
        [phoneNumber]: {
          messages: uniqueMessages,
          hasMore,
          lastLoaded: new Date()
        }
      };
    });
  };

  const handleSelectChat = async (chat: Chat) => {
    console.log('👤 Chat seleccionado:', chat.name, chat.phone);
    setSelectedChat(chat);
    
    
    // Conectar al WebSocket general si no está conectado
    websocketService.connect();
    
    // Cambiar el chat activo en el WebSocket
    websocketService.setCurrentContact(chat.phone);
    
    // Verificar si hay mensajes en cache
    const cached = getCachedMessages(chat.phone);
    
    if (cached && cached.messages.length > 0) {
      // Usar mensajes del cache
      console.log('📦 Usando mensajes del cache para:', chat.phone, 'Total:', cached.messages.length);
      
      // Verificar duplicados en cache
      const uniqueCachedMessages = cached.messages.filter((message, index, self) => 
        index === self.findIndex(m => m.id === message.id)
      );
      
      if (uniqueCachedMessages.length !== cached.messages.length) {
        console.log('⚠️ Duplicados encontrados en cache, limpiando...');
        setCachedMessages(chat.phone, uniqueCachedMessages, cached.hasMore);
      }
      
              setMessages(uniqueCachedMessages);
      setHasMoreOlder(cached.hasMore);
      
      // Hacer scroll al final después de cargar desde cache
      scrollToBottom();
      console.log('✅ Mensajes cargados desde cache y scroll al final');
          } else {
        // Cargar mensajes del servidor
        console.log('🔄 Cargando mensajes del servidor para:', chat.phone);
      setMessages([]); // Limpiar mensajes para resetear el scroll
      setHasMoreOlder(false); // Resetear estado de carga
    }
    
    // Configurar callback para nuevos mensajes
    websocketService.onMessage((data) => {
      if (data.type === 'new_message' && data.message) {
        console.log('📨 Nuevo mensaje recibido:', data.message.text.substring(0, 50) + '...');
        const newMessage: Message = {
          id: data.message.id,
          text: data.message.text,
          sender: (data.message.sender === 'user' ? 'bot' : 'user') as 'user' | 'bot',
          timestamp: new Date(data.message.timestamp),
          // Corregir estados:
          // - Mensajes de 'user' (recibidos) = sin estado (undefined)
          // - Mensajes de 'bot' (enviados) = usar el status real
          status: data.message.sender === 'user' ? undefined : (data.message.status as 'sending' | 'sent' | 'delivered' | 'error')
        };
        
        setMessages(prev => {
          // Evitar duplicados - verificar por ID y también por contenido + timestamp
          const isDuplicate = prev.some(msg => 
            msg.id === newMessage.id || 
            (msg.text === newMessage.text && 
             Math.abs(msg.timestamp.getTime() - newMessage.timestamp.getTime()) < 5000) // 5 segundos de tolerancia
          );
          
          if (isDuplicate) {
            console.log('🚫 Mensaje duplicado ignorado:', newMessage.id);
            return prev;
          }
          
          console.log('✅ Agregando mensaje nuevo:', newMessage.id);
          const updatedMessages = [...prev, newMessage];
          
          // Actualizar cache
          if (selectedChat) {
            setCachedMessages(selectedChat.phone, updatedMessages, hasMoreOlder);
          }
          
          // Solo hacer scroll si estamos cerca del final
          if (isNearBottom()) {
            requestAnimationFrame(() => {
              scrollToBottom();
            });
          }
          
          return updatedMessages;
        });
        

      }
    });
    
    // Cargar mensajes recientes para este contacto
    try {
      setIsLoadingMessages(true);
      const recentMessages = await messageService.getRecentMessages(chat.phone, 50); // Cargar los 50 más recientes
      const formattedMessages = recentMessages.map(msg => ({
        id: msg.id,
        text: msg.text,
        // Corregir la perspectiva: 
        // - Mensajes de 'user' (WhatsApp) = recibidos (bot)
        // - Mensajes de 'bot' (tú) = enviados (user)
        sender: (msg.sender === 'user' ? 'bot' : 'user') as 'user' | 'bot',
        timestamp: new Date(msg.timestamp),
        // Corregir estados:
        // - Mensajes de 'user' (recibidos) = sin estado (undefined)
        // - Mensajes de 'bot' (enviados) = usar el status real
        status: msg.sender === 'user' ? undefined : (msg.status as 'sending' | 'sent' | 'delivered' | 'error')
      }));
      // Eliminar duplicados antes de establecer
      const uniqueMessages = formattedMessages.filter((message, index, self) => 
        index === self.findIndex(m => m.id === message.id)
      );
      
      setMessages(uniqueMessages);
      
      // Verificar si hay más mensajes antiguos disponibles
      const hasMore = uniqueMessages.length >= 50; // Si hay 50+ mensajes, probablemente hay más
      setHasMoreOlder(hasMore);
      
      // Guardar en cache
      setCachedMessages(chat.phone, uniqueMessages, hasMore);
      
      // Si no hay mensajes, mostrar chat vacío
      if (uniqueMessages.length === 0) {
        console.log('📝 No hay mensajes, mostrando chat vacío');
        setMessages([]);
        setHasMoreOlder(false);
        setCachedMessages(chat.phone, [], false);
      }
      

      
      // Hacer scroll al final después de cargar del servidor (solo si no estamos cerca del inicio)
      if (!isNearTop()) {
        scrollToBottom();
      }
    } catch (error) {
      console.error('Error al cargar mensajes:', error);
      const errorMessage = {
        id: 'error',
        text: 'Error al cargar el historial de mensajes. Intenta nuevamente.',
        sender: 'bot' as const,
        timestamp: new Date(),
      };
      setMessages([errorMessage]);
    } finally {
      setIsLoadingMessages(false);

    }
  };

  const handleToggleChatSelection = (chatId: string) => {
    setSelectedChats((prev) =>
      prev.includes(chatId)
        ? prev.filter((id) => id !== chatId)
        : [...prev, chatId]
    );
  };



  const handleSendTemplate = async (templateId: string, contactIds: string[]) => {
    console.log(`Enviando plantilla ${templateId} a ${contactIds.length} contactos`);
    // El WebSocket se encargará de mostrar los mensajes de plantilla automáticamente
  };

  const handleContactUpdate = () => {
    // Recargar la lista de contactos cuando se actualice
    console.log('Contactos actualizados');
  };

  const handleSelectContactFromManager = (contact: any) => {
    // Convertir el contacto del ContactManager a formato Chat
    const chat: Chat = {
      id: contact.phone_number,
      name: contact.name,
      phone: contact.phone_number,
      lastMessage: contact.last_interaction || undefined,
      lastMessageTime: contact.last_interaction ? new Date(contact.last_interaction) : undefined,
      unreadCount: 0,
      isOnline: contact.is_active
    };
    
    // Seleccionar el chat
    handleSelectChat(chat);
    
    // Cambiar a la pestaña de chat
    setActiveTab('chat');
  };

  const handleLoadMore = async () => {
    console.log('🚀 handleLoadMore llamado');
    
    if (!selectedChat || isLoadingMore || !hasMoreOlder) {
      console.log('❌ No se puede cargar más mensajes:', { 
        hasChat: !!selectedChat, 
        isLoading: isLoadingMore, 
        hasMoreOlder 
      });
      return;
    }
    
    try {
      setIsLoadingMore(true);
      
      // Obtener el timestamp del mensaje más antiguo actual
      const oldestMessage = messages[0];
      if (!oldestMessage) {
        console.log('📭 No hay mensajes para cargar más antiguos');
        setHasMoreOlder(false);
        return;
      }
      
      console.log('Cargando mensajes más antiguos que:', oldestMessage.timestamp.toISOString());
      
      const response = await messageService.getOlderMessages(
        selectedChat.phone, 
        oldestMessage.timestamp.toISOString(), 
        50
      );
      
      const formattedMessages = response.messages.map(msg => ({
        id: msg.id,
        text: msg.text,
        sender: (msg.sender === 'user' ? 'bot' : 'user') as 'user' | 'bot',
        timestamp: new Date(msg.timestamp)
      }));
      
      console.log('Mensajes más antiguos cargados:', formattedMessages.length);
      
      // Agregar mensajes antiguos al inicio, evitando duplicados
      const existingIds = new Set(messages.map(msg => msg.id));
      const newMessages = formattedMessages.filter(msg => !existingIds.has(msg.id));
      const updatedMessages = [...newMessages, ...messages];
      
      console.log(`📚 Agregando ${newMessages.length} mensajes nuevos de ${formattedMessages.length} cargados`);
      
      setMessages(updatedMessages);
      setHasMoreOlder(response.hasMore);
      
      // Actualizar cache
      if (selectedChat) {
        setCachedMessages(selectedChat.phone, updatedMessages, response.hasMore);
      }
      
      console.log('📚 Mensajes antiguos cargados, posición mantenida');
    } catch (error) {
      console.error('❌ Error al cargar más mensajes:', error);
      // Si hay error, asumir que no hay más mensajes
      setHasMoreOlder(false);
    } finally {
      setIsLoadingMore(false);
    }
  };

  return (
    <ContactProvider>
      <div className="App">
        <div className="tab-navigation">
          <div className="app-title">
            <h1>Chatbot Agrojurado</h1>
          </div>
          <div className="tab-buttons">
            <button 
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              CHAT
            </button>
            <button 
              className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
              onClick={() => setActiveTab('templates')}
            >
              PLANTILLAS
            </button>
            <button 
              className={`tab-btn ${activeTab === 'contacts' ? 'active' : ''}`}
              onClick={() => setActiveTab('contacts')}
            >
              CONTACTOS
            </button>
            <button 
              className={`tab-btn ${activeTab === 'statistics' ? 'active' : ''}`}
              onClick={() => setActiveTab('statistics')}
            >
              ESTADÍSTICAS
            </button>
          </div>
        </div>
        <div className="App-content">
          {/* Panel de chats siempre visible excepto en estadísticas */}
          {activeTab !== 'statistics' && (
            <ChatPanel
              selectedChat={selectedChat}
              onSelectChat={handleSelectChat}
              selectedChats={selectedChats}
              onToggleSelection={handleToggleChatSelection}
              multiSelect={false}
            />
          )}
          
          {/* Chat y área de entrada siempre visible excepto en estadísticas */}
          {activeTab !== 'statistics' && (
            <div className="chat-section">
              <ChatWindow 
                messages={messages} 
                isLoading={isLoadingMessages}
                onLoadMore={handleLoadMore}
                hasMore={hasMoreOlder}
                isLoadingMore={isLoadingMore}
                selectedChat={selectedChat}
              />
              <InputArea onSendMessage={handleSendMessage} />
            </div>
          )}
          
          {/* Paneles adicionales según la pestaña activa */}
          {activeTab === 'templates' && (
            <TemplatePanel
              onSendTemplate={handleSendTemplate}
            />
          )}
          
          {activeTab === 'contacts' && (
            <ContactManager
              onContactUpdate={handleContactUpdate}
              onSelectChat={handleSelectContactFromManager}
            />
          )}
          
          {activeTab === 'statistics' && (
            <StatisticsDashboard
              isVisible={true}
            />
          )}
        </div>
      </div>
    </ContactProvider>
  );
}

export default App
