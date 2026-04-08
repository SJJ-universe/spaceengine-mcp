import { describe, it, expect } from 'vitest'
import { useSEStore } from '../se-store'

describe('SEStore', () => {
  it('starts disconnected', () => {
    const state = useSEStore.getState()
    expect(state.mcpConnected).toBe(false)
    expect(state.llmConnected).toBe(false)
  })

  it('sets MCP connected status', () => {
    useSEStore.getState().setMcpStatus(true, '0.10.0', 59)
    const state = useSEStore.getState()
    expect(state.mcpConnected).toBe(true)
    expect(state.serverVersion).toBe('0.10.0')
    expect(state.toolsCount).toBe(59)
  })

  it('sets MCP disconnected', () => {
    useSEStore.getState().setMcpStatus(true, '1.0', 10)
    useSEStore.getState().setMcpStatus(false)
    expect(useSEStore.getState().mcpConnected).toBe(false)
  })

  it('sets LLM connected with provider name', () => {
    useSEStore.getState().setLlmStatus(true, 'Groq (Free Cloud)')
    const state = useSEStore.getState()
    expect(state.llmConnected).toBe(true)
    expect(state.llmProvider).toBe('Groq (Free Cloud)')
  })

  it('sets LLM disconnected', () => {
    useSEStore.getState().setLlmStatus(true, 'Groq')
    useSEStore.getState().setLlmStatus(false)
    expect(useSEStore.getState().llmConnected).toBe(false)
  })
})
