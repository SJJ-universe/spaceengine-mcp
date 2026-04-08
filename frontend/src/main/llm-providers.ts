/**
 * LLM Provider Abstraction — Ollama / Groq / Gemini 통합
 *
 * 공통 인터페이스로 여러 LLM 제공자를 지원합니다.
 * Tool calling(function calling) 지원 여부에 따라 Agent 동작이 달라집니다.
 */

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: LLMToolCall[]
  tool_call_id?: string
}

export interface LLMToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string | Record<string, unknown>
  }
}

export interface LLMToolDef {
  type: 'function'
  function: {
    name: string
    description: string
    parameters: Record<string, unknown>
  }
}

export interface LLMChatResponse {
  message: LLMMessage
  done: boolean
}

export type StreamCallback = (token: string) => void

export interface LLMProvider {
  name: string
  supportsToolCalling: boolean
  status(): Promise<{ connected: boolean; model: string }>
  chat(messages: LLMMessage[], tools?: LLMToolDef[]): Promise<LLMChatResponse>
  chatStream(messages: LLMMessage[], onToken: StreamCallback, tools?: LLMToolDef[]): Promise<LLMChatResponse>
  getModel(): string
  setModel(model: string): void
}

// ── Ollama Provider ────────────────────────────────────────────────────────

export class OllamaProvider implements LLMProvider {
  name = 'Ollama (Local)'
  supportsToolCalling = false  // 유저의 모델들이 미지원
  private baseUrl: string
  private model: string

  constructor(baseUrl = 'http://127.0.0.1:11434', model = 'exaone3.5:7.8b') {
    this.baseUrl = baseUrl
    this.model = model
  }

  async status() {
    try {
      const res = await fetch(`${this.baseUrl}/api/tags`)
      const data = await res.json()
      return { connected: true, model: this.model }
    } catch {
      return { connected: false, model: this.model }
    }
  }

  async chat(messages: LLMMessage[], tools?: LLMToolDef[]): Promise<LLMChatResponse> {
    const body: Record<string, unknown> = { model: this.model, messages, stream: false }
    // Ollama에 도구 전송하지 않음 (미지원 모델)
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!data.message) {
      data.message = { role: 'assistant', content: data.response || data.error || '' }
    }
    return data
  }

  async chatStream(messages: LLMMessage[], onToken: StreamCallback): Promise<LLMChatResponse> {
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: this.model, messages, stream: true }),
    })
    return this._parseStream(res, onToken)
  }

  private async _parseStream(res: Response, onToken: StreamCallback): Promise<LLMChatResponse> {
    if (!res.body) throw new Error('No stream body')
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let content = ''
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const chunk = JSON.parse(line)
          if (chunk.message?.content) {
            content += chunk.message.content
            onToken(chunk.message.content)
          }
        } catch { /* skip */ }
      }
    }
    return { message: { role: 'assistant', content }, done: true }
  }

  getModel() { return this.model }
  setModel(model: string) { this.model = model }
}

// ── Groq Provider (무료, tool calling 지원!) ─────────────────────────────────

export class GroqProvider implements LLMProvider {
  name = 'Groq (Free Cloud)'
  supportsToolCalling = true
  private apiKey: string
  private model: string
  private baseUrl = 'https://api.groq.com/openai/v1'

  constructor(apiKey: string, model = 'llama-3.3-70b-versatile') {
    this.apiKey = apiKey
    this.model = model
  }

