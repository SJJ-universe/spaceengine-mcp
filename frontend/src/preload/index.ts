import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // MCP
  mcpHealth: () => ipcRenderer.invoke('mcp:health'),
  mcpTools: () => ipcRenderer.invoke('mcp:tools'),
  mcpExecute: (name: string, args: Record<string, unknown>) => ipcRenderer.invoke('mcp:execute', name, args),

  // Chat
  chatSend: (msg: string) => ipcRenderer.invoke('chat:send', msg),
  chatSendStream: (msg: string) => ipcRenderer.invoke('chat:sendStream', msg),
  chatClear: () => ipcRenderer.invoke('chat:clear'),
  onChatToken: (cb: (token: string) => void) => {
    const handler = (_e: unknown, token: string) => cb(token)
    ipcRenderer.on('chat:token', handler)
    return () => ipcRenderer.removeListener('chat:token', handler)
  },

  // LLM Provider
  llmStatus: () => ipcRenderer.invoke('llm:status'),
  llmGetProvider: () => ipcRenderer.invoke('llm:getProvider'),
  llmSetProvider: (type: string, config: { apiKey?: string; model?: string }) =>
    ipcRenderer.invoke('llm:setProvider', type, config),
  llmGetSettings: () => ipcRenderer.invoke('llm:getSettings'),
  llmListModels: (type: string) => ipcRenderer.invoke('llm:listModels', type),
  llmTestConnection: (type: string, config: { apiKey?: string; model?: string }) =>
    ipcRenderer.invoke('llm:testConnection', type, config),

  // Scenario Builder
  scenarioAdd: (step: Record<string, unknown>) => ipcRenderer.invoke('scenario:add', step),
  scenarioList: () => ipcRenderer.invoke('scenario:list'),
  scenarioClear: () => ipcRenderer.invoke('scenario:clear'),
  scenarioExecute: () => ipcRenderer.invoke('scenario:execute'),
  scenarioRunTemplate: (template: string, params: Record<string, unknown>) =>
    ipcRenderer.invoke('scenario:runTemplate', template, params),
  scenarioTemplates: () => ipcRenderer.invoke('scenario:templates'),

  // Sessions (persist)
  sessionsList: () => ipcRenderer.invoke('sessions:list'),
  sessionsSave: (session: { id: string; title: string; messages: unknown[] }) =>
    ipcRenderer.invoke('sessions:save', session),
  sessionsDelete: (id: string) => ipcRenderer.invoke('sessions:delete', id),
  sessionsDeleteAll: () => ipcRenderer.invoke('sessions:deleteAll'),
  sessionsGetCurrent: () => ipcRenderer.invoke('sessions:getCurrent'),
  sessionsSetCurrent: (id: string) => ipcRenderer.invoke('sessions:setCurrent', id),

  // Favorites (persist)
  favoritesGet: () => ipcRenderer.invoke('favorites:get'),
  favoritesSet: (favs: string[]) => ipcRenderer.invoke('favorites:set', favs),
})
