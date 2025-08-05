import React from 'react';
import './ChatWindow.css';
import InfiniteScroll from './InfiniteScroll';
import MessageStatus from './MessageStatus';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  status?: 'sending' | 'sent' | 'delivered' | 'error';
}

interface ChatWindowProps {
  messages: Message[];
  isLoading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  selectedChat?: {
    name: string;
    phone: string;
  } | null;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ 
  messages, 
  isLoading = false, 
  onLoadMore,
  hasMore = false,
  isLoadingMore = false,
  selectedChat
}) => {
  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };
  return (
    <div className="chat-window">
      {selectedChat && (
        <div className="chat-header">
          <div className="chat-contact-info">
            <div className="contact-avatar">
              {selectedChat.name.charAt(0).toUpperCase()}
            </div>
            <div className="contact-details">
              <div className="contact-name">{selectedChat.name}</div>
              <div className="contact-phone">{formatPhoneNumber(selectedChat.phone)}</div>
            </div>
          </div>
        </div>
      )}
      <InfiniteScroll
        messages={messages}
        onLoadMore={onLoadMore || (() => {})}
        hasMore={hasMore}
        isLoading={isLoadingMore}
      >
        <div className="messages-container">
          {isLoading && (
            <div className="loading-indicator">
              <div className="loading-spinner"></div>
              <span>Cargando mensajes...</span>
            </div>
          )}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
            >
              <div className="message-content">{message.text}</div>
              <MessageStatus 
                status={message.status} 
                timestamp={message.timestamp} 
              />
            </div>
          ))}
        </div>
      </InfiniteScroll>
    </div>
  );
};

export default ChatWindow;