// Types for TestGen AI Agent

export interface JiraConfig {
  enabled: boolean;
  baseUrl: string;
  username: string;
  apiToken: string;
  defaultProject?: string;
}

export interface ValueEdgeConfig {
  enabled: boolean;
  baseUrl: string;
  clientId: string;
  clientSecret: string;
  sharedSpaceId?: number;
}

export interface LLMConfig {
  defaultProvider: 'groq' | 'ollama';
  groq: {
    apiKey: string;
    defaultModel: string;
    defaultTemperature: number;
  };
  ollama: {
    baseUrl: string;
    defaultModel: string;
  };
}

export interface Settings {
  jira: JiraConfig;
  valueedge: ValueEdgeConfig;
  llm: LLMConfig;
}

export interface FileInput {
  file_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  extracted_text: string;
  page_count?: number;
}

export interface GenerationInputs {
  jira_id?: string;
  valueedge_id?: string;
  files: FileInput[];
  custom_prompt?: string;
}

export interface GenerationConfiguration {
  provider: 'groq' | 'ollama';
  model?: string;
  temperature: number;
  max_tokens: number;
}

export interface GenerationOutput {
  content: string;
  format: string;
  token_usage?: number;
  generation_time_ms?: number;
}

export interface TestCasesOutput extends GenerationOutput {
  count?: number;
}

export interface GenerationMetadata {
  model_used: string;
  temperature: number;
  total_tokens?: number;
  sources: string[];
  clarification_required?: boolean;
  clarification_questions?: string[];
}

export interface GenerationResponse {
  request_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  timestamp: string;
  outputs: {
    test_plan?: GenerationOutput;
    test_cases?: TestCasesOutput;
  };
  metadata: GenerationMetadata;
  error?: string;
}

export interface ExportRequest {
  format: 'markdown' | 'pdf' | 'excel' | 'json' | 'gherkin';
  test_plan?: string;
  test_cases?: string;
}
