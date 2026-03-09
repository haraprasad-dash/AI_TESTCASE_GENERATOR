import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  FileText, Copy, Download, Check, FileCode, 
  Table, ScrollText, Braces, TestTube, 
  Sparkles, Cpu, BarChart3, Loader2, RefreshCw, Paperclip
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import type { GenerationResponse } from '../types';

interface Props {
  output: GenerationResponse;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onSubmitClarification?: (answers: string) => void;
  onUploadClarificationFiles?: (files: File[]) => Promise<void> | void;
  clarificationHistory?: Array<{ questions: string[]; answer: string }>;
}

const exportFormats = [
  { key: 'markdown', label: 'Markdown', icon: FileCode, color: 'bg-blue-100 text-blue-700' },
  { key: 'pdf', label: 'PDF', icon: FileText, color: 'bg-red-100 text-red-700' },
  { key: 'excel', label: 'Excel', icon: Table, color: 'bg-green-100 text-green-700' },
  { key: 'json', label: 'JSON', icon: Braces, color: 'bg-purple-100 text-purple-700' },
  { key: 'gherkin', label: 'Gherkin', icon: ScrollText, color: 'bg-amber-100 text-amber-700' },
] as const;

export const OutputPreview: React.FC<Props> = ({
  output,
  onRefresh,
  isRefreshing,
  onSubmitClarification,
  onUploadClarificationFiles,
  clarificationHistory = [],
}) => {
  const [activeTab, setActiveTab] = useState<'plan' | 'cases' | 'both'>('both');
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [clarificationAnswers, setClarificationAnswers] = useState('');
  const [isUploadingClarificationFiles, setIsUploadingClarificationFiles] = useState(false);

  const clarificationRequired = Boolean(output.metadata.clarification_required);
  const clarificationQuestions = output.metadata.clarification_questions || [];

  const handleClarificationSubmit = () => {
    if (!onSubmitClarification || !clarificationAnswers.trim()) return;
    onSubmitClarification(clarificationAnswers);
    setClarificationAnswers('');
  };

  const handleClarificationFilesChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0 || !onUploadClarificationFiles) return;

    setIsUploadingClarificationFiles(true);
    try {
      await onUploadClarificationFiles(files);
    } finally {
      setIsUploadingClarificationFiles(false);
      e.target.value = '';
    }
  };

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast.success('Copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Failed to copy');
    }
  };

  const handleExport = async (format: 'markdown' | 'pdf' | 'excel' | 'json' | 'gherkin') => {
    setExporting(format);
    try {
      const response = await api.export(output.request_id, {
        format,
        test_plan: output.outputs.test_plan?.content,
        test_cases: output.outputs.test_cases?.content,
      });
      
      const downloadUrl = response.data.download_url;
      window.open(`${import.meta.env.VITE_API_URL || ''}${downloadUrl}`, '_blank');
      
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(`Export failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setExporting(null);
    }
  };

  const planContent = output.outputs.test_plan?.content || '';
  const casesContent = output.outputs.test_cases?.content || '';

  const tabs = [
    { key: 'both', label: 'Both', icon: FileText },
    { key: 'plan', label: 'Test Plan', icon: ScrollText },
    { key: 'cases', label: 'Test Cases', icon: TestTube },
  ] as const;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="section-header mb-0">
          <div className="section-icon bg-gradient-to-br from-pink-500 to-rose-600">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="section-title">Generated Output</h2>
            <p className="section-subtitle">Review and export your test artifacts</p>
          </div>
        </div>
        
        {/* Tabs + Refresh */}
        <div className="flex items-center gap-3">
          <div className="tab-group">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                type="button"
                className={`tab-btn ${activeTab === tab.key ? 'tab-btn-active' : ''}`}
              >
                <tab.icon className="w-4 h-4 inline mr-1" />
                {tab.label}
              </button>
            ))}
          </div>
          {onRefresh && (
            <button
              onClick={() => onRefresh()}
              disabled={isRefreshing}
              type="button"
              title="Regenerate"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>{isRefreshing ? 'Regenerating...' : 'Refresh'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <Cpu className="w-3 h-3" />
            Model
          </div>
          <span className="text-sm font-semibold text-slate-700 truncate block">
            {output.metadata.model_used}
          </span>
        </div>
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <BarChart3 className="w-3 h-3" />
            Temperature
          </div>
          <span className="text-sm font-semibold text-slate-700">
            {output.metadata.temperature}
          </span>
        </div>
        {output.metadata.total_tokens && (
          <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <Sparkles className="w-3 h-3" />
              Tokens
            </div>
            <span className="text-sm font-semibold text-slate-700">
              {output.metadata.total_tokens.toLocaleString()}
            </span>
          </div>
        )}
        {output.outputs.test_cases?.count && (
          <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <TestTube className="w-3 h-3" />
              Test Cases
            </div>
            <span className="text-sm font-semibold text-slate-700">
              {output.outputs.test_cases.count}
            </span>
          </div>
        )}
      </div>

      {clarificationRequired && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-bold text-amber-900 mb-2">Clarification Needed Before Test Case Generation</h3>
          <p className="text-sm text-amber-800 mb-3">
            AI needs additional details. Provide answers below, then regenerate.
          </p>
          {clarificationQuestions.length > 0 && (
            <ul className="list-disc pl-5 text-sm text-amber-900 space-y-1 mb-3">
              {clarificationQuestions.map((q, idx) => (
                <li key={`${idx}-${q.slice(0, 20)}`}>{q}</li>
              ))}
            </ul>
          )}
          {clarificationHistory.length > 0 && (
            <div className="mb-3 rounded-lg border border-amber-200 bg-white p-3">
              <p className="text-xs font-semibold text-amber-900 mb-2">Conversation History</p>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {clarificationHistory.map((entry, idx) => (
                  <div key={`hist-${idx}`} className="text-xs text-slate-700">
                    <p className="font-semibold text-slate-800">Round {idx + 1}</p>
                    {entry.questions.length > 0 && (
                      <ul className="list-disc pl-4 mb-1">
                        {entry.questions.map((q, qIdx) => (
                          <li key={`q-${idx}-${qIdx}`}>{q}</li>
                        ))}
                      </ul>
                    )}
                    <p><span className="font-medium">Answer:</span> {entry.answer}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          <textarea
            value={clarificationAnswers}
            onChange={(e) => setClarificationAnswers(e.target.value)}
            placeholder="Provide answers for the above questions..."
            rows={5}
            className="input-field resize-none bg-white"
          />
          <div className="mt-3">
            <label className="inline-flex items-center gap-2 text-sm font-medium text-amber-900 cursor-pointer">
              <Paperclip className="w-4 h-4" />
              Attach snapshots/documents for clarification
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.png,.jpg,.jpeg"
                onChange={handleClarificationFilesChange}
                className="hidden"
                disabled={isUploadingClarificationFiles || isRefreshing}
              />
            </label>
            <p className="text-xs text-amber-700 mt-1">Supported: PDF, DOCX, PNG, JPG, JPEG</p>
          </div>
          <div className="mt-3 flex justify-end">
            <button
              type="button"
              onClick={handleClarificationSubmit}
              disabled={
                isRefreshing ||
                isUploadingClarificationFiles ||
                !clarificationAnswers.trim() ||
                !onSubmitClarification
              }
              className="btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploadingClarificationFiles ? 'Uploading...' : 'Submit Feedback & Regenerate'}
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
        {/* Toolbar */}
        <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex justify-between items-center">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <FileText className="w-4 h-4" />
            <span className="font-medium">Generated Content</span>
          </div>
          <button
            onClick={() => handleCopy(
              activeTab === 'both' ? `${planContent}\n\n${casesContent}` :
              activeTab === 'plan' ? planContent : casesContent
            )}
            type="button"
            className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy
              </>
            )}
          </button>
        </div>

        {/* Markdown Content */}
        <div className="p-6 max-h-[600px] overflow-y-auto markdown-body">
          {(activeTab === 'both' || activeTab === 'plan') && planContent && (
            <div className={activeTab === 'both' ? 'mb-8 pb-8 border-b border-slate-200' : ''}>
              {activeTab === 'both' && (
                <div className="flex items-center gap-2 mb-4">
                  <ScrollText className="w-5 h-5 text-blue-500" />
                  <h3 className="text-lg font-bold text-slate-900 m-0">Test Plan</h3>
                </div>
              )}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {planContent}
              </ReactMarkdown>
            </div>
          )}
          {(activeTab === 'both' || activeTab === 'cases') && !clarificationRequired && casesContent && (
            <div>
              {activeTab === 'both' && (
                <div className="flex items-center gap-2 mb-4">
                  <TestTube className="w-5 h-5 text-emerald-500" />
                  <h3 className="text-lg font-bold text-slate-900 m-0">Test Cases</h3>
                </div>
              )}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {casesContent}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Export Section */}
      <div className="mt-6">
        <div className="flex items-center gap-2 mb-3">
          <Download className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-semibold text-slate-700">Export As</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {exportFormats.map((format) => (
            <button
              key={format.key}
              onClick={() => handleExport(format.key as any)}
              disabled={exporting === format.key}
              type="button"
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-medium text-slate-700 transition-all duration-200 disabled:opacity-50"
            >
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${format.color}`}>
                {exporting === format.key ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <format.icon className="w-3.5 h-3.5" />
                )}
              </div>
              {format.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
