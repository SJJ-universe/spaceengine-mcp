import { describe, it, expect, vi, beforeEach } from 'vitest'
import { OllamaClient } from '../ollama-client'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

describe('OllamaClient', () => {
  let client: OllamaClient

  beforeEach(() => {
    client = new OllamaClient('http://localhost:11434', 'llama3:8b')
    mockFetch.mockReset()
  })

  it('status returns connected with models', async () => {
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ models: [{ name: 'llama3:8b' }, { name: 'qwen2.5:7b' }] }),
    })
    const status = await client.status()
    expect(status.connected).toBe(true)
    expect(status.models).toEqual(['llama3:8b', 'qwen2.5:7b'])
  })

  it('status returns disconnected on error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('ECONNREFUSED'))
    const status = await client.status()
    expect(status.connected).toBe(false)
    expect(status.models).toEqual([])
  })

  it('chat sends correct payload', async () => {
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ message: { role: 'assistant', content: 'Hello!' }, done: true }),
    })
    const result = await client.chat([{ role: 'user', content: 'Hi' }])
    expect(result.message.content).toBe('Hello!')
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:11434/api/chat',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('setModel and getModel work', () => {
    expect(client.getModel()).toBe('llama3:8b')
    client.setModel('qwen2.5:7b')
    expect(client.getModel()).toBe('qwen2.5:7b')
  })
})
