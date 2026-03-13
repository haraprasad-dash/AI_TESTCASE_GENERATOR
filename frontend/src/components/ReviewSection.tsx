import React, { useState } from 'react';
import { CheckSquare, BookOpen, FileSearch, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import type { FileInput, EnhancePromptType } from '../types';

interface Props {
  reviewTestCases: boolean;
  setReviewTestCases: (value: boolean) => void;
  reviewUserGuide: boolean;
  setReviewUserGuide: (value: boolean) => void;
  userGuideUrl: string;
  setUserGuideUrl: (value: string) => void;
  reviewCustomInstructions: string;
  setReviewCustomInstructions: (value: string) => void;
  jiraIds: string[];
  valueEdgeIds: string[];
  uploadedFiles: FileInput[];
  onReviewFilesSelected: (files: FileList) => Promise<void>;
  provider?: 'groq' | 'ollama';
  model?: string;
}

export const ReviewSection: React.FC<Props> = ({
  reviewTestCases,
  setReviewTestCases,
  reviewUserGuide,
  setReviewUserGuide,
  userGuideUrl,
  setUserGuideUrl,
  reviewCustomInstructions,
  setReviewCustomInstructions,
  jiraIds,
  valueEdgeIds,
  uploadedFiles,
  onReviewFilesSelected,
  provider = 'groq',
  model = 'llama-3.3-70b-versatile',
}) => {
  const [isEnhancingInstructions, setIsEnhancingInstructions] = useState(false);

  const handleReviewFileInput = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    await onReviewFilesSelected(files);
    event.target.value = '';
  };

  const handleEnhanceInstructions = async () => {
    if (!reviewCustomInstructions.trim()) {
      toast.error('Type instructions first before enhancing');
      return;
    }

    setIsEnhancingInstructions(true);
    try {
      let promptType: EnhancePromptType = 'review';
      if (reviewTestCases && !reviewUserGuide) {
        promptType = 'review_test_cases';
      } else if (!reviewTestCases && reviewUserGuide) {
        promptType = 'review_user_guide';
      }

      const res = await api.enhancePrompt(reviewCustomInstructions, provider, model, promptType, {
        jira_ids: jiraIds,
        valueedge_ids: valueEdgeIds,
        files: uploadedFiles.slice(0, 8).map((file) => ({
          filename: file.filename,
          content_type: file.content_type,
          extracted_snippet: (file.extracted_text || '').slice(0, 180),
        })),
        user_guide_url: userGuideUrl.trim() || undefined,
        review_test_cases: reviewTestCases,
        review_user_guide: reviewUserGuide,
      });
      setReviewCustomInstructions(res.data.enhanced_prompt);
      toast.success('Review instructions enhanced!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to enhance instructions');
    } finally {
      setIsEnhancingInstructions(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-icon bg-gradient-to-br from-emerald-500 to-teal-600">
          <FileSearch className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="section-title">Review Modes</h2>
          <p className="section-subtitle">Enable one or both review agents and provide optional guide URL</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <label className="flex items-start gap-3 p-4 border border-slate-200 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer">
          <input
            type="checkbox"
            className="mt-1"
            checked={reviewTestCases}
            onChange={(e) => setReviewTestCases(e.target.checked)}
          />
          <div>
            <p className="font-semibold text-slate-800 flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-blue-600" />
              Enable Test Case Review
            </p>
            <p className="text-xs text-slate-600 mt-1">Checks coverage, quality, gaps, and redundancy in uploaded test cases.</p>
          </div>
        </label>

        <label className="flex items-start gap-3 p-4 border border-slate-200 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer">
          <input
            type="checkbox"
            className="mt-1"
            checked={reviewUserGuide}
            onChange={(e) => setReviewUserGuide(e.target.checked)}
          />
          <div>
            <p className="font-semibold text-slate-800 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              Enable User Guide Review
            </p>
            <p className="text-xs text-slate-600 mt-1">Verifies documentation accuracy, completeness, and consistency.</p>
          </div>
        </label>
      </div>

      <div>
        <label className="input-label">User Guide URL (optional)</label>
        <input
          type="url"
          className="input-field"
          placeholder="https://docs.example.com/user-guide"
          value={userGuideUrl}
          onChange={(e) => setUserGuideUrl(e.target.value)}
        />
      </div>

      <div className="mt-4 p-3 rounded-xl border border-slate-200 bg-slate-50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-800">Attach Files for Review</p>
            <p className="text-xs text-slate-600">
              Test cases: .feature, .xlsx, .xls, .txt, .md | User guides: .pdf, .docx, .txt, .md
            </p>
          </div>
          <label className="btn-secondary cursor-pointer">
            Attach Review Files
            <input
              type="file"
              multiple
              className="hidden"
              accept=".feature,.xlsx,.xls,.txt,.md,.pdf,.docx"
              onChange={handleReviewFileInput}
            />
          </label>
        </div>
      </div>

      <div className="mt-4">
        <label className="input-label">Review Custom Instructions (optional)</label>
        <textarea
          className="input-field resize-none"
          rows={4}
          placeholder="Add review-specific instructions (e.g., prioritize security gaps, strict BDD syntax checks, or focus on release scope)."
          value={reviewCustomInstructions}
          onChange={(e) => setReviewCustomInstructions(e.target.value)}
        />
        <div className="flex justify-between items-center mt-2 gap-3">
          <span className="text-xs text-slate-400">
            Use enhance to improve clarity and coverage.
          </span>
          <span className={`text-xs font-medium ${
            reviewCustomInstructions.length > 500 ? 'text-amber-500' : 'text-slate-400'
          }`}>
            {reviewCustomInstructions.length} chars
          </span>
          <button
            type="button"
            onClick={handleEnhanceInstructions}
            disabled={isEnhancingInstructions || !reviewCustomInstructions.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:from-blue-600 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
          >
            <RefreshCw className={`w-3 h-3 ${isEnhancingInstructions ? 'animate-spin' : ''}`} />
            {isEnhancingInstructions ? 'Enhancing...' : '✨ Enhance'}
          </button>
        </div>
      </div>
    </div>
  );
};
