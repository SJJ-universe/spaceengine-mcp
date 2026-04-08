import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Agent } from '../agent'
import type { McpClient } from '../mcp-client'
import type { LLMProvider } from '../llm-providers'

function createMockProvider(): LLMProvider {
  return {
    name: 'MockProvider',
    supportsToolCalling: true,
    status: vi.fn().mockResolvedValue({ connected: true, model: 'test-model' }),
    chat: vi.fn(),
    chatStream: vi.fn(),
    getModel: vi.fn().mockReturnValue('test-model'),
    setModel: vi.fn(),
  }
}

function createMockMcp(): McpClient {
  return {
    health: vi.fn(),
    listTools: vi.fn().mockResolvedValue([
      { name: 'navigate_to', description: 'Navigate' },
      { name: 'take_screenshot', description: 'Screenshot' },
      { name: 'set_time', description: 'Set time' },
    ]),
    executeTool: vi.fn().mockResolvedValue({ status: 'ok', tool: 'navigate_to', result: { status: 'ok' } }),
    listResources: vi.fn(),
    listPrompts: vi.fn(),
  } as any
}

describe('Agent (Action Plan mode)', () => {
  let agent: Agent
  let mockMcp: ReturnType<typeof createMockMcp>
  let mockLlm: LLMProvider

  beforeEach(() => {
    mockMcp = createMockMcp()
    mockLlm = createMockProvider()
    agent = new Agent(mockMcp, mockLlm)
  })

  it('loads tools on first chat', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: { role: 'assistant', content: 'Hello!' }, done: true,
    })
    await agent.chat('hello')
    expect(mockMcp.listTools).toHaveBeenCalled()
  })

  it('returns pure conversation when no JSON action plan', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: { role: 'assistant', content: 'Mars is the fourth planet from the Sun.' }, done: true,
    })
    const result = await agent.chat('What is Mars?')
    expect(result.response).toBe('Mars is the fourth planet from the Sun.')
    expect(result.toolCalls).toBeUndefined()
  })

  it('parses and executes JSON action plan from fenced block', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '화성으로 이동합니다.\n```json\n{"actions":[{"tool":"navigate_to","args":{"target":"Mars"}}],"reply":"화성으로 이동합니다."}\n```',
      }, done: true,
    })
    const result = await agent.chat('화성으로 이동해줘')
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls![0].name).toBe('navigate_to')
    expect(result.toolCalls![0].status).toBe('ok')
    expect(mockMcp.executeTool).toHaveBeenCalledWith('navigate_to', { target: 'Mars' })
  })

  it('parses raw JSON action plan without fenced block', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '{"actions":[{"tool":"take_screenshot","args":{}}],"reply":"스크린샷 촬영!"}',
      }, done: true,
    })
    const result = await agent.chat('스크린샷 찍어')
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls![0].name).toBe('take_screenshot')
  })

  it('executes multi-step action plan sequentially', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '```json\n{"actions":[{"tool":"navigate_to","args":{"target":"Mars"}},{"tool":"take_screenshot","args":{}}],"reply":"화성 이동 후 스크린샷"}\n```',
      }, done: true,
    })
    const result = await agent.chat('화성 가서 스크린샷')
    expect(result.toolCalls).toHaveLength(2)
    expect(result.toolCalls![0].name).toBe('navigate_to')
    expect(result.toolCalls![1].name).toBe('take_screenshot')
    expect(mockMcp.executeTool).toHaveBeenCalledTimes(2)
  })

  it('handles unknown tool name gracefully', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '```json\n{"actions":[{"tool":"nonexistent_tool","args":{}}],"reply":"test"}\n```',
      }, done: true,
    })
    const result = await agent.chat('test')
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls![0].status).toBe('error')
    expect(result.toolCalls![0].name).toBe('nonexistent_tool')
  })

  it('handles malformed JSON as pure conversation', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '```json\n{broken json}\n```\nSome text here.',
      }, done: true,
    })
    const result = await agent.chat('test')
    expect(result.toolCalls).toBeUndefined()
    expect(result.response).toContain('Some text here')
  })

  it('handles LLM error gracefully', async () => {
    vi.mocked(mockLlm.chat).mockRejectedValueOnce(new Error('LLM crashed'))
    const result = await agent.chat('test')
    expect(result.error).toContain('LLM crashed')
  })

  it('uses reply field from action plan', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: {
        role: 'assistant',
        content: '```json\n{"actions":[{"tool":"navigate_to","args":{"target":"Earth"}}],"reply":"지구로 이동합니다."}\n```',
      }, done: true,
    })
    const result = await agent.chat('지구로 가줘')
    expect(result.response).toBe('지구로 이동합니다.')
  })

  it('clearHistory resets conversation', () => {
    agent.clearHistory()
    // Should not throw
    expect(agent.getToolCount()).toBe(0)
  })

  it('getToolCount returns loaded count', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: { role: 'assistant', content: 'ok' }, done: true,
    })
    await agent.chat('test')
    expect(agent.getToolCount()).toBe(3)
  })
})

describe('Agent (Intent Parser fast path)', () => {
  let agent: Agent
  let mockMcp: ReturnType<typeof createMockMcp>
  let mockLlm: LLMProvider

  beforeEach(() => {
    mockMcp = createMockMcp()
    mockLlm = createMockProvider()
    agent = new Agent(mockMcp, mockLlm)
  })

  it('navigates directly without LLM call', async () => {
    const result = await agent.chat('Navigate to Mars')
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls![0].name).toBe('navigate_to')
    expect(mockLlm.chat).not.toHaveBeenCalled()
  })

  it('takes screenshot directly without LLM call', async () => {
    const result = await agent.chat('screenshot')
    expect(result.toolCalls).toHaveLength(1)
    expect(result.toolCalls![0].name).toBe('take_screenshot')
    expect(mockLlm.chat).not.toHaveBeenCalled()
  })

  it('falls back to LLM for unmatched intent', async () => {
    vi.mocked(mockLlm.chat).mockResolvedValueOnce({
      message: { role: 'assistant', content: '안녕하세요!' }, done: true,
    })
    const result = await agent.chat('안녕하세요')
    expect(result.toolCalls).toBeUndefined()
    expect(result.response).toBe('안녕하세요!')
    expect(mockLlm.chat).toHaveBeenCalled()
  })
})
