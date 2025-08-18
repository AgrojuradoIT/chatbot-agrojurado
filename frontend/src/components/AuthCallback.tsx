import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/AuthCallback.css';
import Loader from './Loader';

const AuthCallback: React.FC = () => {
  const { handleCallback } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Procesando autenticación...');
  const hasProcessed = useRef(false);

  useEffect(() => {
    const processCallback = async () => {
      // Prevenir múltiples ejecuciones
      if (hasProcessed.current) {
        return;
      }
      hasProcessed.current = true;

      try {
        // Obtener el código de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
          setStatus('error');
          setMessage('Error en la autenticación: ' + error);
          return;
        }

        if (!code) {
          setStatus('error');
          setMessage('No se recibió el código de autorización');
          return;
        }

        // Procesar el callback
        const success = await handleCallback(code);
        
        if (success) {
          setStatus('success');
          setMessage('¡Autenticación exitosa! Redirigiendo...');
          
          // Redirigir al dashboard después de 2 segundos
          setTimeout(() => {
            window.location.href = '/';
          }, 2000);
        } else {
          setStatus('error');
          setMessage('Error al procesar la autenticación');
        }
      } catch (error) {
        console.error('Error en callback:', error);
        setStatus('error');
        setMessage('Error inesperado durante la autenticación');
      }
    };

    processCallback();
  }, []); // Remover handleCallback de las dependencias para evitar re-ejecuciones

  const handleRetry = () => {
    window.location.href = '/';
  };

  return (
    <div className="callback-container">
      <div className="callback-card">
        <div className="callback-content">
          {status === 'processing' && (
            <>
              <div className="callback-spinner">
                <Loader size={60} />
              </div>
              <h2>Procesando Autenticación</h2>
              <p>{message}</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="callback-icon success">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#66BB6A"/>
                </svg>
              </div>
              <h2>¡Autenticación Exitosa!</h2>
              <p>{message}</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="callback-icon error">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="#ff5252"/>
                </svg>
              </div>
              <h2>Error de Autenticación</h2>
              <p>{message}</p>
              <button className="retry-button" onClick={handleRetry}>
                Volver al Inicio
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;
