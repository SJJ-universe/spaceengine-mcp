import { describe, it, expect, vi, beforeEach } from 'vitest'
import { McpClient } from '../mcp-client'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

describe('McpClient', () => {
  let client: McpClient

  beforeEach(() => {
    client = new McpClient('http://localhost:8765')
    mockFetch.mockReset()
  })

  it('health returns data on success', async () => {
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ status: 'ok', server: 'spaceengine-mcp', version: '0.10.0', tools_count: 59 }),
    })
    const result = await client.health()
    expect(result?.status).toBe('ok')
    expect(result?.tools_count).toBe(59)
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8765/health', expect.anything())
  })

  it('health returns null on error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Connection refused'))
    const result = await client.health()
    expect(result).toBeNull()
  })

  it('listTools returns array', async () => {
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ tools: [{ name: 'navigate_to', description: 'Nav' }], count: 1 }),
    })
    const tools = await client.listTools()
    expect(tools).toHaveLength(1)
    expect(tools[0].name).toBe('navigate_to')
  })

  it('listTools returns empty on error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('fail'))
    const tools = await client.listTools()
    expect(tools).toEqual([])
  })

  it('executeTool sends POST with correct body', async () => {
    mockFetch.mockResolvedValueOnce({
      json: async () => ({ status: 'ok', tool: 'read_log', result: { entries: [] } }),
    })
    const result = await client.executeTool('read_log', { lines: 5 })
    expect(result.status).toBe('ok')
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8765/api/tools/execute',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('executeTool returns error on failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('timeout'))
    const result = await client.executeTool('test', {})
    expect(result.status).toBe('error')
  })
})
