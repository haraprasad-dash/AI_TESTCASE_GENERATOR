import axios, { AxiosInstance } from 'axios';
import type {
  Settings,
  FileInput,
  GenerationInputs,
  GenerationConfiguration,
  GenerationResponse,
  ExportRequest,
  ReviewInputs,
  ReviewConfiguration,
  ReviewResponse,
  EnhancePromptType,
  EnhancePromptContext,
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
  async testJiraConnection(config?: { baseUrl: string; username: string; apiToken: string }) {
    return this.client.post('/api/jira/test-connection', config ? {
      base_url: config.baseUrl,
      username: config.username,
      api_token: config.apiToken,
    } : null, { timeout: 15000 });
  }

  async getJiraIssue(issueKey: string) {
    return this.client.get(`/api/jira/issue/${issueKey}`, { timeout: 20000 });
  }

  // ValueEdge
  async testValueEdgeConnection(config?: { baseUrl: string; clientId: string; clientSecret: string }) {
    return this.client.post('/api/valueedge/test-connection', config ? {
      base_url: config.baseUrl,
      client_id: config.clientId,
      client_secret: config.clientSecret,
    } : null, { timeout: 15000 });
  }

  async getValueEdgeItem(itemId: string) {
    return this.client.get(`/api/valueedge/item/${itemId}`, { timeout: 20000 });
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
  async testLLMConnection(provider: 'groq' | 'ollama', groqApiKey?: string) {
    return this.client.post('/api/llm/test-connection', null, {
      params: { provider },
      timeout: 15000,
      headers: groqApiKey ? { 'x-groq-api-key': groqApiKey } : undefined,
    });
  }

  async listModels(provider: 'groq' | 'ollama', groqApiKey?: string) {
    return this.client.get<string[]>('/api/llm/models', {
      params: { provider },
      timeout: 8000,
      headers: groqApiKey ? { 'x-groq-api-key': groqApiKey } : undefined,
    });
  }

  async enhancePrompt(
    prompt: string,
    provider: 'groq' | 'ollama',
    model: string,
    promptType: EnhancePromptType = 'test_case',
    context?: EnhancePromptContext
  ) {
    return this.client.post<{ enhanced_prompt: string }>('/api/llm/enhance-prompt', {
      prompt,
      provider,
      model,
      prompt_type: promptType,
      context,
    });
  }

  // Generation
  async generate(inputs: GenerationInputs, configuration: GenerationConfiguration) {
    const timeoutMs = configuration.provider === 'ollama' ? 600000 : 180000;
    return this.client.post<GenerationResponse>(
      '/api/generate',
      {
        inputs,
        configuration,
      },
      {
        timeout: timeoutMs,
      }
    );
  }

  createWebSocket(requestId: string): WebSocket {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    return new WebSocket(`${wsUrl}/api/generate/ws/${requestId}`);
  }

  // Export
  async export(requestId: string, request: ExportRequest) {
    return this.client.post(`/api/export/${requestId}`, request);
  }

  // Review
  async reviewTestCases(inputs: ReviewInputs, configuration: ReviewConfiguration) {
    return this.client.post<ReviewResponse>('/api/review/test-cases', { inputs, configuration });
  }

  async reviewUserGuide(inputs: ReviewInputs, configuration: ReviewConfiguration) {
    return this.client.post<ReviewResponse>('/api/review/user-guide', { inputs, configuration });
  }

  async reviewBoth(inputs: ReviewInputs, configuration: ReviewConfiguration) {
    return this.client.post<ReviewResponse>('/api/review/both', { inputs, configuration });
  }

  async reviewStatus(reviewId: string) {
    return this.client.get<ReviewResponse>(`/api/review/${reviewId}/status`);
  }

  async attachReviewClarificationFile(reviewId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.client.post(`/api/review/clarification/${reviewId}/attach`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async exportReview(reviewId: string, format: 'markdown' | 'pdf' | 'excel' | 'json' | 'gherkin') {
    return this.client.post(`/api/review/${reviewId}/export`, { format });
  }

  // Settings
  async getSettings() {
    // Backend returns snake_case keys; the modal maps them into camelCase store fields.
    return this.client.get<any>('/api/settings');
  }

  async updateSettings(settings: Settings) {
    const payload = {
      jira: {
        enabled: settings.jira.enabled,
        base_url: settings.jira.baseUrl,
        username: settings.jira.username,
        api_token: settings.jira.apiToken,
        default_project: settings.jira.defaultProject,
      },
      valueedge: {
        enabled: settings.valueedge.enabled,
        base_url: settings.valueedge.baseUrl,
        client_id: settings.valueedge.clientId,
        client_secret: settings.valueedge.clientSecret,
        shared_space_id: settings.valueedge.sharedSpaceId,
      },
      llm: {
        default_provider: settings.llm.defaultProvider,
        groq: {
          api_key: settings.llm.groq.apiKey,
          default_model: settings.llm.groq.defaultModel,
          default_temperature: settings.llm.groq.defaultTemperature,
        },
        ollama: {
          base_url: settings.llm.ollama.baseUrl,
          default_model: settings.llm.ollama.defaultModel,
        },
      },
      templates: {
        test_plan_path: './templates/test_plan_generation.md',
        test_case_path: './templates/test_case_generation.md',
      },
      export: {
        default_format: 'markdown',
        auto_save: true,
        output_directory: './outputs',
      },
    };

    return this.client.put('/api/settings', payload);
  }
}

export const api = new ApiService();
