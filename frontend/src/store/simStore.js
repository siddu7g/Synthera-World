import { create } from "zustand";

const defaultConfig = {
  robot: {
    category: "humanoid",
    asset_name: "Unitree H1",
    asset_path: "/Isaac/Robots/Unitree/H1/h1.usd"
  },
  scene: {
    environment: "empty",
    lighting: "day",
    obstacles: false
  },
  task: {
    description: "stand still for the full duration",
    duration_seconds: 20
  },
  sensors: {
    camera: false,
    imu: false,
    lidar: false
  },
  output: {
    headless: true,
    export_telemetry: false
  }
};

export const useSimStore = create((set) => ({
  backendUrl: "http://localhost:8765",
  config: defaultConfig,
  generatedScript: "",
  generationId: "",
  logs: [],
  isGenerating: false,
  isSimulating: false,
  apiError: "",
  apiNotice: "Ready",
  assets: { humanoid: [], amr: [] },
  history: [],
  chatSessionId: "default",
  chatMessages: [],
  isChatting: false,
  setConfig: (next) => set((state) => ({ config: { ...state.config, ...next } })),
  setNested: (section, values) =>
    set((state) => ({
      config: {
        ...state.config,
        [section]: { ...state.config[section], ...values }
      }
    })),
  setGenerated: (script, generationId) => set({ generatedScript: script, generationId }),
  addLog: (line) => set((state) => ({ logs: [...state.logs, line] })),
  clearLogs: () => set({ logs: [] }),
  setGenerating: (isGenerating) => set({ isGenerating }),
  setSimulating: (isSimulating) => set({ isSimulating }),
  setApiError: (apiError) => set({ apiError }),
  setApiNotice: (apiNotice) => set({ apiNotice }),
  setAssets: (assets) => set({ assets }),
  setHistory: (history) => set({ history }),
  setChatSessionId: (chatSessionId) => set({ chatSessionId }),
  addChatMessage: (message) => set((state) => ({ chatMessages: [...state.chatMessages, message] })),
  clearChatMessages: () => set({ chatMessages: [] }),
  setChatting: (isChatting) => set({ isChatting })
}));
