import React, { useState, useEffect } from 'react';
import { contactService } from '../services/contactService';
import type { Contact, ContactCreateRequest, ContactTypeEnum } from '../services/contactService';
import ContactImport from './ContactImport';
import SearchInput from './SearchInput';
import LoadingButton from './LoadingButton';
import '../styles/ContactImport.css';
import '../styles/ContactManager.css';
import '../styles/SearchInput.css';
import { useContacts } from '../contexts/ContactContext';
import { ContactProtected } from './ProtectedComponent';
import { useNotifications } from './NotificationContainer';
import { useConfirm } from '../hooks/useConfirm';
import ConfirmDialog from './ConfirmDialog';


interface ContactManagerProps {
  onContactUpdate?: () => void;
  onSelectChat?: (contact: Contact) => void;
}

const ContactManager: React.FC<ContactManagerProps> = ({ 
  onContactUpdate,
  onSelectChat
}) => {
  const { contacts, loading, error } = useContacts();
  const { showNotification } = useNotifications();
  const { confirm, confirmDialog } = useConfirm();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [newContact, setNewContact] = useState<ContactCreateRequest>({
    phone_number: '',
    name: '',
    contact_type: undefined,
    is_active: true
  });
  
  const [phoneInputValue, setPhoneInputValue] = useState('+57'); // Para el input visual con +57
  const [searchTerm, setSearchTerm] = useState(''); // Para la búsqueda

  // Efecto para inicializar el input cuando se abre el modal
  useEffect(() => {
    if (showCreateModal) {
      setPhoneInputValue('+57');
      setNewContact(prev => ({ ...prev, phone_number: '' }));
    }
  }, [showCreateModal]);

  // Filtrar contactos basado en el término de búsqueda
  const filteredContacts = contacts.filter(contact => {
    if (!searchTerm.trim()) return true;
    
    const searchLower = searchTerm.toLowerCase().trim();
    const nameMatch = contact.name.toLowerCase().includes(searchLower);
    
    // Solo buscar en teléfono si el término de búsqueda contiene números
    const hasNumbers = /\d/.test(searchTerm);
    let phoneMatch = false;
    
    if (hasNumbers) {
      const cleanSearch = searchTerm.replace(/\D/g, '');
      const cleanPhone = contact.phone_number.replace(/\D/g, '');
      phoneMatch = cleanPhone.includes(cleanSearch);
    }
    
    return nameMatch || phoneMatch;
  });


  // Función para manejar el cambio en el input de teléfono
  const handlePhoneInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    if (value.length <= 10) {
      setPhoneInputValue(`+57${value}`);
      setNewContact(prev => ({ ...prev, phone_number: `57${value}` }));
    }
  };

  const handleCreateContact = async () => {
    if (!newContact.phone_number || !newContact.name) {
      showNotification({
        type: 'warning',
        title: 'Campos Incompletos',
        message: 'Por favor completa todos los campos requeridos.'
      });
      return;
    }

    // Validar que el número tenga el formato correcto (57 + 10 dígitos)
    const cleanNumber = newContact.phone_number.replace(/\D/g, '');
    if (cleanNumber.length !== 12 || !cleanNumber.startsWith('57')) {
      showNotification({
        type: 'warning',
        title: 'Número Inválido',
        message: 'El número debe tener 10 dígitos (sin incluir el código de país).'
      });
      return;
    }

    setIsCreating(true);
    try {
      await contactService.createContact({
        ...newContact,
        is_active: true // Por defecto, los contactos creados están activos
      });
      setNewContact({ phone_number: '', name: '', contact_type: undefined, is_active: true });
      setPhoneInputValue('+57'); // Resetear el input visual
      setShowCreateModal(false);
      // No recargar aquí, el contexto se encargará de actualizar
      onContactUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Contacto Creado',
        message: `El contacto "${newContact.name}" se ha creado exitosamente.`
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Crear Contacto',
        message: err.message || 'Error al crear el contacto'
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateContact = async () => {
    if (!editingContact) return;

    setIsUpdating(true);
    try {
      await contactService.updateContact(editingContact.phone_number, {
        name: editingContact.name,
        contact_type: editingContact.contact_type as ContactTypeEnum | undefined,
        is_active: editingContact.is_active
      });
      setShowEditModal(false);
      setEditingContact(null);
      // No recargar aquí, el WebSocket se encargará de actualizar
      onContactUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Contacto Actualizado',
        message: `El contacto "${editingContact.name}" se ha actualizado exitosamente.`
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Actualizar Contacto',
        message: err.message || 'Error al actualizar el contacto'
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteContact = async (phoneNumber: string) => {
    const confirmed = await confirm({
      title: 'Eliminar Contacto',
      message: '¿Estás seguro de que quieres eliminar este contacto? Esta acción no se puede deshacer.',
      confirmText: 'Eliminar',
      cancelText: 'Cancelar',
      type: 'delete'
    });

    if (!confirmed) {
      return;
    }

    try {
      await contactService.deleteContact(phoneNumber);
      // No recargar aquí, el WebSocket se encargará de actualizar
      onContactUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Contacto Eliminado',
        message: 'El contacto se ha eliminado exitosamente.'
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Eliminar Contacto',
        message: err.message || 'Error al eliminar el contacto'
      });
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

      {/* Campo de búsqueda */}
      <SearchInput
        value={searchTerm}
        onChange={setSearchTerm}
        placeholder="Buscar contactos por nombre o teléfono..."
        resultsCount={filteredContacts.length}
        totalCount={contacts.length}
        className="contact-search"
      />

      {loading && <div className="loading">Cargando contactos...</div>}
              {error && <div className="template-error">{error}</div>}

      <div className="contacts-list">
        {!loading && !error && filteredContacts.map((contact) => (
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
              {contact.contact_type && (
                <div className="contact-type">
                  <span className="contact-badge" data-type={contact.contact_type}>{contact.contact_type}</span>
                </div>
              )}
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
        
        {!loading && !error && filteredContacts.length === 0 && (
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
              <div className="phone-input-container">
                <span className="phone-prefix">+57</span>
                <input
                  type="tel"
                  value={phoneInputValue.replace('+57', '')}
                  onChange={handlePhoneInputChange}
                  placeholder="3XX XXX XXXX"
                  className="phone-number-input"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Tipo de Contacto:</label>
              <select
                value={newContact.contact_type || ""}
                onChange={(e) => setNewContact({ ...newContact, contact_type: e.target.value as ContactTypeEnum || undefined })}
              >
                <option value="">Seleccionar tipo</option>
                <option value="Administrativo">Administrativo</option>
                <option value="Operario">Operario</option>
                <option value="Proveedor">Proveedor</option>
                <option value="Cliente">Cliente</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
            <div className="modal-actions">
              <LoadingButton onClick={handleCreateContact} loading={isCreating}>
                Crear
              </LoadingButton>
              <button onClick={() => setShowCreateModal(false)} disabled={isCreating}>
                Cancelar
              </button>
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
              <label>Tipo de Contacto:</label>
              <select
                value={editingContact.contact_type || ""}
                onChange={(e) => setEditingContact({ ...editingContact, contact_type: e.target.value as ContactTypeEnum || undefined })}
              >
                <option value="">Seleccionar tipo</option>
                <option value="Administrativo">Administrativo</option>
                <option value="Operario">Operario</option>
                <option value="Proveedor">Proveedor</option>
                <option value="Cliente">Cliente</option>
                <option value="Otro">Otro</option>
              </select>
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
              <LoadingButton onClick={handleUpdateContact} loading={isUpdating}>
                Actualizar
              </LoadingButton>
              <button onClick={() => setShowEditModal(false)} disabled={isUpdating}>
                Cancelar
              </button>
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

      {/* Diálogo de confirmación */}
      {confirmDialog && (
        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          title={confirmDialog.title}
          message={confirmDialog.message}
          confirmText={confirmDialog.confirmText}
          cancelText={confirmDialog.cancelText}
          type={confirmDialog.type}
          onConfirm={confirmDialog.onConfirm}
          onCancel={confirmDialog.onCancel}
        />
      )}
    </div>
  );
};

export default ContactManager; 