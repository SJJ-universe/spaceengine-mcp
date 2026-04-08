/**
 * Ollama Client — 로컬 LLM API와 통신 (OpenAI 호환 API)
 *
 * 스트리밍 + 논스트리밍 모드 지원
 */

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: OllamaToolCall[]
  tool_call_id?: string
}

export interface OllamaToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string | Record<string, unknown>
  }
}

export interface OllamaChatResponse {
  message: OllamaMessage
  done: boolean
}

export type StreamCallback = (token: string) => void

export class OllamaClient {
  private baseUrl: string
  private model: string

  constructor(baseUrl: string = 'http://127.0.0.1:11434', model: string = 'exaone3.5:7.8b') {
    this.baseUrl = baseUrl
    this.model = model
  }

  async status(): Promise<{ connected: boolean; models: string[] }> {
    try {
      const res = await fetch(`${this.baseUrl}/api/tags`)
      const data = await res.json()
      const models = (data.models || []).map((m: { name: string }) => m.name)
      return { connected: true, models }
    } catch {
      return { connected: false, models: [] }
    }
  }

  /** 논스트리밍 chat — tool calling 루프에서 사용 */
  async chat(
    messages: OllamaMessage[],
    tools?: Array<{
      type: 'function'
      function: { name: string; description: string; parameters: Record<string, unknown> }
    }>,
  ): Promise<OllamaChatResponse> {
    const body: Record<string, unknown> = {
      model: this.model,
      messages,
      stream: false,
    }
    if (tools && tools.length > 0) {
      body.tools = tools
    }

    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    // Ollama 응답 안전 처리 — message가 없으면 기본값
    if (!data.message) {
      data.message = {
        role: 'assistant',
        content: data.response || data.error || 'No response',
      }
    }
    return data as OllamaChatResponse
  }

  /**
   * 스트리밍 chat — 토큰 단위로 onToken 콜백 호출.
   * tool_calls 포함 시 마지막에 전체 응답 반환.
   */
  async chatStream(
    messages: OllamaMessage[],
    onToken: StreamCallback,
    tools?: Array<{
      type: 'function'
      function: { name: string; description: string; parameters: Record<string, unknown> }
    }>,
  ): Promise<OllamaChatResponse> {
    const body: Record<string, unknown> = {
      model: this.model,
      messages,
      stream: true,
    }
    if (tools && tools.length > 0) {
      body.tools = tools
    }

    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.body) {
      throw new Error('No response body for streaming')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    let lastMessage: OllamaMessage = { role: 'assistant', content: '' }
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // NDJSON 파싱: 줄 단위로 처리
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''  // 마지막 불완전 줄은 버퍼에 유지

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        try {
          const chunk = JSON.parse(trimmed) as OllamaChatResponse
          if (chunk.message?.content) {
            fullContent += chunk.message.content
            onToken(chunk.message.content)
          }
          if (chunk.done) {
            lastMessage = chunk.message || { role: 'assistant', content: fullContent }
            lastMessage.content = fullContent
          }
          // tool_calls는 마지막 chunk에서 전달됨
          if (chunk.message?.tool_calls) {
            lastMessage.tool_calls = chunk.message.tool_calls
          }
        } catch {
          // 파싱 실패한 줄은 무시
        }
      }
    }

    return { message: lastMessage, done: true }
  }

  setModel(model: string): void {
    this.model = model
  }

  getModel(): string {
    return this.model
  }
}
