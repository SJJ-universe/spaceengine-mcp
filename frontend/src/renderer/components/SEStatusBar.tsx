import React from 'react'
import { useSEStore } from '../stores/se-store'

interface Props {
  onToggleRight?: () => void
  onOpenLLMSettings?: () => void
}

export function SEStatusBar({ onToggleRight, onOpenLLMSettings }: Props) {
  const { mcpConnected, llmConnected, llmProvider, serverVersion, toolsCount } = useSEStore()

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700 text-sm select-none">
      <div className="flex items-center gap-3">
        <span className="font-bold text-blue-400">SpaceEngine MCP</span>
        {serverVersion && <span className="text-gray-500 text-xs">v{serverVersion}</span>}
        <kbd className="text-[10px] text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded ml-2">Ctrl+K</kbd>
      </div>

      <div className="flex items-center gap-4">
        {/* MCP */}
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${mcpConnected ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-gray-400">MCP {mcpConnected ? `(${toolsCount})` : '(꺼짐)'}</span>
        </div>

        {/* LLM */}
        <button
          className="flex items-center gap-1.5 hover:bg-gray-700 px-2 py-0.5 rounded transition-colors"
          onClick={onOpenLLMSettings}
          title="LLM 설정"
        >
          <span className={`w-2 h-2 rounded-full ${llmConnected ? 'bg-green-400' : 'bg-yellow-400'}`} />
          <span className="text-gray-400">LLM ({llmProvider || '꺼짐'})</span>
        </button>

        {onToggleRight && (
          <button
            className="text-gray-400 hover:text-white text-xs px-2 py-1 rounded hover:bg-gray-700 transition-colors"
            onClick={onToggleRight}
          >
            패널
          </button>
        )}
      </div>
    </header>
  )
}
