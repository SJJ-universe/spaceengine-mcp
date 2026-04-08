import { create } from 'zustand'

interface SEStore {
  mcpConnected: boolean
  llmConnected: boolean
  llmProvider: string
  toolsCount: number
  serverVersion: string
  setMcpStatus: (connected: boolean, version?: string, toolsCount?: number) => void
  setLlmStatus: (connected: boolean, provider?: string) => void
}

export const useSEStore = create<SEStore>((set) => ({
  mcpConnected: false,
  llmConnected: false,
  llmProvider: '',
  toolsCount: 0,
  serverVersion: '',
  setMcpStatus: (connected, version, toolsCount) =>
    set({ mcpConnected: connected, serverVersion: version || '', toolsCount: toolsCount || 0 }),
  setLlmStatus: (connected, provider) =>
    set({ llmConnected: connected, llmProvider: provider || '' }),
}))
