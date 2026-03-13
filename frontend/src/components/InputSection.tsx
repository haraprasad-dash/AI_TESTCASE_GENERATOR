import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, FileText, X, FileImage, FileType2, 
  Ticket, Database, CheckCircle2, AlertCircle, Search, Loader2
} from 'lucide-react';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import type { FileInput } from '../types';

interface Props {
  jiraId: string;
  setJiraId: (value: string) => void;
  jiraIds: string[];
  setJiraIds: (value: string[]) => void;
  valueEdgeId: string;
  setValueEdgeId: (value: string) => void;
  valueEdgeIds: string[];
  setValueEdgeIds: (value: string[]) => void;
  uploadedFiles: FileInput[];
  onFileUpload: (file: FileInput) => void;
  onRemoveFile: (fileId: string) => void;
}

type FetchStatus = 'idle' | 'loading' | 'success' | 'error';

export const InputSection: React.FC<Props> = ({
  jiraId,
  setJiraId,
  jiraIds,
  setJiraIds,
  valueEdgeId,
  setValueEdgeId,
  valueEdgeIds,
  setValueEdgeIds,
  uploadedFiles,
  onFileUpload,
  onRemoveFile,
}) => {
  const [jiraStatus, setJiraStatus] = useState<FetchStatus>('idle');
  const [jiraTickets, setJiraTickets] = useState<any[]>([]);
  const [jiraDetailFilters, setJiraDetailFilters] = useState<Record<string, string>>({});
  const [veStatus, setVeStatus] = useState<FetchStatus>('idle');
  const [veTickets, setVeTickets] = useState<any[]>([]);

  const clearJiraTicket = () => {
    setJiraId('');
    setJiraStatus('idle');
  };

  const clearValueEdgeTicket = () => {
    setValueEdgeId('');
    setVeStatus('idle');
  };

  const upsertTicketByKey = (tickets: any[], ticket: any, keyField: 'key' | 'id') => {
    const key = ticket?.[keyField];
    if (!key) return tickets;
    const idx = tickets.findIndex((t) => t?.[keyField] === key);
    if (idx === -1) return [...tickets, ticket];
    const next = [...tickets];
    next[idx] = ticket;
    return next;
  };

  const removeJiraTicket = (ticketKey: string) => {
    setJiraTickets((prev) => prev.filter((t) => t.key !== ticketKey));
    setJiraIds(jiraIds.filter((id) => id !== ticketKey));
    setJiraDetailFilters((prev) => {
      const next = { ...prev };
      delete next[ticketKey];
      return next;
    });
  };

  const removeValueEdgeTicket = (ticketId: string) => {
    setVeTickets((prev) => prev.filter((t) => String(t.id) !== String(ticketId)));
    setValueEdgeIds(valueEdgeIds.filter((id) => id !== String(ticketId)));
  };

  const fetchJiraTicket = async () => {
    if (!jiraId.trim()) { toast.error('Enter a JIRA Issue ID first'); return; }
    const normalizedJiraId = jiraId.trim().toUpperCase();
    setJiraStatus('loading');
    try {
      const res = await api.getJiraIssue(normalizedJiraId);
      setJiraTickets((prev) => upsertTicketByKey(prev, res.data, 'key'));
      setJiraIds(jiraIds.includes(res.data.key) ? jiraIds : [...jiraIds, res.data.key]);
      setJiraStatus('success');
      toast.success(`Fetched: ${res.data.key} — ${res.data.summary}`);
      setJiraId('');
    } catch (err: any) {
      setJiraStatus('error');
      toast.error(err.response?.data?.detail || 'JIRA ticket not found');
    }
  };

  const fetchVeTicket = async () => {
    if (!valueEdgeId.trim()) { toast.error('Enter a ValueEdge Item ID first'); return; }
    const normalizedValueEdgeId = valueEdgeId.trim();
    setVeStatus('loading');
    try {
      const res = await api.getValueEdgeItem(normalizedValueEdgeId);
      setVeTickets((prev) => upsertTicketByKey(prev, res.data, 'id'));
      const resolvedId = String(res.data.id ?? normalizedValueEdgeId);
      setValueEdgeIds(valueEdgeIds.includes(resolvedId) ? valueEdgeIds : [...valueEdgeIds, resolvedId]);
      setVeStatus('success');
      toast.success(`Fetched: ${res.data.name || res.data.id}`);
      setValueEdgeId('');
    } catch (err: any) {
      setVeStatus('error');
      toast.error(err.response?.data?.detail || 'ValueEdge item not found');
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      try {
        const response = await api.uploadFile(file);
        onFileUpload(response.data);
        toast.success(`Uploaded: ${file.name}`);
      } catch (error: any) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/plain': ['.txt', '.feature'],
      'text/markdown': ['.md'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
    maxSize: 20 * 1024 * 1024,
  });

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.pdf')) return <FileType2 className="w-5 h-5 text-red-500" />;
    if (filename.match(/\.(jpg|jpeg|png)$/)) return <FileImage className="w-5 h-5 text-green-500" />;
    return <FileText className="w-5 h-5 text-blue-500" />;
  };

  const formatTicketValue = (value: any): string => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) {
      if (value.length === 0) return '—';
      return value.map((item) => formatTicketValue(item)).join(', ');
    }
    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, any>);
      if (entries.length === 0) return '—';
      return entries
        .map(([key, nested]) => `${key}: ${formatTicketValue(nested)}`)
        .join(' | ');
    }
    return String(value);
  };

  const formatReadableText = (raw: string): string => {
    if (!raw) return '';
    const compact = raw.replace(/\s+/g, ' ').trim();
    return compact
      .replace(/\s([A-Z][A-Za-z\s/&()]{2,40}:)/g, '\n\n$1')
      .replace(/\s([A-Z]{2,}\s?:)/g, '\n\n$1')
      .replace(/\s([A-Z][a-z]+\s*:)/g, '\n$1')
      .replace(/\s(\d+\.)\s/g, '\n$1 ')
      .replace(/\.\s([A-Z])/g, '.\n$1')
      .replace(/\s([•-])\s/g, '\n$1 ')
      .trim();
  };

  const toReadableParagraphs = (raw: string): string[] => {
    const text = formatReadableText(raw);
    if (!text) return [];
    return text
      .split(/\n{2,}/)
      .map((part) => part.trim())
      .filter(Boolean);
  };

  const renderReadableTextBlock = (raw: string, maxHeightClass = 'max-h-56') => {
    const paragraphs = toReadableParagraphs(raw);
    if (paragraphs.length === 0) {
      return <p className="text-emerald-700">—</p>;
    }

    return (
      <div className={`mt-1 ${maxHeightClass} overflow-auto rounded-lg border border-emerald-200 bg-white/60 p-3 space-y-2`}>
        {paragraphs.map((paragraph, index) => {
          const isListLike = /^\d+\.|^[•-]/.test(paragraph);
          return (
            <p
              key={`${index}-${paragraph.slice(0, 16)}`}
              className={`text-emerald-700 whitespace-pre-wrap break-words ${isListLike ? 'pl-1' : ''}`}
            >
              {paragraph}
            </p>
          );
        })}
      </div>
    );
  };

  const renderTicketValue = (value: any) => {
    if (value === null || value === undefined || value === '') {
      return <span className="text-emerald-700">—</span>;
    }

    if (typeof value === 'string') {
      const text = formatReadableText(value);
      const isLong = text.length > 120;
      if (!isLong) {
        return <span className="text-emerald-700">{text}</span>;
      }
      return renderReadableTextBlock(text, 'max-h-52');
    }

    if (typeof value === 'number' || typeof value === 'boolean') {
      return <span className="text-emerald-700">{String(value)}</span>;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-emerald-700">—</span>;
      }
      return (
        <ul className="mt-1 list-disc list-inside space-y-1.5 text-emerald-700">
          {value.map((item, index) => (
            <li key={`${index}-${typeof item}`}>{typeof item === 'object' ? JSON.stringify(item, null, 2) : formatReadableText(String(item))}</li>
          ))}
        </ul>
      );
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value as Record<string, any>);
      if (entries.length === 0) {
        return <span className="text-emerald-700">—</span>;
      }

      return (
        <div className="mt-1 max-h-52 overflow-auto rounded-lg border border-emerald-200 bg-white/60 p-2 space-y-2">
          {entries.map(([nestedKey, nestedValue]) => (
            <div key={nestedKey} className="text-emerald-800">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{nestedKey}</p>
              <div className="mt-0.5">{renderTicketValue(nestedValue)}</div>
            </div>
          ))}
        </div>
      );
    }

    return <span className="text-emerald-700">{String(value)}</span>;
  };

  return (
    <div>
      {/* Header */}
      <div className="section-header">
        <div className="section-icon bg-gradient-to-br from-violet-500 to-purple-600">
          <Upload className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="section-title">Input Sources</h2>
          <p className="section-subtitle">Provide requirements from multiple sources</p>
        </div>
      </div>
      
      {/* Inputs Grid */}
      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* JIRA Input */}
        <div>
          <label className="input-label flex items-center gap-2">
            <Ticket className="w-4 h-4 text-blue-500" />
            JIRA Issue ID
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={jiraId}
                onChange={(e) => { setJiraId(e.target.value.toUpperCase()); setJiraStatus('idle'); }}
                onKeyDown={(e) => e.key === 'Enter' && fetchJiraTicket()}
                placeholder="PROJ-123"
                className={`input-field pl-10 pr-8 ${
                  jiraStatus === 'success' ? 'border-emerald-400 bg-emerald-50' :
                  jiraStatus === 'error'   ? 'border-red-400 bg-red-50' : ''
                }`}
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-mono">#</span>
              {jiraStatus === 'success' && <CheckCircle2 className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500" />}
              {jiraStatus === 'error'   && <AlertCircle  className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500" />}
            </div>
            <button
              type="button"
              onClick={fetchJiraTicket}
              disabled={jiraStatus === 'loading' || !jiraId.trim()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {jiraStatus === 'loading'
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Search className="w-4 h-4" />}
              Fetch
            </button>
            {(jiraId.trim() || jiraStatus === 'success') && (
              <button
                type="button"
                onClick={clearJiraTicket}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
          {jiraTickets.length > 0 && (
            <div className="mt-2 space-y-2">
              {jiraTickets.map((ticket) => {
                const fieldFilter = (jiraDetailFilters[ticket.key] || '').toLowerCase();
                const detailEntries = Object.entries(ticket.additional_details || {}).filter(([fieldKey, fieldData]: [string, any]) => {
                  if (!fieldFilter) return true;
                  const name = String(fieldData?.name || fieldKey).toLowerCase();
                  const value = formatTicketValue(fieldData?.value).toLowerCase();
                  return name.includes(fieldFilter) || value.includes(fieldFilter);
                });

                return (
                  <div key={ticket.key} className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-800 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold">{ticket.key} · {ticket.issue_type} · {ticket.priority}</p>
                        <p className="text-emerald-700 mt-0.5 font-medium">{ticket.summary}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeJiraTicket(ticket.key)}
                        className="w-6 h-6 rounded-md flex items-center justify-center text-emerald-700 hover:text-red-500 hover:bg-red-50 transition-all"
                        title="Remove ticket"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
                      {ticket.status && (
                        <div className="rounded-lg border border-emerald-200 bg-white/50 px-2.5 py-1.5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Status</p>
                          <p className="text-emerald-800">{ticket.status}</p>
                        </div>
                      )}
                      {ticket.assignee && (
                        <div className="rounded-lg border border-emerald-200 bg-white/50 px-2.5 py-1.5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Assignee</p>
                          <p className="text-emerald-800">{ticket.assignee}</p>
                        </div>
                      )}
                      {ticket.reporter && (
                        <div className="rounded-lg border border-emerald-200 bg-white/50 px-2.5 py-1.5">
                          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Reporter</p>
                          <p className="text-emerald-800">{ticket.reporter}</p>
                        </div>
                      )}
                    </div>
                    {ticket.description && (
                      <div>
                        <p className="font-medium text-emerald-800">Description</p>
                        {renderReadableTextBlock(ticket.description, 'max-h-64')}
                      </div>
                    )}
                    {ticket.additional_details && Object.keys(ticket.additional_details).length > 0 && (
                      <details className="mt-1" open>
                        <summary className="cursor-pointer font-medium text-emerald-800">
                          More ticket details ({detailEntries.length}/{Object.keys(ticket.additional_details).length})
                        </summary>
                        <div className="mt-2 space-y-2">
                          <input
                            type="text"
                            value={jiraDetailFilters[ticket.key] || ''}
                            onChange={(e) => setJiraDetailFilters((prev) => ({ ...prev, [ticket.key]: e.target.value }))}
                            placeholder="Filter details..."
                            className="input-field text-sm"
                          />
                          <div className="max-h-72 overflow-auto rounded-lg border border-emerald-200 bg-white/60 p-3 space-y-1.5">
                            {detailEntries.map(([fieldKey, fieldData]: [string, any]) => (
                              <div key={fieldKey} className="text-emerald-800">
                                <p className="font-medium">{fieldData?.name || fieldKey}</p>
                                {renderTicketValue(fieldData?.value)}
                              </div>
                            ))}
                            {detailEntries.length === 0 && (
                              <p className="text-emerald-700">No matching fields.</p>
                            )}
                          </div>
                        </div>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          {jiraStatus === 'idle' && <p className="text-xs text-slate-500 mt-1.5 ml-1">Format: PROJECT-123</p>}
        </div>

        {/* ValueEdge Input */}
        <div>
          <label className="input-label flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-500" />
            ValueEdge Item ID
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={valueEdgeId}
                onChange={(e) => { setValueEdgeId(e.target.value); setVeStatus('idle'); }}
                onKeyDown={(e) => e.key === 'Enter' && fetchVeTicket()}
                placeholder="12345"
                className={`input-field pl-12 pr-8 ${
                  veStatus === 'success' ? 'border-emerald-400 bg-emerald-50' :
                  veStatus === 'error'   ? 'border-red-400 bg-red-50' : ''
                }`}
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs font-mono">ID</span>
              {veStatus === 'success' && <CheckCircle2 className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500" />}
              {veStatus === 'error'   && <AlertCircle  className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500" />}
            </div>
            <button
              type="button"
              onClick={fetchVeTicket}
              disabled={veStatus === 'loading' || !valueEdgeId.trim()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              {veStatus === 'loading'
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Search className="w-4 h-4" />}
              Fetch
            </button>
            {(valueEdgeId.trim() || veStatus === 'success') && (
              <button
                type="button"
                onClick={clearValueEdgeTicket}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
          {veTickets.length > 0 && (
            <div className="mt-2 space-y-2">
              {veTickets.map((ticket) => (
                <div key={String(ticket.id)} className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-800 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold">{ticket.id} · {ticket.type || ticket.item_type}</p>
                      <p className="text-emerald-700 mt-0.5 whitespace-pre-wrap">{ticket.name || ticket.description}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeValueEdgeTicket(String(ticket.id))}
                      className="w-6 h-6 rounded-md flex items-center justify-center text-emerald-700 hover:text-red-500 hover:bg-red-50 transition-all"
                      title="Remove ticket"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {ticket.description && (
                    <div className="max-h-52 overflow-auto rounded-lg border border-emerald-200 bg-white/60 p-2">
                      <p className="text-emerald-700 whitespace-pre-wrap break-words">{formatReadableText(ticket.description)}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {veStatus === 'idle' && <p className="text-xs text-slate-500 mt-1.5 ml-1">Work item ID from ValueEdge</p>}
        </div>
      </div>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200"></div>
        </div>
        <div className="relative flex justify-center">
          <span className="px-4 bg-white text-sm text-slate-400">or upload files</span>
        </div>
      </div>

      {/* File Upload */}
      <div>
        <label className="input-label flex items-center gap-2">
          <FileText className="w-4 h-4 text-orange-500" />
          Attach Requirement Details
        </label>
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300 ${
              isDragActive ? 'bg-blue-100 scale-110' : 'bg-slate-100'
            }`}>
              <Upload className={`w-8 h-8 transition-colors ${isDragActive ? 'text-blue-600' : 'text-slate-400'}`} />
            </div>
            <div className="text-center">
              <p className="text-slate-700 font-medium text-lg">
                {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
              </p>
              <p className="text-sm text-slate-500 mt-1">
                or <span className="text-blue-600 font-medium">click to browse</span>
              </p>
            </div>
            <p className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
              PDF, DOCX, XLSX, TXT, FEATURE, PNG, JPG (max 20MB)
            </p>
          </div>
        </div>

        {/* File Errors */}
        {fileRejections.length > 0 && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Some files were rejected. Check file size (max 20MB) and format.</span>
          </div>
        )}

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            {uploadedFiles.map((file) => (
              <div key={file.file_id} className="file-item">
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
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
