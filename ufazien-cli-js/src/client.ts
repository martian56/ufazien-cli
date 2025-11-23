/**
 * Ufazien API Client
 * Handles all API communication with the Ufazien platform.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import FormData from 'form-data';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';

export interface User {
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface Website {
  id: string;
  name: string;
  website_type: string;
  domain: {
    id: string;
    name: string;
  };
}

export interface Database {
  id: string;
  name: string;
  db_type: string;
  status: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  error_message?: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
}

export class UfazienAPIClient {
  private baseUrl: string;
  private configDir: string;
  private tokensFile: string;
  public accessToken: string | null = null;
  private refreshToken: string | null = null;
  private axiosInstance: AxiosInstance;

  constructor(baseUrl?: string, configDir?: string) {
    this.baseUrl = baseUrl || 'https://api.ufazien.com/api';
    if (!this.baseUrl.endsWith('/api')) {
      if (this.baseUrl.endsWith('/')) {
        this.baseUrl = this.baseUrl.slice(0, -1) + '/api';
      } else {
        this.baseUrl = this.baseUrl + '/api';
      }
    }

    if (configDir) {
      this.configDir = configDir;
    } else {
      const home = os.homedir();
      this.configDir = path.join(home, '.ufazien');
    }

    fs.ensureDirSync(this.configDir);
    this.tokensFile = path.join(this.configDir, 'tokens.json');

    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      timeout: 300000, // 5 minutes for file uploads
    });

    this.loadTokens();
  }

  private loadTokens(): void {
    if (fs.existsSync(this.tokensFile)) {
      try {
        const tokens: Tokens = fs.readJsonSync(this.tokensFile);
        this.accessToken = tokens.access_token;
        this.refreshToken = tokens.refresh_token;
      } catch (error) {
        // Ignore errors
      }
    }
  }

  private saveTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    try {
      fs.writeJsonSync(this.tokensFile, {
        access_token: accessToken,
        refresh_token: refreshToken,
      });
      fs.chmodSync(this.tokensFile, 0o600);
    } catch (error) {
      console.error(`Warning: Could not save tokens: ${error}`);
    }
  }

  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    if (fs.existsSync(this.tokensFile)) {
      try {
        fs.removeSync(this.tokensFile);
      } catch (error) {
        // Ignore errors
      }
    }
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'DELETE',
    endpoint: string,
    data?: any,
    files?: Record<string, string>
  ): Promise<T> {
    const config: any = {
      method,
      url: endpoint,
      headers: {},
    };

    if (this.accessToken) {
      config.headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    if (files) {
      const formData = new FormData();
      
      if (data) {
        for (const [key, value] of Object.entries(data)) {
          formData.append(key, String(value));
        }
      }

      for (const [key, filePath] of Object.entries(files)) {
        formData.append(key, fs.createReadStream(filePath));
      }

      config.data = formData;
      config.headers = {
        ...config.headers,
        ...formData.getHeaders(),
      };
    } else if (data) {
      config.data = data;
      config.headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await this.axiosInstance.request<T>(config);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<any>;
        
        // Handle 401 Unauthorized - try to refresh token
        if (
          axiosError.response?.status === 401 &&
          this.refreshToken &&
          endpoint !== '/auth/token/refresh/'
        ) {
          if (await this.refreshAccessToken()) {
            return this.makeRequest<T>(method, endpoint, data, files);
          } else {
            this.clearTokens();
            throw new Error("Authentication failed. Please login again using 'ufazienjs login'");
          }
        }

        const errorData = axiosError.response?.data || {};
        const errorMsg =
          errorData.detail ||
          errorData.message ||
          `HTTP ${axiosError.response?.status}: ${axiosError.message}`;
        throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg, null, 2));
      }
      throw error;
    }
  }

  private async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) {
      return false;
    }

    try {
      const response = await axios.post(
        `${this.baseUrl}/auth/token/refresh/`,
        { refresh: this.refreshToken },
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 10000,
        }
      );

      const newAccessToken = response.data.access;
      if (newAccessToken) {
        this.saveTokens(newAccessToken, this.refreshToken!);
        return true;
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  async login(email: string, password: string): Promise<User> {
    const response = await this.makeRequest<{ access: string; refresh: string; user: User }>(
      'POST',
      '/auth/login/',
      { email, password }
    );

    if (response.access && response.refresh) {
      this.saveTokens(response.access, response.refresh);
    }

    return response.user || {};
  }

  async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await this.makeRequest('POST', '/auth/logout/');
      }
    } catch (error) {
      // Ignore errors
    } finally {
      this.clearTokens();
    }
  }

  async getProfile(): Promise<User> {
    return this.makeRequest<User>('GET', '/auth/user/');
  }

  async createWebsite(
    name: string,
    subdomain: string,
    websiteType: string,
    description?: string,
    environmentVariables?: Record<string, string>,
    domainId?: string
  ): Promise<Website> {
    const data: any = {
      name,
      website_type: websiteType,
    };

    if (description) {
      data.description = description;
    }

    if (environmentVariables) {
      data.environment_variables = environmentVariables;
    }

    if (domainId) {
      data.domain_id = domainId;
    } else {
      const domain = await this.makeRequest<{ id: string }>('POST', '/hosting/domains/', {
        name: `${subdomain}.ufazien.com`,
        domain_type: 'subdomain',
      });
      data.domain_id = domain.id;
    }

    return this.makeRequest<Website>('POST', '/hosting/websites/', data);
  }

  async createDatabase(
    name: string,
    dbType: string = 'mysql',
    description?: string
  ): Promise<Database> {
    const data: any = {
      name,
      db_type: dbType,
    };

    if (description) {
      data.description = description;
    }

    return this.makeRequest<Database>('POST', '/hosting/databases/', data);
  }

  async uploadZip(websiteId: string, zipFilePath: string): Promise<any> {
    return this.makeRequest('POST', `/hosting/websites/${websiteId}/upload_zip/`, undefined, {
      zip_file: zipFilePath,
    });
  }

  async getWebsites(): Promise<Website[]> {
    return this.makeRequest<Website[]>('GET', '/hosting/websites/');
  }

  async getWebsite(websiteId: string): Promise<Website> {
    return this.makeRequest<Website>('GET', `/hosting/websites/${websiteId}/`);
  }

  async deployWebsite(websiteId: string): Promise<any> {
    return this.makeRequest('POST', `/hosting/websites/${websiteId}/deploy/`);
  }

  async getAvailableDomains(): Promise<any[]> {
    return this.makeRequest<any[]>('GET', '/hosting/domains/available/');
  }

  async getDatabase(databaseId: string): Promise<Database> {
    return this.makeRequest<Database>('GET', `/hosting/databases/${databaseId}/`);
  }
}

