import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { contactService } from '../services/contactService';
import { websocketService } from '../services/websocketService';
import type { Contact } from '../services/contactService';

interface ContactContextType {
  contacts: Contact[];
  loading: boolean;
  error: string | null;
  refreshContacts: () => Promise<void>;
}

const ContactContext = createContext<ContactContextType | undefined>(undefined);

interface ContactProviderProps {
  children: ReactNode;
}

export const ContactProvider: React.FC<ContactProviderProps> = ({ children }) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contactsLoaded, setContactsLoaded] = useState(false);

  const fetchContacts = async () => {
    try {
      setLoading(true);
      const contactsData = await contactService.getContacts();
      setContacts(contactsData);
      setError(null);
      setContactsLoaded(true);
    } catch (err) {
      setError('Error al cargar contactos');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshContacts = async () => {
    await fetchContacts();
  };

  // Cargar contactos inicialmente
  useEffect(() => {
    if (!contactsLoaded) {
      fetchContacts();
    }
  }, [contactsLoaded]);

  // Configurar WebSocket para actualizaciones en tiempo real
  useEffect(() => {
    // Conectar WebSocket
    websocketService.connect();

    // Configurar listener para actualizaciones de contactos
    websocketService.onMessage((message) => {
      if (message.type === 'contact_updated' && message.data) {
        console.log('🔄 Actualización de contacto recibida en ContactContext:', message.data);
        
        // Actualizar la lista de contactos
        fetchContacts();
      }
    });

    // Cleanup al desmontar
    return () => {
      console.log('🧹 Limpiando WebSocket listener de ContactContext');
    };
  }, []);

  return (
    <ContactContext.Provider value={{ contacts, loading, error, refreshContacts }}>
      {children}
    </ContactContext.Provider>
  );
};

export const useContacts = () => {
  const context = useContext(ContactContext);
  if (context === undefined) {
    throw new Error('useContacts must be used within a ContactProvider');
  }
  return context;
}; 