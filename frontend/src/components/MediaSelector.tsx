import React, { useState, useRef } from 'react';
import '../styles/MediaSelector.css';
import { useNotifications } from './NotificationContainer';
import LoadingButton from './LoadingButton';

interface MediaSelectorProps {
  onMediaSelected: (mediaId: string, mediaType: string, mediaUrl?: string) => void;
  onImageUrlSelected?: (imageUrl: string) => void;
  onFileSelected?: (file: File, mediaType: string) => void;
  onClear: () => void;
  selectedMediaId?: string;
  selectedMediaType?: string;
  selectedImageUrl?: string;
  selectedFile?: File;
  mode?: 'message' | 'template'; // Nuevo prop para distinguir el modo
}

const MediaSelector: React.FC<MediaSelectorProps> = ({
  onMediaSelected,
  onImageUrlSelected,
  onFileSelected,
  onClear,
  selectedMediaId,
  selectedMediaType,
  selectedImageUrl,
  selectedFile,
  mode = 'message'
}) => {
  const { showNotification } = useNotifications();
  const [activeTab, setActiveTab] = useState<'upload' | 'url'>('upload');
  const [uploading, setUploading] = useState(false);
  const [imageUrl, setImageUrl] = useState(selectedImageUrl || '');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validar formatos soportados por WhatsApp para plantillas
    if (mode === 'template' && !isWhatsAppSupportedFormat(file.type, file.name)) {
      showNotification({
        type: 'warning',
        title: 'Formato No Soportado',
        message: `Formato no soportado por WhatsApp: ${file.type || file.name}. Formatos soportados para plantillas: Imágenes (JPEG, PNG), Videos (MP4, 3GPP), Documentos (PDF)`
      });
      return;
    }

    const mediaType = getMediaType(file.type, file.name);
    
    if (mode === 'template' && onFileSelected) {
      // Para plantillas, solo pasamos el archivo sin subirlo aún
      // El backend se encargará de la subida usando la API de subida reanudable
      onFileSelected(file, mediaType);
      return;
    }

    // Para mensajes, mantenemos el flujo original
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/media/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error al subir el archivo');
      }

      const result = await response.json();
      onMediaSelected(result.id, mediaType, result.url);
    } catch (error) {
      console.error('Error uploading file:', error);
      showNotification({
        type: 'error',
        title: 'Error al Subir Archivo',
        message: 'No se pudo subir el archivo. Intenta nuevamente.'
      });
    } finally {
      setUploading(false);
    }
  };

  const getMediaType = (mimeType: string, fileName?: string): string => {
    // Detectar tipo basado en MIME type
    if (mimeType.startsWith('image/')) return 'IMAGE';
    if (mimeType.startsWith('video/')) return 'VIDEO';
    if (mimeType.startsWith('application/')) return 'DOCUMENT';
    
    // Si el MIME type no es claro, intentar detectar por extensión del archivo
    if (fileName) {
      const extension = fileName.toLowerCase().split('.').pop();
      if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension || '')) {
        return 'IMAGE';
      }
      if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', '3gp', '3gpp'].includes(extension || '')) {
        return 'VIDEO';
      }
      if (['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'].includes(extension || '')) {
        return 'DOCUMENT';
      }
    }
    
    // Por defecto, asumir que es imagen
    return 'IMAGE';
  };

  // Validar formatos soportados por WhatsApp para plantillas multimedia
  const isWhatsAppSupportedFormat = (mimeType: string, fileName?: string): boolean => {
    const supportedFormats = [
      // Imágenes
      'image/jpeg',
      'image/jpg', 
      'image/png',
      // Videos
      'video/mp4',
      'video/3gpp',
      'video/3gp',
      // Documentos
      'application/pdf'
    ];
    
    // Verificar MIME type
    if (supportedFormats.includes(mimeType.toLowerCase())) {
      return true;
    }
    
    // Si el MIME type no está en la lista, verificar por extensión del archivo
    if (fileName) {
      const extension = fileName.toLowerCase().split('.').pop();
      const supportedExtensions = ['jpg', 'jpeg', 'png', 'mp4', '3gp', '3gpp', 'pdf'];
      return supportedExtensions.includes(extension || '');
    }
    
    return false;
  };



  const handleImageUrlSubmit = () => {
    if (imageUrl.trim()) {
      onImageUrlSelected?.(imageUrl.trim());
    }
  };

  const handleClear = () => {
    setImageUrl('');
    onClear();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileDisplayName = (file: File) => {
    if (file.name.length > 20) {
      return file.name.substring(0, 17) + '...';
    }
    return file.name;
  };

  return (
    <div className="media-selector">
      <div className="media-selector-tabs">
        <button
          className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📁 Subir Archivo
        </button>
        <button
          className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
          onClick={() => setActiveTab('url')}
        >
          🌐 URL de Imagen
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="upload-section">
          <div className="file-upload-area">
            <input
              ref={fileInputRef}
              type="file"
              accept={mode === 'template' ? 'image/jpeg,image/jpg,image/png,video/mp4,application/pdf' : 'image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <LoadingButton
              className="upload-btn"
              onClick={() => fileInputRef.current?.click()}
              loading={uploading}
              loadingText="⏳ Subiendo..."
            >
              📁 Seleccionar Archivo
            </LoadingButton>
            <p className="upload-hint">
              {mode === 'template' 
                ? 'Formatos soportados por WhatsApp: JPEG, PNG, MP4, 3GPP, PDF'
                : 'Formatos soportados: JPG, PNG, GIF, MP4, PDF, DOC, etc.'}
            </p>
          </div>
        </div>
      )}

      {activeTab === 'url' && (
        <div className="url-section">
          <div className="url-input-group">
            <input
              type="url"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://ejemplo.com/imagen.jpg"
              className="url-input"
            />
            <button
              onClick={handleImageUrlSubmit}
              className="url-submit-btn"
              disabled={!imageUrl.trim()}
            >
              Usar URL
            </button>
          </div>
          <p className="url-hint">
            Ingresa la URL de una imagen pública
          </p>
        </div>
      )}

      {(selectedMediaId || selectedImageUrl || selectedFile) && (
        <div className="selected-media">
          <div className="selected-media-info">
            <span className="media-type-icon">
              {selectedMediaType === 'IMAGE' ? '🖼️' : 
               selectedMediaType === 'VIDEO' ? '🎥' : '📄'}
            </span>
            <span className="media-label">
              {selectedFile ? `Archivo: ${getFileDisplayName(selectedFile)}` :
               selectedMediaId ? 'Archivo subido' : 'URL de imagen'}
            </span>
          </div>
          <button onClick={handleClear} className="clear-media-btn">
            ×
          </button>
        </div>
      )}
    </div>
  );
};

export default MediaSelector; 