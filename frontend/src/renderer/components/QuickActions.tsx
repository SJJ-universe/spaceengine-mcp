import React, { useState, useEffect } from 'react'
import { useChatStore } from '../stores/chat-store'
import { useToastStore } from './Toast'

interface QuickAction {
  label: string
  icon: string
  tool: string
  args: Record<string, unknown>
}

interface Preset {
  id: string
  label: string
  icon: string
  desc: string
}

interface Scenario {
  id: string
  label: string
  icon: string
  desc: string
  duration: string
  steps: Record<string, unknown>[]
}

const PRESETS: Preset[] = [
  { id: 'cinematic_dark',  icon: '🎥', label: '시네마틱 다크', desc: 'UI 숨김, 깨끗한 화면' },
  { id: 'cinematic_wide',  icon: '🎬', label: '시네마틱 광각', desc: 'UI 숨김, 넓은 시야' },
  { id: 'educational',     icon: '📚', label: '교육 모드',    desc: '라벨, 궤도, 별자리 표시' },
  { id: 'observation',     icon: '🔭', label: '관측 모드',    desc: '라벨만 표시, 깔끔' },
  { id: 'screenshot',      icon: '📷', label: '스크린샷',     desc: 'UI 숨김, 표준 FOV' },
  { id: 'default',         icon: '🔄', label: '기본 복원',    desc: '기본 설정 복원' },
]

