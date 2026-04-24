import { useEffect, useState } from 'react';
import { 
  Bot, Cloud, Server, Check, AlertCircle, 
  Cpu, Thermometer, Link2, Loader2, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import { useSettingsStore } from '../store/settingsStore';

interface Props {
  provider: 'groq' | 'ollama';
  setProvider: (provider: 'groq' | 'ollama') => void;
  model: string;
  setModel: (model: string) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
}

export const AIConfigSection: React.FC<Props> = ({
  provider,
  setProvider,
  model,
  setModel,
  temperature,
  setTemperature,
}) => {
  const GROQ_FALLBACK_MODELS = [
    'openai/gpt-oss-120b',
    'llama-3.3-70b-versatile',
    'meta-llama/llama-4-scout-17b-16e-instruct',
  ];

  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'connected' | 'error'>('idle');
  const [loadError, setLoadError] = useState<string | null>(null);
  const groqApiKey = useSettingsStore((s) => s.llm.groq.apiKey);

  useEffect(() => {
    loadModels();
  }, [provider]);

  const normalizeModelPayload = (payload: any): string[] => {
    if (Array.isArray(payload)) {
      return payload.filter((m) => typeof m === 'string' && m.trim().length > 0);
    }

    // Backward/forward compatibility if API returns wrapped payload.
    if (payload && Array.isArray(payload.models)) {
      return payload.models.filter((m: any) => typeof m === 'string' && m.trim().length > 0);
    }

    return [];
  };

  const applyModels = (models: string[]) => {
    setAvailableModels(models);
    if (!models.includes(model)) {
      const defaultModel = provider === 'ollama'
        ? models[0]
        : (
            models.find((m: string) =>
              m.includes('llama-3.3-70b-versatile') ||
              m.includes('openai/gpt-oss-120b') ||
              m.includes('llama-3.1-70b') ||
              m.includes('mixtral')
            ) || models[0]
          );
      setModel(defaultModel);
    }
  };

  const loadModels = async () => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const response = await api.listModels(provider, provider === 'groq' ? groqApiKey : undefined);
      const models = normalizeModelPayload(response.data);
      
      if (models && models.length > 0) {
        applyModels(models);
      } else {
        if (provider === 'groq') {
          applyModels(GROQ_FALLBACK_MODELS);
          setLoadError('Live Groq model list returned empty. Showing fallback models.');
          return;
        }
        setLoadError('No models available');
        setAvailableModels([]);
      }
    } catch (error: any) {
      console.error('Failed to load models:', error);
      if (provider === 'groq') {
        applyModels(GROQ_FALLBACK_MODELS);
        const detail = error?.response?.data?.detail;
        if (detail && String(detail).toLowerCase().includes('api key')) {
          setLoadError('Groq API key missing. Add key in Settings to fetch live available models.');
        } else {
          setLoadError('Could not fetch live Groq models. Showing fallback models.');
        }
        return;
      }
      // Check if it's a network error (backend not running)
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error') || !error.response) {
        setLoadError('Cannot connect to backend. Please ensure the backend server is running on http://localhost:7000');
      } else {
        setLoadError(error.response?.data?.detail || 'Failed to load models');
      }
      setAvailableModels([]);
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async () => {
    setConnectionStatus('testing');
    try {
      await api.testLLMConnection(provider, provider === 'groq' ? groqApiKey : undefined);
      setConnectionStatus('connected');
      toast.success(`Connected to ${provider}!`);
      // Reload models on successful connection
      await loadModels();
      setTimeout(() => setConnectionStatus('idle'), 3000);
    } catch (error: any) {
      setConnectionStatus('error');
      const message = error?.code === 'ECONNABORTED'
        ? `Connection timed out for ${provider}.`
        : 'Connection failed';
      toast.error(message);
      setTimeout(() => setConnectionStatus('idle'), 3000);
    }
  };

  // Get model display name with friendly formatting
  const getModelDisplayName = (modelId: string) => {
    const displayNames: Record<string, string> = {
      'openai/gpt-oss-120b': 'OpenAI GPT-OSS 120B',
      'llama-3.3-70b-versatile': 'Llama 3.3 70B (Versatile)',
      'llama-3.3-70b-specdec': 'Llama 3.3 70B (Speculative Decoding)',
      'llama-3.1-8b-instant': 'Llama 3.1 8B (Instant)',
      'llama-3.1-70b-versatile': 'Llama 3.1 70B (Versatile)',
      'llama-3.1-405b-reasoning': 'Llama 3.1 405B (Reasoning)',
      'llama-3.2-1b-preview': 'Llama 3.2 1B (Preview)',
      'llama-3.2-3b-preview': 'Llama 3.2 3B (Preview)',
      'llama-3.2-11b-vision-preview': 'Llama 3.2 11B Vision (Preview)',
      'llama-3.2-90b-vision-preview': 'Llama 3.2 90B Vision (Preview)',
      'llama-guard-3-8b': 'Llama Guard 3 8B',
      'mixtral-8x7b-32768': 'Mixtral 8x7B',
      'mixtral-8x22b-instruct': 'Mixtral 8x22B (Instruct)',
      'gemma-7b-it': 'Gemma 7B (IT)',
      'gemma2-9b-it': 'Gemma 2 9B (IT)',
      'qwen-2.5-32b-instruct': 'Qwen 2.5 32B (Instruct)',
      'qwen-2.5-coder-32b-instruct': 'Qwen 2.5 Coder 32B',
      'deepseek-r1-distill-qwen-32b': 'DeepSeek R1 Distill (Qwen 32B)',
      'deepseek-r1-distill-llama-70b': 'DeepSeek R1 Distill (Llama 70B)',
      'llama3-8b-8192': 'Llama 3 8B',
      'llama3-70b-8192': 'Llama 3 70B',
    };
    return displayNames[modelId] || modelId;
  };

  // Group models by category
  const getModelCategory = (modelId: string) => {
    if (modelId.includes('openai/')) return '\u{1F916} OpenAI';
    if (modelId.includes('llama-3.3')) return '🦙 Llama 3.3';
    if (modelId.includes('llama-3.2')) return modelId.includes('vision') ? '👁️ Llama 3.2 Vision' : '🦙 Llama 3.2';
    if (modelId.includes('llama-3.1')) return '🦙 Llama 3.1';
    if (modelId.includes('llama3')) return '🦙 Llama 3';
    if (modelId.includes('mixtral')) return '⚡ Mixtral';
    if (modelId.includes('gemma')) return '💎 Gemma';
    if (modelId.includes('qwen')) return '🌐 Qwen';
    if (modelId.includes('deepseek')) return '🔍 DeepSeek';
    if (modelId.includes('guard')) return '🛡️ Guard';
    return '📦 Other';
  };

  // Group models for display
  const groupedModels = availableModels.reduce((acc, model) => {
    const category = getModelCategory(model);
    if (!acc[category]) acc[category] = [];
    acc[category].push(model);
    return acc;
  }, {} as Record<string, string[]>);

  const categoryOrder = [
    '\u{1F916} OpenAI',
    '🦙 Llama 3.3',
    '🦙 Llama 3.2 Vision',
    '🦙 Llama 3.2',
    '🦙 Llama 3.1',
    '🦙 Llama 3',
    '🔍 DeepSeek',
    '⚡ Mixtral',
    '💎 Gemma',
    '🌐 Qwen',
    '🛡️ Guard',
    '📦 Other'
  ];

  return (
    <div>
      {/* Header */}
      <div className="section-header">
        <div className="section-icon bg-gradient-to-br from-emerald-500 to-teal-600">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="section-title">AI Configuration</h2>
          <p className="section-subtitle">Configure your AI model and parameters</p>
        </div>
      </div>
      
      {/* Provider Selection */}
      <div className="mb-6">
        <label className="input-label flex items-center gap-2">
          <Cloud className="w-4 h-4 text-sky-500" />
          AI Provider
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => setProvider('groq')}
            type="button"
            className={`relative flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${
              provider === 'groq'
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              provider === 'groq' ? 'bg-blue-500' : 'bg-slate-200'
            }`}>
              <Cloud className="w-6 h-6 text-white" />
            </div>
            <div className="text-left flex-1">
              <span className="block font-bold text-slate-900">Groq Cloud</span>
              <span className="text-xs text-slate-500">Fast cloud inference</span>
            </div>
            {provider === 'groq' && (
              <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
                <Check className="w-4 h-4 text-white" />
              </div>
            )}
          </button>

          <button
            onClick={() => setProvider('ollama')}
            type="button"
            className={`relative flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${
              provider === 'ollama'
                ? 'border-purple-500 bg-purple-50'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              provider === 'ollama' ? 'bg-purple-500' : 'bg-slate-200'
            }`}>
              <Server className="w-6 h-6 text-white" />
            </div>
            <div className="text-left flex-1">
              <span className="block font-bold text-slate-900">Ollama Local</span>
              <span className="text-xs text-slate-500">Run models locally</span>
            </div>
            {provider === 'ollama' && (
              <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center">
                <Check className="w-4 h-4 text-white" />
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Model & Temperature */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="input-label flex items-center gap-2 mb-0">
              <Cpu className="w-4 h-4 text-violet-500" />
              Model
            </label>
            <button
              onClick={loadModels}
              disabled={isLoading}
              type="button"
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          
          {isLoading ? (
            <div className="input-field flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading models...
            </div>
          ) : loadError ? (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {loadError}
              </div>
              <button
                onClick={loadModels}
                type="button"
                className="mt-2 text-xs underline hover:no-underline"
              >
                Try again
              </button>
            </div>
          ) : (
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={availableModels.length === 0}
              className="input-field appearance-none cursor-pointer"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3E%3C/svg%3E")`,
                backgroundPosition: 'right 0.75rem center',
                backgroundSize: '1.5em 1.5em',
                backgroundRepeat: 'no-repeat',
                paddingRight: '2.5rem'
              }}
            >
              {availableModels.length === 0 ? (
                <option>No models available</option>
              ) : (
                categoryOrder.map(category => {
                  const models = groupedModels[category];
                  if (!models || models.length === 0) return null;
                  return (
                    <optgroup key={category} label={category}>
                      {models.map((m) => (
                        <option key={m} value={m}>
                          {getModelDisplayName(m)}
                        </option>
                      ))}
                    </optgroup>
                  );
                })
              )}
            </select>
          )}
          
          {availableModels.length > 0 && (
            <p className="text-xs text-slate-500 mt-2">
              {availableModels.length} models available
            </p>
          )}
        </div>

        <div>
          <label className="input-label flex items-center gap-2">
            <Thermometer className="w-4 h-4 text-orange-500" />
            Temperature
            <span className="ml-auto text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">
              {temperature}
            </span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full mt-2"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>Precise (0)</span>
            <span>Creative (1)</span>
          </div>
        </div>
      </div>

      {/* Test Connection */}
      <button
        onClick={testConnection}
        disabled={connectionStatus === 'testing'}
        type="button"
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200 ${
          connectionStatus === 'connected'
            ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
            : connectionStatus === 'error'
            ? 'bg-red-100 text-red-700 border border-red-200'
            : 'bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200'
        }`}
      >
        {connectionStatus === 'testing' ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : connectionStatus === 'connected' ? (
          <Check className="w-4 h-4" />
        ) : connectionStatus === 'error' ? (
          <AlertCircle className="w-4 h-4" />
        ) : (
          <Link2 className="w-4 h-4" />
        )}
        {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'error' ? 'Failed' : 'Test Connection'}
      </button>
    </div>
  );
};
