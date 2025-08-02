import React, { useState, useEffect } from 'react';
import './ContactsPanel.css';

interface Chat {
  id: string;
  name: string;
  phone: string;
  lastMessage?: string;
  lastMessageTime?: Date;
  unreadCount?: number;
  isOnline?: boolean;
}

interface ContactsPanelProps {
  selectedChat: Chat | null;
  onSelectChat: (chat: Chat) => void;
  selectedChats: string[];
  onToggleSelection: (chatId: string) => void;
  multiSelect: boolean;
  refreshTrigger?: number;
}

const ContactsPanel: React.FC<ContactsPanelProps> = ({
  selectedChat,
  onSelectChat,
  selectedChats,
  onToggleSelection,
  multiSelect,
  refreshTrigger,
}) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/api/contacts');
        if (!response.ok) {
          throw new Error('Error al cargar contactos');
        }
        const data = await response.json();
        setChats(data.contacts.map((contact: any) => ({ 
          id: contact.phone_number, 
          name: contact.name || 'Sin nombre', 
          phone: contact.phone_number,
          lastMessage: contact.last_interaction ? 'Última interacción: ' + new Date(contact.last_interaction).toLocaleDateString() : undefined,
          lastMessageTime: contact.last_interaction ? new Date(contact.last_interaction) : undefined,
          unreadCount: 0,
          isOnline: false
        })));
      } catch (err) {
        setError('Error al conectar con el servidor');
        console.error('Error fetching contacts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchContacts();
  }, [refreshTrigger]);

  if (loading) {
    return <div className="contacts-panel">Cargando contactos...</div>;
  }

  if (error) {
    return <div className="contacts-panel" style={{ color: 'red' }}>Error: {error}</div>;
  }
  return (
    <div className="contacts-panel">
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
              <div className="contact-phone">{chat.phone}</div>
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

export default ContactsPanel;