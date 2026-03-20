import React, { useState } from 'react';
import { CheckSquare, BookOpen, FileSearch, RefreshCw, X, FileText, FileImage, FileType2 } from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import type { FileInput, EnhancePromptType } from '../types';

interface Props {
  reviewTestCases: boolean;
  setReviewTestCases: (value: boolean) => void;
  reviewUserGuide: boolean;
  setReviewUserGuide: (value: boolean) => void;
  testCaseReviewInstructions: string;
  setTestCaseReviewInstructions: (value: string) => void;
  userGuideReviewInstructions: string;
  setUserGuideReviewInstructions: (value: string) => void;
  jiraIds: string[];
  valueEdgeIds: string[];
  uploadedFiles: FileInput[];
  reviewTestCaseFileIds: string[];
  userGuideDocumentFileIds: string[];
  userGuideReferenceFileIds: string[];
  onTestCaseFilesSelected: (files: FileList) => Promise<void>;
  onUserGuideDocumentsSelected: (files: FileList) => Promise<void>;
  onUserGuideReferenceFilesSelected: (files: FileList) => Promise<void>;
  onRemoveFile: (fileId: string) => void;
  provider?: 'groq' | 'ollama';
  model?: string;
}

export const ReviewSection: React.FC<Props> = ({
  reviewTestCases,
  setReviewTestCases,
  reviewUserGuide,
  setReviewUserGuide,
  testCaseReviewInstructions,
  setTestCaseReviewInstructions,
  userGuideReviewInstructions,
  setUserGuideReviewInstructions,
  jiraIds,
  valueEdgeIds,
  uploadedFiles,
  reviewTestCaseFileIds,
  userGuideDocumentFileIds,
  userGuideReferenceFileIds,
  onTestCaseFilesSelected,
  onUserGuideDocumentsSelected,
  onUserGuideReferenceFilesSelected,
  onRemoveFile,
  provider = 'groq',
  model = 'llama-3.3-70b-versatile',
}) => {
  const [enhancingTarget, setEnhancingTarget] = useState<'test-cases' | 'user-guide' | null>(null);

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.pdf')) return <FileType2 className="w-5 h-5 text-red-500" />;
    if (filename.match(/\.(jpg|jpeg|png)$/i)) return <FileImage className="w-5 h-5 text-green-500" />;
    return <FileText className="w-5 h-5 text-blue-500" />;
  };

  const handleReviewFileInput = async (
    event: React.ChangeEvent<HTMLInputElement>,
    target: 'test-cases' | 'user-guide-docs' | 'user-guide-reference'
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    if (target === 'test-cases') {
      await onTestCaseFilesSelected(files);
    } else if (target === 'user-guide-docs') {
      await onUserGuideDocumentsSelected(files);
    } else {
      await onUserGuideReferenceFilesSelected(files);
    }
    event.target.value = '';
  };

  const handleEnhanceInstructions = async (
    value: string,
    promptType: EnhancePromptType,
    applyEnhanced: (next: string) => void,
    target: 'test-cases' | 'user-guide'
  ) => {
    if (!value.trim()) {
      toast.error('Type instructions first before enhancing');
      return;
    }

    setEnhancingTarget(target);
    try {
      const res = await api.enhancePrompt(value, provider, model, promptType, {
        jira_ids: jiraIds,
        valueedge_ids: valueEdgeIds,
        files: uploadedFiles.slice(0, 8).map((file) => ({
          filename: file.filename,
          content_type: file.content_type,
          extracted_snippet: (file.extracted_text || '').slice(0, 180),
        })),
        review_test_cases: reviewTestCases,
        review_user_guide: reviewUserGuide,
      });
      applyEnhanced(res.data.enhanced_prompt);
      toast.success('Review instructions enhanced!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to enhance instructions');
    } finally {
      setEnhancingTarget(null);
    }
  };

  const isGuideDocumentFile = (filename: string) => /\.(pdf|docx|txt|md)$/i.test(filename);
  const isGuideReferenceFile = (filename: string) => /\.(feature|pdf|docx|txt|md|xlsx|xls)$/i.test(filename);
  const isGuideReferenceOnlyFile = (filename: string) => /\.(feature|xlsx|xls)$/i.test(filename);
  const scopedTestCaseFiles = uploadedFiles.filter((file) => reviewTestCaseFileIds.includes(file.file_id));
  const scopedUserGuideDocumentFiles = uploadedFiles.filter((file) => userGuideDocumentFileIds.includes(file.file_id));
  const scopedUserGuideReferenceFiles = uploadedFiles.filter((file) => userGuideReferenceFileIds.includes(file.file_id));
  const testCaseFiles = scopedTestCaseFiles.length > 0
    ? scopedTestCaseFiles
    : uploadedFiles.filter(
        (file) => /\.(feature|xlsx|xls|txt|md)$/i.test(file.filename)
          && !userGuideDocumentFileIds.includes(file.file_id)
          && !userGuideReferenceFileIds.includes(file.file_id)
      );
  const userGuideDocumentFiles = scopedUserGuideDocumentFiles.length > 0
    ? scopedUserGuideDocumentFiles
    : uploadedFiles.filter(
        (file) => isGuideDocumentFile(file.filename)
          && !userGuideReferenceFileIds.includes(file.file_id)
      );
  const userGuideReferenceFiles = scopedUserGuideReferenceFiles.length > 0
    ? scopedUserGuideReferenceFiles
    : uploadedFiles.filter(
        (file) => isGuideReferenceOnlyFile(file.filename)
          && !reviewTestCaseFileIds.includes(file.file_id)
          && !userGuideDocumentFileIds.includes(file.file_id)
      );

  const renderInstructionField = (
    label: string,
    value: string,
    setValue: (next: string) => void,
    promptType: EnhancePromptType,
    target: 'test-cases' | 'user-guide',
    placeholder: string,
    className = 'mt-4',
  ) => (
    <div className={className}>
      <label className="input-label">{label}</label>
      <textarea
        className="input-field resize-none"
        rows={4}
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <div className="flex justify-between items-center mt-2 gap-3">
        <span className="text-xs text-slate-400">
          Use enhance to improve clarity and coverage.
        </span>
        <span className={`text-xs font-medium ${
          value.length > 500 ? 'text-amber-500' : 'text-slate-400'
        }`}>
          {value.length} chars
        </span>
        <button
          type="button"
          onClick={() => handleEnhanceInstructions(value, promptType, setValue, target)}
          disabled={enhancingTarget !== null || !value.trim()}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:from-blue-600 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
        >
          <RefreshCw className={`w-3 h-3 ${enhancingTarget === target ? 'animate-spin' : ''}`} />
          {enhancingTarget === target ? 'Enhancing...' : '✨ Enhance'}
        </button>
      </div>
    </div>
  );

  return (
    <div>
      <div className="section-header">
        <div className="section-icon bg-gradient-to-br from-emerald-500 to-teal-600">
          <FileSearch className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="section-title">Review Modes</h2>
          <p className="section-subtitle">Configure each review mode independently.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4 lg:items-stretch">
        <div className={`rounded-2xl border p-4 transition-colors h-full flex flex-col ${reviewTestCases ? 'border-blue-200 bg-blue-50/60' : 'border-slate-200 bg-slate-50'}`}>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              checked={reviewTestCases}
              onChange={(e) => setReviewTestCases(e.target.checked)}
            />
            <div>
              <p className="font-semibold text-slate-800 flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-blue-600" />
                Test Case Review Section
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Checks coverage, quality, gaps, redundancy, and BDD/test-structure issues in uploaded test cases.
              </p>
            </div>
          </label>
          <div className="mt-4" aria-hidden="true">
            <label className="input-label opacity-0 select-none">User Guide Documents</label>
            <div className="h-[48px] rounded-xl border border-transparent" />
          </div>
          <div className="mt-4 p-3 rounded-xl border border-blue-200 bg-white/70 min-h-[92px]">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-800">Attach Review Files</p>
              <label className="btn-secondary cursor-pointer">
                Attach Review Files
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept=".feature,.xlsx,.xls,.txt,.md"
                  onChange={(event) => handleReviewFileInput(event, 'test-cases')}
                />
              </label>
            </div>
            {testCaseFiles.length > 0 && (
              <div className="mt-3 space-y-2 max-h-44 overflow-auto pr-1">
                {testCaseFiles.map((file) => (
                  <div key={file.file_id} className="file-item bg-white">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                        {getFileIcon(file.filename)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-700">{file.filename}</p>
                        <p className="text-xs text-slate-400">{(file.size_bytes / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => onRemoveFile(file.file_id)}
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                      type="button"
                      aria-label={`Remove ${file.filename}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {!reviewTestCases && (
            <p className="mt-4 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
              Template is disabled for Test Case Review. Submitted instructions will be used directly.
            </p>
          )}
          {renderInstructionField(
            'Test Case Review Instructions (optional)',
            testCaseReviewInstructions,
            setTestCaseReviewInstructions,
            'review_test_cases',
            'test-cases',
            'Add test case review-specific instructions (e.g., strict BDD syntax checks, prioritize coverage gaps, traceability, duplicates).',
            'mt-4',
          )}
        </div>

        <div className={`rounded-2xl border p-4 transition-colors h-full flex flex-col ${reviewUserGuide ? 'border-indigo-200 bg-indigo-50/60' : 'border-slate-200 bg-slate-50'}`}>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              checked={reviewUserGuide}
              onChange={(e) => setReviewUserGuide(e.target.checked)}
            />
            <div>
              <p className="font-semibold text-slate-800 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                User Guide Review Section
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Verifies user documentation accuracy, completeness, consistency, usability, and missing prerequisites.
              </p>
            </div>
          </label>
          <div className="mt-4 p-3 rounded-xl border border-indigo-200 bg-white/70 min-h-[116px]">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">Attach User Guide Documents</p>
                <p className="text-xs text-slate-500">Attach one or more user guide files used for review (.pdf, .docx, .txt, .md).</p>
              </div>
              <label className="btn-secondary cursor-pointer">
                Attach Guide Documents
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(event) => handleReviewFileInput(event, 'user-guide-docs')}
                />
              </label>
            </div>
            {userGuideDocumentFiles.length > 0 && (
              <div className="mt-3 space-y-2 max-h-44 overflow-auto pr-1">
                {userGuideDocumentFiles.filter((file) => isGuideDocumentFile(file.filename)).map((file) => (
                  <div key={file.file_id} className="file-item bg-white">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                        {getFileIcon(file.filename)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-700">{file.filename}</p>
                        <p className="text-xs text-slate-400">{(file.size_bytes / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => onRemoveFile(file.file_id)}
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                      type="button"
                      aria-label={`Remove ${file.filename}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="mt-3 p-3 rounded-xl border border-indigo-200 bg-white/70 min-h-[92px]">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">Attach Reference Files (optional)</p>
                <p className="text-xs text-slate-500">Attach testcase/PRD artifacts used as supporting context (.feature, .xlsx, .xls, .pdf, .docx, .txt, .md).</p>
              </div>
              <label className="btn-secondary cursor-pointer">
                Attach Reference Files
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept=".feature,.xlsx,.xls,.pdf,.docx,.txt,.md"
                  onChange={(event) => handleReviewFileInput(event, 'user-guide-reference')}
                />
              </label>
            </div>
            {userGuideReferenceFiles.length > 0 && (
              <div className="mt-3 space-y-2 max-h-44 overflow-auto pr-1">
                {userGuideReferenceFiles.filter((file) => isGuideReferenceFile(file.filename)).map((file) => (
                  <div key={file.file_id} className="file-item bg-white">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                        {getFileIcon(file.filename)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-700">{file.filename}</p>
                        <p className="text-xs text-slate-400">{(file.size_bytes / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => onRemoveFile(file.file_id)}
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                      type="button"
                      aria-label={`Remove ${file.filename}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          {!reviewUserGuide && (
            <p className="mt-4 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
              Template is disabled for User Guide Review. Submitted instructions will be used directly.
            </p>
          )}
          {renderInstructionField(
            'User Guide Review Instructions (optional)',
            userGuideReviewInstructions,
            setUserGuideReviewInstructions,
            'review_user_guide',
            'user-guide',
            'Add user guide review-specific instructions (e.g., focus on customer-facing guidance, domain terminology, and practical usage steps).',
            'mt-4',
          )}
        </div>
      </div>
    </div>
  );
};
