import React, { useState } from 'react'
import { useToastStore } from './Toast'

interface Props {
  toolCall: {
    name: string
    arguments: Record<string, unknown>
    result: unknown
    status: 'ok' | 'error'
  }
  index?: number
}

export function ToolCallCard({ toolCall, index }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState<'args' | 'result' | null>(null)
  const isError = toolCall.status === 'error'
  const { addToast } = useToastStore()

  const handleCopy = async (e: React.MouseEvent, type: 'args' | 'result') => {
    e.stopPropagation()
    const data = type === 'args' ? toolCall.arguments : toolCall.result
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    setCopied(type)
    addToast('클립보드에 복사됨', 'success')
    setTimeout(() => setCopied(null), 1500)
  }

  // 결과에서 주요 필드를 추출하여 미리보기로 표시
  const getPreview = (): string => {
    if (toolCall.result == null) return ''
    if (typeof toolCall.result === 'string') return toolCall.result.slice(0, 60)
    if (typeof toolCall.result === 'object') {
      const r = toolCall.result as Record<string, unknown>
      // status/message 패턴
      if (r.message) return String(r.message).slice(0, 60)
      // 배열 결과
      if (Array.isArray(toolCall.result)) return `[${toolCall.result.length}개 항목]`
      const keys = Object.keys(r)
      if (keys.length <= 3) return keys.map((k) => `${k}: ${JSON.stringify(r[k])}`).join(', ').slice(0, 80)
      return `{${keys.length}개 필드}`
    }
    return String(toolCall.result).slice(0, 60)
  }

  return (
    <div
      className={`ml-2 mt-1 border rounded-lg text-xs cursor-pointer transition-colors
        ${isError
          ? 'bg-red-900/30 border-red-700 hover:border-red-500'
          : 'bg-gray-800 border-gray-600 hover:border-gray-500'
        }`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-2 px-3 py-2">
        <span className={`w-1.5 h-1.5 rounded-full ${isError ? 'bg-red-400' : 'bg-green-400'}`} />
        {index !== undefined && (
          <span className="text-gray-500">#{index + 1}</span>
        )}
        <span className="text-blue-400 font-mono">{toolCall.name}</span>
        <span className="text-gray-500 truncate max-w-[200px]" title={getPreview()}>
          {getPreview() || `(${Object.keys(toolCall.arguments).length}개 인수)`}
        </span>
        <span className="ml-auto text-gray-500">{expanded ? '▾' : '▸'}</span>
      </div>

      {expanded && (
        <div className="border-t border-gray-700 px-3 py-2 space-y-2">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-[11px] uppercase">인수</span>
              <button
                onClick={(e) => handleCopy(e, 'args')}
                className="text-gray-500 hover:text-white text-[10px] px-1"
              >
                {copied === 'args' ? '✓' : '📋'}
              </button>
            </div>
            <pre className="text-green-300 mt-0.5 overflow-x-auto whitespace-pre-wrap max-h-32 overflow-y-auto bg-gray-900/50 rounded p-1.5">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-[11px] uppercase">결과</span>
              <button
                onClick={(e) => handleCopy(e, 'result')}
                className="text-gray-500 hover:text-white text-[10px] px-1"
              >
                {copied === 'result' ? '✓' : '📋'}
              </button>
            </div>
            <pre className={`mt-0.5 overflow-x-auto whitespace-pre-wrap max-h-48 overflow-y-auto bg-gray-900/50 rounded p-1.5
              ${isError ? 'text-red-300' : 'text-yellow-300'}`}>
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
