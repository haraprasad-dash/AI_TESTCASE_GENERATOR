import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Settings } from '../types';

interface SettingsStore extends Settings {
  setAll: (settings: Settings) => void;
  updateJira: (settings: Partial<Settings['jira']>) => void;
  updateValueEdge: (settings: Partial<Settings['valueedge']>) => void;
  updateLLM: (settings: Partial<Settings['llm']>) => void;
  reset: () => void;
}

const defaultSettings: Settings = {
  jira: {
    enabled: true,
    baseUrl: '',
    username: '',
    apiToken: '',
  },
  valueedge: {
    enabled: false,
    baseUrl: '',
    clientId: '',
    clientSecret: '',
  },
  llm: {
    defaultProvider: 'groq',
    groq: {
      apiKey: '',
      defaultModel: 'llama-3.3-70b-versatile',
      defaultTemperature: 0.2,
    },
    ollama: {
      baseUrl: 'http://localhost:11434',
      defaultModel: '',
    },
  },
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      ...defaultSettings,
      setAll: (settings) => set(() => ({ ...settings })),
      updateJira: (settings) =>
        set((state) => ({ jira: { ...state.jira, ...settings } })),
      updateValueEdge: (settings) =>
        set((state) => ({ valueedge: { ...state.valueedge, ...settings } })),
      updateLLM: (settings) =>
        set((state) => ({ llm: { ...state.llm, ...settings } })),
      reset: () => set(defaultSettings),
    }),
    {
      name: 'testgen-settings',
    }
  )
);
