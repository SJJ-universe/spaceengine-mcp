/**
 * MCP HTTP Client — MCP 서버 REST API와 통신
 *
 * 기능: timeout (AbortController), retry (네트워크 오류만)
 */

const DEFAULT_TIMEOUT = 30_000  // 30초
const MAX_RETRIES = 2
const RETRY_DELAY = 1_000  // 1초

export interface McpTool {
  name: string
  description: string
  parameters?: Record<string, unknown>
}

export interface McpHealthResponse {
  status: string
  server: string
  version: string
  transport: string
  tools_count: number
}

export interface McpToolResult {
  status: string
  tool: string
  result?: unknown
  message?: string
  error_type?: string
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT,
): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT,
  maxRetries: number = MAX_RETRIES,
): Promise<Response> {
  let lastError: unknown
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fetchWithTimeout(url, options, timeout)
    } catch (err) {
      lastError = err
      // AbortError(timeout)는 재시도하지 않음
      if (err instanceof DOMException && err.name === 'AbortError') throw err
      // 마지막 시도가 아니면 대기 후 재시도
      if (attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY * (attempt + 1)))
      }
    }
  }
  throw lastError
}

export class McpClient {
  private baseUrl: string

  constructor(baseUrl: string = 'http://127.0.0.1:8765') {
    this.baseUrl = baseUrl
  }

  async health(): Promise<McpHealthResponse | null> {
    try {
      const res = await fetchWithTimeout(`${this.baseUrl}/health`, {}, 5000)
      return await res.json()
    } catch {
      return null
    }
  }

  async listTools(): Promise<McpTool[]> {
    try {
      const res = await fetchWithRetry(`${this.baseUrl}/api/tools`, {}, 10_000)
      const data = await res.json()
      return data.tools || []
    } catch {
      return []
    }
  }

  async executeTool(
    name: string,
    args: Record<string, unknown>,
    timeout: number = DEFAULT_TIMEOUT,
  ): Promise<McpToolResult> {
    try {
      const res = await fetchWithRetry(
        `${this.baseUrl}/api/tools/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, arguments: args, timeout: timeout / 1000 }),
        },
        timeout,
        1, // tool 실행은 1회만 재시도
      )
      return await res.json()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return { status: 'error', error_type: 'timeout', tool: name, message: `Timed out after ${timeout / 1000}s` }
      }
      return { status: 'error', error_type: 'network', tool: name, message: String(err) }
    }
  }

  async listResources(): Promise<Array<{ uri: string; name: string; description: string }>> {
    try {
      const res = await fetchWithRetry(`${this.baseUrl}/api/resources`, {}, 10_000)
      const data = await res.json()
      return data.resources || []
    } catch {
      return []
    }
  }

  async listPrompts(): Promise<Array<{ name: string; description: string }>> {
    try {
      const res = await fetchWithRetry(`${this.baseUrl}/api/prompts`, {}, 10_000)
      const data = await res.json()
      return data.prompts || []
    } catch {
      return []
    }
  }
}
