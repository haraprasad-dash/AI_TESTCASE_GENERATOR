import React, { useState } from 'react';
import { FileDown, RefreshCw, Upload, ChevronDown } from 'lucide-react';
import toast from 'react-hot-toast';
import type { ReviewResponse } from '../types';
import { api } from '../services/api';

interface Props {
  review: ReviewResponse;
  onRefreshStatus: () => Promise<void>;
  refreshing: boolean;
  onSubmitClarification: (answer: string) => Promise<void>;
  onUploadClarificationFiles: (files: File[]) => Promise<void>;
  clarificationHistory: Array<{ questions: string[]; answer: string }>;
}

const clarificationTemplates = [
  'Not applicable to this release',
  'Requirements are correct, test cases need update',
  'Test cases are correct, requirements are outdated',
  'Will provide details via attachment',
  'Proceed with best-effort assumptions',
];

export const ReviewOutput: React.FC<Props> = ({
  review,
  onRefreshStatus,
  refreshing,
  onSubmitClarification,
  onUploadClarificationFiles,
  clarificationHistory,
}) => {
  const [exporting, setExporting] = useState<string | null>(null);
  const [clarificationAnswer, setClarificationAnswer] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState(false);

  const handleExport = async (format: 'markdown' | 'pdf' | 'excel' | 'json' | 'gherkin') => {
    setExporting(format);
    try {
      const response = await api.exportReview(review.review_id, format);
      const downloadUrl = response.data.download_url;
      window.open(`${import.meta.env.VITE_API_URL || ''}${downloadUrl}`, '_blank');
      toast.success(`Exported review as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(`Review export failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setExporting(null);
    }
  };

  const handleClarificationSubmit = async () => {
    if (!clarificationAnswer.trim()) {
      toast.error('Please provide clarification response before submitting');
      return;
    }
    await onSubmitClarification(clarificationAnswer.trim());
    setClarificationAnswer('');
  };

  const handleTemplateClick = (value: string) => {
    setClarificationAnswer(value);
  };

  const handleAttach = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploadingFiles(true);
    try {
      await onUploadClarificationFiles(Array.from(files));
      toast.success('Clarification attachments uploaded');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to upload clarification attachments');
    } finally {
      setUploadingFiles(false);
      event.target.value = '';
    }
  };

  const partial = review.partial_results as Record<string, any> | undefined;
  const pendingTopics = Array.isArray(partial?.pending_clarification_topics)
    ? partial.pending_clarification_topics as string[]
    : [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Review Results</h3>
          <p className="text-sm text-slate-500">Status: {review.status}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn-secondary"
            onClick={onRefreshStatus}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh Status
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleExport('markdown')}
            disabled={exporting !== null}
          >
            <FileDown className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {pendingTopics.length > 0 && (
        <div className="mb-4 p-4 rounded-xl border border-blue-200 bg-blue-50">
          <p className="font-semibold text-blue-800 mb-2">Partial Results Available</p>
          <p className="text-sm text-blue-700 mb-2">! This section is pending clarification on:</p>
          <ul className="list-disc pl-5 text-sm text-blue-900 space-y-1">
            {pendingTopics.map((topic, idx) => (
              <li key={idx}>{topic}</li>
            ))}
          </ul>
        </div>
      )}

      {partial?.assumptions_disclaimer && (
        <div className="mb-4 p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-sm">
          {String(partial.assumptions_disclaimer)}
        </div>
      )}

      {review.metadata.clarification_required && review.metadata.clarification_questions.length > 0 && (
        <div className="mb-4 p-4 rounded-xl border border-amber-200 bg-amber-50">
          <p className="font-semibold text-amber-800 mb-2">Clarification Needed</p>
          <ul className="list-disc pl-5 text-sm text-amber-900 space-y-1">
            {review.metadata.clarification_questions.map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>

          <div className="mt-3 flex flex-wrap gap-2">
            {clarificationTemplates.map((template) => (
              <button
                key={template}
                type="button"
                className="px-2.5 py-1 text-xs rounded-full bg-white border border-amber-200 text-amber-800 hover:bg-amber-100"
                onClick={() => handleTemplateClick(template)}
              >
                {template}
              </button>
            ))}
          </div>

          <textarea
            className="input-field mt-3"
            rows={4}
            value={clarificationAnswer}
            onChange={(e) => setClarificationAnswer(e.target.value)}
            placeholder="Provide clarification response..."
          />

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <label className="btn-secondary cursor-pointer">
              <Upload className="w-4 h-4" />
              {uploadingFiles ? 'Uploading...' : 'Attach Clarification Files'}
              <input
                type="file"
                multiple
                className="hidden"
                onChange={handleAttach}
              />
            </label>
            <button className="btn-primary" onClick={handleClarificationSubmit}>
              Submit Clarification
            </button>
          </div>
        </div>
      )}

      {clarificationHistory.length > 0 && (
        <details className="mb-4 p-4 rounded-xl border border-slate-200 bg-slate-50">
          <summary className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
            <ChevronDown className="w-4 h-4" />
            Clarification History ({clarificationHistory.length})
          </summary>
          <div className="mt-3 space-y-3">
            {clarificationHistory.map((entry, idx) => (
              <div key={idx} className="p-3 bg-white border border-slate-200 rounded-lg">
                <p className="text-xs font-semibold text-slate-500 mb-1">Round {idx + 1}</p>
                <ul className="list-disc pl-5 text-sm text-slate-700 mb-2">
                  {entry.questions.map((q, qIdx) => (
                    <li key={qIdx}>{q}</li>
                  ))}
                </ul>
                <p className="text-sm text-slate-800">{entry.answer}</p>
                <button
                  type="button"
                  className="mt-2 text-xs text-blue-600 hover:underline"
                  onClick={() => setClarificationAnswer(entry.answer)}
                >
                  Reuse/Edit this answer
                </button>
              </div>
            ))}
          </div>
        </details>
      )}

      <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs overflow-auto max-h-[32rem] whitespace-pre-wrap">
        {review.report_markdown}
      </pre>
    </div>
  );
};
