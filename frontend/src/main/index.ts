/**
 * Electron Main Process
 *
 * LLM Provider: Ollama(로컬) / Groq(무료) / Gemini(무료) 선택 가능
 */
import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { join } from 'path'
import Store from 'electron-store'
import { McpClient } from './mcp-client'
import { Agent } from './agent'
import {
  createProvider, OllamaProvider, GroqProvider, GeminiProvider,
  type LLMProvider, type ProviderType,
} from './llm-providers'

let mainWindow: BrowserWindow | null = null
let mcpClient: McpClient
let agent: Agent
let currentProvider: LLMProvider

// electron-store 영속 저장
const store = new Store({
  defaults: {
    llmProvider: 'groq',
    groqApiKey: '',
    geminiApiKey: '',
    ollamaModel: 'exaone3.5:7.8b',
    groqModel: 'llama-3.3-70b-versatile',
    geminiModel: 'gemini-2.0-flash',
    chatSessions: [] as Array<{ id: string; title: string; messages: unknown[]; updatedAt: number }>,
    currentSessionId: '',
    favorites: [] as string[],
  },
})

// settings proxy — electron-store 래핑
const settings = {
  get llmProvider() { return store.get('llmProvider') as string },
  set llmProvider(v: string) { store.set('llmProvider', v) },
  get groqApiKey() { return store.get('groqApiKey') as string },
  set groqApiKey(v: string) { store.set('groqApiKey', v) },
  get geminiApiKey() { return store.get('geminiApiKey') as string },
  set geminiApiKey(v: string) { store.set('geminiApiKey', v) },
  get ollamaModel() { return store.get('ollamaModel') as string },
  set ollamaModel(v: string) { store.set('ollamaModel', v) },
  get groqModel() { return store.get('groqModel') as string },
  set groqModel(v: string) { store.set('groqModel', v) },
  get geminiModel() { return store.get('geminiModel') as string },
  set geminiModel(v: string) { store.set('geminiModel', v) },
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280, height: 800, minWidth: 900, minHeight: 600,
    title: 'SpaceEngine MCP',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true, nodeIntegration: false,
    },
  })
  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
  mainWindow.on('closed', () => { mainWindow = null })
  mainWindow.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' } })
}

