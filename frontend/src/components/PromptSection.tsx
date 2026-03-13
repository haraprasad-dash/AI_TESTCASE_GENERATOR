import { useState } from 'react';
import { 
  Sparkles, Lightbulb, Wand2, Shield, 
  Bug, Zap, FileCheck, ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

interface Props {
  testPlanPrompt: string;
  onTestPlanPromptChange: (value: string) => void;
  testCasePrompt: string;
  onTestCasePromptChange: (value: string) => void;
  useTestPlanTemplate: boolean;
  onUseTestPlanTemplateChange: (value: boolean) => void;
  useTestCaseTemplate: boolean;
  onUseTestCaseTemplateChange: (value: boolean) => void;
  provider?: 'groq' | 'ollama';
  model?: string;
}

const promptSuggestions = [
  { icon: Shield, label: 'Security Focus', text: 'Focus on security testing including authentication, authorization, input validation, and vulnerability assessments.' },
  { icon: Bug, label: 'Negative Tests', text: 'Include comprehensive negative test cases and error handling scenarios for all major functions.' },
  { icon: Zap, label: 'Performance', text: 'Add performance and load testing scenarios with specific thresholds and benchmarks.' },
  { icon: FileCheck, label: 'API Coverage', text: 'Ensure all API endpoints are covered with valid and invalid request scenarios.' },
];

export const PromptSection: React.FC<Props> = ({
  testPlanPrompt,
  onTestPlanPromptChange,
  testCasePrompt,
  onTestCasePromptChange,
  useTestPlanTemplate,
  onUseTestPlanTemplateChange,
  useTestCaseTemplate,
  onUseTestCaseTemplateChange,
  provider = 'groq',
  model = 'llama-3.3-70b-versatile',
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<number | null>(null);
  const [isEnhancingPlan, setIsEnhancingPlan] = useState(false);
  const [isEnhancingCase, setIsEnhancingCase] = useState(false);

  const handleEnhance = async (target: 'plan' | 'case') => {
    const sourceValue = target === 'plan' ? testPlanPrompt : testCasePrompt;
    if (!sourceValue.trim()) {
      toast.error('Type a prompt first before enhancing');
      return;
    }

    if (target === 'plan') {
      setIsEnhancingPlan(true);
    } else {
      setIsEnhancingCase(true);
    }

    try {
      const promptType = target === 'plan' ? 'test_plan' : 'test_case';
      const res = await api.enhancePrompt(sourceValue, provider, model, promptType);
      if (target === 'plan') {
        onTestPlanPromptChange(res.data.enhanced_prompt);
      } else {
        onTestCasePromptChange(res.data.enhanced_prompt);
      }
      toast.success('Prompt enhanced!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to enhance prompt');
    } finally {
      if (target === 'plan') {
        setIsEnhancingPlan(false);
      } else {
        setIsEnhancingCase(false);
      }
    }
  };

  const handleSuggestionClick = (index: number, text: string) => {
    setSelectedSuggestion(index);
    const nextPlan = testPlanPrompt ? `${testPlanPrompt}\n\n${text}` : text;
    const nextCase = testCasePrompt ? `${testCasePrompt}\n\n${text}` : text;
    onTestPlanPromptChange(nextPlan);
    onTestCasePromptChange(nextCase);
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
      
      {/* Horizontal Prompt Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 p-4 bg-gradient-to-b from-white to-slate-50">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Test Plan Prompt</h3>
              <p className="text-xs text-slate-500">Template: <span className="font-semibold">test_plan_generation.md</span></p>
            </div>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useTestPlanTemplate}
                onChange={(e) => onUseTestPlanTemplateChange(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-xs font-medium text-slate-600">Use Template</span>
            </label>
          </div>

          <textarea
            value={testPlanPrompt}
            onChange={(e) => onTestPlanPromptChange(e.target.value)}
            placeholder="Add test plan-specific instructions..."
            rows={5}
            className="input-field resize-none"
          />

          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-slate-400">
              Empty + selected uses default template.
            </span>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${
                testPlanPrompt.length > 500 ? 'text-amber-500' : 'text-slate-400'
              }`}>
                {testPlanPrompt.length} chars
              </span>
              <button
                type="button"
                onClick={() => handleEnhance('plan')}
                disabled={isEnhancingPlan || !testPlanPrompt.trim()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:from-blue-600 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
              >
                <RefreshCw className={`w-3 h-3 ${isEnhancingPlan ? 'animate-spin' : ''}`} />
                {isEnhancingPlan ? 'Enhancing...' : '✨ Enhance'}
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 p-4 bg-gradient-to-b from-white to-slate-50">
          <div className="flex items-center justify-between gap-3 mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Test Case Prompt</h3>
              <p className="text-xs text-slate-500">Template: <span className="font-semibold">test_case_generation.md</span></p>
            </div>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useTestCaseTemplate}
                onChange={(e) => onUseTestCaseTemplateChange(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-xs font-medium text-slate-600">Use Template</span>
            </label>
          </div>

          <textarea
            value={testCasePrompt}
            onChange={(e) => onTestCasePromptChange(e.target.value)}
            placeholder="Add test case-specific instructions..."
            rows={5}
            className="input-field resize-none"
          />

          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-slate-400">
              Empty + selected uses default template.
            </span>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${
                testCasePrompt.length > 500 ? 'text-amber-500' : 'text-slate-400'
              }`}>
                {testCasePrompt.length} chars
              </span>
              <button
                type="button"
                onClick={() => handleEnhance('case')}
                disabled={isEnhancingCase || !testCasePrompt.trim()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:from-blue-600 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
              >
                <RefreshCw className={`w-3 h-3 ${isEnhancingCase ? 'animate-spin' : ''}`} />
                {isEnhancingCase ? 'Enhancing...' : '✨ Enhance'}
              </button>
            </div>
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
              Keep "Use Template" selected to fuse your custom text with the matching file.
              If both prompt boxes are empty, both templates stay selected by default and AI uses
              <span className="font-semibold"> test_plan_generation.md </span>
              and
              <span className="font-semibold"> test_case_generation.md</span>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
