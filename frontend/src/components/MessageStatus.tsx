import React from 'react';
import '../styles/MessageStatus.css';

interface MessageStatusProps {
  status?: 'sending' | 'sent' | 'delivered' | 'error';
  timestamp: Date;
}

const MessageStatus: React.FC<MessageStatusProps> = ({ status, timestamp }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'sending':
        return <div className="status-icon sending"><span className="material-icons">schedule</span></div>;
      case 'sent':
        return <div className="status-icon sent"><span className="material-icons">check</span></div>;
      case 'delivered':
        return <div className="status-icon delivered"><span className="material-icons">done_all</span></div>;
      case 'error':
        return <div className="status-icon error"><span className="material-icons">error</span></div>;
      default:
        return null;
    }
  };



  return (
    <div className="message-status">
      <span className="message-time">
        {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
      {status && getStatusIcon()}
    </div>
  );
};

export default MessageStatus; 