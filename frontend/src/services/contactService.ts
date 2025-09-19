import { getAuthHeaders } from '../utils/auth';

// Definir las opciones de tipo de contacto para referencia
export const VALID_CONTACT_TYPES = ['Administrativo', 'Operario', 'Proveedor', 'Cliente', 'Otro'] as const;
export type ContactTypeEnum = typeof VALID_CONTACT_TYPES[number];

export interface Contact {
  phone_number: string;
  name: string;
  contact_type?: string | null;
  last_interaction: string | null;
  is_active: boolean;
}

export interface ContactCreateRequest {
  phone_number: string;
  name: string;
  contact_type?: string;
  is_active: boolean;
}

export interface ContactUpdateRequest {
  name: string;
  contact_type?: string;
  is_active: boolean;
}

class ContactService {
  private baseUrl = `${import.meta.env.VITE_API_BASE_URL}/api`;

  async getContacts(): Promise<Contact[]> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Error al obtener contactos');
      }
      const data = await response.json();
      return data.contacts || [];
    } catch (error) {
      console.error('Error fetching contacts:', error);
      throw error;
    }
  }

  async createContact(contact: ContactCreateRequest): Promise<Contact> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(contact),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear contacto');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating contact:', error);
      throw error;
    }
  }

  async createContactsBulk(contacts: ContactCreateRequest[]): Promise<{message: string, results: {created: number, skipped: number, errors: string[], duplicates: string[]}}> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts/bulk`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(contacts),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al importar contactos');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating contacts bulk:', error);
      throw error;
    }
  }

  async updateContact(phoneNumber: string, contact: ContactUpdateRequest): Promise<Contact> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts/${phoneNumber}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(contact),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al actualizar contacto');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating contact:', error);
      throw error;
    }
  }

  async deleteContact(phoneNumber: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts/${phoneNumber}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al eliminar contacto');
      }
    } catch (error) {
      console.error('Error deleting contact:', error);
      throw error;
    }
  }

  async getContact(phoneNumber: string): Promise<Contact> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts/${phoneNumber}`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al obtener contacto');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting contact:', error);
      throw error;
    }
  }
}

export const contactService = new ContactService(); 