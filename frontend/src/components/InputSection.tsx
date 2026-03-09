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
  valueEdgeId: string;
  setValueEdgeId: (value: string) => void;
  uploadedFiles: FileInput[];
  onFileUpload: (file: FileInput) => void;
  onRemoveFile: (fileId: string) => void;
}

type FetchStatus = 'idle' | 'loading' | 'success' | 'error';

export const InputSection: React.FC<Props> = ({
  jiraId,
  setJiraId,
  valueEdgeId,
  setValueEdgeId,
  uploadedFiles,
  onFileUpload,
  onRemoveFile,
}) => {
  const [jiraStatus, setJiraStatus] = useState<FetchStatus>('idle');
  const [jiraTicket, setJiraTicket] = useState<any>(null);
  const [veStatus, setVeStatus] = useState<FetchStatus>('idle');
  const [veTicket, setVeTicket] = useState<any>(null);

  const clearJiraTicket = () => {
    setJiraId('');
    setJiraStatus('idle');
    setJiraTicket(null);
  };

  const clearValueEdgeTicket = () => {
    setValueEdgeId('');
    setVeStatus('idle');
    setVeTicket(null);
  };

  const fetchJiraTicket = async () => {
    if (!jiraId.trim()) { toast.error('Enter a JIRA Issue ID first'); return; }
    setJiraStatus('loading');
    setJiraTicket(null);
    try {
      const res = await api.getJiraIssue(jiraId.trim());
      setJiraTicket(res.data);
      setJiraStatus('success');
      toast.success(`Fetched: ${res.data.key} — ${res.data.summary}`);
    } catch (err: any) {
      setJiraStatus('error');
      toast.error(err.response?.data?.detail || 'JIRA ticket not found');
    }
  };

  const fetchVeTicket = async () => {
    if (!valueEdgeId.trim()) { toast.error('Enter a ValueEdge Item ID first'); return; }
    setVeStatus('loading');
    setVeTicket(null);
    try {
      const res = await api.getValueEdgeItem(valueEdgeId.trim());
      setVeTicket(res.data);
      setVeStatus('success');
      toast.success(`Fetched: ${res.data.name || res.data.id}`);
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
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
    maxSize: 20 * 1024 * 1024,
  });

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.pdf')) return <FileType2 className="w-5 h-5 text-red-500" />;
    if (filename.match(/\.(jpg|jpeg|png)$/)) return <FileImage className="w-5 h-5 text-green-500" />;
    return <FileText className="w-5 h-5 text-blue-500" />;
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
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
                onChange={(e) => { setJiraId(e.target.value.toUpperCase()); setJiraStatus('idle'); setJiraTicket(null); }}
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
                Remove
              </button>
            )}
          </div>
          {jiraStatus === 'success' && jiraTicket && (
            <div className="mt-2 p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800">
              <p className="font-semibold">{jiraTicket.key} · {jiraTicket.issue_type} · {jiraTicket.priority}</p>
              <p className="text-emerald-700 mt-0.5 line-clamp-2">{jiraTicket.summary}</p>
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
                onChange={(e) => { setValueEdgeId(e.target.value); setVeStatus('idle'); setVeTicket(null); }}
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
                Remove
              </button>
            )}
          </div>
          {veStatus === 'success' && veTicket && (
            <div className="mt-2 p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800">
              <p className="font-semibold">{veTicket.id} · {veTicket.type || veTicket.item_type}</p>
              <p className="text-emerald-700 mt-0.5 line-clamp-2">{veTicket.name || veTicket.description}</p>
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
          Attach Documents
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
              PDF, DOCX, PNG, JPG (max 20MB)
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
