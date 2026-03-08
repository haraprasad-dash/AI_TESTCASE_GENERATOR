import axios, { AxiosInstance } from 'axios';
import type {
  Settings,
  FileInput,
  GenerationInputs,
  GenerationConfiguration,
  GenerationResponse,
  ExportRequest
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Health Check
  async healthCheck() {
    return this.client.get('/api/health');
  }

  // JIRA
  async testJiraConnection() {
    return this.client.post('/api/jira/test-connection');
  }

  async getJiraIssue(issueKey: string) {
    return this.client.get(`/api/jira/issue/${issueKey}`);
  }

  // ValueEdge
  async testValueEdgeConnection() {
    return this.client.post('/api/valueedge/test-connection');
  }

  async getValueEdgeItem(itemId: string) {
    return this.client.get(`/api/valueedge/item/${itemId}`);
  }

  // Documents
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.client.post<FileInput>('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async deleteFile(fileId: string) {
    return this.client.delete(`/api/documents/${fileId}`);
  }

  // LLM
  async testLLMConnection(provider: 'groq' | 'ollama') {
    return this.client.post('/api/llm/test-connection', null, {
      params: { provider },
    });
  }

  async listModels(provider: 'groq' | 'ollama') {
    return this.client.get<string[]>('/api/llm/models', { params: { provider } });
  }

  // Generation
  async generate(inputs: GenerationInputs, configuration: GenerationConfiguration) {
    return this.client.post<GenerationResponse>('/api/generate', {
      inputs,
      configuration,
    });
  }

  createWebSocket(requestId: string): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    return new WebSocket(`${wsUrl}/api/generate/ws/${requestId}`);
  }

  // Export
  async export(requestId: string, request: ExportRequest) {
    return this.client.post(`/api/export/${requestId}`, request);
  }

  // Settings
  async getSettings() {
    return this.client.get<Settings>('/api/settings');
  }

  async updateSettings(settings: Settings) {
    return this.client.put('/api/settings', settings);
  }
}

export const api = new ApiService();
