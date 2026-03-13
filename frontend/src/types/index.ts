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
  jira_ids?: string[];
  valueedge_id?: string;
  valueedge_ids?: string[];
  files: FileInput[];
  custom_prompt?: string;
  test_plan_prompt?: string;
  test_case_prompt?: string;
  use_test_plan_template?: boolean;
  use_test_case_template?: boolean;
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

export interface ClarificationEntry {
  questions: string[];
  answer: string;
}

export interface ReviewInputs {
  jira_id?: string;
  jira_ids?: string[];
  valueedge_id?: string;
  valueedge_ids?: string[];
  files: FileInput[];
  custom_instructions?: string;
  review_test_cases?: boolean;
  review_user_guide?: boolean;
  user_guide_url?: string;
  clarification_history?: ClarificationEntry[];
}

export interface ReviewConfiguration {
  provider: 'groq' | 'ollama';
  model?: string;
  temperature: number;
}

export interface ReviewResponse {
  review_id: string;
  status: 'completed' | 'clarification_required' | 'failed';
  timestamp: string;
  report_markdown: string;
  report_json: Record<string, unknown>;
  partial_results?: Record<string, unknown>;
  metadata: {
    review_type: 'test-cases' | 'user-guide' | 'both';
    clarification_required: boolean;
    clarification_questions: string[];
    clarification_round: number;
    max_clarification_rounds: number;
    assumptions_applied: boolean;
    sources: string[];
  };
  error?: string;
}
