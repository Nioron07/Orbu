/**
 * Authentication API Service
 * Handles login, logout, registration, and user management
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Get API base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// User settings interface
export interface UserSettings {
  theme?: 'light' | 'dark';
  autoConnectMode?: 'manual' | 'last' | 'default';
  defaultClientId?: string | null;
  lastConnectedClientId?: string | null;
}

// User interface
export interface User {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  is_active: boolean;
  is_approved: boolean;
  settings: UserSettings;
  created_at: string;
  updated_at?: string;
  last_login_at?: string;
}

// App config interface
export interface AppConfig {
  orgName: string;
}

// Login response
export interface LoginResponse {
  success: boolean;
  access_token: string;
  refresh_token: string;
  user: User;
}

// Register request
export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

// Update user request (admin)
export interface UpdateUserRequest {
  name?: string;
  is_admin?: boolean;
  is_active?: boolean;
}

class AuthApiService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      response => response,
      error => {
        const errorMessage = error.response?.data?.error || '';

        // If signature verification failed, the JWT secret changed (app was updated)
        // Force logout and reload to get new tokens
        if (errorMessage.includes('Signature verification failed') ||
            errorMessage.includes('Invalid token')) {
          console.warn('[AuthApi] Token invalid after update, forcing logout');
          this.forceLogoutOnTokenInvalid();
        }

        if (errorMessage) {
          throw new Error(errorMessage);
        }
        throw error;
      }
    );
  }

  /**
   * Force logout when token becomes invalid (e.g., after app update)
   * Clears tokens and reloads the page to redirect to login
   */
  private forceLogoutOnTokenInvalid() {
    // Clear tokens from storage
    localStorage.removeItem('orbu_access_token');
    localStorage.removeItem('orbu_refresh_token');

    // Clear auth header
    delete this.axiosInstance.defaults.headers.common['Authorization'];

    // Redirect to login, preserving the current page for post-login redirect
    const currentPath = window.location.pathname + window.location.search;
    const redirect = currentPath && currentPath !== '/login' ? `&redirect=${encodeURIComponent(currentPath)}` : '';
    window.location.href = `/login?reason=session_expired${redirect}`;
  }

  /**
   * Set the auth token for all requests
   */
  setAuthToken(token: string | null) {
    if (token) {
      this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.axiosInstance.defaults.headers.common['Authorization'];
    }
  }

  // ========== Authentication ==========

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.axiosInstance.post('/auth/login', { email, password });
    return response.data;
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    await this.axiosInstance.post('/auth/logout');
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await this.axiosInstance.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<{ user: User }> {
    const response = await this.axiosInstance.get('/auth/me');
    return response.data;
  }

  /**
   * Get current user's settings
   */
  async getUserSettings(): Promise<{ settings: UserSettings }> {
    const response = await this.axiosInstance.get('/auth/me/settings');
    return response.data;
  }

  /**
   * Update current user's settings
   */
  async updateUserSettings(settings: Partial<UserSettings>): Promise<{ settings: UserSettings }> {
    const response = await this.axiosInstance.put('/auth/me/settings', settings);
    return response.data;
  }

  /**
   * Get app configuration (org name, etc.)
   */
  async getAppConfig(): Promise<{ config: AppConfig }> {
    const response = await this.axiosInstance.get('/auth/config');
    return response.data;
  }

  /**
   * Register a new account (pending approval)
   */
  async register(data: RegisterRequest): Promise<{ success: boolean; message: string }> {
    const response = await this.axiosInstance.post('/auth/register', data);
    return response.data;
  }

  // ========== Admin: User Management ==========

  /**
   * List all users (admin only)
   */
  async listUsers(status?: 'pending' | 'approved' | 'deactivated'): Promise<{ users: User[]; total: number }> {
    const params = status ? { status } : {};
    const response = await this.axiosInstance.get('/auth/users', { params });
    return response.data;
  }

  /**
   * List pending user requests (admin only)
   */
  async listPendingUsers(): Promise<{ users: User[]; total: number }> {
    const response = await this.axiosInstance.get('/auth/users/pending');
    return response.data;
  }

  /**
   * Approve a user request (admin only)
   */
  async approveUser(userId: string): Promise<{ user: User }> {
    const response = await this.axiosInstance.post(`/auth/users/${userId}/approve`);
    return response.data;
  }

  /**
   * Deny and delete a user request (admin only)
   */
  async denyUser(userId: string): Promise<{ success: boolean }> {
    const response = await this.axiosInstance.post(`/auth/users/${userId}/deny`);
    return response.data;
  }

  /**
   * Update a user (admin only)
   */
  async updateUser(userId: string, updates: UpdateUserRequest): Promise<{ user: User }> {
    const response = await this.axiosInstance.put(`/auth/users/${userId}`, updates);
    return response.data;
  }

  /**
   * Delete a user (admin only)
   */
  async deleteUser(userId: string): Promise<void> {
    await this.axiosInstance.delete(`/auth/users/${userId}`);
  }
}

// Export singleton instance
export const authApi = new AuthApiService();
