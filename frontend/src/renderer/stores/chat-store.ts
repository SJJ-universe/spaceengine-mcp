import { create } from 'zustand'

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: number
  toolCalls?: Array<{
    name: string
    arguments: Record<string, unknown>
    result: unknown
    status: 'ok' | 'error'
  }>
  error?: string
}

export interface SessionInfo {
  id: string
  title: string
  updatedAt: number
}

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  sessionId: string
  sessions: SessionInfo[]
  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateLastMessage: (
    content: string,
    toolCalls?: ChatMessage['toolCalls'],
    error?: string,
  ) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
  // Session management
  loadSessions: () => Promise<void>
  newSession: () => void
  switchSession: (id: string) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  deleteAllSessions: () => Promise<void>
  persistSession: () => void
}

let persistTimer: ReturnType<typeof setTimeout> | null = null

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isLoading: false,
  sessionId: crypto.randomUUID(),
  sessions: [],

  addMessage: (msg) => {
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: crypto.randomUUID(), timestamp: Date.now() },
      ],
    }))
    // 디바운스 persist (500ms)
    if (persistTimer) clearTimeout(persistTimer)
    persistTimer = setTimeout(() => get().persistSession(), 500)
  },

  updateLastMessage: (content, toolCalls, error) => {
    set((state) => {
      if (state.messages.length === 0) return state
      const msgs = [...state.messages]
      const last = { ...msgs[msgs.length - 1] }
      last.content = content
      if (toolCalls !== undefined) last.toolCalls = toolCalls
      if (error !== undefined) last.error = error
      msgs[msgs.length - 1] = last
      return { messages: msgs }
    })
  },

  setLoading: (loading) => {
    set({ isLoading: loading })
    // 로딩 종료 시 persist
    if (!loading) {
      if (persistTimer) clearTimeout(persistTimer)
      persistTimer = setTimeout(() => get().persistSession(), 300)
    }
  },

  clearMessages: () => set({ messages: [], sessionId: crypto.randomUUID() }),

  persistSession: () => {
    const { messages, sessionId } = get()
    if (messages.length === 0) return
    const firstUser = messages.find((m) => m.role === 'user')
    const title = firstUser?.content.slice(0, 40) || '새 대화'
    window.api.sessionsSave({ id: sessionId, title, messages })
    window.api.sessionsSetCurrent(sessionId)
    // sessions 목록 갱신
    get().loadSessions()
  },

  loadSessions: async () => {
    const sessions = await window.api.sessionsList()
    set({ sessions: sessions.map((s: any) => ({ id: s.id, title: s.title, updatedAt: s.updatedAt })) })
  },

  newSession: () => {
    const { messages } = get()
    if (messages.length > 0) get().persistSession()
    set({ messages: [], sessionId: crypto.randomUUID() })
    window.api.chatClear()
  },

  switchSession: async (id: string) => {
    // 현재 세션 저장
    const { messages } = get()
    if (messages.length > 0) get().persistSession()

    const sessions = await window.api.sessionsList()
    const session = sessions.find((s: any) => s.id === id)
    if (session) {
      set({ messages: session.messages as ChatMessage[], sessionId: id })
      window.api.sessionsSetCurrent(id)
      window.api.chatClear() // LLM 히스토리 리셋
    }
  },

  deleteSession: async (id: string) => {
    await window.api.sessionsDelete(id)
    const { sessionId } = get()
    if (sessionId === id) set({ messages: [], sessionId: crypto.randomUUID() })
    await get().loadSessions()
  },

  deleteAllSessions: async () => {
    await window.api.sessionsDeleteAll()
    set({ messages: [], sessions: [], sessionId: crypto.randomUUID() })
    window.api.chatClear()
  },
}))
