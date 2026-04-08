interface ToolExecution {
  name: string
  arguments: Record<string, unknown>
  result: unknown
  status: 'ok' | 'error'
}

interface ChatResult {
  response: string
  toolCalls?: ToolExecution[]
  error?: string
}

interface McpHealth {
  status: string
  server: string
  version: string
  transport: string
  tools_count: number
}

interface McpTool {
  name: string
  description: string
  parameters?: Record<string, unknown>
}

interface McpToolResult {
  status: string
  tool: string
  result?: unknown
  message?: string
  error_type?: string
}

interface LLMStatus {
  connected: boolean
  model: string
  provider: string
  supportsToolCalling: boolean
}

interface LLMProviderInfo {
  type: string
  name: string
  model: string
  supportsToolCalling: boolean
}

interface LLMSetResult {
  status: string
  provider?: string
  model?: string
  supportsToolCalling?: boolean
  message?: string
}

interface ChatSession {
  id: string
  title: string
  messages: unknown[]
  updatedAt: number
}

interface ElectronAPI {
  mcpHealth: () => Promise<McpHealth | null>
  mcpTools: () => Promise<McpTool[]>
  mcpExecute: (name: string, args: Record<string, unknown>) => Promise<McpToolResult>

  chatSend: (message: string) => Promise<ChatResult>
  chatSendStream: (message: string) => Promise<ChatResult>
  chatClear: () => Promise<{ status: string }>
  onChatToken: (callback: (token: string) => void) => () => void

  llmStatus: () => Promise<LLMStatus>
  llmGetProvider: () => Promise<LLMProviderInfo>
  llmSetProvider: (type: string, config: { apiKey?: string; model?: string }) => Promise<LLMSetResult>
  llmGetSettings: () => Promise<Record<string, unknown>>
  llmListModels: (type: string) => Promise<{ status: string; models: string[] }>
  llmTestConnection: (type: string, config: { apiKey?: string; model?: string }) => Promise<{ status: string; model?: string; message?: string }>

  // Scenario Builder
  scenarioAdd: (step: Record<string, unknown>) => Promise<{ status: string; count: number; summary: string }>
  scenarioList: () => Promise<{ status: string; steps: unknown[]; count: number; summary: string }>
  scenarioClear: () => Promise<{ status: string }>
  scenarioExecute: () => Promise<McpToolResult>
  scenarioRunTemplate: (template: string, params: Record<string, unknown>) => Promise<McpToolResult>
  scenarioTemplates: () => Promise<Array<{ id: string; name: string; description: string }>>

  // Sessions
  sessionsList: () => Promise<ChatSession[]>
  sessionsSave: (session: { id: string; title: string; messages: unknown[] }) => Promise<{ status: string }>
  sessionsDelete: (id: string) => Promise<{ status: string }>
  sessionsDeleteAll: () => Promise<{ status: string }>
  sessionsGetCurrent: () => Promise<string>
  sessionsSetCurrent: (id: string) => Promise<{ status: string }>

  // Favorites
  favoritesGet: () => Promise<string[]>
  favoritesSet: (favs: string[]) => Promise<{ status: string }>
}

declare global {
  interface Window {
    api: ElectronAPI
  }
}

export {}
