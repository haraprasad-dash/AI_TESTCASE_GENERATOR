import { useState } from 'react';
import { 
  Beaker, Settings, Sparkles, FileText, 
  Upload, Zap, ArrowRight
} from 'lucide-react';
import { InputSection } from '../components/InputSection';
import { AIConfigSection } from '../components/AIConfigSection';
import { PromptSection } from '../components/PromptSection';
import { OutputPreview } from '../components/OutputPreview';
import { SettingsModal } from '../components/SettingsModal';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import type { FileInput, GenerationInputs, GenerationConfiguration, GenerationResponse } from '../types';

export const HomePage: React.FC = () => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState<GenerationResponse | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  
  // Form state
  const [jiraId, setJiraId] = useState('');
  const [valueEdgeId, setValueEdgeId] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<FileInput[]>([]);
  const [customPrompt, setCustomPrompt] = useState('');
  const [provider, setProvider] = useState<'groq' | 'ollama'>('groq');
  const [model, setModel] = useState('llama-3.3-70b-versatile');
  const [temperature, setTemperature] = useState(0.2);

  const hasInput = jiraId || valueEdgeId || uploadedFiles.length > 0;

  const handleFileUpload = (file: FileInput) => {
    setUploadedFiles((prev) => [...prev, file]);
    setCurrentStep(2);
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.file_id !== fileId));
  };

  const handleGenerate = async () => {
    if (!hasInput) {
      toast.error('Please provide at least one input source');
      return;
    }

    setIsGenerating(true);
    setCurrentStep(3);
    
    try {
      const inputs: GenerationInputs = {
        jira_id: jiraId || undefined,
        valueedge_id: valueEdgeId || undefined,
        files: uploadedFiles,
        custom_prompt: customPrompt || undefined,
      };

      const configuration: GenerationConfiguration = {
        provider,
        model,
        temperature,
        max_tokens: 4096,
      };

      const response = await api.generate(inputs, configuration);
      setOutput(response.data);
      
      if (response.data.status === 'completed') {
        toast.success('Generation complete! 🎉');
      } else if (response.data.error) {
        toast.error(`Generation failed: ${response.data.error}`);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Generation failed');
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const steps = [
    { num: 1, label: 'Input', desc: 'Add requirements' },
    { num: 2, label: 'Configure', desc: 'Set AI options' },
    { num: 3, label: 'Generate', desc: 'Create tests' },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-white/20 sticky top-0 z-40">
        <div className="main-wrapper">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Beaker className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">
                  TestGen <span className="gradient-text">AI</span>
                </h1>
                <p className="text-xs text-slate-500">Intelligent Test Case Generation</p>
              </div>
            </div>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="btn-secondary"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white/60 backdrop-blur-sm border-b border-white/20">
        <div className="main-wrapper">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-2 sm:gap-4">
              {steps.map((step, idx) => (
                <div key={step.num} className="flex items-center gap-2 sm:gap-4">
                  <div 
                    className={`flex flex-col sm:flex-row items-center gap-2 sm:gap-3 px-4 py-3 rounded-xl transition-all duration-300 cursor-pointer ${
                      currentStep >= step.num 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'bg-slate-100 text-slate-400'
                    }`}
                    onClick={() => setCurrentStep(step.num)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      currentStep >= step.num 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-slate-300 text-slate-500'
                    }`}>
                      {step.num}
                    </div>
                    <div className="text-center sm:text-left">
                      <span className="block text-sm font-semibold">{step.label}</span>
                      <span className="hidden sm:block text-xs opacity-75">{step.desc}</span>
                    </div>
                  </div>
                  {idx < 2 && (
                    <ArrowRight className={`w-5 h-5 hidden md:block ${
                      currentStep > step.num ? 'text-blue-500' : 'text-slate-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-wrapper">
        {/* Welcome Card */}
        {!hasInput && (
          <div className="content-card p-8 text-center mb-8 animate-fade-in">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/30">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900 mb-3">
              Welcome to TestGen AI
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto mb-8 text-lg">
              Generate comprehensive test plans and test cases using AI. 
              Start by providing requirements from JIRA, ValueEdge, or uploading documents.
            </p>
            <div className="flex flex-wrap justify-center gap-6">
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <FileText className="w-4 h-4 text-blue-500" /> 
                <span className="text-sm font-medium">JIRA Integration</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <Upload className="w-4 h-4 text-green-500" /> 
                <span className="text-sm font-medium">File Upload</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <Zap className="w-4 h-4 text-amber-500" /> 
                <span className="text-sm font-medium">AI-Powered</span>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <InputSection
            jiraId={jiraId}
            setJiraId={setJiraId}
            valueEdgeId={valueEdgeId}
            setValueEdgeId={setValueEdgeId}
            uploadedFiles={uploadedFiles}
            onFileUpload={handleFileUpload}
            onRemoveFile={handleRemoveFile}
          />
        </div>

        {/* AI Configuration */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <AIConfigSection
            provider={provider}
            setProvider={setProvider}
            model={model}
            setModel={setModel}
            temperature={temperature}
            setTemperature={setTemperature}
          />
        </div>

        {/* Custom Prompt */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <PromptSection
            value={customPrompt}
            onChange={setCustomPrompt}
          />
        </div>

        {/* Generate Button */}
        <div className="flex justify-center mb-8 animate-fade-in">
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !hasInput}
            className="btn-primary text-lg px-12 py-4"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Generate Test Plan & Cases</span>
              </>
            )}
          </button>
        </div>

        {/* Output Preview */}
        {output && (
          <div className="content-card p-6 animate-fade-in">
            <OutputPreview output={output} onRefresh={handleGenerate} isRefreshing={isGenerating} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-white/70 text-sm">
        <p>© 2026 TestGen AI Agent. Powered by Advanced Language Models.</p>
      </footer>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};