function setupIPC(): void {
  // MCP
  ipcMain.handle('mcp:health', () => mcpClient.health())
  ipcMain.handle('mcp:tools', () => mcpClient.listTools())
  ipcMain.handle('mcp:execute', (_e, name: string, args: Record<string, unknown>) => mcpClient.executeTool(name, args))

  // Chat
  ipcMain.handle('chat:send', async (_e, msg: string) => {
    try { const r = await agent.chat(msg); agent.trimHistory(); return r }
    catch (err) { return { response: '', error: String(err) } }
  })
  ipcMain.handle('chat:sendStream', async (_e, msg: string) => {
    try {
      const r = await agent.chatStream(msg, (token) => { mainWindow?.webContents.send('chat:token', token) })
      agent.trimHistory(); return r
    } catch (err) { return { response: '', error: String(err) } }
  })
  ipcMain.handle('chat:clear', () => { agent.clearHistory(); return { status: 'ok' } })

  // Scenario Builder
  ipcMain.handle('scenario:add', (_e, step: Record<string, unknown>) => {
    agent.getScenarioBuilder().addStep(step as any)
    return { status: 'ok', count: agent.getScenarioBuilder().getStepCount(), summary: agent.getScenarioBuilder().summarize() }
  })
  ipcMain.handle('scenario:list', () => ({
    status: 'ok',
    steps: agent.getScenarioBuilder().getSteps(),
    count: agent.getScenarioBuilder().getStepCount(),
    summary: agent.getScenarioBuilder().summarize(),
  }))
  ipcMain.handle('scenario:clear', () => { agent.getScenarioBuilder().clear(); return { status: 'ok' } })
  ipcMain.handle('scenario:execute', async () => {
    const builder = agent.getScenarioBuilder()
    if (!builder.isActive()) return { status: 'error', message: '시나리오가 비어있습니다' }
    const args = builder.toCinematicArgs()
    const result = await mcpClient.executeTool('cinematic_sequence', args)
    builder.clear()
    return result
  })
  ipcMain.handle('scenario:runTemplate', async (_e, templateName: string, params: Record<string, unknown>) => {
    const { SCENARIO_TEMPLATES } = await import('./scenario-builder')
    const template = SCENARIO_TEMPLATES[templateName]
    if (!template) return { status: 'error', message: `알 수 없는 템플릿: ${templateName}` }
    const steps = template.generate(params)
    return mcpClient.executeTool('cinematic_sequence', { steps, auto_hide_gui: true })
  })
  ipcMain.handle('scenario:templates', async () => {
    const { SCENARIO_TEMPLATES } = await import('./scenario-builder')
    return Object.entries(SCENARIO_TEMPLATES).map(([id, t]) => ({ id, name: t.name, description: t.description }))
  })

  // LLM Provider
  ipcMain.handle('llm:status', async () => {
    const s = await currentProvider.status()
    return { ...s, provider: currentProvider.name, supportsToolCalling: currentProvider.supportsToolCalling }
  })
  ipcMain.handle('llm:getProvider', () => ({
    type: settings.llmProvider,
    name: currentProvider.name,
    model: currentProvider.getModel(),
    supportsToolCalling: currentProvider.supportsToolCalling,
  }))
  ipcMain.handle('llm:setProvider', async (_e, type: ProviderType, config: { apiKey?: string; model?: string }) => {
    try {
      // Provider별 기본 모델 보장
      const model = config.model
        || (type === 'groq' ? 'llama-3.3-70b-versatile'
          : type === 'gemini' ? 'gemini-2.0-flash'
          : settings.ollamaModel as string)
      const provider = createProvider(type, {
        apiKey: config.apiKey || (type === 'groq' ? settings.groqApiKey as string : settings.geminiApiKey as string),
        model,
        baseUrl: type === 'ollama' ? 'http://127.0.0.1:11434' : undefined,
      })
      const s = await provider.status()
      if (!s.connected) return { status: 'error', message: `Cannot connect to ${type}` }

      currentProvider = provider
      agent.setProvider(provider)
      settings.llmProvider = type
      if (config.apiKey) {
        if (type === 'groq') settings.groqApiKey = config.apiKey
        if (type === 'gemini') settings.geminiApiKey = config.apiKey
      }
      if (config.model) {
        if (type === 'ollama') settings.ollamaModel = config.model
        if (type === 'groq') settings.groqModel = config.model
        if (type === 'gemini') settings.geminiModel = config.model
      }
      return { status: 'ok', provider: provider.name, model: provider.getModel(), supportsToolCalling: provider.supportsToolCalling }
    } catch (err) {
      return { status: 'error', message: String(err) }
    }
  })
  ipcMain.handle('llm:getSettings', () => ({
    provider: settings.llmProvider,
    groqApiKey: settings.groqApiKey ? '***' : '',  // 마스킹
    geminiApiKey: settings.geminiApiKey ? '***' : '',
    ollamaModel: settings.ollamaModel,
    groqModel: settings.groqModel,
    geminiModel: settings.geminiModel,
  }))

  ipcMain.handle('llm:listModels', async (_e, type: string) => {
    try {
      if (type === 'ollama') {
        const res = await fetch('http://127.0.0.1:11434/api/tags')
        const data = await res.json()
        return { status: 'ok', models: (data.models || []).map((m: { name: string }) => m.name) }
      }
      if (type === 'groq') {
        return { status: 'ok', models: [
          'llama-3.3-70b-versatile',
          'openai/gpt-oss-120b',
          'qwen/qwen3-32b',
          'moonshotai/kimi-k2-instruct',
          'meta-llama/llama-4-scout-17b-16e-instruct',
          'llama-3.1-8b-instant',
        ] }
      }
      if (type === 'gemini') {
        return { status: 'ok', models: ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-1.5-pro'] }
      }
      return { status: 'error', models: [] }
    } catch {
      return { status: 'error', models: [] }
    }
  })

  ipcMain.handle('llm:testConnection', async (_e, type: ProviderType, config: { apiKey?: string; model?: string }) => {
    try {
      const provider = createProvider(type, {
        apiKey: config.apiKey || (type === 'groq' ? settings.groqApiKey as string : settings.geminiApiKey as string),
        model: config.model,
        baseUrl: type === 'ollama' ? 'http://127.0.0.1:11434' : undefined,
      })
      const s = await provider.status()
      return { status: s.connected ? 'ok' : 'error', model: provider.getModel(), message: s.connected ? '연결 성공' : '연결 실패' }
    } catch (err) {
      return { status: 'error', message: String(err) }
    }
  })

  // Chat sessions persist
  ipcMain.handle('sessions:list', () => store.get('chatSessions'))
  ipcMain.handle('sessions:save', (_e, session: { id: string; title: string; messages: unknown[] }) => {
    const sessions = store.get('chatSessions') as Array<{ id: string; title: string; messages: unknown[]; updatedAt: number }>
    const idx = sessions.findIndex((s) => s.id === session.id)
    const entry = { ...session, updatedAt: Date.now() }
    if (idx >= 0) sessions[idx] = entry; else sessions.unshift(entry)
    // 최대 50개 세션
    if (sessions.length > 50) sessions.length = 50
    store.set('chatSessions', sessions)
    return { status: 'ok' }
  })
  ipcMain.handle('sessions:delete', (_e, id: string) => {
    const sessions = (store.get('chatSessions') as Array<{ id: string }>).filter((s) => s.id !== id)
    store.set('chatSessions', sessions)
    return { status: 'ok' }
  })
  ipcMain.handle('sessions:deleteAll', () => {
    store.set('chatSessions', [])
    store.set('currentSessionId', '')
    return { status: 'ok' }
  })
  ipcMain.handle('sessions:getCurrent', () => store.get('currentSessionId'))
  ipcMain.handle('sessions:setCurrent', (_e, id: string) => { store.set('currentSessionId', id); return { status: 'ok' } })

  // Favorites persist
  ipcMain.handle('favorites:get', () => store.get('favorites'))
  ipcMain.handle('favorites:set', (_e, favs: string[]) => { store.set('favorites', favs); return { status: 'ok' } })
}

app.whenReady().then(() => {
  mcpClient = new McpClient('http://127.0.0.1:8765')

  // 저장된 Provider 설정으로 초기화 (기본값: Groq)
  const savedType = settings.llmProvider as ProviderType
  console.log(`[LLM BOOT] savedType=${savedType}, groqApiKey=${settings.groqApiKey ? 'SET(' + (settings.groqApiKey as string).length + ' chars)' : 'EMPTY'}, groqModel=${settings.groqModel}`)
  // Groq/Gemini 모델명이 Ollama 모델명으로 오염된 경우 기본값으로 복구
  const GROQ_DEFAULT = 'llama-3.3-70b-versatile'
  const GEMINI_DEFAULT = 'gemini-2.0-flash'
  const groqModel = (settings.groqModel && !settings.groqModel.includes(':')) ? settings.groqModel : GROQ_DEFAULT
  const geminiModel = (settings.geminiModel && settings.geminiModel.startsWith('gemini')) ? settings.geminiModel : GEMINI_DEFAULT
  if (groqModel !== settings.groqModel) settings.groqModel = groqModel
  if (geminiModel !== settings.geminiModel) settings.geminiModel = geminiModel

  try {
    currentProvider = createProvider(savedType, {
      apiKey: savedType === 'groq' ? settings.groqApiKey
            : savedType === 'gemini' ? settings.geminiApiKey
            : undefined,
      model: savedType === 'groq' ? groqModel
           : savedType === 'gemini' ? geminiModel
           : settings.ollamaModel,
      baseUrl: savedType === 'ollama' ? 'http://127.0.0.1:11434' : undefined,
    })
    console.log(`[LLM] Initialized: ${currentProvider.name} (${currentProvider.getModel()})`)
  } catch (err) {
    console.warn(`[LLM] Failed to init ${savedType}: ${err}. Falling back to Ollama.`)
    currentProvider = new OllamaProvider()
  }
  agent = new Agent(mcpClient, currentProvider)

  setupIPC()
  createWindow()
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })
})

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
