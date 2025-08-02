import React from 'react';
import './MessageStatus.css';

interface MessageStatusProps {
  status?: 'sending' | 'sent' | 'delivered' | 'error';
  timestamp: Date;
}

const MessageStatus: React.FC<MessageStatusProps> = ({ status, timestamp }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'sending':
        return <div className="status-icon sending">⏳</div>;
      case 'sent':
        return <div className="status-icon sent">✓</div>;
      case 'delivered':
        return <div className="status-icon delivered">✓✓</div>;
      case 'error':
        return <div className="status-icon error">⚠️</div>;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'sending':
        return 'Enviando...';
      case 'sent':
        return 'Enviado';
      case 'delivered':
        return 'Entregado';
      case 'error':
        return 'Error';
      default:
        return '';
    }
  };

  return (
    <div className="message-status">
      {status && getStatusIcon()}
      {status && <span className="status-text">{getStatusText()}</span>}
      <span className="message-time">
        {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
};

export default MessageStatus; 