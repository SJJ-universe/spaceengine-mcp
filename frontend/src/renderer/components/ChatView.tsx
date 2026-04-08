import React, { useRef, useEffect, useState, useCallback } from 'react'
import { useChatStore } from '../stores/chat-store'
import { ChatMessage } from './ChatMessage'
import { ToolCallCard } from './ToolCallCard'

export function ChatView() {
  const { messages, isLoading, addMessage, setLoading, clearMessages, updateLastMessage } = useChatStore()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const streamContentRef = useRef('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const autoResize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'  // max ~6줄
  }, [])

  const handleStop = () => {
    // 스트리밍 중지 — 로딩 상태만 해제
    setLoading(false)
    streamContentRef.current = ''
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 스트리밍 토큰 수신
  useEffect(() => {
    const cleanup = window.api.onChatToken((token: string) => {
      streamContentRef.current += token
      updateLastMessage(streamContentRef.current)
    })
    return cleanup
  }, [updateLastMessage])

  // Ctrl+L 클리어 단축키
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'l') {
        e.preventDefault()
        handleClear()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const handleClear = async () => {
    clearMessages()
    await window.api.chatClear()
  }

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isLoading) return

    setInput('')
    addMessage({ role: 'user', content: text })
    setLoading(true)
    streamContentRef.current = ''

    try {
      // 빈 어시스턴트 메시지 추가 (스트리밍으로 채워질 예정)
      addMessage({ role: 'assistant', content: '' })

      const result = await window.api.chatSendStream(text)

      // 스트리밍 완료 후 최종 결과로 교체 (toolCalls 포함)
      if (result.error) {
        updateLastMessage(result.error, result.toolCalls, result.error)
      } else {
        const content = result.response || streamContentRef.current
        if (!content && !result.toolCalls?.length) {
          updateLastMessage('응답을 받지 못했습니다. LLM 연결 상태를 확인하세요.', undefined, 'LLM 응답 없음')
        } else {
          updateLastMessage(content, result.toolCalls)
        }
      }
    } catch (err) {
      updateLastMessage(`연결 오류: ${err}`, undefined, `연결 오류: ${err}`)
    } finally {
      setLoading(false)
      streamContentRef.current = ''
    }
  }, [input, isLoading, addMessage, setLoading, updateLastMessage])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <p className="text-lg mb-2">SpaceEngine MCP 어시스턴트</p>
            <p className="text-sm">자연어로 SpaceEngine을 제어하세요.</p>
            <p className="text-xs mt-1 text-gray-600">예: "화성으로 이동" / "토성 고리 보여줘"</p>
            <p className="text-xs mt-4 text-gray-700">Ctrl+K: 툴 검색 | Ctrl+L: 대화 초기화</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="animate-[fadeSlideIn_0.25s_ease-out]">
            <ChatMessage message={msg} />
            {msg.toolCalls?.map((tc, i) => (
              <ToolCallCard key={`${msg.id}-tc-${i}`} toolCall={tc} index={i} />
            ))}
          </div>
        ))}

        {isLoading && !messages.at(-1)?.content && (
          <div className="flex items-center gap-2 text-gray-400 pl-2">
            <div className="animate-pulse flex gap-1">
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:0.15s]" />
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:0.3s]" />
            </div>
            <span className="text-sm">생각 중...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-700 bg-gray-800 px-4 py-3">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 resize-none outline-none
                       focus:ring-2 focus:ring-blue-500 placeholder-gray-400 text-sm"
            rows={1}
            style={{ maxHeight: '160px' }}
            placeholder="메시지 입력... (Enter: 전송, Ctrl+L: 초기화)"
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium transition-colors"
              onClick={handleStop}
            >
              중지
            </button>
          ) : (
            <button
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600
                         rounded-lg text-sm font-medium transition-colors"
              onClick={handleSend}
              disabled={!input.trim()}
            >
              전송
            </button>
          )}
          {messages.length > 0 && (
            <button
              className="px-3 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-sm transition-colors"
              onClick={handleClear}
              disabled={isLoading}
              title="대화 초기화 (Ctrl+L)"
            >
              초기화
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
