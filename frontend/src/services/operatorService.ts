import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface Operator {
  id: number;
  cedula: string;
  name: string;
  expedition_date: string;
  is_active: boolean;
  created_at: string;
}

export interface OperatorCreateRequest {
  cedula: string;
  name: string;
  expedition_date: string;
}

export interface OperatorUpdateRequest {
  name?: string;
  expedition_date?: string;
  is_active?: boolean;
}

export interface OperatorListResponse {
  operators: Operator[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface BulkCreateResponse {
  message: string;
  results: {
    created: number;
    skipped: number;
    errors: string[];
    duplicates: string[];
  };
}

class OperatorService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async getOperators(
    page: number = 1,
    perPage: number = 10,
    search: string = ''
  ): Promise<OperatorListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...(search && { search }),
    });

    return this.makeRequest<OperatorListResponse>(`/operators?${params}`);
  }

  async getOperator(cedula: string): Promise<Operator> {
    return this.makeRequest<Operator>(`/operators/${cedula}`);
  }

  async createOperator(operator: OperatorCreateRequest): Promise<Operator> {
    return this.makeRequest<Operator>('/operators', {
      method: 'POST',
      body: JSON.stringify(operator),
    });
  }

  async updateOperator(cedula: string, operator: OperatorUpdateRequest): Promise<Operator> {
    return this.makeRequest<Operator>(`/operators/${cedula}`, {
      method: 'PUT',
      body: JSON.stringify(operator),
    });
  }

  async deleteOperator(cedula: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>(`/operators/${cedula}`, {
      method: 'DELETE',
    });
  }

  async createOperatorsBulk(operators: OperatorCreateRequest[]): Promise<BulkCreateResponse> {
    return this.makeRequest<BulkCreateResponse>('/operators/bulk', {
      method: 'POST',
      body: JSON.stringify(operators),
    });
  }
}

export const operatorService = new OperatorService();
