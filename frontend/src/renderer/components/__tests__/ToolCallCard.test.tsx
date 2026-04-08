import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ToolCallCard } from '../ToolCallCard'

const okCall = {
  name: 'navigate_to',
  arguments: { target: 'Mars' },
  result: { status: 'ok' },
  status: 'ok' as const,
}

describe('ToolCallCard', () => {
  it('shows tool name in collapsed state', () => {
    render(<ToolCallCard toolCall={okCall} />)
    expect(screen.getByText('navigate_to')).toBeInTheDocument()
  })

  it('shows result preview in collapsed state', () => {
    render(<ToolCallCard toolCall={okCall} />)
    expect(screen.getByText(/status: "ok"/)).toBeInTheDocument()
  })

  it('expands to show details on click', () => {
    render(<ToolCallCard toolCall={okCall} />)
    fireEvent.click(screen.getByText('navigate_to'))
    expect(screen.getByText('인수')).toBeInTheDocument()
    expect(screen.getByText('결과')).toBeInTheDocument()
  })

  it('shows index when provided', () => {
    render(<ToolCallCard toolCall={okCall} index={2} />)
    expect(screen.getByText('#3')).toBeInTheDocument()
  })
})
