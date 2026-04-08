import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatMessage } from '../ChatMessage'

const baseMsg = { id: '1', timestamp: Date.now(), role: 'user' as const, content: '' }

describe('ChatMessage', () => {
  it('renders user message content', () => {
    render(<ChatMessage message={{ ...baseMsg, content: 'Hello Mars' }} />)
    expect(screen.getByText('Hello Mars')).toBeInTheDocument()
  })

  it('renders assistant message', () => {
    render(<ChatMessage message={{ ...baseMsg, role: 'assistant', content: 'Navigating...' }} />)
    expect(screen.getByText('Navigating...')).toBeInTheDocument()
  })

  it('renders error message', () => {
    render(<ChatMessage message={{ ...baseMsg, role: 'assistant', content: '', error: 'Connection lost' }} />)
    expect(screen.getByText('Connection lost')).toBeInTheDocument()
  })

  it('shows timestamp', () => {
    const { container } = render(<ChatMessage message={{ ...baseMsg, content: 'test' }} />)
    // 타임스탬프가 어딘가에 렌더링됨
    expect(container.textContent).toContain(':')
  })
})
