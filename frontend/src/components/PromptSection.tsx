import { useState } from 'react';
import { 
  Sparkles, Lightbulb, Wand2, Shield, 
  Bug, Zap, FileCheck, ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

interface Props {
  value: string;
  onChange: (value: string) => void;
  provider?: 'groq' | 'ollama';
  model?: string;
}

const promptSuggestions = [
  { icon: Shield, label: 'Security Focus', text: 'Focus on security testing including authentication, authorization, input validation, and vulnerability assessments.' },
  { icon: Bug, label: 'Negative Tests', text: 'Include comprehensive negative test cases and error handling scenarios for all major functions.' },
  { icon: Zap, label: 'Performance', text: 'Add performance and load testing scenarios with specific thresholds and benchmarks.' },
  { icon: FileCheck, label: 'API Coverage', text: 'Ensure all API endpoints are covered with valid and invalid request scenarios.' },
];

export const PromptSection: React.FC<Props> = ({ value, onChange, provider = 'groq', model = 'llama-3.3-70b-versatile' }) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<number | null>(null);
  const [isEnhancing, setIsEnhancing] = useState(false);

  const handleEnhance = async () => {
    if (!value.trim()) {
      toast.error('Type a prompt first before enhancing');
      return;
    }
    setIsEnhancing(true);
    try {
      const res = await api.enhancePrompt(value, provider, model);
      onChange(res.data.enhanced_prompt);
      toast.success('Prompt enhanced!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to enhance prompt');
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleSuggestionClick = (index: number, text: string) => {
    setSelectedSuggestion(index);
    const newValue = value ? `${value}\n\n${text}` : text;
    onChange(newValue);
    setTimeout(() => setSelectedSuggestion(null), 1000);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="section-header mb-0">
          <div className="section-icon bg-gradient-to-br from-amber-500 to-orange-600">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="section-title">Custom Instructions</h2>
            <p className="section-subtitle">Fine-tune the AI output with specific requirements</p>
          </div>
        </div>
        <span className="text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
          Optional
        </span>
      </div>

      {/* Suggestions */}
      <div className="mb-4">
        <button
          onClick={() => setShowSuggestions(!showSuggestions)}
          type="button"
          className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
          <Wand2 className="w-4 h-4" />
          Quick suggestions
          {showSuggestions ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
        
        {showSuggestions && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
            {promptSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(index, suggestion.text)}
                type="button"
                className={`flex items-center gap-3 p-3 rounded-xl text-left transition-all duration-200 border-2 ${
                  selectedSuggestion === index
                    ? 'bg-blue-50 border-blue-300'
                    : 'bg-slate-50 border-transparent hover:bg-slate-100'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  selectedSuggestion === index ? 'bg-blue-100' : 'bg-white'
                }`}>
                  <suggestion.icon className={`w-4 h-4 ${
                    selectedSuggestion === index ? 'text-blue-600' : 'text-slate-500'
                  }`} />
                </div>
                <span className={`text-sm font-medium ${
                  selectedSuggestion === index ? 'text-blue-700' : 'text-slate-700'
                }`}>
                  {suggestion.label}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* Textarea */}
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter specific instructions for test generation...

Example: Focus on security testing and negative test cases for the authentication module. Include API validation tests."
          rows={5}
          className="input-field resize-none"
        />
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-slate-400">
            Leave empty to use default templates
          </span>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-medium ${
              value.length > 500 ? 'text-amber-500' : 'text-slate-400'
            }`}>
              {value.length} chars
            </span>
            <button
              type="button"
              onClick={handleEnhance}
              disabled={isEnhancing || !value.trim()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-violet-500 to-purple-600 text-white hover:from-violet-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
            >
              <RefreshCw className={`w-3 h-3 ${isEnhancing ? 'animate-spin' : ''}`} />
              {isEnhancing ? 'Enhancing...' : '✨ Enhance'}
            </button>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-bold text-blue-900 mb-1">
              Pro Tip
            </p>
            <p className="text-sm text-blue-700">
              Be specific about test types, coverage areas, or compliance requirements. 
              The AI will tailor the output to match your exact needs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
