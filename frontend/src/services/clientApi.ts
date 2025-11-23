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
  api_key?: string;   // Full API key - always unmasked for internal use
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

// Endpoint interfaces
export interface Endpoint {
  id: string;
  client_id: string;
  service_name: string;
  method_name: string;
  display_name?: string;
  description?: string;
  request_schema: any;
  response_schema: any;
  is_active: boolean;
  log_retention_hours: number;
  url_path: string;
  created_at: string;
  updated_at: string;
  stats?: EndpointStats;
}

export interface EndpointStats {
  total_executions: number;
  avg_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
  successful: number;
  failed: number;
  success_rate: number;
}

export interface EndpointExecution {
  id: string;
  endpoint_id: string;
  executed_at: string;
  duration_ms: number;
  status_code: number;
  error_message?: string;
  request_method?: string;
  request_path?: string;
  ip_address?: string;
  user_agent?: string;
  request_data?: any;
  response_data?: any;
}

export interface CreateEndpointRequest {
  service_name: string;
  method_name: string;
  display_name?: string;
  description?: string;
  auto_generate_schema?: boolean;
  request_schema?: any;
  response_schema?: any;
  is_active?: boolean;
}

export interface DeployServiceRequest {
  service_name: string;
  methods?: string[];
  auto_generate_schema?: boolean;
  log_retention_hours?: number;
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

  // ========== API Key Management ==========

  /**
   * Get the full API key for a client
   */
  async getApiKey(clientId: string) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/api-key`);
    return response.data;
  }

  /**
   * Regenerate API key for a client
   */
  async regenerateApiKey(clientId: string) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/regenerate-api-key`);
    return response.data;
  }

  // ========== Endpoint Management ==========

  /**
   * List all endpoints for a client
   */
  async listEndpoints(clientId: string, params?: { is_active?: boolean; service_name?: string; method_name?: string }) {
    const response = await this.axiosInstance.get(`/v1/clients/${clientId}/endpoints`, { params });
    return response.data;
  }

  /**
   * Create a single endpoint
   */
  async createEndpoint(clientId: string, data: CreateEndpointRequest) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/endpoints`, data);
    return response.data;
  }

  /**
   * Deploy all methods of a service as endpoints
   */
  async deployService(clientId: string, data: DeployServiceRequest) {
    const response = await this.axiosInstance.post(`/v1/clients/${clientId}/endpoints/batch`, data);
    return response.data;
  }

  /**
   * Get endpoint details
   */
  async getEndpoint(endpointId: string) {
    const response = await this.axiosInstance.get(`/v1/endpoints/${endpointId}`);
    return response.data;
  }

  /**
   * Update an endpoint
   */
  async updateEndpoint(endpointId: string, updates: Partial<Endpoint>) {
    const response = await this.axiosInstance.put(`/v1/endpoints/${endpointId}`, updates);
    return response.data;
  }

  /**
   * Delete an endpoint
   */
  async deleteEndpoint(endpointId: string) {
    const response = await this.axiosInstance.delete(`/v1/endpoints/${endpointId}`);
    return response.data;
  }

  /**
   * Activate an endpoint
   */
  async activateEndpoint(endpointId: string) {
    const response = await this.axiosInstance.post(`/v1/endpoints/${endpointId}/activate`);
    return response.data;
  }

  /**
   * Deactivate an endpoint
   */
  async deactivateEndpoint(endpointId: string) {
    const response = await this.axiosInstance.post(`/v1/endpoints/${endpointId}/deactivate`);
    return response.data;
  }

  /**
   * Get execution logs for an endpoint with filtering
   */
  async getEndpointLogs(
    endpointId: string,
    options: {
      limit?: number;
      offset?: number;
      status?: number;
      search?: string;
      since?: string;
      until?: string;
    } = {}
  ) {
    const params = {
      limit: options.limit || 50,
      offset: options.offset || 0,
      ...(options.status && { status: options.status }),
      ...(options.search && { search: options.search }),
      ...(options.since && { since: options.since }),
      ...(options.until && { until: options.until }),
    };
    const response = await this.axiosInstance.get(`/v1/endpoints/${endpointId}/logs`, { params });
    return response.data;
  }

  /**
   * Test an endpoint with parameters
   */
  async testEndpoint(endpointId: string, requestBody: any = {}) {
    const response = await this.axiosInstance.post(`/v1/endpoints/${endpointId}/test`, requestBody);
    return response.data;
  }

  /**
   * Execute an endpoint using API key (for external services)
   */
  async executeEndpoint(clientId: string, serviceName: string, methodName: string, requestBody: any, apiKey: string) {
    const response = await this.axiosInstance.post(
      `/v1/endpoints/${clientId}/${serviceName}/${methodName}`,
      requestBody,
      {
        headers: {
          'X-API-Key': apiKey
        }
      }
    );
    return response.data;
  }
}

// Export singleton instance
export const clientApi = new ClientApiService();