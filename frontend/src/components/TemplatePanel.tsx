import React, { useState, useEffect } from 'react';
import './TemplatePanel.css';
import { templateService } from '../services/templateService';
import { useContacts } from '../contexts/ContactContext';

interface Template {
  id: string;
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  status: 'APPROVED' | 'PENDING' | 'REJECTED' | 'DRAFT';
  rejected_reason?: string;
  created_at: string;
  footer?: string;
}



interface TemplatePanelProps {
  onSendTemplate: (templateId: string, contactIds: string[]) => void;
}

const TemplatePanel: React.FC<TemplatePanelProps> = ({
  onSendTemplate,
}) => {
  const formatPhoneNumber = (phone: string) => {
    // Formatear número de teléfono para mostrar
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };
  const { contacts } = useContacts();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWhatsAppInfo, setShowWhatsAppInfo] = useState(true);
  const [showTemplateMenu, setShowTemplateMenu] = useState<string | null>(null);
  const [showArchivedTemplates, setShowArchivedTemplates] = useState(false);
  const [archivedTemplates, setArchivedTemplates] = useState<Template[]>([]);
  const [archivingTemplate, setArchivingTemplate] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates();
    fetchArchivedTemplates(); // Cargar plantillas archivadas al inicio
  }, []);

  // Cerrar menús cuando se hace clic fuera
  useEffect(() => {
    const handleClickOutside = () => {
      setShowTemplateMenu(null);
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);



  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const templatesList = await templateService.getTemplates();
      setTemplates(templatesList);
    } catch (err) {
      setError('Error al conectar con el servidor');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchArchivedTemplates = async () => {
    try {
      const archivedList = await templateService.getArchivedTemplates();
      setArchivedTemplates(archivedList);
    } catch (err) {
      console.error('Error cargando plantillas archivadas:', err);
    }
  };

  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const handleToggleContactSelection = (contactId: string) => {
    setSelectedContacts((prev) =>
      prev.includes(contactId)
        ? prev.filter((id) => id !== contactId)
        : [...prev, contactId]
    );
  };

  const handleSelectAllContacts = () => {
    // Solo seleccionar contactos activos
    const activeContactIds = contacts
      .filter(contact => contact.is_active)
      .map(contact => contact.phone_number);
    setSelectedContacts(activeContactIds);
  };

  const handleDeselectAllContacts = () => {
    setSelectedContacts([]);
  };

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showContactsModal, setShowContactsModal] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    content: '',
    category: 'UTILITY',
    footer: '',
  });

  const handleSendTemplate = async () => {
    if (selectedContacts.length === 0) {
      alert('Por favor selecciona al menos un contacto');
      return;
    }

    try {
      const templateName = templates.find(t => t.id === selectedTemplate)?.name;
      if (!templateName) {
        throw new Error('Plantilla no encontrada');
      }

      const result = await templateService.sendTemplate(templateName, selectedContacts, {});
      alert(`Plantilla enviada exitosamente a ${result.results.filter((r: any) => r.success).length} contactos`);
      onSendTemplate(selectedTemplate, selectedContacts);
      setSelectedTemplate('');
    } catch (err: any) {
      console.error('Error:', err);
      alert(err.message || 'Error al enviar la plantilla');
    }
  };



  const handleArchiveTemplate = async (templateId: string, templateName: string) => {
    if (!confirm(`¿Estás seguro de que quieres archivar la plantilla "${templateName}"?`)) {
      return;
    }

    try {
      setArchivingTemplate(templateId);
      await templateService.archiveTemplate(templateId);
      alert('Plantilla archivada exitosamente');
      
      // Pequeño delay para asegurar que la base de datos se actualice
      setTimeout(() => {
        // Recargar ambas listas
        fetchTemplates(); // Recargar la lista de activas
        fetchArchivedTemplates(); // Recargar la lista de archivadas
        setArchivingTemplate(null);
      }, 100);
    } catch (err: any) {
      console.error('Error al archivar plantilla:', err);
      alert(err.message || 'Error al archivar plantilla');
      setArchivingTemplate(null);
    }
  };

  const handleUnarchiveTemplate = async (templateId: string) => {
    try {
      setArchivingTemplate(templateId);
      await templateService.unarchiveTemplate(templateId);
      alert('Plantilla desarchivada exitosamente');
      
      // Pequeño delay para asegurar que la base de datos se actualice
      setTimeout(() => {
        // Recargar ambas listas
        fetchArchivedTemplates(); // Recargar la lista de archivadas
        fetchTemplates(); // Recargar la lista de activas
        
        // Si estamos en la vista de archivadas, cambiar a activas
        if (showArchivedTemplates) {
          setShowArchivedTemplates(false);
        }
        setArchivingTemplate(null);
      }, 100);
    } catch (err: any) {
      console.error('Error al desarchivar plantilla:', err);
      alert(err.message || 'Error al desarchivar plantilla');
      setArchivingTemplate(null);
    }
  };

  const handleCreateTemplate = async () => {
    if (newTemplate.name && newTemplate.content) {
      try {
        await templateService.createTemplate({
          name: newTemplate.name,
          content: newTemplate.content,
          category: newTemplate.category as 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP',
          footer: newTemplate.footer || undefined
        });
        
        await fetchTemplates();
        setNewTemplate({ name: '', content: '', category: 'UTILITY', footer: '' });
        setShowCreateModal(false);
      } catch (err: any) {
        console.error('Error:', err);
        alert(err.message || 'Error al crear la plantilla');
      }
    }
  };

  return (
    <div className="template-panel">
        <div className="template-header">
          <h3>Plantillas de Mensajes</h3>
          {!showArchivedTemplates && (
            <button 
              className="create-template-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="material-icons">add</span>
              Agregar
            </button>
          )}
        </div>
        
        <div className="template-tabs">
          <button 
            className={`tab-btn ${!showArchivedTemplates ? 'active' : ''}`}
            onClick={() => {
              setShowArchivedTemplates(false);
              fetchTemplates();
            }}
          >
            Activas ({templates.length})
          </button>
          <button 
            className={`tab-btn ${showArchivedTemplates ? 'active' : ''}`}
            onClick={() => {
              setShowArchivedTemplates(true);
              fetchArchivedTemplates();
            }}
          >
            Archivadas ({archivedTemplates.length})
          </button>
        </div>
        {showWhatsAppInfo && (
          <div className="whatsapp-info">
            <p>📱<strong>Importante:</strong> Las plantillas requieren aprobación de WhatsApp y puede tomar de 24-48 horas.</p>
            <button 
              className="close-info-btn"
              onClick={() => setShowWhatsAppInfo(false)}
              title="Cerrar"
            >
              ×
            </button>
          </div>
        )}

      <div className="template-list">
        {loading && <div className="loading">Cargando plantillas...</div>}
        {error && <div className="error">{error}</div>}
        {!loading && !error && (showArchivedTemplates ? archivedTemplates : templates).map((template) => (
          <div
            key={template.id}
            className={`template-item ${
              selectedTemplate === template.id ? 'selected' : ''
            }`}
            onClick={() => setSelectedTemplate(template.id)}
          >
            <div className="template-info">
              <div className="template-name">{template.name}</div>
              <div className="template-meta">
                <span className="template-category">{template.category}</span>
                <span className={`template-status status-${template.status.toLowerCase()}`}>
                  {template.status === 'APPROVED' && (
                    <>
                      <span className="material-icons">check_circle</span>
                      Aprobado
                    </>
                  )}
                  {template.status === 'PENDING' && (
                    <>
                      <span className="material-icons">schedule</span>
                      Pendiente
                    </>
                  )}
                  {template.status === 'REJECTED' && (
                    <>
                      <span className="material-icons">cancel</span>
                      Rechazado
                    </>
                  )}
                  {template.status === 'DRAFT' && (
                    <>
                      <span className="material-icons">edit</span>
                      Borrador
                    </>
                  )}
                </span>
              </div>
              <div className="template-preview">{template.content}</div>
              {template.footer && (
                <div className="template-footer">
                  {template.footer}
                </div>
              )}
              {template.rejected_reason && (
                <div className="rejection-reason">
                  <strong>Razón de rechazo:</strong> {template.rejected_reason}
                </div>
              )}
            </div>
            <div className="template-item-actions">
              <div className="template-menu">
                <button
                  className="template-menu-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedTemplate(template.id);
                    setShowTemplateMenu(showTemplateMenu === template.id ? null : template.id);
                  }}
                  title="Más opciones"
                >
                  ⋮
                </button>
                {showTemplateMenu === template.id && (
                  <div className="template-menu-dropdown">
                    <button
                      className="menu-item delete-item"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowTemplateMenu(null);
                        if (showArchivedTemplates) {
                          handleUnarchiveTemplate(template.id);
                        } else {
                          handleArchiveTemplate(template.id, template.name);
                        }
                      }}
                      disabled={archivingTemplate === template.id}
                    >
                      {archivingTemplate === template.id 
                        ? '⏳ Procesando...' 
                        : showArchivedTemplates 
                          ? '📤 Desarchivar' 
                          : '📁 Archivar'
                      }
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Botón compuesto para gestionar contactos */}
      <div className="contacts-modal-trigger">
        <div className="composite-contacts-btn">
          <button 
            className={`select-contacts-btn ${selectedContacts.length === 0 ? 'alone' : ''}`}
            onClick={() => setShowContactsModal(true)}
          >
            Contactos ({selectedContacts.length})
          </button>
          {selectedContacts.length > 0 && (
            <button 
              className="clear-contacts-btn"
              onClick={handleDeselectAllContacts}
              title="Limpiar selección"
            >
              ×
            </button>
          )}
        </div>
      </div>

      <div className="template-actions">
        <div className="selection-info">
          Contactos seleccionados: {selectedContacts.length}
        </div>
        <button
          className="send-template-btn"
          onClick={handleSendTemplate}
          disabled={!selectedTemplate || selectedContacts.length === 0}
        >
          Enviar Plantilla
        </button>
      </div>

      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Crear Nueva Plantilla</h4>
            <div className="form-group">
              <label>Nombre:</label>
              <input
                type="text"
                value={newTemplate.name}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, name: e.target.value })
                }
                placeholder="Nombre de la plantilla"
              />
            </div>
            <div className="form-group">
              <label>Categoría:</label>
              <select
                value={newTemplate.category}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, category: e.target.value })
                }
              >
                <option value="UTILITY">UTILITY</option>
                <option value="MARKETING">MARKETING</option>
                <option value="TRANSACTIONAL">TRANSACTIONAL</option>
                <option value="OTP">OTP</option>
              </select>
            </div>
            <div className="form-group">
              <label>Mensaje:</label>
              <textarea
                value={newTemplate.content}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, content: e.target.value })
                }
                placeholder="Contenido del mensaje"
                rows={4}
              />
            </div>
            <div className="form-group">
              <label>Pie de Página (Opcional):</label>
              <input
                type="text"
                value={newTemplate.footer}
                onChange={(e) =>
                  setNewTemplate({ ...newTemplate, footer: e.target.value })
                }
                placeholder="Pie de página del mensaje"
              />
            </div>
            <div className="modal-actions">
              <button onClick={handleCreateTemplate}>Crear</button>
              <button onClick={() => setShowCreateModal(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para seleccionar contactos */}
      {showContactsModal && (
        <div className="modal-overlay">
          <div className="contacts-modal">
            <div className="contacts-modal-header">
              <h4>Seleccionar Contactos</h4>
              <button 
                className="close-modal-btn"
                onClick={() => setShowContactsModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="contacts-modal-actions">
              <button 
                className="select-all-btn"
                onClick={handleSelectAllContacts}
              >
                Todos
              </button>
              <button 
                className="deselect-all-btn"
                onClick={handleDeselectAllContacts}
              >
                Ninguno
              </button>
            </div>
            
                        <div className="contacts-modal-list">
              {contacts.length === 0 ? (
                <div className="no-active-contacts">
                  <p>No hay contactos activos disponibles</p>
                  <p>Solo se muestran contactos que han interactuado recientemente</p>
                </div>
              ) : (
                contacts.map((contact) => (
                  <div 
                    key={contact.phone_number}
                    className={`contact-modal-item ${
                      selectedContacts.includes(contact.phone_number) ? 'selected' : ''
                    }`}
                    onClick={() => handleToggleContactSelection(contact.phone_number)}
                  >
                    <div className="contact-checkbox">
                      {selectedContacts.includes(contact.phone_number) ? '✓' : '○'}
                    </div>
                    <div className="contact-info">
                      <div className="contact-name">{contact.name}</div>
                      <div className="contact-phone">{formatPhoneNumber(contact.phone_number)}</div>
                      <div className="contact-status">
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
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="contacts-modal-footer">
              <div className="selection-count">
                {selectedContacts.length} contactos seleccionados
              </div>
              <button 
                className="confirm-selection-btn"
                onClick={() => setShowContactsModal(false)}
              >
                Listo
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplatePanel;