/**
 * Client Management API Service
 * Handles all client-related operations for the new multi-client architecture
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Get API base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Client configuration interface
export interface Client {
  id?: string;
  name: string;
  description?: string;
  base_url: string;
  tenant: string;
  branch?: string;
  username?: string;  // Only for creation/update
  password?: string;  // Only for creation/update
  endpoint_name?: string;
  endpoint_version?: string;
  locale?: string;
  verify_ssl?: boolean;
  persistent_login?: boolean;
  retry_on_idle_logout?: boolean;
  timeout?: number;
  rate_limit_calls_per_second?: number;
  cache_methods?: boolean;
  cache_ttl_hours?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  last_connected_at?: string;
}

// Service and Model interfaces (same as before)
export interface ServiceInfo {
  name: string;
  methods: string[];
  method_count: number;
  error?: string;
}

export interface ServiceMethod {
  name: string;
  signature?: string;
  docstring?: string;
  doc?: string;
  type?: string;
  error?: string;
}

export interface ServiceDetails {
  name: string;
  url?: string;
  methods: ServiceMethod[];
  description: string;
  total_methods: number;
}

export interface ModelInfo {
  name: string;
  field_count: number;
  error?: string;
}

export interface ModelField {
  type: string;
  required?: boolean;
  description?: string;
  default?: any;
  max_length?: number;
  choices?: string[];
  value?: string;
}

export interface ModelDetails {
  name: string;
  fields: Record<string, ModelField>;
  field_count: number;
  methods: string[];
  description: string;
  key_fields: string[];
  schema: any;
}

class ClientApiService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Important for session management
    });

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.data?.error) {
          throw new Error(error.response.data.error);
        }
        throw error;
      }
    );
  }

  // ========== Client Management ==========

  /**
   * List all clients with optional filtering
   */
  async listClients(params?: { active?: boolean; search?: string }) {
    const response = await this.axiosInstance.get('/v1/clients', { params });
    return response.data;
  }

  /**
   * Create a new client configuration
   */
  async createClient(client: Client) {
    const response = await this.axiosInstance.post('/v1/clients', client);
    return response.data;
  }

  /**
   * Get details of a specific client
   */
  async getClient(clientId: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}`);
    return response.data;
  }

  /**
   * Update a client configuration
   */
  async updateClient(clientId: string, updates: Partial<Client>) {
    const response = await this.axiosInstance.put(`/v1/clients/${clientId}`, updates);
    return response.data;
  }

  /**
   * Delete a client configuration
   */
  async deleteClient(clientId: string) {
    await this.axiosInstance.delete(`/v1/clients/${clientId}`);
    return { success: true };
  }

  /**
   * Test connection to a client
   */
  async testClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/test`);
    return response.data;
  }

  /**
   * Connect to a client (establish session)
   */
  async connectToClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/connect`);
    return response.data;
  }

  /**
   * Disconnect from a client
   */
  async disconnectFromClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/disconnect`);
    return response.data;
  }

  /**
   * Rebuild/refresh a client connection (invalidate cache and reconnect)
   */
  async rebuildClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/rebuild`);
    return response.data;
  }

  // ========== Service Browsing (Client-specific) ==========

  /**
   * List services for a specific client
   */
  async listServices(clientId: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/services`);
    return response.data;
  }

  /**
   * Get service details for a specific client
   */
  async getServiceDetails(clientId: string, serviceName: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/services/${serviceName}`);
    return response.data;
  }

  // ========== Model Browsing (Client-specific) ==========

  /**
   * List models for a specific client
   */
  async listModels(clientId: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/models`);
    return response.data;
  }

  /**
   * Get model details for a specific client
   */
  async getModelDetails(clientId: string, modelName: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/models/${modelName}`);
    return response.data;
  }

  // ========== Client Activation ==========

  /**
   * Activate a client
   */
  async activateClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/activate`);
    return response.data;
  }

  /**
   * Deactivate a client
   */
  async deactivateClient(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/deactivate`);
    return response.data;
  }

  // ========== Health & Status ==========

  /**
   * Check API health
   */
  async healthCheck() {
    const response = await this.axiosInstance.get('/health');
    return response.data;
  }

  /**
   * Get API root info
   */
  async getApiInfo() {
    const response = await this.axiosInstance.get('/');
    return response.data;
  }
}

// Export singleton instance
export const clientApi = new ClientApiService();