const SCENARIOS: Scenario[] = [
  {
    id: 'solar_tour',
    label: '태양계 그랜드 투어',
    icon: '🪐',
    desc: '수성→금성→지구→화성→목성→토성→천왕성→해왕성 순차 탐험',
    duration: '~2분',
    steps: [
      { action: 'message', text: '태양계 그랜드 투어를 시작합니다', value: 3 },
      { action: 'navigate', target: 'Sun',     distance_rad: 20.0, transition_time: 4 },
      { action: 'message', text: '태양 — 우리 태양계의 중심', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Mercury', distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '수성 — 태양에서 가장 가까운 행성', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Venus',   distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '금성 — 두꺼운 대기로 뒤덮인 지옥', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Earth',   distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '지구 — 우리의 고향', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Mars',    distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '화성 — 붉은 행성', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Jupiter', distance_rad: 5.0, transition_time: 5 },
      { action: 'message', text: '목성 — 태양계 최대의 가스 거인', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Saturn',  distance_rad: 8.0, transition_time: 5 },
      { action: 'message', text: '토성 — 아름다운 고리의 행성', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Uranus',  distance_rad: 5.0, transition_time: 5 },
      { action: 'message', text: '천왕성 — 옆으로 누운 얼음 거인', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Neptune', distance_rad: 5.0, transition_time: 5 },
      { action: 'message', text: '해왕성 — 태양계 끝의 푸른 행성', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'message', text: '태양계 그랜드 투어 완료!', value: 4 },
    ],
  },
  {
    id: 'stellar_evolution',
    label: '항성 진화 여행',
    icon: '⭐',
    desc: '적색왜성→태양→청색거성→적색초거성→백색왜성 비교',
    duration: '~1분 30초',
    steps: [
      { action: 'message', text: '항성 진화 여행 — 다양한 별의 일생을 둘러봅니다', value: 4 },
      { action: 'navigate', target: 'Proxima Cen', distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '프록시마 센타우리 — 적색왜성 (M형, 태양의 0.12배)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Sun', distance_rad: 10.0, transition_time: 4 },
      { action: 'message', text: '태양 — 주계열성 (G형, 46억년)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Sirius', distance_rad: 8.0, transition_time: 4 },
      { action: 'message', text: '시리우스 A — 밝은 주계열성 (A형, 태양의 2배)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Rigel', distance_rad: 15.0, transition_time: 5 },
      { action: 'message', text: '리겔 — 청색초거성 (B형, 태양의 78배 크기)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Betelgeuse', distance_rad: 15.0, transition_time: 5 },
      { action: 'message', text: '베텔게우스 — 적색초거성 (M형, 태양의 ~1000배 크기)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'navigate', target: 'Sirius B', distance_rad: 3.0, transition_time: 4 },
      { action: 'message', text: '시리우스 B — 백색왜성 (별의 최후, 지구 크기에 태양 질량)', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'message', text: '항성 진화 여행 완료!', value: 3 },
    ],
  },
  {
    id: 'earth_moon',
    label: '지구-달 타임랩스',
    icon: '🌙',
    desc: '지구 궤도에서 달의 공전을 시간 가속으로 관측',
    duration: '~30초',
    steps: [
      { action: 'message', text: '지구-달 타임랩스를 시작합니다', value: 3 },
      { action: 'navigate', target: 'Earth', distance_rad: 15.0, transition_time: 4 },
      { action: 'wait', value: 2 },
      { action: 'overlay_on', overlay: 'Orbits' },
      { action: 'message', text: '시간을 가속하여 달의 공전을 관측합니다', value: 3 },
      { action: 'time_rate', value: 100000 },
      { action: 'wait', value: 15 },
      { action: 'time_rate', value: 1 },
      { action: 'overlay_off', overlay: 'Orbits' },
      { action: 'message', text: '지구-달 타임랩스 완료!', value: 3 },
    ],
  },
  {
    id: 'black_hole',
    label: '블랙홀 접근',
    icon: '🕳️',
    desc: '은하 중심 블랙홀에 시네마틱하게 접근',
    duration: '~40초',
    steps: [
      { action: 'set_fov', value: 45 },
      { action: 'message', text: '블랙홀로의 여행을 시작합니다', value: 3 },
      { action: 'navigate', target: 'Sagittarius A*', distance_rad: 50.0, transition_time: 6 },
      { action: 'message', text: '궁수자리 A* — 우리 은하 중심의 초대질량 블랙홀', value: 4 },
      { action: 'wait', value: 2 },
      { action: 'set_fov', value: 30 },
      { action: 'navigate', target: 'Sagittarius A*', distance_rad: 10.0, transition_time: 8 },
      { action: 'message', text: '사건의 지평선에 접근 중...', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'set_fov', value: 60 },
      { action: 'message', text: '시공간의 왜곡이 극심해집니다', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'set_fov', value: 45 },
      { action: 'message', text: '블랙홀 접근 완료!', value: 3 },
    ],
  },
  {
    id: 'scale_comparison',
    label: '천체 크기 비교',
    icon: '📏',
    desc: '달→지구→목성→태양→시리우스→베텔게우스 크기 비교',
    duration: '~1분 30초',
    steps: [
      { action: 'message', text: '천체 크기 비교 — 작은 것부터 큰 것으로', value: 3 },
      { action: 'navigate', target: 'Moon', distance_rad: 3.0, transition_time: 3 },
      { action: 'message', text: '달 — 직경 3,474km', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Earth', distance_rad: 3.0, transition_time: 3 },
      { action: 'message', text: '지구 — 직경 12,742km (달의 3.7배)', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Jupiter', distance_rad: 3.0, transition_time: 4 },
      { action: 'message', text: '목성 — 직경 139,820km (지구의 11배)', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Sun', distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '태양 — 직경 1,392,700km (목성의 10배)', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Sirius', distance_rad: 5.0, transition_time: 4 },
      { action: 'message', text: '시리우스 A — 태양의 1.7배 크기', value: 3 },
      { action: 'wait', value: 2 },
      { action: 'navigate', target: 'Betelgeuse', distance_rad: 8.0, transition_time: 5 },
      { action: 'message', text: '베텔게우스 — 태양의 ~1000배! 목성 궤도까지 삼킴', value: 4 },
      { action: 'wait', value: 3 },
      { action: 'message', text: '크기 비교 완료!', value: 3 },
    ],
  },
]

// Quick Action은 LLM을 거치지 않고 MCP 도구를 직접 호출합니다
const QUICK_ACTIONS: QuickAction[] = [
  { label: '지구로 이동',    icon: '🌍', tool: 'navigate_to',     args: { target: 'Earth', mode: 'goto', distance_rad: 5.0 } },
  { label: '화성으로 이동',  icon: '🔴', tool: 'navigate_to',     args: { target: 'Mars', mode: 'goto', distance_rad: 3.0 } },
  { label: '토성으로 이동',  icon: '🪐', tool: 'navigate_to',     args: { target: 'Saturn', mode: 'goto', distance_rad: 8.0 } },
  { label: '스크린샷',       icon: '📸', tool: 'take_screenshot',  args: {} },
  { label: '궤도선 표시',    icon: '🔵', tool: 'toggle_overlay',  args: { overlay: 'Orbits', visible: true } },
  { label: '궤도선 숨김',    icon: '⚫', tool: 'toggle_overlay',  args: { overlay: 'Orbits', visible: false } },
  { label: '시간 x1000',    icon: '⏩', tool: 'set_time',        args: { rate: 1000 } },
  { label: '시간 정지',      icon: '⏸', tool: 'set_time',        args: { rate: 0 } },
  { label: 'UI 숨김',        icon: '🎬', tool: 'toggle_gui',      args: { visible: false } },
  { label: 'UI 표시',        icon: '🖥', tool: 'toggle_gui',      args: { visible: true } },
  { label: '최저사양 모드',  icon: '🐢', tool: 'set_performance', args: { preset: 'potato' } },
  { label: '균형 모드',      icon: '⚖', tool: 'set_performance', args: { preset: 'balanced' } },
  { label: '최고사양 모드',  icon: '🚀', tool: 'set_performance', args: { preset: 'ultra' } },
  { label: '설정 초기화',    icon: '🔄', tool: 'restore_defaults', args: {} },
]

export function QuickActions() {
  const { addMessage, setLoading, isLoading } = useChatStore()
  const { addToast } = useToastStore()
  const [favorites, setFavorites] = useState<string[]>([])
  const [scenarioActive, setScenarioActive] = useState(false)
  const [scenarioSummary, setScenarioSummary] = useState('')

  useEffect(() => {
    window.api.favoritesGet().then(setFavorites)
  }, [])

  const toggleFavorite = async (label: string) => {
    const next = favorites.includes(label)
      ? favorites.filter((f) => f !== label)
      : [...favorites, label]
    setFavorites(next)
    await window.api.favoritesSet(next)
  }

  // 즐겨찾기 항목을 상단에 표시
  const sortedActions = [...QUICK_ACTIONS].sort((a, b) => {
    const aFav = favorites.includes(a.label) ? 0 : 1
    const bFav = favorites.includes(b.label) ? 0 : 1
    return aFav - bFav
  })

  const handleClick = async (action: QuickAction) => {
    if (isLoading) return

    addMessage({ role: 'user', content: action.label })
    setLoading(true)

    try {
      const result = await window.api.mcpExecute(action.tool, action.args)

      const isOk = result.status === 'ok'
      const isPartial = result.status === 'partial'
      const statusMsg = isOk
        ? `${action.label} — done.`
        : isPartial
        ? `${action.label} — 일부 실행: ${result.message || '부분 완료'}`
        : `${action.label} — failed: ${result.message || 'error'}`

      addMessage({
        role: 'assistant',
        content: statusMsg,
        toolCalls: [{
          name: action.tool,
          arguments: action.args,
          result: result.result ?? result,
          status: isOk ? 'ok' : 'error',
        }],
      })
      addToast(
        isOk ? `${action.label} 완료` : isPartial ? `${action.label} 부분 실행` : `${action.label} 실패`,
        isOk ? 'success' : isPartial ? 'warning' : 'error',
      )
    } catch (err) {
      addMessage({ role: 'assistant', content: '', error: String(err) })
      addToast(`오류: ${err}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handlePreset = async (preset: Preset) => {
    if (isLoading) return
    addMessage({ role: 'user', content: `프리셋: ${preset.label}` })
    setLoading(true)
    try {
      const result = await window.api.mcpExecute('apply_preset', { preset: preset.id })
      addMessage({
        role: 'assistant',
        content: result.status === 'ok' ? `${preset.label} 프리셋 적용됨` : `프리셋 실패: ${result.message}`,
        toolCalls: [{
          name: 'apply_preset',
          arguments: { preset: preset.id },
          result: result.result ?? result,
          status: result.status === 'ok' ? 'ok' : 'error',
        }],
      })
      addToast(result.status === 'ok' ? `${preset.label} 적용` : '프리셋 실패', result.status === 'ok' ? 'success' : 'error')
    } catch (err) {
      addMessage({ role: 'assistant', content: '', error: String(err) })
    } finally {
      setLoading(false)
    }
  }

  const handleScenarioStart = () => {
    setScenarioActive(true)
    setScenarioSummary('')
    addMessage({ role: 'user', content: '시나리오 시작' })
    addMessage({ role: 'assistant', content: '시나리오 빌더를 시작합니다.\n채팅에서 "화성 추가", "토성 추가" 등으로 스텝을 추가하세요.\n완료 후 "시나리오 실행"을 입력하세요.' })
    // Agent의 시나리오 빌더도 활성화 (채팅 경유)
    window.api.chatSendStream('시나리오 시작')
  }

  const handleScenarioExecute = async () => {
    if (isLoading) return
    setLoading(true)
    addMessage({ role: 'user', content: '시나리오 실행' })
    try {
      const result = await window.api.scenarioExecute()
      const isOk = result.status === 'ok'
      addMessage({
        role: 'assistant',
        content: isOk ? '시나리오 실행 완료!' : `시나리오 실패: ${result.message}`,
        toolCalls: [{ name: 'scenario_execute', arguments: {}, result: result.result ?? result, status: isOk ? 'ok' : 'error' }],
      })
      setScenarioActive(false)
      setScenarioSummary('')
      addToast(isOk ? '시나리오 완료' : '시나리오 실패', isOk ? 'success' : 'error')
    } catch (err) {
      addMessage({ role: 'assistant', content: '', error: String(err) })
    } finally {
      setLoading(false)
    }
  }

  const handleScenarioClear = async () => {
    await window.api.scenarioClear()
    setScenarioActive(false)
    setScenarioSummary('')
    addToast('시나리오 초기화', 'info')
  }

  const refreshScenario = async () => {
    const info = await window.api.scenarioList()
    setScenarioActive(info.count > 0)
    setScenarioSummary(info.summary)
  }

  const handleTemplate = async (templateId: string, templateName: string, params: Record<string, unknown> = {}) => {
    if (isLoading) return
    addMessage({ role: 'user', content: `고급 시나리오: ${templateName}` })
    setLoading(true)
    try {
      const result = await window.api.scenarioRunTemplate(templateId, params)
      const isOk = result.status === 'ok'
      addMessage({
        role: 'assistant',
        content: isOk ? `${templateName} 시나리오 완료!` : `시나리오 실패: ${result.message}`,
        toolCalls: [{
          name: `template:${templateId}`,
          arguments: params,
          result: result.result ?? result,
          status: isOk ? 'ok' : 'error',
        }],
      })
      addToast(isOk ? `${templateName} 완료` : '시나리오 실패', isOk ? 'success' : 'error')
    } catch (err) {
      addMessage({ role: 'assistant', content: '', error: String(err) })
      addToast(`오류: ${err}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleScenario = async (scenario: Scenario) => {
    if (isLoading) return
    addMessage({ role: 'user', content: `시나리오: ${scenario.label}` })
    setLoading(true)
    try {
      const result = await window.api.mcpExecute(
        'cinematic_sequence',
        { steps: scenario.steps, auto_hide_gui: true },
      )

      const isOk = result.status === 'ok'
      const isPartial = result.status === 'partial'
      addMessage({
        role: 'assistant',
        content: isOk
          ? `${scenario.label} 시나리오 완료!`
          : isPartial
          ? `${scenario.label} — 일부 완료: ${result.message || ''}`
          : `시나리오 실패: ${result.message}`,
        toolCalls: [{
          name: 'cinematic_sequence',
          arguments: { steps: scenario.steps },
          result: result.result ?? result,
          status: isOk ? 'ok' : 'error',
        }],
      })
      addToast(
        isOk ? `${scenario.label} 완료` : isPartial ? `${scenario.label} 부분 완료` : '시나리오 실패',
        isOk ? 'success' : isPartial ? 'warning' : 'error',
      )
    } catch (err) {
      addMessage({ role: 'assistant', content: '', error: String(err) })
      addToast(`오류: ${err}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-3 space-y-3">
      {/* 시나리오 데모 */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          시나리오 데모
        </h3>
        <div className="space-y-1.5">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700
                         transition-colors border border-gray-700 hover:border-blue-500 disabled:opacity-50"
              onClick={() => handleScenario(scenario)}
              disabled={isLoading}
              title={scenario.desc}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{scenario.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-200">{scenario.label}</div>
                  <div className="text-[10px] text-gray-500 truncate">{scenario.desc}</div>
                </div>
                <span className="text-[10px] text-gray-600 whitespace-nowrap">{scenario.duration}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 시나리오 빌더 */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          시나리오 빌더
        </h3>
        {!scenarioActive ? (
          <button
            className="w-full px-3 py-2 rounded-lg text-sm bg-purple-600/20 border border-purple-500/50
                       hover:bg-purple-600/30 transition-colors text-purple-300"
            onClick={handleScenarioStart}
          >
            + 새 시나리오 만들기
          </button>
        ) : (
          <div className="space-y-1.5">
            <div className="px-3 py-2 rounded-lg bg-gray-700/50 text-xs text-gray-300 whitespace-pre-line">
              {scenarioSummary || '채팅에서 "화성 추가" 등으로 스텝 추가 중...'}
            </div>
            <div className="flex gap-1.5">
              <button
                className="flex-1 px-2 py-1.5 rounded-lg text-xs bg-green-600/20 border border-green-500/50
                           hover:bg-green-600/30 text-green-300 disabled:opacity-50"
                onClick={handleScenarioExecute}
                disabled={isLoading}
              >
                실행
              </button>
              <button
                className="flex-1 px-2 py-1.5 rounded-lg text-xs bg-gray-600 hover:bg-gray-500 text-gray-300"
                onClick={refreshScenario}
              >
                새로고침
              </button>
              <button
                className="px-2 py-1.5 rounded-lg text-xs bg-red-600/20 border border-red-500/50
                           hover:bg-red-600/30 text-red-300"
                onClick={handleScenarioClear}
              >
                취소
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 고급 시나리오 (템플릿) */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          고급 시나리오
        </h3>
        <div className="space-y-1.5">
          {[
            { id: 'exoplanet_tour', icon: '🪐', label: '외계행성 탐사 (5개)', params: { count: 5 } },
            { id: 'grand_voyage', icon: '🚀', label: '그랜드 보야주', params: { exoplanet_count: 5 } },
            { id: 'size_comparison', icon: '📏', label: '천체 크기 비교', params: {} },
            { id: 'black_hole_tour', icon: '🕳', label: '블랙홀 투어', params: {} },
            { id: 'cinematic_documentary', icon: '🎬', label: '토성 다큐멘터리', params: { target: 'Saturn' } },
          ].map((t) => (
            <button
              key={t.id}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700
                         transition-colors border border-gray-700 hover:border-purple-500 disabled:opacity-50"
              onClick={() => handleTemplate(t.id, t.label, t.params)}
              disabled={isLoading}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{t.icon}</span>
                <span className="text-sm text-gray-200">{t.label}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 프리셋 카드 */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          프리셋
        </h3>
        <div className="grid grid-cols-2 gap-1.5">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              className="text-left px-2 py-1.5 rounded-lg text-[11px] hover:bg-gray-700
                         transition-colors border border-gray-700 hover:border-gray-500 disabled:opacity-50"
              onClick={() => handlePreset(preset)}
              disabled={isLoading}
              title={preset.desc}
            >
              <span className="mr-1">{preset.icon}</span>
              <span>{preset.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 빠른 실행 */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          빠른 실행
        </h3>
      {sortedActions.map((action) => (
        <button
          key={action.label}
          className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-gray-700
                     transition-colors flex items-center gap-2 disabled:opacity-50 group"
          onClick={() => handleClick(action)}
          disabled={isLoading}
        >
          <span>{action.icon}</span>
          <span className="flex-1">{action.label}</span>
          <span
            className={`text-[10px] cursor-pointer transition-opacity
              ${favorites.includes(action.label) ? 'text-yellow-400 opacity-100' : 'text-gray-600 opacity-0 group-hover:opacity-100'}`}
            onClick={(e) => { e.stopPropagation(); toggleFavorite(action.label) }}
          >
            {favorites.includes(action.label) ? '★' : '☆'}
          </span>
        </button>
      ))}
      </div>
    </div>
  )
}
