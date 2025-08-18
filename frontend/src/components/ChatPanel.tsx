import React, { useState, useEffect } from 'react';
import '../styles/ChatPanel.css';
import { messageService } from '../services/messageService';
import { websocketService } from '../services/websocketService';

interface Chat {
  id: string;
  name: string;
  phone: string;
  lastMessage?: string;
  lastMessageTime?: Date;
  unreadCount?: number;
  isOnline?: boolean;
}

interface ChatPanelProps {
  selectedChat: Chat | null;
  onSelectChat: (chat: Chat) => void;
  selectedChats: string[];
  onToggleSelection: (chatId: string) => void;
  multiSelect: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  selectedChat,
  onSelectChat,
  selectedChats,
  onToggleSelection,
  multiSelect,
}) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };

  // Cargar chats (solo contactos con mensajes)
  const fetchChats = async () => {
    try {
      setLoading(true);
      setError(null);
      const chatList = await messageService.getChatList();
      
      // Convertir datos del backend al formato esperado por el frontend
      const formattedChats = chatList.map((chat: any) => ({
        id: chat.phone,
        name: chat.name,
        phone: chat.phone,
        lastMessage: chat.lastMessage,
        lastMessageTime: chat.lastMessageTime ? new Date(chat.lastMessageTime) : undefined,
        lastMessageSender: chat.lastMessageSender,
        unreadCount: chat.unreadCount || 0,
        isOnline: chat.isOnline || false
      }));
      
      setChats(formattedChats);
    } catch (err) {
      setError('Error al cargar chats');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Cargar chats inicialmente
  useEffect(() => {
    fetchChats();
  }, []);

  // Configurar WebSocket para actualizaciones en tiempo real
  useEffect(() => {
    websocketService.connect();

    const removeListener = websocketService.onMessage((message) => {
      if (message.type === 'contact_updated') {
        console.log('🔄 Actualizando lista de chats por:', message.type);
        fetchChats();
      } else if (message.type === 'new_message' && message.message) {
        console.log('📨 Actualizando último mensaje en lista de chats para:', message.message.phone_number);
        
        // Verificación de seguridad de tipos
        const wsMessage = message.message;
        if (!wsMessage) return;
        
        // Actualizar solo el último mensaje del chat específico SIN refrescar toda la lista
        setChats(prevChats => {
          const updatedChats = prevChats.map(chat => {
            if (chat.phone === wsMessage.phone_number) {
              return {
                ...chat,
                lastMessage: wsMessage.text,
                lastMessageTime: new Date(wsMessage.timestamp),
                lastMessageSender: wsMessage.sender
              };
            }
            return chat;
          });
          
          // Reordenar para que el chat con mensaje más reciente esté arriba
          return updatedChats.sort((a, b) => {
            const timeA = a.lastMessageTime ? new Date(a.lastMessageTime).getTime() : 0;
            const timeB = b.lastMessageTime ? new Date(b.lastMessageTime).getTime() : 0;
            return timeB - timeA;
          });
        });
      }
    });

    return () => {
      removeListener();
    };
  }, []);



  if (loading) {
    return <div className="contacts-panel">Cargando chats...</div>;
  }

  if (error) {
    return <div className="contacts-panel" style={{ color: 'red' }}>Error: {error}</div>;
  }
  return (
    <div className="chat-panel">
      <div className="contacts-header">
        <h3>Chats</h3>
        {multiSelect && (
          <div className="selection-count">
            {selectedChats.length} seleccionados
          </div>
        )}
      </div>
      <div className="contacts-list">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`contact-item ${
              multiSelect && selectedChats.includes(chat.id)
                ? 'selected'
                : !multiSelect && selectedChat?.id === chat.id
                ? 'selected'
                : ''
            }`}
            onClick={() =>
              multiSelect
                ? onToggleSelection(chat.id)
                : onSelectChat(chat)
            }>
            <div className="contact-avatar">
              {chat.name.charAt(0).toUpperCase()}
            </div>
            <div className="contact-info">
              <div className="contact-name">{chat.name}</div>
              <div className="contact-phone">{formatPhoneNumber(chat.phone)}</div>
              {chat.lastMessage && (
                <div className="contact-last-message">
                  {chat.lastMessage}
                </div>
              )}
            </div>
            {chat.lastMessageTime && (
              <div className="contact-time">
                {chat.lastMessageTime.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatPanel;