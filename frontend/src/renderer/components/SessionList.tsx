import React from 'react'
import { useChatStore, type SessionInfo } from '../stores/chat-store'

export function SessionList() {
  const { sessions, sessionId, newSession, switchSession, deleteSession, deleteAllSessions } = useChatStore()

  const handleDeleteAll = () => {
    if (sessions.length === 0) return
    if (confirm(`${sessions.length}개의 대화를 모두 삭제하시겠습니까?`)) {
      deleteAllSessions()
    }
  }

  return (
    <div className="p-3 space-y-1">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          대화 목록
        </h3>
        <div className="flex gap-1">
          {sessions.length > 1 && (
            <button
              onClick={handleDeleteAll}
              className="text-red-400 hover:text-red-300 text-xs px-1.5 py-0.5 rounded hover:bg-gray-700 transition-colors"
              title="전체 삭제"
            >
              전체 삭제
            </button>
          )}
          <button
            onClick={newSession}
            className="text-blue-400 hover:text-blue-300 text-xs px-1.5 py-0.5 rounded hover:bg-gray-700 transition-colors"
            title="새 대화"
          >
            + 새 대화
          </button>
        </div>
      </div>

      {sessions.length === 0 ? (
        <p className="text-gray-600 text-xs">저장된 대화 없음</p>
      ) : (
        sessions.map((s: SessionInfo) => (
          <div
            key={s.id}
            className={`group flex items-center gap-1 rounded-lg text-sm cursor-pointer transition-colors
              ${s.id === sessionId
                ? 'bg-blue-600/20 text-blue-300'
                : 'text-gray-400 hover:bg-gray-700'
              }`}
          >
            <button
              className="flex-1 text-left px-3 py-1.5 truncate"
              onClick={() => switchSession(s.id)}
              title={s.title}
            >
              {s.title}
            </button>
            <button
              className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 px-2 py-1 transition-opacity"
              onClick={(e) => { e.stopPropagation(); deleteSession(s.id) }}
              title="삭제"
            >
              ×
            </button>
          </div>
        ))
      )}
    </div>
  )
}
