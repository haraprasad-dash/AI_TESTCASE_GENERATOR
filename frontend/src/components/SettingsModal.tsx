import { useState } from 'react';
import { 
  X, Check, AlertCircle, Link2, Server, 
  Cloud, Key, Globe, Lock, Save, Loader2,
  ExternalLink
} from 'lucide-react';
import { useSettingsStore } from '../store/settingsStore';
import { api } from '../services/api';
import toast from 'react-hot-toast';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const settings = useSettingsStore();
  const [activeTab, setActiveTab] = useState<'jira' | 'valueedge' | 'llm'>('jira');
  const [testing, setTesting] = useState<{ jira: boolean; valueedge: boolean }>({
    jira: false,
    valueedge: false,
  });
  const [testStatus, setTestStatus] = useState<{ 
    jira: 'idle' | 'success' | 'error'; 
    valueedge: 'idle' | 'success' | 'error' 
  }>({
    jira: 'idle',
    valueedge: 'idle',
  });

  if (!isOpen) return null;

  const testJiraConnection = async () => {
    setTesting(prev => ({ ...prev, jira: true }));
    setTestStatus(prev => ({ ...prev, jira: 'idle' }));
    try {
      await api.testJiraConnection();
      setTestStatus(prev => ({ ...prev, jira: 'success' }));
      toast.success('JIRA connection successful!');
    } catch (error: any) {
      setTestStatus(prev => ({ ...prev, jira: 'error' }));
      toast.error('JIRA connection failed');
    } finally {
      setTesting(prev => ({ ...prev, jira: false }));
    }
  };

  const testValueEdgeConnection = async () => {
    setTesting(prev => ({ ...prev, valueedge: true }));
    setTestStatus(prev => ({ ...prev, valueedge: 'idle' }));
    try {
      await api.testValueEdgeConnection();
      setTestStatus(prev => ({ ...prev, valueedge: 'success' }));
      toast.success('ValueEdge connection successful!');
    } catch (error: any) {
      setTestStatus(prev => ({ ...prev, valueedge: 'error' }));
      toast.error('ValueEdge connection failed');
    } finally {
      setTesting(prev => ({ ...prev, valueedge: false }));
    }
  };

  const tabs = [
    { key: 'jira', label: 'JIRA', icon: Globe },
    { key: 'valueedge', label: 'ValueEdge', icon: Server },
    { key: 'llm', label: 'LLM Settings', icon: Cloud },
  ] as const;

  return (
    <div 
      className="modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-200 flex justify-between items-center bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center">
              <Server className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Settings</h2>
              <p className="text-sm text-slate-500">Configure your integrations</p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col md:flex-row" style={{ maxHeight: 'calc(90vh - 80px)' }}>
          {/* Sidebar Tabs */}
          <div className="md:w-48 bg-slate-50 border-r border-slate-200 p-4">
            <div className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  type="button"
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
                    activeTab === tab.key
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <tab.icon className={`w-4 h-4 ${
                    activeTab === tab.key ? 'text-blue-500' : 'text-slate-400'
                  }`} />
                  <span className="font-medium text-sm">{tab.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeTab === 'jira' && (
              <div className="space-y-5 animate-fade-in">
                <div className="flex items-center gap-2 mb-4">
                  <Globe className="w-5 h-5 text-blue-500" />
                  <h3 className="font-bold text-slate-900 text-lg">JIRA Configuration</h3>
                </div>
                
                <div>
                  <label className="input-label flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-400" />
                    Base URL
                  </label>
                  <input
                    type="text"
                    value={settings.jira.baseUrl}
                    onChange={(e) => settings.updateJira({ baseUrl: e.target.value })}
                    placeholder="https://your-instance.atlassian.net"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="input-label flex items-center gap-2">
                    <Server className="w-4 h-4 text-slate-400" />
                    Username / Email
                  </label>
                  <input
                    type="text"
                    value={settings.jira.username}
                    onChange={(e) => settings.updateJira({ username: e.target.value })}
                    placeholder="user@example.com"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="input-label flex items-center gap-2">
                    <Lock className="w-4 h-4 text-slate-400" />
                    API Token
                  </label>
                  <input
                    type="password"
                    value={settings.jira.apiToken}
                    onChange={(e) => settings.updateJira({ apiToken: e.target.value })}
                    placeholder="••••••••••••••••••••"
                    className="input-field"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Create at:{' '}
                    <a
                      href="https://id.atlassian.com/manage-profile/security/api-tokens"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline inline-flex items-center gap-1"
                    >
                      Atlassian Account
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </p>
                </div>

                <button
                  onClick={testJiraConnection}
                  disabled={testing.jira}
                  type="button"
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200 ${
                    testStatus.jira === 'success'
                      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                      : testStatus.jira === 'error'
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  {testing.jira ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : testStatus.jira === 'success' ? (
                    <Check className="w-4 h-4" />
                  ) : testStatus.jira === 'error' ? (
                    <AlertCircle className="w-4 h-4" />
                  ) : (
                    <Link2 className="w-4 h-4" />
                  )}
                  {testStatus.jira === 'success' ? 'Connected' : 'Test Connection'}
                </button>
              </div>
            )}

            {activeTab === 'valueedge' && (
              <div className="space-y-5 animate-fade-in">
                <div className="flex items-center gap-2 mb-4">
                  <Server className="w-5 h-5 text-indigo-500" />
                  <h3 className="font-bold text-slate-900 text-lg">ValueEdge Configuration</h3>
                </div>
                
                <div>
                  <label className="input-label flex items-center gap-2">
                    <Globe className="w-4 h-4 text-slate-400" />
                    Base URL
                  </label>
                  <input
                    type="text"
                    value={settings.valueedge.baseUrl}
                    onChange={(e) => settings.updateValueEdge({ baseUrl: e.target.value })}
                    placeholder="https://valueedge.yourcompany.com"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="input-label flex items-center gap-2">
                    <Key className="w-4 h-4 text-slate-400" />
                    Client ID
                  </label>
                  <input
                    type="text"
                    value={settings.valueedge.clientId}
                    onChange={(e) => settings.updateValueEdge({ clientId: e.target.value })}
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="input-label flex items-center gap-2">
                    <Lock className="w-4 h-4 text-slate-400" />
                    Client Secret
                  </label>
                  <input
                    type="password"
                    value={settings.valueedge.clientSecret}
                    onChange={(e) => settings.updateValueEdge({ clientSecret: e.target.value })}
                    className="input-field"
                  />
                </div>

                <button
                  onClick={testValueEdgeConnection}
                  disabled={testing.valueedge}
                  type="button"
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200 ${
                    testStatus.valueedge === 'success'
                      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                      : testStatus.valueedge === 'error'
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                  }`}
                >
                  {testing.valueedge ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : testStatus.valueedge === 'success' ? (
                    <Check className="w-4 h-4" />
                  ) : testStatus.valueedge === 'error' ? (
                    <AlertCircle className="w-4 h-4" />
                  ) : (
                    <Link2 className="w-4 h-4" />
                  )}
                  {testStatus.valueedge === 'success' ? 'Connected' : 'Test Connection'}
                </button>
              </div>
            )}

            {activeTab === 'llm' && (
              <div className="space-y-5 animate-fade-in">
                <div className="flex items-center gap-2 mb-4">
                  <Cloud className="w-5 h-5 text-purple-500" />
                  <h3 className="font-bold text-slate-900 text-lg">LLM Configuration</h3>
                </div>
                
                <div className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
                  <h4 className="font-bold text-blue-900 mb-1 flex items-center gap-2">
                    <Cloud className="w-4 h-4" />
                    Groq Cloud
                  </h4>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 mt-3">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={settings.llm.groq.apiKey}
                    onChange={(e) =>
                      settings.updateLLM({
                        groq: { ...settings.llm.groq, apiKey: e.target.value },
                      })
                    }
                    placeholder="gsk_..."
                    className="input-field"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    Get from:{' '}
                    <a
                      href="https://console.groq.com/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline inline-flex items-center gap-1"
                    >
                      Groq Console
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </p>
                </div>

                <div className="p-5 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100">
                  <h4 className="font-bold text-purple-900 mb-1 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Ollama Local
                  </h4>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 mt-3">
                    Base URL
                  </label>
                  <input
                    type="text"
                    value={settings.llm.ollama.baseUrl}
                    onChange={(e) =>
                      settings.updateLLM({
                        ollama: { ...settings.llm.ollama, baseUrl: e.target.value },
                      })
                    }
                    placeholder="http://localhost:11434"
                    className="input-field"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button 
            onClick={onClose} 
            type="button"
            className="btn-secondary"
          >
            <Save className="w-4 h-4" />
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};
