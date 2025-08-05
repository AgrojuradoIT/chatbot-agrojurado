import React, { useState, useEffect } from 'react';
import './ChatPanel.css';
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
  const { contacts, loading, error } = useContacts();
  const [chats, setChats] = useState<Chat[]>([]);

  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };

  // Convertir contactos a chats cuando cambien
  useEffect(() => {
    if (contacts) {
      setChats(contacts.map((contact: any) => ({ 
        id: contact.phone_number, 
        name: contact.name || 'Sin nombre', 
        phone: contact.phone_number,
        lastMessage: contact.last_interaction ? 'Última interacción: ' + new Date(contact.last_interaction).toLocaleDateString() : undefined,
        lastMessageTime: contact.last_interaction ? new Date(contact.last_interaction) : undefined,
        unreadCount: 0,
        isOnline: false
      })));
    }
  }, [contacts]);



  if (loading) {
    return <div className="contacts-panel">Cargando contactos...</div>;
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