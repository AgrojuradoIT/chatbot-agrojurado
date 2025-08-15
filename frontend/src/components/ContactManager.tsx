import React, { useState } from 'react';
import { contactService } from '../services/contactService';
import type { Contact, ContactCreateRequest } from '../services/contactService';
import ContactImport from './ContactImport';
import './ContactImport.css';
import { useContacts } from '../contexts/ContactContext';
import { ContactProtected } from './ProtectedComponent';


interface ContactManagerProps {
  onContactUpdate?: () => void;
  onSelectChat?: (contact: Contact) => void;
}

const ContactManager: React.FC<ContactManagerProps> = ({ 
  onContactUpdate,
  onSelectChat
}) => {
  const { contacts, loading, error } = useContacts();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [newContact, setNewContact] = useState<ContactCreateRequest>({
    phone_number: '',
    name: '',
    is_active: true
  });

  const handleCreateContact = async () => {
    if (!newContact.phone_number || !newContact.name) {
      alert('Por favor completa todos los campos');
      return;
    }

    try {
      await contactService.createContact({
        ...newContact,
        is_active: true // Por defecto, los contactos creados están activos
      });
      setNewContact({ phone_number: '', name: '', is_active: true });
      setShowCreateModal(false);
      // No recargar aquí, el contexto se encargará de actualizar
      onContactUpdate?.();
      alert('Contacto creado exitosamente');
    } catch (err: any) {
      alert(err.message || 'Error al crear contacto');
    }
  };

  const handleUpdateContact = async () => {
    if (!editingContact) return;

    try {
      await contactService.updateContact(editingContact.phone_number, {
        name: editingContact.name,
        is_active: editingContact.is_active
      });
      setShowEditModal(false);
      setEditingContact(null);
      // No recargar aquí, el WebSocket se encargará de actualizar
      onContactUpdate?.();
      alert('Contacto actualizado exitosamente');
    } catch (err: any) {
      alert(err.message || 'Error al actualizar contacto');
    }
  };

  const handleDeleteContact = async (phoneNumber: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este contacto?')) {
      return;
    }

    try {
      await contactService.deleteContact(phoneNumber);
      // No recargar aquí, el WebSocket se encargará de actualizar
      onContactUpdate?.();
      alert('Contacto eliminado exitosamente');
    } catch (err: any) {
      alert(err.message || 'Error al eliminar contacto');
    }
  };

  const openEditModal = (contact: Contact) => {
    setEditingContact({ ...contact });
    setShowEditModal(true);
  };

  const handleSelectContact = (contact: Contact) => {
    if (onSelectChat) {
      onSelectChat(contact);
    }
  };

  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    return new Date(dateString).toLocaleString('es-ES');
  };

  return (
    <div className="contact-manager-panel">
      <div className="contacts-header">
        <h3>Contactos</h3>
        <div className="contacts-actions">
          <ContactProtected action="manage">
            <button 
              className="import-contact-btn"
              onClick={() => setShowImportModal(true)}
              title="Importar contactos desde Excel"
            >
              <span className="material-icons">upload_file</span>
              Importar
            </button>
          </ContactProtected>
          <ContactProtected action="manage">
            <button 
              className="create-contact-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="material-icons">add</span>
              Agregar
            </button>
          </ContactProtected>
        </div>
      </div>

      {loading && <div className="loading">Cargando contactos...</div>}
      {error && <div className="error">{error}</div>}

      <div className="contacts-list">
        {!loading && !error && contacts.map((contact) => (
          <div 
            key={contact.phone_number} 
            className="contact-item"
            onClick={() => handleSelectContact(contact)}
            style={{ cursor: 'pointer' }}
          >
            <div className="contact-avatar">
              {contact.name.charAt(0).toUpperCase()}
            </div>
            <div className="contact-info">
              <div className="contact-name">{contact.name}</div>
              <div className="contact-phone">{formatPhoneNumber(contact.phone_number)}</div>
              <div className="contact-last-message">
                {contact.is_active ? (
                  <>
                    <span className="material-icons">check_circle</span>
                    Activo
                  </>
                ) : (
                  <>
                    <span className="material-icons">cancel</span>
                    Inactivo
                  </>
                )} • Última interacción: {formatDate(contact.last_interaction)}
              </div>
            </div>
            <div className="contact-actions" onClick={(e) => e.stopPropagation()}>
              <ContactProtected action="manage">
                <button 
                  className="edit-btn"
                  onClick={() => openEditModal(contact)}
                  title="Editar contacto"
                >
                  <span className="material-icons">edit</span>
                </button>
              </ContactProtected>
              <ContactProtected action="manage">
                <button 
                  className="delete-btn"
                  onClick={() => handleDeleteContact(contact.phone_number)}
                  title="Eliminar contacto"
                >
                  <span className="material-icons">delete</span>
                </button>
              </ContactProtected>
            </div>
          </div>
        ))}
        
        {!loading && !error && contacts.length === 0 && (
          <div className="no-contacts">
            <p>No hay contactos registrados</p>
            <p>Crea tu primer contacto para comenzar</p>
          </div>
        )}
      </div>

      {/* Modal para crear contacto */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Agregar Nuevo Contacto</h4>
            <div className="form-group">
              <label>Nombre:</label>
              <input
                type="text"
                value={newContact.name}
                onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                placeholder="Nombre del contacto"
              />
            </div>
            <div className="form-group">
              <label>Número de teléfono:</label>
              <input
                type="tel"
                value={newContact.phone_number}
                onChange={(e) => setNewContact({ ...newContact, phone_number: e.target.value })}
                placeholder="57XXXXXXXXX"
              />
            </div>
            <div className="modal-actions">
              <button onClick={handleCreateContact}>Crear</button>
              <button onClick={() => setShowCreateModal(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para editar contacto */}
      {showEditModal && editingContact && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Editar Contacto</h4>
            <div className="form-group">
              <label>Número de teléfono:</label>
              <input
                type="tel"
                value={editingContact.phone_number}
                disabled
                className="disabled-input"
              />
            </div>
            <div className="form-group">
              <label>Nombre:</label>
              <input
                type="text"
                value={editingContact.name}
                onChange={(e) => setEditingContact({ ...editingContact, name: e.target.value })}
                placeholder="Nombre del contacto"
              />
            </div>
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={editingContact.is_active}
                  onChange={(e) => setEditingContact({ ...editingContact, is_active: e.target.checked })}
                />
                Contacto activo
              </label>
            </div>
            <div className="modal-actions">
              <button onClick={handleUpdateContact}>Actualizar</button>
              <button onClick={() => setShowEditModal(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para importar contactos */}
      {showImportModal && (
        <ContactImport
          onImportComplete={() => {
            // No recargar aquí, el contexto se encargará de actualizar
            onContactUpdate?.();
          }}
          onClose={() => setShowImportModal(false)}
        />
      )}
    </div>
  );
};

export default ContactManager; 