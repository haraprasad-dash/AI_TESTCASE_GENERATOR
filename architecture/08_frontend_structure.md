# SOP 08: Frontend Structure

## Goal
Build a responsive React frontend for the TestGen AI Agent.

## Layer
Layer 3: Tools (`frontend/src/`)

## Component Architecture

```
App.tsx
├── HomePage.tsx
│   ├── Header (with Settings button)
│   ├── InputSection.tsx
│   │   ├── JiraIdInput
│   │   ├── ValueEdgeIdInput
│   │   └── FileUpload.tsx
│   ├── AIConfigSection.tsx
│   │   ├── ProviderSelector
│   │   ├── ModelSelector
│   │   └── TemperatureSlider
│   ├── PromptSection.tsx
│   ├── GenerateButton
│   └── OutputPreview.tsx
│       ├── TabSelector (Plan/Cases/Both)
│       ├── MarkdownRenderer
│       └── ActionButtons (Save/Copy)
└── SettingsModal.tsx
    ├── JiraConfigForm
    ├── ValueEdgeConfigForm
    ├── LLMConfigForm
    └── TemplateConfigForm
```

## Key Components

### 1. API Service (`services/api.ts`)

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

  // Documents
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.client.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  // LLM
  async testLLMConnection(provider: 'groq' | 'ollama') {
    return this.client.post('/api/llm/test-connection', null, {
      params: { provider },
    });
  }

  async listModels(provider: 'groq' | 'ollama') {
    return this.client.get('/api/llm/models', { params: { provider } });
  }

  // Generation
  async generate(request: GenerationRequest) {
    return this.client.post('/api/generate', request);
  }

  async generateStream(request: GenerationRequest, onChunk: (chunk: any) => void) {
    const ws = new WebSocket(`ws://${API_BASE_URL}/ws/generate/${request.request_id}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onChunk(data);
      if (data.type === 'completed' || data.type === 'error') {
        ws.close();
      }
    };

    ws.onopen = () => {
      ws.send(JSON.stringify(request));
    };

    return ws;
  }

  // Export
  async export(requestId: string, format: string) {
    return this.client.post(`/api/generate/${requestId}/export`, { format });
  }
}

export const api = new ApiService();
```

### 2. State Store (`store/settingsStore.ts`)

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Settings {
  jira: {
    enabled: boolean;
    baseUrl: string;
    username: string;
    apiToken: string;
  };
  valueedge: {
    enabled: boolean;
    baseUrl: string;
    clientId: string;
    clientSecret: string;
  };
  llm: {
    defaultProvider: 'groq' | 'ollama';
    groq: {
      apiKey: string;
      defaultModel: string;
    };
    ollama: {
      baseUrl: string;
      defaultModel: string;
    };
  };
}

interface SettingsStore extends Settings {
  updateJira: (settings: Partial<Settings['jira']>) => void;
  updateValueEdge: (settings: Partial<Settings['valueedge']>) => void;
  updateLLM: (settings: Partial<Settings['llm']>) => void;
  reset: () => void;
}

const defaultSettings: Settings = {
  jira: {
    enabled: true,
    baseUrl: '',
    username: '',
    apiToken: '',
  },
  valueedge: {
    enabled: false,
    baseUrl: '',
    clientId: '',
    clientSecret: '',
  },
  llm: {
    defaultProvider: 'groq',
    groq: {
      apiKey: '',
      defaultModel: 'llama-3.3-70b-versatile',
    },
    ollama: {
      baseUrl: 'http://localhost:11434',
      defaultModel: 'llama3.1',
    },
  },
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      ...defaultSettings,
      updateJira: (settings) =>
        set((state) => ({ jira: { ...state.jira, ...settings } })),
      updateValueEdge: (settings) =>
        set((state) => ({ valueedge: { ...state.valueedge, ...settings } })),
      updateLLM: (settings) =>
        set((state) => ({ llm: { ...state.llm, ...settings } })),
      reset: () => set(defaultSettings),
    }),
    {
      name: 'testgen-settings',
    }
  )
);
```

### 3. Home Page (`pages/HomePage.tsx`)

```typescript
import React, { useState } from 'react';
import { InputSection } from '../components/InputSection';
import { AIConfigSection } from '../components/AIConfigSection';
import { PromptSection } from '../components/PromptSection';
import { OutputPreview } from '../components/OutputPreview';
import { SettingsModal } from '../components/SettingsModal';
import { api } from '../services/api';
import toast from 'react-hot-toast';

export const HomePage: React.FC = () => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState<GenerationResponse | null>(null);

  const handleGenerate = async (request: GenerationRequest) => {
    setIsGenerating(true);
    
    try {
      const response = await api.generate(request);
      setOutput(response.data);
      toast.success('Generation complete!');
    } catch (error) {
      toast.error('Generation failed');
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            🧪 TestGen AI Agent
          </h1>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            ⚙️ Settings
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <InputSection />
        <AIConfigSection />
        <PromptSection />
        
        <div className="flex justify-center">
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <LoadingSpinner />
                Generating...
              </>
            ) : (
              '🚀 Generate Test Plan & Cases'
            )}
          </button>
        </div>

        {output && <OutputPreview output={output} />}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};
```

## Styling (Tailwind CSS)

```javascript
// tailwind.config.js
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
};
```

## Edge Cases
1. **API unavailable**: Show error message with retry option
2. **Large file upload**: Show progress indicator
3. **Generation timeout**: Show partial results
4. **Mobile responsiveness**: Stack inputs vertically on small screens
5. **Dark mode**: Support system preference