  async status() {
    try {
      const res = await fetch(`${this.baseUrl}/models`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      })
      return { connected: res.ok, model: this.model }
    } catch {
      return { connected: false, model: this.model }
    }
  }

  async chat(messages: LLMMessage[], tools?: LLMToolDef[]): Promise<LLMChatResponse> {
    const body: Record<string, unknown> = {
      model: this.model,
      messages: messages.map(m => ({
        role: m.role, content: m.content,
        ...(m.tool_calls ? { tool_calls: m.tool_calls } : {}),
        ...(m.tool_call_id ? { tool_call_id: m.tool_call_id } : {}),
      })),
    }
    if (tools && tools.length > 0) body.tools = tools

    console.log(`[Groq] chat request: model=${this.model}, messages=${messages.length}, tools=${tools?.length || 0}`)
    const res = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const errText = await res.text()
      console.error(`[Groq] HTTP ${res.status}: ${errText}`)
      return { message: { role: 'assistant', content: `Groq API error (${res.status}): ${errText}` }, done: true }
    }
    const data = await res.json()
    const choice = data.choices?.[0]
    if (!choice) {
      console.error(`[Groq] No choices in response:`, JSON.stringify(data).slice(0, 500))
      return { message: { role: 'assistant', content: data.error?.message || 'No response from Groq' }, done: true }
    }
    const msg: LLMMessage = {
      role: 'assistant',
      content: choice.message.content || '',
      tool_calls: choice.message.tool_calls?.map((tc: any) => ({
        id: tc.id,
        type: 'function',
        function: { name: tc.function.name, arguments: tc.function.arguments },
      })),
    }
    return { message: msg, done: true }
  }

  async chatStream(messages: LLMMessage[], onToken: StreamCallback, tools?: LLMToolDef[]): Promise<LLMChatResponse> {
    const body: Record<string, unknown> = {
      model: this.model,
      messages: messages.map(m => ({
        role: m.role, content: m.content,
        ...(m.tool_calls ? { tool_calls: m.tool_calls } : {}),
        ...(m.tool_call_id ? { tool_call_id: m.tool_call_id } : {}),
      })),
      stream: true,
    }
    if (tools && tools.length > 0) body.tools = tools

    console.log(`[Groq] chatStream request: model=${this.model}, messages=${messages.length}`)
    const res = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const errText = await res.text()
      console.error(`[Groq] Stream HTTP ${res.status}: ${errText}`)
      const errMsg = `Groq API error (${res.status}): ${errText}`
      onToken(errMsg)
      return { message: { role: 'assistant', content: errMsg }, done: true }
    }

    if (!res.body) throw new Error('No stream')
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let content = ''
    let toolCalls: LLMToolCall[] = []
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ') || line === 'data: [DONE]') continue
        try {
          const chunk = JSON.parse(line.slice(6))
          const delta = chunk.choices?.[0]?.delta
          if (delta?.content) {
            content += delta.content
            onToken(delta.content)
          }
          if (delta?.tool_calls) {
            for (const tc of delta.tool_calls) {
              if (tc.index !== undefined) {
                if (!toolCalls[tc.index]) {
                  toolCalls[tc.index] = { id: tc.id || '', type: 'function', function: { name: '', arguments: '' } }
                }
                if (tc.function?.name) toolCalls[tc.index].function.name += tc.function.name
                if (tc.function?.arguments) toolCalls[tc.index].function.arguments += tc.function.arguments
              }
            }
          }
        } catch { /* skip */ }
      }
    }

    const msg: LLMMessage = { role: 'assistant', content }
    if (toolCalls.length > 0) msg.tool_calls = toolCalls.filter(Boolean)
    return { message: msg, done: true }
  }

  getModel() { return this.model }
  setModel(model: string) { this.model = model }
}

// ── Gemini Provider (무료 250 RPD) ───────────────────────────────────────────

export class GeminiProvider implements LLMProvider {
  name = 'Gemini (Free Cloud)'
  supportsToolCalling = true
  private apiKey: string
  private model: string

  constructor(apiKey: string, model = 'gemini-2.0-flash') {
    this.apiKey = apiKey
    this.model = model
  }

  async status() {
    try {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models?key=${this.apiKey}`,
      )
      return { connected: res.ok, model: this.model }
    } catch {
      return { connected: false, model: this.model }
    }
  }

  async chat(messages: LLMMessage[], tools?: LLMToolDef[]): Promise<LLMChatResponse> {
    // Gemini API 형식으로 변환
    const geminiMessages = messages
      .filter(m => m.role !== 'system')
      .map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
      }))

    const systemInstruction = messages.find(m => m.role === 'system')

    const body: Record<string, unknown> = { contents: geminiMessages }
    if (systemInstruction) {
      body.systemInstruction = { parts: [{ text: systemInstruction.content }] }
    }
    if (tools && tools.length > 0) {
      body.tools = [{
        functionDeclarations: tools.map(t => ({
          name: t.function.name,
          description: t.function.description,
          parameters: t.function.parameters,
        })),
      }]
    }

    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${this.apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      },
    )
    const data = await res.json()
    const candidate = data.candidates?.[0]
    if (!candidate) {
      return { message: { role: 'assistant', content: data.error?.message || 'No response' }, done: true }
    }

    let content = ''
    const toolCalls: LLMToolCall[] = []
    for (const part of candidate.content?.parts || []) {
      if (part.text) content += part.text
      if (part.functionCall) {
        toolCalls.push({
          id: `call_${Date.now()}_${toolCalls.length}`,
          type: 'function',
          function: {
            name: part.functionCall.name,
            arguments: JSON.stringify(part.functionCall.args || {}),
          },
        })
      }
    }

    const msg: LLMMessage = { role: 'assistant', content }
    if (toolCalls.length > 0) msg.tool_calls = toolCalls
    return { message: msg, done: true }
  }

  async chatStream(messages: LLMMessage[], onToken: StreamCallback, tools?: LLMToolDef[]): Promise<LLMChatResponse> {
    // Gemini 스트리밍은 복잡하므로 논스트리밍 사용 후 한 번에 전달
    const result = await this.chat(messages, tools)
    if (result.message.content) onToken(result.message.content)
    return result
  }

  getModel() { return this.model }
  setModel(model: string) { this.model = model }
}

// ── Provider Factory ─────────────────────────────────────────────────────────

export type ProviderType = 'ollama' | 'groq' | 'gemini'

export function createProvider(type: ProviderType, config: { apiKey?: string; model?: string; baseUrl?: string }): LLMProvider {
  switch (type) {
    case 'ollama':
      return new OllamaProvider(config.baseUrl, config.model)
    case 'groq':
      if (!config.apiKey) throw new Error('Groq API key required')
      return new GroqProvider(config.apiKey, config.model || 'llama-3.3-70b-versatile')
    case 'gemini':
      if (!config.apiKey) throw new Error('Gemini API key required')
      return new GeminiProvider(config.apiKey, config.model || 'gemini-2.0-flash')
    default:
      throw new Error(`Unknown provider: ${type}`)
  }
}
