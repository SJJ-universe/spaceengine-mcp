import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useChatStore } from '../stores/chat-store'
import { useToastStore } from './Toast'

interface Tool {
  name: string
  description: string
  parameters?: Record<string, unknown>
}

// Phase별 카테고리 매핑
const PHASE_CATEGORIES: Record<string, { label: string; prefix: string[] }> = {
  all:       { label: '전체', prefix: [] },
  nav:       { label: '탐색', prefix: ['navigate_to', 'search_catalog'] },
  camera:    { label: '카메라', prefix: ['control_camera', 'set_fov'] },
  visual:    { label: '시각', prefix: ['toggle_overlay', 'toggle_gui', 'set_performance', 'fade_effect', 'set_variable'] },
  time:      { label: '시간', prefix: ['set_time', 'get_time', 'set_date'] },
  capture:   { label: '캡처', prefix: ['take_screenshot', 'start_video', 'stop_video'] },
  state:     { label: '상태', prefix: ['read_se_state', 'get_system_info', 'restore_defaults'] },
  tour:      { label: '투어', prefix: ['create_tour', 'run_tour'] },
  cinematic: { label: '시네마틱', prefix: ['cinematic_sequence', 'apply_preset', 'timelapse_capture', 'save_scene', 'load_scene', 'list_scenes', 'get_object_info'] },
}

interface ParamField {
  name: string
  type: string
  description: string
  required: boolean
  enumValues?: string[]
  default?: unknown
}

