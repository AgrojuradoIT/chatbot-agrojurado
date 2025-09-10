import React, { useState, useEffect } from 'react';
import '../styles/ChatPanel.css';
import { messageService } from '../services/messageService';
import { websocketService } from '../services/websocketService';
import { useContacts } from '../contexts/ContactContext';

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
  const { contacts, refreshContacts } = useContacts(); // Obtener contactos del contexto

  // Función para actualizar inmediatamente un contacto eliminado
  const updateDeletedContact = (phoneNumber: string) => {
    setChats(prevChats => {
      const updatedChats = prevChats.map(chat => {
        if (chat.phone === phoneNumber && chat.name !== 'Número Desconocido') {
          console.log('🔄 Actualizando contacto eliminado:', phoneNumber);
          return {
            ...chat,
            name: 'Número Desconocido', // Usar "Número Desconocido" cuando se elimina el contacto
            isOnline: false // Marcar como no activo
          };
        }
        return chat;
      });
      return updatedChats;
    });
  };

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

  // Sincronizar información de contactos con chats cuando cambien
  useEffect(() => {
    if (chats.length > 0) {
      setChats(prevChats => {
        const updatedChats = prevChats.map(chat => {
          const contact = contacts.find(c => c.phone_number === chat.phone);
          if (contact) {
            // Contacto existe, usar su información
            return {
              ...chat,
              name: contact.name,
              isOnline: contact.is_active
            };
          } else {
            // Contacto no existe (fue eliminado), usar "Número Desconocido"
            return {
              ...chat,
              name: 'Número Desconocido', // Usar "Número Desconocido" cuando no hay contacto registrado
              isOnline: false // Marcar como no activo
            };
          }
        });
        return updatedChats;
      });
    }
  }, [contacts]); // Se ejecuta solo cuando cambian los contactos



  // Configurar WebSocket para actualizaciones en tiempo real
  useEffect(() => {
    websocketService.connect();

    const removeListener = websocketService.onMessage((message) => {
      if (message.type === 'new_message' && message.message) {
        console.log('📨 Actualizando último mensaje en lista de chats para:', message.message.phone_number);
        
        // Verificación de seguridad de tipos
        const wsMessage = message.message;
        if (!wsMessage) return;
        
        // Verificar si el contacto existe en el contexto
        const contactExists = contacts.some(c => c.phone_number === wsMessage.phone_number);
        
        // Si el contacto no existe, podría ser un nuevo contacto creado automáticamente
        if (!contactExists) {
          console.log('🆕 Nuevo contacto detectado, actualizando lista de contactos:', wsMessage.phone_number);
          // Actualizar la lista de contactos para incluir el nuevo contacto
          refreshContacts();
        }
        
        // Actualizar o agregar el chat según corresponda
        setChats(prevChats => {
          const existingChatIndex = prevChats.findIndex(chat => chat.phone === wsMessage.phone_number);
          
          if (existingChatIndex >= 0) {
            // Chat existe, actualizar solo el último mensaje
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
          } else {
            // Chat no existe, agregarlo solo si tiene mensaje
            const newChat = {
              id: wsMessage.phone_number,
              name: wsMessage.phone_number, // Usar número como nombre temporal
              phone: wsMessage.phone_number,
              isOnline: false,
              lastMessage: wsMessage.text,
              lastMessageTime: new Date(wsMessage.timestamp),
              lastMessageSender: wsMessage.sender
            };
            
            // Agregar al inicio y reordenar
            const updatedChats = [newChat, ...prevChats];
            return updatedChats.sort((a, b) => {
              const timeA = a.lastMessageTime ? new Date(a.lastMessageTime).getTime() : 0;
              const timeB = b.lastMessageTime ? new Date(b.lastMessageTime).getTime() : 0;
              return timeB - timeA;
            });
          }
        });
      }
      
      // Manejar actualizaciones de contactos (nombre, estado activo, eliminación)
      if (message.type === 'contact_updated' && message.data) {
        console.log('👥 Actualizando información de contacto en lista de chats:', message.data);
        
        const { contact_phone, action } = message.data;
        
        if (action === 'deleted' && contact_phone) {
          // Cuando se elimina un contacto, actualizar inmediatamente
          console.log('🗑️ Contacto eliminado via WebSocket, actualizando chat:', contact_phone);
          updateDeletedContact(contact_phone);
        } else if (action === 'updated' || action === 'created') {
          // Actualizar información del contacto usando el contexto
          setChats(prevChats => {
            const updatedChats = prevChats.map(chat => {
              if (chat.phone === contact_phone) {
                // Buscar el contacto actualizado en el contexto
                const updatedContact = contacts.find(c => c.phone_number === contact_phone);
                if (updatedContact) {
                  return {
                    ...chat,
                    name: updatedContact.name,
                    isOnline: updatedContact.is_active
                  };
                }
              }
              return chat;
            });
            return updatedChats;
          });
        }
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