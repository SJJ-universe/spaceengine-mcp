/**
 * Scenario Builder — 액션 누적 + 시나리오 템플릿
 *
 * 1. 빌더 모드: 사용자가 여러 턴에 걸쳐 액션을 추가 → "실행" 시 일괄 실행
 * 2. 템플릿: exoplanet_tour, grand_voyage 등 복잡한 시나리오를 코드로 생성
 */

// ── 빌더 모드 ─────────────────────────────────────────────────────────────

export interface ScenarioStep {
  action: string
  target?: string
  text?: string
  value?: number
  distance_rad?: number
  transition_time?: number
}

export class ScenarioBuilder {
  private steps: ScenarioStep[] = []
  private title = ''

  isActive(): boolean { return this.steps.length > 0 }

  getSteps(): ScenarioStep[] { return [...this.steps] }
  getTitle(): string { return this.title }
  getStepCount(): number { return this.steps.length }

  setTitle(title: string): void { this.title = title }

  addStep(step: ScenarioStep): void { this.steps.push(step) }

  addSteps(steps: ScenarioStep[]): void { this.steps.push(...steps) }

  removeLastStep(): ScenarioStep | undefined { return this.steps.pop() }

  clear(): void {
    this.steps = []
    this.title = ''
  }

  /** cinematic_sequence 도구에 전달할 args 형식으로 변환 */
  toCinematicArgs(): { steps: ScenarioStep[], auto_hide_gui?: boolean } {
    return { steps: this.steps, auto_hide_gui: true }
  }

  /** 현재 시나리오 요약 (LLM/사용자에게 표시) */
  summarize(): string {
    if (this.steps.length === 0) return '시나리오가 비어있습니다.'
    const lines = this.steps.map((s, i) => {
      const desc = s.target ? `${s.action}: ${s.target}` : s.action
      const extra = s.text ? ` — "${s.text}"` : ''
      return `  ${i + 1}. ${desc}${extra}`
    })
    const header = this.title ? `**${this.title}** (${this.steps.length}단계)` : `시나리오 (${this.steps.length}단계)`
    return `${header}\n${lines.join('\n')}`
  }
}

// ── 시나리오 템플릿 ──────────────────────────────────────────────────────────

export interface TemplateConfig {
  name: string
  description: string
  generate: (params: Record<string, unknown>) => ScenarioStep[]
}

/** 외계행성 탐사 투어 */
function generateExoplanetTour(params: Record<string, unknown>): ScenarioStep[] {
  const count = Math.min(Number(params.count) || 5, 20)
  const EXOPLANETS = [
    'Proxima Cen b', 'TRAPPIST-1 e', 'TRAPPIST-1 f', 'TRAPPIST-1 g',
    'Kepler-442 b', 'Kepler-186 f', 'Ross 128 b', 'K2-18 b',
    'Gliese 667 C c', 'Gliese 581 c', 'HD 189733 b', 'WASP-12 b',
    'HR 8799 b', 'HR 8799 c', '51 Peg b', 'Kepler-10 b',
    'TRAPPIST-1 b', 'TRAPPIST-1 c', 'TRAPPIST-1 d', 'TRAPPIST-1 h',
  ]
  const targets = EXOPLANETS.slice(0, count)
  const steps: ScenarioStep[] = [
    { action: 'message', text: `외계행성 탐사 투어 — ${count}개의 외계행성을 탐험합니다`, value: 4 },
  ]
  for (const planet of targets) {
    steps.push({ action: 'navigate', target: planet, distance_rad: 5.0, transition_time: 4 })
    steps.push({ action: 'message', text: planet, value: 3 })
    steps.push({ action: 'wait', value: 2 })
  }
  steps.push({ action: 'message', text: `외계행성 탐사 투어 완료! (${count}개 탐방)`, value: 4 })
  return steps
}

/** 그랜드 보야주 — 외계행성 → 태양계 → 지구 귀환 */
function generateGrandVoyage(params: Record<string, unknown>): ScenarioStep[] {
  const exoCount = Math.min(Number(params.exoplanet_count) || 5, 15)
  const EXOPLANETS = [
    'Proxima Cen b', 'TRAPPIST-1 e', 'TRAPPIST-1 f',
    'Kepler-442 b', 'Ross 128 b', 'K2-18 b',
    'Gliese 667 C c', 'HD 189733 b', 'WASP-12 b',
    'HR 8799 b', 'Kepler-186 f', '51 Peg b',
    'Kepler-10 b', 'Gliese 581 c', 'TRAPPIST-1 g',
  ]
  const SOLAR_SYSTEM = ['Neptune', 'Saturn', 'Jupiter', 'Mars', 'Earth']

  const steps: ScenarioStep[] = [
    { action: 'message', text: '그랜드 보야주 — 외계행성에서 지구까지의 대항해', value: 5 },
  ]

  // Phase 1: 외계행성 탐사
  steps.push({ action: 'message', text: '— Phase 1: 외계행성 탐사 —', value: 3 })
  for (const planet of EXOPLANETS.slice(0, exoCount)) {
    steps.push({ action: 'navigate', target: planet, distance_rad: 5.0, transition_time: 5 })
    steps.push({ action: 'message', text: planet, value: 2 })
    steps.push({ action: 'wait', value: 2 })
  }

  // Phase 2: 태양계 귀환
  steps.push({ action: 'message', text: '— Phase 2: 태양계 귀환 —', value: 3 })
  for (const planet of SOLAR_SYSTEM) {
    steps.push({ action: 'navigate', target: planet, distance_rad: 5.0, transition_time: 4 })
    steps.push({ action: 'message', text: `${planet}에 도착`, value: 2 })
    steps.push({ action: 'wait', value: 2 })
  }

  // 지구 최종 도착
  steps.push({ action: 'navigate', target: 'Earth', distance_rad: 3.0, transition_time: 3 })
  steps.push({ action: 'message', text: '지구에 무사히 귀환했습니다!', value: 4 })
  return steps
}

