import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SEStatusBar } from '../SEStatusBar'
import { useSEStore } from '../../stores/se-store'

describe('SEStatusBar', () => {
  it('shows SpaceEngine MCP title', () => {
    render(<SEStatusBar />)
    expect(screen.getByText('SpaceEngine MCP')).toBeInTheDocument()
  })

  it('shows MCP disconnected by default', () => {
    useSEStore.getState().setMcpStatus(false)
    render(<SEStatusBar />)
    expect(screen.getByText(/MCP.*꺼짐/)).toBeInTheDocument()
  })

  it('shows MCP connected with tool count', () => {
    useSEStore.getState().setMcpStatus(true, '0.10.0', 59)
    render(<SEStatusBar />)
    expect(screen.getByText(/MCP.*59/)).toBeInTheDocument()
  })

  it('calls onToggleRight when 패널 button clicked', () => {
    const handler = vi.fn()
    render(<SEStatusBar onToggleRight={handler} />)
    fireEvent.click(screen.getByText('패널'))
    expect(handler).toHaveBeenCalledOnce()
  })
})
