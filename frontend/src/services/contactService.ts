export interface Contact {
  phone_number: string;
  name: string;
  last_interaction: string | null;
  is_active: boolean;
}

export interface ContactCreateRequest {
  phone_number: string;
  name: string;
  is_active: boolean;
}

export interface ContactUpdateRequest {
  name: string;
  is_active: boolean;
}

class ContactService {
  private baseUrl = 'http://localhost:8000/api';

  async getContacts(): Promise<Contact[]> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts`);
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
        headers: {
          'Content-Type': 'application/json',
        },
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

  async updateContact(phoneNumber: string, contact: ContactUpdateRequest): Promise<Contact> {
    try {
      const response = await fetch(`${this.baseUrl}/contacts/${phoneNumber}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
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
      const response = await fetch(`${this.baseUrl}/contacts/${phoneNumber}`);
      
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