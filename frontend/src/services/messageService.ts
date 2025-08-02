export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: string;
  status?: 'sending' | 'sent' | 'delivered' | 'error';
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface MessagesResponse {
  messages: Message[];
  pagination: PaginationInfo;
}

export const messageService = {
  async getMessages(phoneNumber: string, page: number = 1, limit: number = 50): Promise<MessagesResponse> {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/messages/${phoneNumber}?page=${page}&limit=${limit}`);
      if (!response.ok) {
        throw new Error('Error al cargar mensajes');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching messages:', error);
      return { messages: [], pagination: { page: 1, limit, total: 0, total_pages: 0, has_next: false, has_prev: false } };
    }
  },

  async getRecentMessages(phoneNumber: string, limit: number = 20): Promise<Message[]> {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/messages/${phoneNumber}/recent?limit=${limit}`);
      if (!response.ok) {
        throw new Error('Error al cargar mensajes recientes');
      }
      const data = await response.json();
      return data.messages;
    } catch (error) {
      console.error('Error fetching recent messages:', error);
      return [];
    }
  },

  async getOlderMessages(phoneNumber: string, beforeTimestamp: string, limit: number = 50): Promise<{messages: Message[], hasMore: boolean}> {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/messages/${phoneNumber}/older?before_timestamp=${beforeTimestamp}&limit=${limit}`);
      if (!response.ok) {
        throw new Error('Error al cargar mensajes más antiguos');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching older messages:', error);
      return { messages: [], hasMore: false };
    }
  },

  async sendMessage(phoneNumber: string, message: string): Promise<boolean> {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/messages/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          message: message
        }),
      });
      
      if (!response.ok) {
        throw new Error('Error al enviar mensaje');
      }
      
      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Error sending message:', error);
      return false;
    }
  }
};