function extractParams(tool: Tool): ParamField[] {
  if (!tool.parameters) return []
  const schema = tool.parameters as any
  const props = schema.properties || {}
  const required = schema.required || []
  return Object.entries(props).map(([name, prop]: [string, any]) => ({
    name,
    type: prop.type || 'string',
    description: prop.description || '',
    required: required.includes(name),
    enumValues: prop.enum,
    default: prop.default,
  }))
}

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [tools, setTools] = useState<Tool[]>([])
  const [filtered, setFiltered] = useState<Tool[]>([])
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [category, setCategory] = useState('all')
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [formArgs, setFormArgs] = useState<Record<string, string>>({})
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const { addMessage, setLoading } = useChatStore()
  const { addToast } = useToastStore()

  // Cmd+K / Ctrl+K 단축키
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      if (e.key === 'Escape') {
        if (selectedTool) { setSelectedTool(null); return }
        setOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedTool])

  // 열릴 때 도구 목록 로드 + 포커스
  useEffect(() => {
    if (open) {
      setQuery('')
      setSelectedIdx(0)
      setCategory('all')
      setSelectedTool(null)
      inputRef.current?.focus()
      window.api.mcpTools().then((t) => {
        setTools(t)
        setFiltered(t)
      })
    }
  }, [open])

  // 검색 + 카테고리 필터
  useEffect(() => {
    let list = tools
    if (category !== 'all') {
      const prefixes = PHASE_CATEGORIES[category]?.prefix || []
      list = list.filter((t) => prefixes.some((p) => t.name.startsWith(p) || t.name === p))
    }
    if (query.trim()) {
      const q = query.toLowerCase()
      list = list.filter(
        (t) => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q),
      )
    }
    setFiltered(list)
    setSelectedIdx(0)
  }, [query, tools, category])

  // 선택 항목이 보이도록 스크롤
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${selectedIdx}"]`)
    el?.scrollIntoView({ block: 'nearest' })
  }, [selectedIdx])

  const openToolForm = (tool: Tool) => {
    const params = extractParams(tool)
    if (params.length === 0) {
      executeTool(tool, {})
    } else {
      setSelectedTool(tool)
      const defaults: Record<string, string> = {}
      params.forEach((p) => {
        if (p.default !== undefined) defaults[p.name] = String(p.default)
        else defaults[p.name] = ''
      })
      setFormArgs(defaults)
    }
  }

  const executeTool = useCallback(
    async (tool: Tool, args: Record<string, unknown>) => {
      setOpen(false)
      setSelectedTool(null)
      const argStr = Object.keys(args).length > 0
        ? ` (${Object.entries(args).map(([k, v]) => `${k}=${v}`).join(', ')})`
        : ''
      addMessage({ role: 'user', content: `${tool.name}${argStr}` })
      setLoading(true)
      try {
        const result = await window.api.mcpExecute(tool.name, args)
        const status = result.status === 'ok' ? 'ok' : 'error'
        addMessage({
          role: 'assistant',
          content: status === 'ok'
            ? `${tool.name} 실행 완료`
            : `${tool.name} 실패: ${result.message || 'error'}`,
          toolCalls: [{
            name: tool.name,
            arguments: args as Record<string, unknown>,
            result: result.result ?? result,
            status: status as 'ok' | 'error',
          }],
          error: status === 'error' ? result.message : undefined,
        })
        addToast(status === 'ok' ? `${tool.name} 완료` : `${tool.name} 실패`, status === 'ok' ? 'success' : 'error')
      } catch (err) {
        addMessage({ role: 'assistant', content: '', error: String(err) })
        addToast(`오류: ${err}`, 'error')
      } finally {
        setLoading(false)
      }
    },
    [addMessage, setLoading, addToast],
  )

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTool) return
    const params = extractParams(selectedTool)
    const args: Record<string, unknown> = {}
    params.forEach((p) => {
      const val = formArgs[p.name]
      if (val === '' && !p.required) return
      if (p.type === 'number' || p.type === 'integer') args[p.name] = Number(val) || 0
      else if (p.type === 'boolean') args[p.name] = val === 'true'
      else if (p.type === 'array' || p.type === 'object') {
        try { args[p.name] = JSON.parse(val) } catch { args[p.name] = val }
      } else args[p.name] = val
    })
    executeTool(selectedTool, args)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx((prev) => Math.min(prev + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && filtered[selectedIdx]) {
      openToolForm(filtered[selectedIdx])
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/50">
      <div className="w-[620px] bg-gray-800 border border-gray-600 rounded-xl shadow-2xl overflow-hidden">
        {/* 검색 입력 */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-700">
          <span className="text-gray-400 text-sm">{'>'}</span>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-white outline-none text-sm placeholder-gray-500"
            placeholder={`툴 검색... (${tools.length}개 사용 가능)`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="text-[10px] text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">ESC</kbd>
        </div>

        {/* 카테고리 필터 */}
        <div className="flex gap-1 px-3 py-2 border-b border-gray-700 overflow-x-auto">
          {Object.entries(PHASE_CATEGORIES).map(([key, { label }]) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={`px-2 py-0.5 rounded text-[11px] whitespace-nowrap transition-colors
                ${category === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:text-white hover:bg-gray-600'
                }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 인자 입력 폼 */}
        {selectedTool ? (
          <form onSubmit={handleFormSubmit} className="p-4 space-y-3 max-h-96 overflow-y-auto">
            <div className="flex items-center gap-2 mb-2">
              <button
                type="button"
                onClick={() => setSelectedTool(null)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ←
              </button>
              <span className="text-blue-400 font-mono text-sm">{selectedTool.name}</span>
            </div>
            <p className="text-gray-400 text-xs mb-3">{selectedTool.description}</p>

            {extractParams(selectedTool).map((param) => (
              <div key={param.name}>
                <label className="flex items-center gap-1 text-xs text-gray-300 mb-1">
                  <span className="font-mono">{param.name}</span>
                  {param.required && <span className="text-red-400">*</span>}
                  <span className="text-gray-500">({param.type})</span>
                </label>
                {param.description && (
                  <p className="text-[10px] text-gray-500 mb-1">{param.description}</p>
                )}
                {param.enumValues ? (
                  <select
                    className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-xs outline-none focus:ring-1 focus:ring-blue-500"
                    value={formArgs[param.name] || ''}
                    onChange={(e) => setFormArgs((prev) => ({ ...prev, [param.name]: e.target.value }))}
                  >
                    <option value="">선택...</option>
                    {param.enumValues.map((v) => <option key={v} value={v}>{v}</option>)}
                  </select>
                ) : param.type === 'boolean' ? (
                  <select
                    className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-xs outline-none focus:ring-1 focus:ring-blue-500"
                    value={formArgs[param.name] || ''}
                    onChange={(e) => setFormArgs((prev) => ({ ...prev, [param.name]: e.target.value }))}
                  >
                    <option value="">선택...</option>
                    <option value="true">true</option>
                    <option value="false">false</option>
                  </select>
                ) : (
                  <input
                    className="w-full bg-gray-700 text-white rounded px-2 py-1.5 text-xs outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={param.type === 'number' ? '0' : param.type === 'array' ? '[...]' : ''}
                    value={formArgs[param.name] || ''}
                    onChange={(e) => setFormArgs((prev) => ({ ...prev, [param.name]: e.target.value }))}
                  />
                )}
              </div>
            ))}

            <button
              type="submit"
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
            >
              실행
            </button>
          </form>
        ) : (
          /* 결과 목록 */
          <div ref={listRef} className="max-h-80 overflow-y-auto">
            {filtered.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500 text-sm">
                검색 결과 없음
              </div>
            ) : (
              filtered.map((tool, i) => (
                <div
                  key={tool.name}
                  data-idx={i}
                  className={`flex items-start gap-3 px-4 py-2.5 cursor-pointer text-sm
                    ${i === selectedIdx ? 'bg-blue-600/20 border-l-2 border-blue-400' : 'hover:bg-gray-700/50 border-l-2 border-transparent'}`}
                  onClick={() => openToolForm(tool)}
                  onMouseEnter={() => setSelectedIdx(i)}
                >
                  <span className="text-blue-400 font-mono text-xs mt-0.5 whitespace-nowrap">
                    {tool.name}
                  </span>
                  <span className="text-gray-400 text-xs leading-relaxed truncate">
                    {tool.description}
                  </span>
                </div>
              ))
            )}
          </div>
        )}

        {/* 하단 힌트 */}
        <div className="px-4 py-2 border-t border-gray-700 flex gap-4 text-[10px] text-gray-500">
          <span>↑↓ 이동</span>
          <span>Enter 선택</span>
          <span>ESC {selectedTool ? '뒤로' : '닫기'}</span>
          <span className="ml-auto">{filtered.length}개 도구</span>
        </div>
      </div>
    </div>
  )
}
