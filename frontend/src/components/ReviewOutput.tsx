import React, { useState } from 'react';
import { FileDown, RefreshCw, Upload, ChevronDown } from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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

  const reportJson = (review.report_json || {}) as Record<string, any>;
  const testCaseReview = reportJson.test_case_review as Record<string, any> | undefined;
  const testCaseSummary = (testCaseReview?.summary || {}) as Record<string, any>;
  const coverageMatrix = Array.isArray(testCaseReview?.coverage_matrix)
    ? testCaseReview?.coverage_matrix as Array<Record<string, string>>
    : [];
  const criticalGaps = Array.isArray(testCaseReview?.critical_gaps)
    ? testCaseReview?.critical_gaps as Array<Record<string, string>>
    : [];

  const userGuideReview = reportJson.user_guide_review as Record<string, any> | undefined;
  const guideSummary = (userGuideReview?.summary || {}) as Record<string, any>;
  const strengths = Array.isArray(userGuideReview?.strengths) ? userGuideReview?.strengths as Array<Record<string, string>> : [];
  const modifications = Array.isArray(userGuideReview?.modification_recommendations)
    ? userGuideReview?.modification_recommendations as Array<Record<string, string>>
    : [];
  const missingTopics = Array.isArray(userGuideReview?.missing_topics)
    ? userGuideReview?.missing_topics as Array<Record<string, string>>
    : [];
  const instructionChecks = Array.isArray(userGuideReview?.instruction_checks)
    ? userGuideReview?.instruction_checks as Array<Record<string, string>>
    : [];

  const qualityScoreFromMarkdown = (() => {
    const match = /Quality Score:\s*(\d{1,3})\s*\/\s*100/i.exec(review.report_markdown || '');
    return match ? Number(match[1]) : null;
  })();
  const resolvedGuideQualityScore = guideSummary.quality_score ?? qualityScoreFromMarkdown;

  const hasTestCaseData = Boolean(
    testCaseReview &&
    (Object.keys(testCaseSummary).length > 0 || coverageMatrix.length > 0 || criticalGaps.length > 0)
  );
  const hasGuideData = Boolean(
    userGuideReview &&
    (Object.keys(guideSummary).length > 0 || strengths.length > 0 || modifications.length > 0 || missingTopics.length > 0)
  );
  const hasGuideDetailLists = strengths.length > 0 || modifications.length > 0 || missingTopics.length > 0;
  const hasStructuredData = hasTestCaseData || hasGuideData;
  const hasMarkdown = Boolean((review.report_markdown || '').trim());
  const showNarrativeFallback = hasMarkdown && (!hasStructuredData || (hasGuideData && !hasGuideDetailLists && !hasTestCaseData));

  const recommendationLines = (review.report_markdown || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => Boolean(line))
    .filter((line) => /how to fix|recommended|suggested rewrite|line to modify|add section|\bfix\b/i.test(line))
    .map((line) => line.replace(/^[-*]\s*/, '').replace(/^\d+\.\s*/, '').trim())
    .filter((line, index, array) => array.indexOf(line) === index)
    .slice(0, 8);

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

      {!review.metadata.clarification_required ? (
        <div className="space-y-4">
          {hasTestCaseData && (
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-4">
              <h4 className="text-base font-semibold text-slate-900">Test Case Review</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Requirements</p>
                  <p className="text-lg font-semibold text-slate-900">{String(testCaseSummary.requirements ?? 0)}</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Test Cases</p>
                  <p className="text-lg font-semibold text-slate-900">{String(testCaseSummary.test_cases ?? 0)}</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Coverage Score</p>
                  <p className="text-lg font-semibold text-slate-900">{String(testCaseSummary.coverage_score ?? 0)}%</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Overall Health</p>
                  <p className="text-lg font-semibold text-slate-900">{String(testCaseSummary.overall_health || '-')}</p>
                </div>
              </div>
              {testCaseSummary.review_mode && (
                <p className="text-xs text-slate-500">Mode: {String(testCaseSummary.review_mode)}</p>
              )}

              {criticalGaps.length > 0 && (
                <div className="p-3 rounded-lg border border-red-200 bg-red-50">
                  <p className="text-sm font-semibold text-red-900 mb-2">Critical Gaps</p>
                  <ul className="space-y-1">
                    {criticalGaps.slice(0, 8).map((gap, idx) => (
                      <li key={`${gap.req_id || 'gap'}-${idx}`} className="text-sm text-red-900">
                        <span className="font-semibold">{gap.req_id || `Gap ${idx + 1}`}</span>
                        {gap.description ? ` — ${gap.description}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coverageMatrix.length > 0 && (
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 overflow-auto">
                  <p className="text-sm font-semibold text-slate-800 mb-2">Coverage Mapping</p>
                  <table className="min-w-full text-xs border-collapse">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="py-1 pr-3">Req ID</th>
                        <th className="py-1 pr-3">Covered By</th>
                        <th className="py-1 pr-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {coverageMatrix.slice(0, 10).map((row, idx) => (
                        <tr key={`${row.req_id || 'row'}-${idx}`} className="border-t border-slate-200 text-slate-700">
                          <td className="py-1 pr-3 font-medium">{row.req_id || '-'}</td>
                          <td className="py-1 pr-3">{row.covered_by || '-'}</td>
                          <td className="py-1 pr-3">{row.coverage_status || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {hasGuideData && (
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-4">
              <h4 className="text-base font-semibold text-slate-900">User Guide Review</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Guide Readiness</p>
                  <p className="text-lg font-semibold text-slate-900">{String(guideSummary.overall_grade || '-')}</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Quality Score</p>
                  <p className="text-lg font-semibold text-slate-900">{resolvedGuideQualityScore !== null && resolvedGuideQualityScore !== undefined ? `${String(resolvedGuideQualityScore)}/100` : '-'}</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Needs Modification</p>
                  <p className="text-lg font-semibold text-slate-900">{String(guideSummary.needs_modification ?? 0)}</p>
                </div>
                <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                  <p className="text-xs text-slate-500">Missing Topics</p>
                  <p className="text-lg font-semibold text-slate-900">{String(guideSummary.missing ?? 0)}</p>
                </div>
              </div>
              {guideSummary.review_mode && (
                <p className="text-xs text-slate-500">Mode: {String(guideSummary.review_mode)}</p>
              )}
              {guideSummary.instruction_influence_count !== undefined && (
                <p className="text-xs text-slate-500">Instruction influence: {String(guideSummary.instruction_influence_count)}</p>
              )}

              {modifications.length > 0 && (
                <div className="p-3 rounded-lg border border-amber-200 bg-amber-50">
                  <p className="text-sm font-semibold text-amber-900 mb-2">Line-Level Modifications Required</p>
                  <div className="space-y-2">
                    {modifications.map((row, idx) => (
                      <div key={`${row.line_reference || 'line'}-${idx}`} className="p-3 rounded-lg border border-amber-200 bg-white">
                        <p className="text-sm font-semibold text-slate-900">
                          {idx + 1}. {row.issue_type || 'Modification required'}
                        </p>
                        <p className="text-xs text-slate-500">Line: {row.line_reference || 'Not found in extracted text'}</p>
                        {row.observed_text && (
                          <p className="text-sm text-slate-700 mt-1">Current: {row.observed_text}</p>
                        )}
                        {row.recommendation && (
                          <p className="text-sm text-slate-800 mt-1">Fix: {row.recommendation}</p>
                        )}
                        {row.replacement_example && (
                          <p className="text-sm text-slate-700 mt-1">Suggested rewrite: {row.replacement_example}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {missingTopics.length > 0 && (
                <div className="p-3 rounded-lg border border-blue-200 bg-blue-50">
                  <p className="text-sm font-semibold text-blue-900 mb-2">Missing Customer Topics</p>
                  <ul className="space-y-2">
                    {missingTopics.map((row, idx) => (
                      <li key={`${row.expected_topic || 'topic'}-${idx}`} className="text-sm text-blue-900">
                        <span className="font-semibold">{row.expected_topic || 'Untitled topic'}</span>
                        {row.suggested_location ? ` — ${row.suggested_location}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {strengths.length > 0 && (
                <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50">
                  <p className="text-sm font-semibold text-emerald-900 mb-2">Confirmed Strong Areas</p>
                  <ul className="space-y-1">
                    {strengths.map((row, idx) => (
                      <li key={`${row.title || 'strength'}-${idx}`} className="text-sm text-emerald-900">
                        <span className="font-semibold">{row.title || row.section || 'Guide section'}</span>
                        {row.verification_status ? ` — ${row.verification_status}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {instructionChecks.length > 0 && (
                <div className="p-3 rounded-lg border border-indigo-200 bg-indigo-50">
                  <p className="text-sm font-semibold text-indigo-900 mb-2">Custom Instruction Compliance</p>
                  <ul className="space-y-1">
                    {instructionChecks.map((row, idx) => (
                      <li key={`${row.instruction || 'instruction'}-${idx}`} className="text-sm text-indigo-900">
                        <span className="font-semibold">{row.status === 'matched' ? 'Matched' : 'Missing'}:</span> {row.instruction || '-'}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {showNarrativeFallback && (
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <p className="text-sm font-semibold text-slate-800 mb-2">Detailed Findings</p>
              {recommendationLines.length > 0 && (
                <div className="mb-3 rounded-lg border border-indigo-200 bg-indigo-50 p-3">
                  <p className="text-sm font-semibold text-indigo-900 mb-2">Actionable Recommendations</p>
                  <ul className="list-disc pl-5 space-y-1">
                    {recommendationLines.map((line, index) => (
                      <li key={`${line}-${index}`} className="text-sm text-indigo-900">{line}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="max-h-[26rem] overflow-auto rounded-lg border border-slate-200 bg-white p-4 prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h1 className="text-2xl font-bold text-slate-900 mb-3">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-xl font-semibold text-slate-900 mt-5 mb-2 border-b border-slate-200 pb-1">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-semibold text-slate-800 mt-4 mb-2">{children}</h3>,
                    p: ({ children }) => <p className="text-sm leading-6 text-slate-700 mb-2">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 mb-3">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 mb-3">{children}</ol>,
                    li: ({ children }) => <li className="text-sm leading-6 text-slate-700">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
                    table: ({ children }) => <table className="min-w-full text-sm border border-slate-200 rounded-lg overflow-hidden mb-3">{children}</table>,
                    thead: ({ children }) => <thead className="bg-slate-100">{children}</thead>,
                    th: ({ children }) => <th className="px-3 py-2 text-left text-xs font-semibold text-slate-700 border-b border-slate-200">{children}</th>,
                    td: ({ children }) => <td className="px-3 py-2 text-sm text-slate-700 border-b border-slate-100">{children}</td>,
                    hr: () => <hr className="my-4 border-slate-200" />,
                  }}
                >
                  {review.report_markdown}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {!hasStructuredData && !hasMarkdown && (
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <p className="text-sm font-semibold text-slate-800">No review details available yet</p>
              <p className="text-sm text-slate-600 mt-1">
                Status: {review.status}. Try Refresh Status once, or rerun review if this persists.
              </p>
              {review.error && (
                <p className="text-sm text-red-700 mt-2">Error: {review.error}</p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-600">
          Full report is withheld until clarification is completed. Submit clarification to view the finalized review output.
        </div>
      )}
    </div>
  );
};
