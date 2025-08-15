import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();

  const handleLogin = () => {
    if (!isLoading) {
      login();
    }
  };

  return (
    <div className="login-container">
      <div className="floating-element"></div>
      <div className="login-card">
        <div className="login-header">
          <h1>Chatbot Agrojurado</h1>
          <p>Sistema de gestión de WhatsApp</p>
        </div>
        
        <div className="login-content">
                     <div className="login-icon">
             <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
               <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#66BB6A"/>
             </svg>
           </div>
          
          <h2>Iniciar Sesión</h2>
          <p className="login-description">
            Accede con tu cuenta autorizada para gestionar el chatbot de WhatsApp
          </p>
          
          <button 
            className={`login-button ${isLoading ? 'loading' : ''}`}
            onClick={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="spinner"></div>
                Cargando...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" fill="white"/>
                </svg>
                Iniciar Sesión con OAuth
              </>
            )}
          </button>
          
          <div className="login-footer">
            <p>¿Necesitas acceso? Contacta al administrador del sistema</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
