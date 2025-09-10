import React, { useState, useEffect } from 'react';
import '../styles/TemplatePanel.css';
import '../styles/SearchInput.css';
import { templateService } from '../services/templateService';
import type { TemplateWithMediaRequest } from '../services/templateService';
import { useContacts } from '../contexts/ContactContext';
import { useAuth } from '../contexts/AuthContext';
import { getAuthHeaders } from '../utils/auth';
import MediaSelector from './MediaSelector';
import LoadingButton from './LoadingButton';
import SearchInput from './SearchInput';
import { TemplateProtected } from './ProtectedComponent';
import { useNotifications } from './NotificationContainer';
import { useConfirm } from '../hooks/useConfirm';
import ConfirmDialog from './ConfirmDialog';

interface Template {
  id: string;
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  status: 'APPROVED' | 'PENDING' | 'REJECTED' | 'DRAFT';
  rejected_reason?: string;
  created_at: string;
  footer?: string;
  // Campos para plantillas con medios
  has_media?: boolean;
  header_text?: string;
  media_type?: 'IMAGE' | 'VIDEO' | 'DOCUMENT';
  media_id?: string;
  image_url?: string;
  header_handle?: string;
}

// Función para detectar el tipo específico de archivo
const getFileTypeInfo = (template: Template) => {
  if (!template.header_handle) return null;
  
  const handle = Array.isArray(template.header_handle) 
    ? template.header_handle[0] 
    : template.header_handle;
  
  // Detectar tipo desde la URL
  const url = handle.toLowerCase();
  
  if (template.media_type === 'IMAGE') {
    if (url.includes('.jpg') || url.includes('.jpeg')) {
      return { type: 'JPEG', icon: 'image', label: 'Archivo JPEG', color: '#00a884' };
    } else if (url.includes('.png')) {
      return { type: 'PNG', icon: 'image', label: 'Archivo PNG', color: '#00a884' };
    } else {
      return { type: 'IMAGEN', icon: 'image', label: 'Archivo de imagen', color: '#00a884' };
    }
  } else if (template.media_type === 'VIDEO') {
    if (url.includes('.mp4')) {
      return { type: 'MP4', icon: 'videocam', label: 'Archivo MP4', color: '#f59e0b' };
    } else if (url.includes('.3gp') || url.includes('.3gpp')) {
      return { type: '3GPP', icon: 'videocam', label: 'Archivo 3GPP', color: '#f59e0b' };
    } else {
      return { type: 'VIDEO', icon: 'videocam', label: 'Archivo de video', color: '#f59e0b' };
    }
  } else if (template.media_type === 'DOCUMENT') {
    if (url.includes('.pdf')) {
      return { type: 'PDF', icon: 'picture_as_pdf', label: 'Archivo PDF', color: '#ef4444' };
    } else {
      return { type: 'DOCUMENTO', icon: 'description', label: 'Archivo de documento', color: '#6b7280' };
    }
  }
  
  return null;
};


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
  const { user } = useAuth();
  const { showNotification } = useNotifications();
  const { confirm, confirmDialog } = useConfirm();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWhatsAppInfo, setShowWhatsAppInfo] = useState(true);
  const [showTemplateMenu, setShowTemplateMenu] = useState<string | null>(null);
  const [showArchivedTemplates, setShowArchivedTemplates] = useState(false);
  const [archivedTemplates, setArchivedTemplates] = useState<Template[]>([]);
  const [archivingTemplate, setArchivingTemplate] = useState<string | null>(null);
  const [isSendingTemplate, setIsSendingTemplate] = useState(false);
  const [isCreatingTemplate, setIsCreatingTemplate] = useState(false);
  const [searchTerm, setSearchTerm] = useState(''); // Para la búsqueda

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

  // Filtrar plantillas basado en el término de búsqueda
  const filteredTemplates = (showArchivedTemplates ? archivedTemplates : templates).filter(template => {
    if (!searchTerm.trim()) return true;
    
    const searchLower = searchTerm.toLowerCase().trim();
    const nameMatch = template.name.toLowerCase().includes(searchLower);
    const contentMatch = template.content.toLowerCase().includes(searchLower);
    const categoryMatch = template.category.toLowerCase().includes(searchLower);
    const statusMatch = template.status.toLowerCase().includes(searchLower);
    return nameMatch || contentMatch || categoryMatch || statusMatch;
  });


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

  // Autocompletar el campo footer con el sector del usuario cuando esté disponible
  useEffect(() => {
    if (user && user.sector && showCreateModal) {
      setNewTemplate(prev => ({
        ...prev,
        footer: user.sector
      }));
    }
  }, [user, showCreateModal]);

  // Estados para plantillas con medios
  const [templateType, setTemplateType] = useState<'text' | 'media'>('text');
  const [selectedMediaId, setSelectedMediaId] = useState<string>('');
  const [selectedMediaType, setSelectedMediaType] = useState<string>('');
  const [selectedImageUrl, setSelectedImageUrl] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Categorías que permiten medios
  const mediaAllowedCategories = ['MARKETING', 'UTILITY', 'TRANSACTIONAL'];

  // Función para verificar si la categoría permite medios
  const categoryAllowsMedia = (category: string) => {
    return mediaAllowedCategories.includes(category);
  };

  // Función para obtener descripción de la categoría
  const getCategoryDescription = (category: string) => {
    switch (category) {
      case 'MARKETING':
        return 'Promociones y ofertas comerciales';
      case 'UTILITY':
        return 'Recordatorios y servicios informativos';
      case 'TRANSACTIONAL':
        return 'Confirmaciones de pedidos y facturas';
      case 'OTP':
        return 'Códigos de verificación (solo texto)';
      default:
        return '';
    }
  };



  const handleArchiveTemplate = async (templateId: string, templateName: string) => {
    const confirmed = await confirm({
      title: 'Archivar Plantilla',
      message: `¿Estás seguro de que quieres archivar la plantilla "${templateName}"?`,
      confirmText: 'Archivar',
      cancelText: 'Cancelar',
      type: 'warning'
    });

    if (!confirmed) {
      return;
    }

    try {
      setArchivingTemplate(templateId);
      await templateService.archiveTemplate(templateId);
      
      showNotification({
        type: 'success',
        title: 'Plantilla Archivada',
        message: 'La plantilla se ha archivado exitosamente.'
      });
      
      // Pequeño delay para asegurar que la base de datos se actualice
      setTimeout(() => {
        // Recargar ambas listas
        fetchTemplates(); // Recargar la lista de activas
        fetchArchivedTemplates(); // Recargar la lista de archivadas
        setArchivingTemplate(null);
      }, 100);
    } catch (err: any) {
      console.error('Error al archivar plantilla:', err);
      showNotification({
        type: 'error',
        title: 'Error al Archivarla Plantilla',
        message: err.message || 'Error al archivar la plantilla'
      });
      setArchivingTemplate(null);
    }
  };

  const handleUnarchiveTemplate = async (templateId: string) => {
    try {
      setArchivingTemplate(templateId);
      await templateService.unarchiveTemplate(templateId);
      
      showNotification({
        type: 'success',
        title: 'Plantilla Desarchivada',
        message: 'La plantilla se ha desarchivado exitosamente.'
      });
      
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
      showNotification({
        type: 'error',
        title: 'Error al Desarchivar Plantilla',
        message: err.message || 'Error al desarchivar la plantilla'
      });
      setArchivingTemplate(null);
    }
  };

  const handleCreateTemplate = async () => {
    if (newTemplate.name && newTemplate.content) {
      try {
        setIsCreatingTemplate(true);
        await templateService.createTemplate({
          name: newTemplate.name,
          content: newTemplate.content,
          category: newTemplate.category as 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP',
          footer: newTemplate.footer || undefined
        });
        
        await fetchTemplates();
        setNewTemplate({ name: '', content: '', category: 'UTILITY', footer: '' });
        setShowCreateModal(false);
        
        showNotification({
          type: 'success',
          title: 'Plantilla Creada',
          message: `La plantilla "${newTemplate.name}" se ha creado exitosamente.`
        });
      } catch (err: any) {
        console.error('Error:', err);
        showNotification({
          type: 'error',
          title: 'Error al Crear Plantilla',
          message: err.message || 'Error al crear la plantilla'
        });
      } finally {
        setIsCreatingTemplate(false);
      }
    }
  };

  const handleCreateTemplateWithMedia = async () => {
    if (newTemplate.name && newTemplate.content) {
      try {
        setIsCreatingTemplate(true);
        // Validar que la categoría permita medios si se seleccionó tipo media
        if (templateType === 'media' && !categoryAllowsMedia(newTemplate.category)) {
          showNotification({
            type: 'warning',
            title: 'Categoría No Compatible',
            message: 'Esta categoría no permite medios multimedia. Selecciona otra categoría o cambia a "Solo Texto".'
          });
          return;
        }

        // Validar que se haya seleccionado un medio si es tipo media
        if (templateType === 'media' && !selectedFile && !selectedImageUrl) {
          showNotification({
            type: 'warning',
            title: 'Medio Requerido',
            message: 'Por favor selecciona una imagen o video para la plantilla con medios.'
          });
          return;
        }

        if (templateType === 'media') {
          if (selectedFile) {
            // Crear plantilla con archivo usando el nuevo endpoint
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('name', newTemplate.name);
            formData.append('content', newTemplate.content);
            formData.append('category', newTemplate.category);
            formData.append('media_type', selectedMediaType);
            formData.append('language', 'es');
            if (newTemplate.footer) {
              formData.append('footer', newTemplate.footer);
            }
            
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/templates/create-with-file`, {
              method: 'POST',
              headers: {
                ...getAuthHeaders({}, false) // false = no incluir Content-Type para FormData
              },
              body: formData,
            });
            
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.detail || 'Error al crear plantilla con archivo');
            }
            
            const result = await response.json();
            console.log('Plantilla creada exitosamente:', result);
          } else if (selectedImageUrl) {
            // Usar el servicio existente para URL de imagen
            const templateData: TemplateWithMediaRequest = {
              name: newTemplate.name,
              content: newTemplate.content,
              category: newTemplate.category as 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP',
              footer: newTemplate.footer || undefined,
              media_type: 'IMAGE',
              image_url: selectedImageUrl
            };
            await templateService.createTemplateWithMedia(templateData);
          }
        } else {
          // Crear plantilla solo texto
          await templateService.createTemplate({
            name: newTemplate.name,
            content: newTemplate.content,
            category: newTemplate.category as 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP',
            footer: newTemplate.footer
          });
        }
        
        await fetchTemplates();
        // Limpiar estados
        setNewTemplate({ name: '', content: '', category: 'UTILITY', footer: '' });
        setTemplateType('text');
        setSelectedMediaId('');
        setSelectedMediaType('');
        setSelectedImageUrl('');
        setSelectedFile(null);
        setShowCreateModal(false);
        
        showNotification({
          type: 'success',
          title: 'Plantilla Creada',
          message: `La plantilla "${newTemplate.name}" se ha creado exitosamente.`
        });
      } catch (err: any) {
        console.error('Error:', err);
        showNotification({
          type: 'error',
          title: 'Error al Crear Plantilla',
          message: err.message || 'Error al crear la plantilla'
        });
      } finally {
        setIsCreatingTemplate(false);
      }
    }
  };

  const handleMediaSelected = (mediaId: string, mediaType: string, _mediaUrl?: string) => {
    setSelectedMediaId(mediaId);
    setSelectedMediaType(mediaType);
    setSelectedImageUrl(''); // Limpiar URL si se selecciona archivo
    setSelectedFile(null); // Limpiar archivo si se selecciona media ID
  };

  const handleFileSelected = (file: File, mediaType: string) => {
    setSelectedFile(file);
    setSelectedMediaType(mediaType);
    setSelectedMediaId(''); // Limpiar media ID si se selecciona archivo
    setSelectedImageUrl(''); // Limpiar URL si se selecciona archivo
  };

  const handleImageUrlSelected = (imageUrl: string) => {
    setSelectedImageUrl(imageUrl);
    setSelectedMediaType('IMAGE');
  };

  const handleClearMedia = () => {
    setSelectedMediaId('');
    setSelectedMediaType('');
    setSelectedImageUrl('');
    setSelectedFile(null);
  };

  const handleSendTemplateWithMedia = async () => {
    if (selectedContacts.length === 0) {
      showNotification({
        type: 'warning',
        title: 'Sin Contactos Seleccionados',
        message: 'Por favor selecciona al menos un contacto para enviar la plantilla.'
      });
      return;
    }

    try {
      setIsSendingTemplate(true);
      const templateName = templates.find(t => t.id === selectedTemplate)?.name;
      if (!templateName) {
        throw new Error('Plantilla no encontrada');
      }

      const template = templates.find(t => t.id === selectedTemplate);
      
      // Verificar si la plantilla tiene multimedia
      if (template?.has_media || template?.media_id || template?.image_url) {
        // Para plantillas con multimedia, usar el endpoint específico
        console.log('Enviando plantilla con multimedia:', template);
        
        // Determinar el media_id a usar
        const mediaId = template.media_id || template.image_url || '';
        
        // Preparar header_parameters con el enlace si está disponible
        const headerParams: any = {};
        if (template.header_handle && template.media_type === 'IMAGE') {
          // Asegurar que el enlace sea un string (puede venir como array)
          const imageLink = Array.isArray(template.header_handle) 
            ? template.header_handle[0] 
            : template.header_handle;
          headerParams.image_link = imageLink;
        } else if (template.header_handle && template.media_type === 'VIDEO') {
          const videoLink = Array.isArray(template.header_handle) 
            ? template.header_handle[0] 
            : template.header_handle;
          headerParams.video_link = videoLink;
        } else if (template.header_handle && template.media_type === 'DOCUMENT') {
          const documentLink = Array.isArray(template.header_handle) 
            ? template.header_handle[0] 
            : template.header_handle;
          headerParams.document_link = documentLink;
        }
        
        console.log('Enviando plantilla con multimedia:', {
          templateName,
          mediaId,
          headerParams,
          template
        });
        
        // Usar el servicio específico para plantillas con multimedia
        const result = await templateService.sendTemplateWithMedia(
          templateName, 
          selectedContacts, 
          mediaId,
          {}, // parameters
          headerParams // header_parameters con el enlace
        );

        const successCount = result.results.filter((r: any) => r.success).length;
        if (successCount > 0) {
          showNotification({
            type: 'success',
            title: 'Plantilla Enviada',
            message: `Plantilla "${templateName}" enviada exitosamente a ${successCount} contactos.`
          });
        } else {
          showNotification({
            type: 'warning',
            title: 'Envío sin éxito',
            message: 'No se pudo entregar la plantilla a ningún contacto. Verifica el estado de la plantilla y los contactos.'
          });
        }
      } else {
        // Plantilla solo texto
        const result = await templateService.sendTemplate(templateName, selectedContacts, {});

        const successCount = result.results.filter((r: any) => r.success).length;
        if (successCount > 0) {
          showNotification({
            type: 'success',
            title: 'Plantilla Enviada',
            message: `Plantilla "${templateName}" enviada exitosamente a ${successCount} contactos.`
          });
        } else {
          showNotification({
            type: 'warning',
            title: 'Envío sin éxito',
            message: 'No se pudo entregar la plantilla a ningún contacto. Verifica el estado de la plantilla y los contactos.'
          });
        }
      }
      
      onSendTemplate(selectedTemplate, selectedContacts);
      setSelectedTemplate('');
    } catch (err: any) {
      console.error('Error:', err);
      showNotification({
        type: 'error',
        title: 'Error al Enviar Plantilla',
        message: err.message || 'Error al enviar la plantilla'
      });
    } finally {
      setIsSendingTemplate(false);
    }
  };

  return (
    <div className="template-panel">
        <div className="template-header">
          <h3>Plantillas de Mensajes</h3>
          {!showArchivedTemplates && (
            <TemplateProtected action="create">
              <button 
                className="create-template-btn"
                onClick={() => setShowCreateModal(true)}
              >
                <span className="material-icons">add</span>
                Agregar
              </button>
            </TemplateProtected>
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

        {/* Campo de búsqueda */}
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Buscar plantillas por nombre, contenido, categoría o estado..."
          resultsCount={filteredTemplates.length}
          totalCount={(showArchivedTemplates ? archivedTemplates : templates).length}
          className="template-search"
        />
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
        {error && <div className="template-error">{error}</div>}
        {!loading && !error && filteredTemplates.map((template) => (
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
                      APROBADO
                    </>
                  )}
                  {template.status === 'PENDING' && (
                    <>
                      <span className="material-icons">schedule</span>
                      PENDIENTE
                    </>
                  )}
                  {template.status === 'REJECTED' && (
                    <>
                      <span className="material-icons">cancel</span>
                      RECHAZADO
                    </>
                  )}
                  {template.status === 'DRAFT' && (
                    <>
                      <span className="material-icons">edit</span>
                      BORRADOR
                    </>
                  )}
                </span>
                {/* Mostrar si la plantilla tiene medios */}
                {(template.has_media || template.media_id || template.image_url) && (
                  <span className="template-media-indicator">
                    <span className="material-icons">
                      {template.media_type === 'IMAGE' ? 'image' : 
                       template.media_type === 'VIDEO' ? 'videocam' : 'description'}
                    </span>
                    {template.media_type === 'IMAGE' ? 'IMAGEN' : 
                     template.media_type === 'VIDEO' ? 'VIDEO' : 'DOCUMENTO'}
                  </span>
                )}
              </div>
              
              <div className="template-content">
                {/* Mostrar información de multimedia si existe */}
                {(template.has_media || template.media_type) && (
                  <div className="template-media-info">
                    {template.header_text && (
                      <div className="header-text">
                        <strong>Encabezado:</strong> {template.header_text}
                      </div>
                    )}
                    {/* Mostrar vista previa solo para imágenes */}
                    {template.header_handle && template.media_type === 'IMAGE' && (
                      <div className="template-media-preview">
                        <img 
                          src={Array.isArray(template.header_handle) ? template.header_handle[0] : template.header_handle}
                          alt="Vista previa de la plantilla"
                          onError={(e) => {
                            // Si la imagen falla al cargar, ocultar el elemento
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    {/* Mostrar información de archivo para videos y documentos */}
                    {(template.media_type === 'VIDEO' || template.media_type === 'DOCUMENT') && template.header_handle && (
                      <div className="template-file-info">
                        {(() => {
                          const fileInfo = getFileTypeInfo(template);
                          return (
                            <>
                              <span className="file-icon">
                                <span 
                                  className="material-icons"
                                  style={{ color: fileInfo?.color || '#00a884' }}
                                >
                                  {fileInfo?.icon || 'description'}
                                </span>
                              </span>
                              <span className="file-label">
                                {fileInfo?.label || 'Archivo'}
                              </span>
                              {template.media_id && (
                                <span className="file-id">ID: {template.media_id}</span>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                )}
                
                {/* Contenido principal de la plantilla */}
                {template.content && (
                  <p>{template.content}</p>
                )}
                
                {/* Pie de página de la plantilla */}
                {template.footer && (
                  <div className="template-footer">
                    <small>{template.footer}</small>
                  </div>
                )}
              </div>
              
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
                    <TemplateProtected action="delete">
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
                    </TemplateProtected>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="template-actions">
        <div className="selection-info">
          Contactos seleccionados: {selectedContacts.length}
        </div>
        <div className="action-buttons">
          <div className="composite-contacts-btn">
            <button 
              className={`select-contacts-btn ${selectedContacts.length === 0 ? 'alone' : ''}`}
              onClick={() => setShowContactsModal(true)}
            >
              Seleccionar Contactos ({selectedContacts.length})
            </button>
            {selectedContacts.length > 0 && (
              <button 
                className="clear-contacts-btn"
                onClick={handleDeselectAllContacts}
                title="Limpiar selección"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
                </svg>
              </button>
            )}
          </div>
          <TemplateProtected action="use" fallback={<div className="no-permission-input">No tienes permisos para enviar plantillas</div>}>
            <LoadingButton
              className="send-template-btn icon-only"
              onClick={handleSendTemplateWithMedia}
              disabled={!selectedTemplate || selectedContacts.length === 0}
              loading={isSendingTemplate}
              loadingText=""
              title="Enviar Plantilla"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
              </svg>
            </LoadingButton>
          </TemplateProtected>
        </div>
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
                onChange={(e) => {
                  const category = e.target.value;
                  setNewTemplate({ ...newTemplate, category });
                  // Si la categoría no permite medios, cambiar a texto
                  if (!categoryAllowsMedia(category)) {
                    setTemplateType('text');
                    handleClearMedia();
                  }
                }}
              >
                <option value="UTILITY">UTILITY - Recordatorios y servicios</option>
                <option value="MARKETING">MARKETING - Promociones y ofertas</option>
                <option value="TRANSACTIONAL">TRANSACTIONAL - Confirmaciones y facturas</option>
                <option value="OTP">OTP - Códigos de verificación (solo texto)</option>
              </select>
              <div className="category-description">
                {getCategoryDescription(newTemplate.category)}
              </div>
            </div>

            {/* Mostrar selector de tipo solo si la categoría permite medios */}
            {categoryAllowsMedia(newTemplate.category) && (
              <div className="template-type-selector">
                <label>Tipo de Plantilla:</label>
                <div className="template-type-buttons">
                  <button
                    className={`type-btn ${templateType === 'text' ? 'active' : ''}`}
                    onClick={() => setTemplateType('text')}
                  >
                    📝 Solo Texto
                  </button>
                  <button
                    className={`type-btn ${templateType === 'media' ? 'active' : ''}`}
                    onClick={() => setTemplateType('media')}
                  >
                    🖼️ Con Multimedia
                  </button>
                </div>
                <div className="type-description">
                  {templateType === 'text' 
                    ? 'Plantilla tradicional sin medios'
                    : 'Plantilla con imagen o video en el encabezado'
                  }
                </div>
              </div>
            )}

            {/* Mostrar mensaje si la categoría no permite medios */}
            {!categoryAllowsMedia(newTemplate.category) && (
              <div className="category-warning">
                <div className="warning-icon">ℹ️</div>
                <div className="warning-text">
                  La categoría {newTemplate.category} no permite medios multimedia.
                </div>
              </div>
            )}

            {/* Información de ayuda sobre categorías */}
            <div className="category-help">
              <details>
                <summary>ℹ️ Información sobre categorías</summary>
                <div className="help-content">
                  <div className="help-section">
                    <h5>✅ Categorías con imágenes:</h5>
                    <ul>
                      <li><strong>UTILITY:</strong> Recordatorios y servicios informativos</li>
                      <li><strong>MARKETING:</strong> Promociones y ofertas comerciales</li>
                      <li><strong>TRANSACTIONAL:</strong> Confirmaciones de pedidos y facturas</li>
                    </ul>
                  </div>
                  <div className="help-section">
                    <h5>❌ Solo texto:</h5>
                    <ul>
                      <li><strong>OTP:</strong> Códigos de verificación</li>
                    </ul>
                  </div>
                </div>
              </details>
            </div>

            {/* MediaSelector para plantillas con medios */}
            {templateType === 'media' && categoryAllowsMedia(newTemplate.category) && (
              <>
                <MediaSelector
                  onMediaSelected={handleMediaSelected}
                  onImageUrlSelected={handleImageUrlSelected}
                  onFileSelected={handleFileSelected}
                  onClear={handleClearMedia}
                  selectedMediaId={selectedMediaId}
                  selectedMediaType={selectedMediaType}
                  selectedImageUrl={selectedImageUrl}
                  selectedFile={selectedFile || undefined}
                  mode="template"
                />
              </>
            )}

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
              <label>Pie de Página:</label>
              <input
                type="text"
                value={newTemplate.footer}
                readOnly
                placeholder="Sector del usuario (automático)"
              />
            </div>
            <div className="modal-actions">
              <LoadingButton 
                onClick={templateType === 'media' ? handleCreateTemplateWithMedia : handleCreateTemplate}
                disabled={!newTemplate.name || !newTemplate.content || 
                         (templateType === 'media' && categoryAllowsMedia(newTemplate.category) && 
                          !selectedFile && !selectedImageUrl)}
                loading={isCreatingTemplate}
                loadingText="Creando..."
              >
                {templateType === 'media' ? 'Crear con Medio' : 'Crear Plantilla'}
              </LoadingButton>
              <button onClick={() => {
                setShowCreateModal(false);
                setTemplateType('text');
                handleClearMedia();
              }}
              disabled={isCreatingTemplate}>
                Cancelar
              </button>
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

export default TemplatePanel;