import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chat-store'

describe('ChatStore', () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages()
  })

  it('starts with empty messages', () => {
    expect(useChatStore.getState().messages).toHaveLength(0)
  })

  it('adds a message with auto id and timestamp', () => {
    useChatStore.getState().addMessage({ role: 'user', content: 'hello' })
    const msgs = useChatStore.getState().messages
    expect(msgs).toHaveLength(1)
    expect(msgs[0].content).toBe('hello')
    expect(msgs[0].role).toBe('user')
    expect(msgs[0].id).toBeTruthy()
    expect(msgs[0].timestamp).toBeGreaterThan(0)
  })

  it('maintains message order', () => {
    const store = useChatStore.getState()
    store.addMessage({ role: 'user', content: 'first' })
    store.addMessage({ role: 'assistant', content: 'second' })
    const msgs = useChatStore.getState().messages
    expect(msgs[0].content).toBe('first')
    expect(msgs[1].content).toBe('second')
  })

  it('sets loading state', () => {
    useChatStore.getState().setLoading(true)
    expect(useChatStore.getState().isLoading).toBe(true)
    useChatStore.getState().setLoading(false)
    expect(useChatStore.getState().isLoading).toBe(false)
  })

  it('clears all messages', () => {
    useChatStore.getState().addMessage({ role: 'user', content: 'msg' })
    useChatStore.getState().addMessage({ role: 'assistant', content: 'reply' })
    expect(useChatStore.getState().messages).toHaveLength(2)
    useChatStore.getState().clearMessages()
    expect(useChatStore.getState().messages).toHaveLength(0)
  })

  it('stores toolCalls in message', () => {
    useChatStore.getState().addMessage({
      role: 'assistant',
      content: 'done',
      toolCalls: [{ name: 'navigate_to', arguments: { target: 'Mars' }, result: {}, status: 'ok' }],
    })
    const msg = useChatStore.getState().messages[0]
    expect(msg.toolCalls).toHaveLength(1)
    expect(msg.toolCalls![0].name).toBe('navigate_to')
  })

  it('stores error in message', () => {
    useChatStore.getState().addMessage({ role: 'assistant', content: '', error: 'Connection failed' })
    expect(useChatStore.getState().messages[0].error).toBe('Connection failed')
  })
})