/** 시네마틱 다큐멘터리 — 특정 천체 접근 + 공전 + 스크린샷 */
function generateCinematicDocumentary(params: Record<string, unknown>): ScenarioStep[] {
  const target = String(params.target || 'Saturn')
  return [
    { action: 'message', text: `${target} 시네마틱 다큐멘터리`, value: 3 },
    { action: 'navigate', target, distance_rad: 15.0, transition_time: 5 },
    { action: 'wait', value: 2 },
    { action: 'navigate', target, distance_rad: 5.0, transition_time: 8 },
    { action: 'message', text: `${target}에 접근 중...`, value: 3 },
    { action: 'wait', value: 3 },
    { action: 'screenshot' },
    { action: 'navigate', target, distance_rad: 3.0, transition_time: 5 },
    { action: 'wait', value: 3 },
    { action: 'screenshot' },
    { action: 'message', text: `${target} 다큐멘터리 촬영 완료`, value: 3 },
  ]
}

/** 천체 크기 비교 투어 */
function generateSizeComparison(params: Record<string, unknown>): ScenarioStep[] {
  const objects = [
    { name: 'Moon', desc: '달 — 지름 3,474km', rad: 3.0 },
    { name: 'Earth', desc: '지구 — 지름 12,742km (달의 3.7배)', rad: 3.0 },
    { name: 'Jupiter', desc: '목성 — 지름 139,820km (지구의 11배)', rad: 4.0 },
    { name: 'Sun', desc: '태양 — 지름 1,391,000km (목성의 10배)', rad: 10.0 },
    { name: 'Sirius', desc: '시리우스 A — 태양의 1.7배', rad: 10.0 },
    { name: 'Betelgeuse', desc: '베텔게우스 — 태양의 ~1,000배', rad: 15.0 },
    { name: 'UY Sct', desc: 'UY Scuti — 알려진 가장 큰 별 중 하나', rad: 15.0 },
  ]
  const steps: ScenarioStep[] = [
    { action: 'message', text: '천체 크기 비교 — 달에서 가장 큰 별까지', value: 4 },
  ]
  for (const obj of objects) {
    steps.push({ action: 'navigate', target: obj.name, distance_rad: obj.rad, transition_time: 4 })
    steps.push({ action: 'message', text: obj.desc, value: 4 })
    steps.push({ action: 'wait', value: 3 })
  }
  steps.push({ action: 'message', text: '크기 비교 투어 완료!', value: 3 })
  return steps
}

/** 블랙홀 투어 */
function generateBlackHoleTour(_params: Record<string, unknown>): ScenarioStep[] {
  const targets = [
    { name: 'Sgr A*', desc: '궁수자리 A* — 은하 중심 초대질량 블랙홀 (태양 400만배)' },
    { name: 'Cygnus X-1', desc: '백조자리 X-1 — 최초 발견된 블랙홀 후보' },
    { name: 'Powehi', desc: 'M87* — 최초로 촬영된 블랙홀 (태양 65억배)' },
  ]
  const steps: ScenarioStep[] = [
    { action: 'message', text: '블랙홀 투어 — 우주에서 가장 극단적인 천체들', value: 4 },
  ]
  for (const t of targets) {
    steps.push({ action: 'navigate', target: t.name, distance_rad: 10.0, transition_time: 6 })
    steps.push({ action: 'message', text: t.desc, value: 5 })
    steps.push({ action: 'wait', value: 3 })
    steps.push({ action: 'screenshot' })
  }
  steps.push({ action: 'message', text: '블랙홀 투어 완료!', value: 3 })
  return steps
}

// ── 템플릿 레지스트리 ────────────────────────────────────────────────────────

export const SCENARIO_TEMPLATES: Record<string, TemplateConfig> = {
  exoplanet_tour: {
    name: '외계행성 탐사 투어',
    description: '외계행성 N개를 순차 탐방 (기본 5개, 최대 20개)',
    generate: generateExoplanetTour,
  },
  grand_voyage: {
    name: '그랜드 보야주',
    description: '외계행성 탐사 → 태양계 귀환 → 지구 도착',
    generate: generateGrandVoyage,
  },
  cinematic_documentary: {
    name: '시네마틱 다큐멘터리',
    description: '특정 천체의 접근 + 공전 + 스크린샷 촬영',
    generate: generateCinematicDocumentary,
  },
  size_comparison: {
    name: '천체 크기 비교',
    description: '달 → 지구 → 목성 → 태양 → 거성 순서로 크기 비교',
    generate: generateSizeComparison,
  },
  black_hole_tour: {
    name: '블랙홀 투어',
    description: 'Sgr A*, Cygnus X-1, M87* 블랙홀 탐방',
    generate: generateBlackHoleTour,
  },
}
