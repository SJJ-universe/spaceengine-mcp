/**
 * Vitest 글로벌 셋업 — window.api Mock (Electron IPC 브릿지)
 */
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// crypto.randomUUID polyfill (jsdom에서 누락될 수 있음)
if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, 'crypto', {
    value: {
      randomUUID: () =>
        'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
          const r = (Math.random() * 16) | 0
          return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
        }),
    },
  })
}

// window.api Mock — Electron preload bridge
const mockApi = {
  mcpHealth: vi.fn().mockResolvedValue({
    status: 'ok',
    server: 'spaceengine-mcp',
    version: '0.10.0',
    transport: 'sse',
    tools_count: 59,
  }),
  mcpTools: vi.fn().mockResolvedValue([
    { name: 'navigate_to', description: 'Navigate to celestial object' },
    { name: 'take_screenshot', description: 'Take screenshot' },
  ]),
  mcpExecute: vi.fn().mockResolvedValue({ status: 'ok', tool: 'test', result: {} }),
  chatSend: vi.fn().mockResolvedValue({ response: 'Test response', toolCalls: [] }),
  chatClear: vi.fn().mockResolvedValue({ status: 'ok' }),
  ollamaStatus: vi.fn().mockResolvedValue({ connected: true, models: ['llama3:8b'] }),
  ollamaSetModel: vi.fn().mockResolvedValue({ status: 'ok', model: 'llama3:8b' }),
  ollamaGetModel: vi.fn().mockResolvedValue('llama3:8b'),
}

Object.defineProperty(window, 'api', { value: mockApi, writable: true })
