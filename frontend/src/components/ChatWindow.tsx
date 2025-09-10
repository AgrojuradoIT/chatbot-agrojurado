import React, { useState } from 'react';
import '../styles/ChatWindow.css';
import '../styles/SearchInput.css';
import InfiniteScroll from './InfiniteScroll';
import MessageStatus from './MessageStatus';
import Loader from './Loader';
import SearchInput from './SearchInput';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  status?: 'sending' | 'sent' | 'delivered' | 'error';
  message_type?: 'text' | 'image' | 'video' | 'audio' | 'document';
  media_id?: string;
  media_url?: string;
  mime_type?: string;
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
  const [searchTerm, setSearchTerm] = useState(''); // Para la búsqueda de mensajes
  const [showSearch, setShowSearch] = useState(false); // Para mostrar/ocultar el campo de búsqueda

  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };

  // Filtrar mensajes basado en el término de búsqueda
  const filteredMessages = messages.filter(message => {
    if (!searchTerm.trim()) return true;
    const searchLower = searchTerm.toLowerCase().trim();
    return message.text.toLowerCase().includes(searchLower);
  });

  // Función para manejar el toggle del campo de búsqueda
  const handleSearchToggle = () => {
    setShowSearch(!showSearch);
    if (showSearch) {
      setSearchTerm(''); // Limpiar búsqueda al cerrar
    }
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
          
          {/* Botón de búsqueda y campo desplegable */}
          <div className="chat-search-container">
            {!showSearch ? (
              <button
                className="search-toggle-btn"
                onClick={handleSearchToggle}
                title="Buscar en mensajes"
              >
                <span className="material-icons">search</span>
              </button>
            ) : (
              <div className="search-expanded">
                <SearchInput
                  value={searchTerm}
                  onChange={setSearchTerm}
                  placeholder="Buscar en mensajes..."
                  resultsCount={filteredMessages.length}
                  totalCount={messages.length}
                  className="chat-search"
                  showResultsInfo={false}
                  showClearButton={false}
                />
                <button
                  className="search-close-btn"
                  onClick={handleSearchToggle}
                  title="Cerrar búsqueda"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
      <InfiniteScroll
        messages={filteredMessages}
        onLoadMore={onLoadMore || (() => {})}
        hasMore={hasMore}
        isLoading={isLoadingMore}
      >
        <div className="messages-container">
          {isLoading && (
            <div className="loading-indicator">
              <Loader size={20} />
              <span>Cargando mensajes...</span>
            </div>
          )}
          {filteredMessages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
            >
              <div className="message-content">{message.text}</div>
              <MessageStatus 
                status={message.sender === 'user' ? message.status : undefined} 
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