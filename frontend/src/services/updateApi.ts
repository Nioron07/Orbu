/**
 * Update API Service
 * Handles version checking and auto-update deployment
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Get API base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Current version response
export interface CurrentVersionResponse {
  success: boolean;
  version: string;
  platform: string;
  can_auto_update: boolean;
}

// Update check response
export interface UpdateCheckResponse {
  success: boolean;
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  release_url: string | null;
  release_notes: string;
  platform: string;
  can_auto_update: boolean;
  error?: string;
}

// Deploy response
export interface DeployResponse {
  success: boolean;
  message?: string;
  error?: string;
  service?: string;
  region?: string;
}

class UpdateApi {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
    });

    // Add auth token interceptor
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('orbu_access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  /**
   * Get current version info (no GitHub API call)
   */
  async getCurrentVersion(): Promise<CurrentVersionResponse> {
    const response = await this.api.get<CurrentVersionResponse>('/updates/current');
    return response.data;
  }

  /**
   * Check GitHub for latest release (admin only)
   */
  async checkForUpdates(): Promise<UpdateCheckResponse> {
    const response = await this.api.get<UpdateCheckResponse>('/updates/check');
    return response.data;
  }

  /**
   * Trigger deployment update (admin only, GCP only)
   */
  async triggerDeploy(): Promise<DeployResponse> {
    const response = await this.api.post<DeployResponse>('/updates/deploy');
    return response.data;
  }
}

export const updateApi = new UpdateApi();
