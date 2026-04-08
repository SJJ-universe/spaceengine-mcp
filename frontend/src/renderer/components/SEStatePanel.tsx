import React, { useEffect, useState } from 'react'

interface SEState {
  selected_object: string | null
  camera_info: { fov?: number; dist_rad?: number } | null
  recent_errors: string[]
  log_stats: {
    exists?: boolean
    total_lines?: number
    errors?: number
    warnings?: number
    size_kb?: number
  }
}

export function SEStatePanel() {
  const [state, setState] = useState<SEState | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchState = async () => {
    setLoading(true)
    try {
      const result = await window.api.mcpExecute('read_se_state', {})
      if (result.status === 'ok' && result.result) {
        setState(result.result as SEState)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchState()
    const interval = setInterval(fetchState, 10000) // 10초마다 폴링
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          SE 상태
        </h3>
        <button
          onClick={fetchState}
          className="text-[10px] text-blue-400 hover:text-blue-300"
          disabled={loading}
        >
          {loading ? '...' : '새로고침'}
        </button>
      </div>

      {state ? (
        <div className="space-y-2 text-sm">
          {/* 선택된 천체 */}
          <div className="bg-gray-700/50 rounded-lg p-2">
            <span className="text-gray-400 text-xs">선택된 천체</span>
            <p className="text-white font-medium">
              {state.selected_object || '(없음)'}
            </p>
          </div>

          {/* 카메라 정보 */}
          {state.camera_info && (
            <div className="bg-gray-700/50 rounded-lg p-2">
              <span className="text-gray-400 text-xs">카메라</span>
              <div className="grid grid-cols-2 gap-1 mt-0.5">
                {state.camera_info.fov && (
                  <div>
                    <span className="text-gray-500 text-[11px]">FOV</span>
                    <p className="text-white">{state.camera_info.fov.toFixed(1)}</p>
                  </div>
                )}
                {state.camera_info.dist_rad && (
                  <div>
                    <span className="text-gray-500 text-[11px]">DistRad</span>
                    <p className="text-white">{state.camera_info.dist_rad.toFixed(2)}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 로그 통계 */}
          {state.log_stats?.exists && (
            <div className="bg-gray-700/50 rounded-lg p-2">
              <span className="text-gray-400 text-xs">로그</span>
              <div className="grid grid-cols-3 gap-1 mt-0.5 text-center">
                <div>
                  <p className="text-white text-xs">{state.log_stats.total_lines}</p>
                  <span className="text-gray-500 text-[10px]">줄</span>
                </div>
                <div>
                  <p className={`text-xs ${(state.log_stats.errors ?? 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {state.log_stats.errors}
                  </p>
                  <span className="text-gray-500 text-[10px]">오류</span>
                </div>
                <div>
                  <p className="text-yellow-400 text-xs">{state.log_stats.warnings}</p>
                  <span className="text-gray-500 text-[10px]">경고</span>
                </div>
              </div>
            </div>
          )}

          {/* 최근 에러 */}
          {state.recent_errors.length > 0 && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-2">
              <span className="text-red-400 text-xs">최근 오류</span>
              <div className="mt-1 space-y-0.5">
                {state.recent_errors.slice(0, 3).map((err, i) => (
                  <p key={i} className="text-red-300 text-[11px] truncate" title={err}>
                    {err}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <p className="text-gray-500 text-xs">
          {loading ? '불러오는 중...' : 'MCP 서버 미연결'}
        </p>
      )}
    </div>
  )
}
