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
}

export interface TemplateRequest {
  name: string;
  content: string;
  category: 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP';
  footer?: string;
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
        // Plantillas hardcodeadas de fallback
        templatesList = data.templates.map((template: any) => ({
          id: template.id,
          name: template.name,
          content: template.components?.find((c: any) => c.type === 'BODY')?.text || '',
          category: template.category,
          status: template.status,
          created_at: new Date().toISOString(),
          language: template.language,
          footer: template.components?.find((c: any) => c.type === 'FOOTER')?.text || '',
          is_archived: template.is_archived || false
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
  }
}; 