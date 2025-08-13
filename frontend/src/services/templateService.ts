export interface Template {
  id: string;
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  status: 'APPROVED' | 'PENDING' | 'REJECTED' | 'DRAFT';
  rejected_reason?: string;
  created_at: string;
  footer?: string;
  is_archived?: boolean;
  // Nuevos campos para plantillas con medios
  has_media?: boolean;
  header_text?: string;
  media_type?: 'IMAGE' | 'VIDEO' | 'DOCUMENT';
  media_id?: string;
  image_url?: string;
  header_handle?: string;
}

export interface TemplateRequest {
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  footer?: string;
}

export interface TemplateWithMediaRequest {
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  footer?: string;
  header_text?: string;
  media_type?: 'IMAGE' | 'VIDEO' | 'DOCUMENT';
  media_id?: string;
  image_url?: string;
}

export interface MediaUploadResponse {
  id: string;
  media_id?: string;
  url?: string;
  success?: boolean;
  filename?: string;
}

export const templateService = {
  async getTemplates(): Promise<Template[]> {
    try {
      const response = await fetch('http://localhost:8000/api/templates');
      if (!response.ok) {
        throw new Error('Error al cargar plantillas');
      }
      
      const data = await response.json();
      
      // Manejar tanto la respuesta de WhatsApp API como plantillas locales
      let templatesList: Template[] = [];
      
      if (data.data) {
        // Respuesta de WhatsApp Business API
        templatesList = data.data.map((template: any) => ({
          id: template.id || template.name,
          name: template.name,
          content: template.components?.find((c: any) => c.type === 'BODY')?.text || '',
          category: template.category,
          status: template.status,
          created_at: template.created_at || new Date().toISOString(),
          language: template.language,
          footer: template.components?.find((c: any) => c.type === 'FOOTER')?.text || '',
          is_archived: template.is_archived || false
        }));
      } else if (data.templates) {
        // Plantillas del backend (incluye información multimedia)
        templatesList = data.templates.map((template: any) => ({
          id: template.id,
          name: template.name,
          content: template.content || template.components?.find((c: any) => c.type === 'BODY')?.text || '',
          category: template.category,
          status: template.status,
          created_at: template.created_at || new Date().toISOString(),
          language: template.language,
          footer: template.footer || template.components?.find((c: any) => c.type === 'FOOTER')?.text || '',
          is_archived: template.is_archived || false,
          // Incluir información multimedia
          has_media: template.has_media || false,
          media_type: template.media_type || '',
          header_text: template.header_text || '',
          header_handle: template.header_handle || '',
          media_id: template.media_id || '',
          image_url: template.image_url || ''
        }));
      } else if (Array.isArray(data)) {
        // Plantillas locales
        templatesList = data;
      }
      
      return templatesList;
    } catch (error) {
      console.error('Error fetching templates:', error);
      return [];
    }
  },

  async getArchivedTemplates(): Promise<Template[]> {
    try {
      const response = await fetch('http://localhost:8000/api/templates/archived');
      if (!response.ok) {
        throw new Error('Error al cargar plantillas archivadas');
      }
      
      const data = await response.json();
      return data.templates || [];
    } catch (error) {
      console.error('Error fetching archived templates:', error);
      return [];
    }
  },

  async archiveTemplate(templateId: string): Promise<boolean> {
    try {
      const response = await fetch(`http://localhost:8000/api/templates/${encodeURIComponent(templateId)}/archive`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al archivar plantilla');
      }
      
      return true;
    } catch (error) {
      console.error('Error archiving template:', error);
      throw error;
    }
  },

  async unarchiveTemplate(templateId: string): Promise<boolean> {
    try {
      const response = await fetch(`http://localhost:8000/api/templates/${encodeURIComponent(templateId)}/unarchive`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al desarchivar plantilla');
      }
      
      return true;
    } catch (error) {
      console.error('Error unarchiving template:', error);
      throw error;
    }
  },

  async createTemplate(template: TemplateRequest): Promise<any> {
    try {
      const response = await fetch('http://localhost:8000/api/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(template),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear plantilla');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating template:', error);
      throw error;
    }
  },

  async deleteTemplate(templateName: string): Promise<boolean> {
    try {
      const response = await fetch(`http://localhost:8000/api/templates/${encodeURIComponent(templateName)}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al eliminar plantilla');
      }
      
      return true;
    } catch (error) {
      console.error('Error deleting template:', error);
      throw error;
    }
  },

  async sendTemplate(templateName: string, phoneNumbers: string[], parameters?: any): Promise<any> {
    try {
      const response = await fetch('http://localhost:8000/api/templates/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_name: templateName,
          phone_numbers: phoneNumbers,
          parameters: parameters || {}
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al enviar plantilla');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error sending template:', error);
      throw error;
    }
  },

  async uploadMedia(file: File): Promise<MediaUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/api/media/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al subir medio');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading media:', error);
      throw error;
    }
  },

  async uploadMediaFromBase64(base64Data: string, filename: string, fileType: string): Promise<MediaUploadResponse> {
    try {
      const response = await fetch('http://localhost:8000/api/media/upload-base64', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base64_data: base64Data,
          filename: filename,
          file_type: fileType
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al subir medio');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading media from base64:', error);
      throw error;
    }
  },

  async uploadMediaFile(file: File): Promise<MediaUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/api/media/upload-file', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al subir archivo');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading media file:', error);
      throw error;
    }
  },

  async createTemplateWithMedia(template: TemplateWithMediaRequest): Promise<any> {
    try {
      // Validaciones del lado del cliente
      if (!template.name || template.name.trim() === '') {
        throw new Error('El nombre de la plantilla es requerido');
      }
      
      if (!template.content || template.content.trim() === '') {
        throw new Error('El contenido de la plantilla es requerido');
      }
      
      if (!template.media_id && !template.image_url) {
        throw new Error('Se requiere un medio (imagen, video o documento) para crear esta plantilla');
      }
      
      console.log('Sending template with media:', template);
      
      const response = await fetch('http://localhost:8000/api/templates/with-media', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(template),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        
        // Proporcionar mensajes de error más específicos
        if (response.status === 400) {
          if (errorData.detail && (errorData.detail.includes('media_id') || errorData.detail.includes('image_url'))) {
            throw new Error('Se requiere un medio (imagen, video o documento) para crear esta plantilla');
          } else if (errorData.detail && errorData.detail.includes('name')) {
            throw new Error('El nombre de la plantilla no es válido. Use solo letras, números y guiones bajos');
          } else if (errorData.detail && errorData.detail.includes('category')) {
            throw new Error('La categoría de la plantilla no es válida');
          } else if (errorData.detail && errorData.detail.includes('content')) {
            throw new Error('El contenido de la plantilla es requerido');
          } else {
            throw new Error(`Error en la solicitud: ${errorData.detail || 'Datos inválidos'}`);
          }
        } else if (response.status === 401) {
          throw new Error('Error de autenticación. Verifique su token de acceso');
        } else if (response.status === 403) {
          throw new Error('No tiene permisos para crear plantillas');
        } else if (response.status === 500) {
          throw new Error('Error interno del servidor. Intente nuevamente');
        } else {
          throw new Error(errorData.detail || 'Error al crear plantilla con medio');
        }
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating template with media:', error);
      throw error;
    }
  },

  async sendTemplateWithMedia(
    templateName: string, 
    phoneNumbers: string[], 
    mediaId: string,
    parameters?: any,
    headerParameters?: any
  ): Promise<any> {
    try {
      const response = await fetch('http://localhost:8000/api/templates/send-with-media', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_name: templateName,
          phone_numbers: phoneNumbers,
          media_id: mediaId,
          parameters: parameters || {},
          header_parameters: headerParameters || {}
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al enviar plantilla con medio');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error sending template with media:', error);
      throw error;
    }
  }
}; 