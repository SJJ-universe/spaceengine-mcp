/**
 * Agent — 대화 오케스트레이터 (Action Plan 모드)
 *
 * LLM에 Tool 스키마를 전송하지 않고, 시스템 프롬프트에 자연어로 도구 목록을 기술.
 * LLM이 JSON 액션 플랜을 응답에 포함하면 Agent가 파싱하여 MCP 도구를 실행.
 * - 토큰 절감: ~7,500 → ~1,300 (5.6배)
 * - Intent Parser: 간단한 명령은 LLM 호출 없이 직접 실행
 */
import { McpClient, McpTool } from './mcp-client'
import { LLMProvider, LLMMessage, StreamCallback } from './llm-providers'
import { ScenarioBuilder, SCENARIO_TEMPLATES } from './scenario-builder'
import { CelestialRAG } from './celestial-rag'

export interface ToolExecution {
  name: string
  arguments: Record<string, unknown>
  result: unknown
  status: 'ok' | 'error'
}

export interface ChatResult {
  response: string
  toolCalls?: ToolExecution[]
  error?: string
}

// ── Action Plan 타입 ────────────────────────────────────────────────────────

interface ActionStep {
  tool: string
  args: Record<string, unknown>
}

interface ActionPlan {
  actions: ActionStep[]
  reply: string
}

// ── Intent Parser (간단한 명령은 LLM 호출 없이 직접 실행) ───────────────────

interface IntentRule {
  patterns: RegExp[]
  tool: string
  extractArgs: (m: RegExpMatchArray, input: string) => Record<string, unknown>
}

function extractTarget(match: RegExpMatchArray): string {
  return (match[1] || '').replace(/\s+$/, '').trim()
}

const INTENT_RULES: IntentRule[] = [
  { patterns: [/(?:go|navigate|take me|fly|move|travel)\s+(?:to\s+)?((?:(?!and\b|then\b|with\b|show\b|hide\b)[\w''. -])+)/i],
    tool: 'navigate_to', extractArgs: (m) => ({ target: extractTarget(m), mode: 'goto', distance_rad: 3.0 }) },
  { patterns: [/screenshot/i, /캡처|사진|찍/i],
    tool: 'take_screenshot', extractArgs: () => ({}) },
  { patterns: [/show\s+orbit/i, /궤도.*(?:보|표시|켜)/i],
    tool: 'toggle_overlay', extractArgs: () => ({ overlay: 'Orbits', visible: true }) },
  { patterns: [/hide\s+orbit/i, /궤도.*(?:숨|끄)/i],
    tool: 'toggle_overlay', extractArgs: () => ({ overlay: 'Orbits', visible: false }) },
  { patterns: [/time.*(?:speed|fast|x?\s*(\d+))/i, /시간.*(?:빠르|가속|배속)/i],
    tool: 'set_time', extractArgs: (m) => ({ rate: parseInt(m[1]) || 1000 }) },
  { patterns: [/(?:pause|stop)\s*time/i, /시간.*(?:멈|정지)/i],
    tool: 'set_time', extractArgs: () => ({ rate: 0 }) },
  { patterns: [/hide\s*(?:gui|ui)/i, /UI.*숨/i],
    tool: 'toggle_gui', extractArgs: () => ({ visible: false }) },
  { patterns: [/show\s*(?:gui|ui)/i, /UI.*보/i],
    tool: 'toggle_gui', extractArgs: () => ({ visible: true }) },
  { patterns: [/fade\s*out/i], tool: 'fade_effect', extractArgs: () => ({ action: 'fade_out', duration: 2.0 }) },
  { patterns: [/fade\s*in/i], tool: 'fade_effect', extractArgs: () => ({ action: 'fade_in', duration: 1.0 }) },
  { patterns: [/save\s*state/i, /상태.*저장/i], tool: 'save_state', extractArgs: () => ({}) },
  { patterns: [/restore\s*state/i, /상태.*복원/i], tool: 'restore_state', extractArgs: () => ({}) },
  { patterns: [/status/i, /상태.*확인/i], tool: 'read_se_state', extractArgs: () => ({}) },
  { patterns: [/(?:최저|최소|potato|감자)\s*(?:사양|성능|품질|모드)/i],
    tool: 'set_performance', extractArgs: () => ({ preset: 'potato' }) },
  { patterns: [/(?:최고|최대|울트라|ultra)\s*(?:사양|성능|품질|모드)/i],
    tool: 'set_performance', extractArgs: () => ({ preset: 'ultra' }) },
  { patterns: [/(?:설정|세팅)\s*(?:초기화|리셋|기본값|원래대로)/i, /restore\s*default/i],
    tool: 'restore_defaults', extractArgs: () => ({}) },
  // 시나리오 템플릿
  { patterns: [/(?:외계행성|exoplanet)\s*(?:투어|탐사|tour)/i],
    tool: '_template', extractArgs: () => ({ template: 'exoplanet_tour', params: { count: 5 } }) },
  { patterns: [/(?:그랜드|grand)\s*(?:보야주|voyage|투어)/i],
    tool: '_template', extractArgs: () => ({ template: 'grand_voyage', params: { exoplanet_count: 5 } }) },
  { patterns: [/(?:크기|size)\s*(?:비교|comparison)/i],
    tool: '_template', extractArgs: () => ({ template: 'size_comparison', params: {} }) },
  { patterns: [/(?:블랙홀|black\s*hole)\s*(?:투어|tour)/i],
    tool: '_template', extractArgs: () => ({ template: 'black_hole_tour', params: {} }) },
  // RAG: 천체 추천/검색/투어
  { patterns: [/(?:성운|nebula)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?nebula/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'nebula', count: 5 }) },
  { patterns: [/(?:은하|galaxy|galaxies)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?galax/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'galaxy', count: 5 }) },
  { patterns: [/(?:별|항성|star)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?star/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'star', count: 5 }) },
  { patterns: [/(?:외계행성|exoplanet)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?exoplanet/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'exoplanet', count: 5 }) },
  { patterns: [/(?:블랙홀|black\s*hole)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?black\s*hole/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'black_hole', count: 5 }) },
  { patterns: [/(?:성단|cluster)\s*(?:보여|추천|recommend|show)/i, /(?:show|recommend)\s+(?:me\s+)?cluster/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'cluster', count: 5 }) },
  { patterns: [/(?:태양계|solar\s*system)\s*(?:보여|추천|천체)/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'solar_system', count: 5 }) },
  { patterns: [/(?:천체|object)\s*(?:추천|recommend|보여|show)/i, /(?:추천|recommend)\s*(?:해|좀)/i],
    tool: '_rag_recommend', extractArgs: () => ({ category: 'all', count: 5 }) },
  { patterns: [/(\d+)\s*번\s*(?:으로|선택|가|go)/i, /(?:select|pick|choose)\s*(?:#?\s*)?(\d+)/i],
    tool: '_rag_select', extractArgs: (m) => ({ index: parseInt(m[1] || m[2]) }) },
  { patterns: [/(?:성운|nebula)\s*(?:투어|tour)/i],
    tool: '_rag_tour', extractArgs: () => ({ category: 'nebula', count: 5 }) },
  { patterns: [/(?:은하|galaxy)\s*(?:투어|tour)/i],
    tool: '_rag_tour', extractArgs: () => ({ category: 'galaxy', count: 5 }) },
  { patterns: [/(?:성단|cluster)\s*(?:투어|tour)/i],
    tool: '_rag_tour', extractArgs: () => ({ category: 'cluster', count: 5 }) },
  { patterns: [/(?:별|항성|star)\s*(?:투어|tour)/i],
    tool: '_rag_tour', extractArgs: () => ({ category: 'star', count: 5 }) },
  { patterns: [/오늘의\s*천체|daily\s*pick|random\s*(?:object|천체)/i],
    tool: '_rag_daily', extractArgs: () => ({}) },
  { patterns: [/천체\s*(?:검색|찾기|search)\s+(.+)/i, /(?:search|find)\s+(?:celestial\s+)?(.+)/i],
    tool: '_rag_search', extractArgs: (m) => ({ query: (m[1] || '').trim() }) },
  // 시나리오 빌더 커맨드
  { patterns: [/(?:시나리오|scenario)\s*(?:시작|start|begin|만들기|새로)/i],
    tool: '_scenario_start', extractArgs: () => ({}) },
  { patterns: [/(?:시나리오|scenario)\s*(?:확인|목록|list|show|보기)/i],
    tool: '_scenario_list', extractArgs: () => ({}) },
  { patterns: [/(?:시나리오|scenario)\s*(?:실행|run|execute|시작해|돌려)/i],
    tool: '_scenario_execute', extractArgs: () => ({}) },
  { patterns: [/(?:시나리오|scenario)\s*(?:취소|clear|reset|초기화)/i],
    tool: '_scenario_clear', extractArgs: () => ({}) },
]

function parseIntent(input: string): { tool: string; args: Record<string, unknown> } | null {
  for (const rule of INTENT_RULES) {
    for (const pat of rule.patterns) {
      const m = input.match(pat)
      if (m) return { tool: rule.tool, args: rule.extractArgs(m, input) }
    }
  }
  return null
}

// ── 시스템 프롬프트 (~700 토큰) ──────────────────────────────────────────────

const SYSTEM_PROMPT = `You are an AI assistant controlling SpaceEngine, a realistic universe simulator.
You can control the simulator by returning an action plan in JSON format.
Always respond in the same language the user uses.

## Available Actions (tool_name: description)

NAVIGATION: navigate_to(target, mode?, distance_rad?, transition_time?), follow_object(target, mode?), smart_navigation(description)
CAMERA: control_camera(action, fov?, yaw?, pitch?, roll?), take_screenshot(), hi_res_screenshot()
DISPLAY: show_message(text, duration?), hide_message(), toggle_gui(visible), toggle_overlay(overlay, visible), fade_effect(action, duration?)
TIME: set_time(date?, rate?)
STATE: read_se_state(), save_state(), restore_state(), get_object_info(target?)
WORKFLOW: cinematic_sequence(steps), apply_preset(preset), timelapse_capture(target, duration_seconds), set_performance(preset), restore_defaults()
CREATION: create_star(params), create_planet(params), create_tour(title, stops)
SEARCH: search_catalog(query, obj_type?), search_object(query)
CELESTIAL RAG: Built-in celestial database (~600 objects). Users can say "성운 보여줘", "은하 추천", "블랙홀 투어", "오늘의 천체", "천체 검색 [query]" and the system handles it automatically via Intent Parser.
SCRIPT: run_script(commands), set_variable(name, value), interpolate_variable(name, start, end, duration)
SCENE: save_scene(name, description?), load_scene(name), list_scenes()
SOUND: play_sound(filename), stop_sound()
CONFIG: edit_config(section, key, value), keyboard_shortcut(keys)

## Response Format

If the user requests an action, include a JSON block:
\`\`\`json
{"actions":[{"tool":"tool_name","args":{...}}],"reply":"brief summary"}
\`\`\`

If the user asks a question or makes conversation, respond normally WITHOUT any JSON block.

## Key Rules
- navigate_to: target is celestial object name (e.g. "Mars", "Sirius", "Proxima Cen"), mode defaults to "goto"
- set_time: rate=0 stops, rate=1 normal, rate=1000 fast
- toggle_overlay: overlay names: "Orbits", "Labels", "Constellations", "Grids"
- apply_preset: "cinematic_dark", "cinematic_wide", "educational", "observation", "screenshot", "default"
- set_performance: "potato", "low", "balanced", "high", "ultra"
- Multi-step: put multiple actions in the actions array, they execute sequentially
- For cinematic: toggle_gui(false) → navigate → take_screenshot → toggle_gui(true)

## Scenario Templates (use with run_template action)
- exoplanet_tour(count): Explore N exoplanets (max 20)
- grand_voyage(exoplanet_count): Exoplanets → Solar System → Earth return
- cinematic_documentary(target): Approach + orbit + screenshot a celestial body
- size_comparison(): Moon → Earth → Jupiter → Sun → giant stars
- black_hole_tour(): Sgr A*, Cygnus X-1, M87*

For templates, use: {"actions":[{"tool":"run_template","args":{"template":"grand_voyage","params":{"exoplanet_count":10}}}],"reply":"..."}`

// ── Agent ─────────────────────────────────────────────────────────────────────

export class Agent {
  private mcpClient: McpClient
  private llm: LLMProvider
  private history: LLMMessage[] = []
  private tools: McpTool[] = []
  private toolNames: Set<string> = new Set()
  private scenarioBuilder = new ScenarioBuilder()
  private rag = new CelestialRAG()

  constructor(mcpClient: McpClient, llm: LLMProvider) {
    this.mcpClient = mcpClient
    this.llm = llm
    this.history = [{ role: 'system', content: SYSTEM_PROMPT }]
    this.rag.load().catch(err => console.warn('[Agent] RAG load failed:', err))
  }

  getScenarioBuilder(): ScenarioBuilder { return this.scenarioBuilder }

  setProvider(llm: LLMProvider): void {
    this.llm = llm
    this.clearHistory()
  }

  async loadTools(): Promise<void> {
    this.tools = await this.mcpClient.listTools()
    this.toolNames = new Set(this.tools.map(t => t.name))
  }

  // ── 메인 진입점 ───────────────────────────────────────────────────────────

  async chat(userMessage: string): Promise<ChatResult> {
    if (this.tools.length === 0) await this.loadTools()
    this.history.push({ role: 'user', content: userMessage })

    // Fast path: Intent Parser로 간단한 명령 직접 실행 (LLM 호출 안 함)
    const intent = parseIntent(userMessage)
    if (intent) {
      return this._handleIntent(intent)
    }

    // 시나리오 빌더 활성 시: "XX 추가" 패턴으로 스텝 자동 추가
    if (this.scenarioBuilder.isActive()) {
      const builderResult = this._tryAddToScenario(userMessage)
      if (builderResult) return builderResult
    }

    return this._chatWithActionPlan()
  }

  async chatStream(userMessage: string, onToken: StreamCallback): Promise<ChatResult> {
    if (this.tools.length === 0) await this.loadTools()
    this.history.push({ role: 'user', content: userMessage })

    // Fast path
    const intent = parseIntent(userMessage)
    if (intent) {
      const result = await this._handleIntent(intent)
      if (result.response) onToken(result.response)
      return result
    }

    // 시나리오 빌더 활성 시
    if (this.scenarioBuilder.isActive()) {
      const builderResult = this._tryAddToScenario(userMessage)
      if (builderResult) {
        if (builderResult.response) onToken(builderResult.response)
        return builderResult
      }
    }

    return this._chatStreamWithActionPlan(onToken)
  }

  // ── Action Plan 모드 ──────────────────────────────────────────────────────

  private async _chatWithActionPlan(): Promise<ChatResult> {
    try {
      // LLM에 tools 파라미터 없이 호출
      const resp = await this.llm.chat(this.history)
      const msg = resp.message
      if (!msg) return { response: 'LLM 응답 없음.' }

      this.history.push(msg)
      const fullText = msg.content || ''

      // 응답에서 액션 플랜 파싱
      const plan = this.parseActionPlan(fullText)

      if (!plan || plan.actions.length === 0) {
        // 순수 대화 — JSON 아티팩트 제거
        return { response: this.cleanResponse(fullText) }
      }

      // 액션 플랜 실행
      const toolCalls = await this._executePlan(plan)
      const reply = plan.reply || this.extractReplyBeforeJson(fullText)
      return { response: reply, toolCalls }
    } catch (err) {
      const errMsg = `Agent error: ${err instanceof Error ? err.message : err}`
      console.error('[Agent]', errMsg)
      return { response: errMsg, error: errMsg }
    }
  }

  private async _chatStreamWithActionPlan(onToken: StreamCallback): Promise<ChatResult> {
    try {
      const resp = await this.llm.chatStream(this.history, onToken)
      const msg = resp.message
      if (!msg) return { response: 'LLM 응답 없음.' }

      this.history.push(msg)
      const fullText = msg.content || ''

      const plan = this.parseActionPlan(fullText)

      if (!plan || plan.actions.length === 0) {
        return { response: this.cleanResponse(fullText) }
      }

      // 액션 플랜 실행
      const toolCalls = await this._executePlan(plan)
      const reply = plan.reply || this.extractReplyBeforeJson(fullText)
      return { response: reply, toolCalls }
    } catch (err) {
      const errMsg = `Agent error: ${err instanceof Error ? err.message : err}`
      console.error('[Agent]', errMsg)
      return { response: errMsg, error: errMsg }
    }
  }

  // ── Action Plan 파싱 ──────────────────────────────────────────────────────

  private parseActionPlan(text: string): ActionPlan | null {
    // Strategy 1: ```json ... ``` 펜스 블록
    const fenced = text.match(/```json\s*\n?([\s\S]*?)\n?\s*```/)
    if (fenced) {
      try {
        const parsed = JSON.parse(fenced[1])
        if (parsed.actions && Array.isArray(parsed.actions)) return parsed
      } catch { /* fall through */ }
    }

    // Strategy 2: raw {"actions":[...]} 패턴
    const raw = text.match(/\{[\s\S]*?"actions"\s*:\s*\[[\s\S]*?\][\s\S]*?\}/)
    if (raw) {
      try {
        const parsed = JSON.parse(raw[0])
        if (parsed.actions && Array.isArray(parsed.actions)) return parsed
      } catch { /* fall through */ }
    }

    return null
  }

  private cleanResponse(text: string): string {
    // JSON 블록 제거하고 순수 텍스트만 반환
    return text
      .replace(/```json[\s\S]*?```/g, '')
      .replace(/\{[\s\S]*?"actions"\s*:\s*\[[\s\S]*?\][\s\S]*?\}/g, '')
      .trim()
  }

  private extractReplyBeforeJson(text: string): string {
    // JSON 블록 이전의 텍스트 추출
    const jsonStart = text.indexOf('```json')
    if (jsonStart > 0) return text.slice(0, jsonStart).trim()
    const braceStart = text.indexOf('{"actions"')
    if (braceStart > 0) return text.slice(0, braceStart).trim()
    return text.trim()
  }

  // ── 시나리오 빌더 자동 추가 ────────────────────────────────────────────

  private _tryAddToScenario(message: string): ChatResult | null {
    // "XX 추가" / "add XX" / 단순 천체 이름 패턴
    const addMatch = message.match(/(.+?)(?:\s*추가|add\s+(.+))/i)
    const target = addMatch ? (addMatch[1] || addMatch[2]).trim() : null

    if (!target) return null

    // 특수 스텝: 스크린샷, 대기 등
    if (/스크린샷|screenshot|캡처/i.test(target)) {
      this.scenarioBuilder.addStep({ action: 'screenshot' })
    } else if (/대기|wait|(\d+)\s*초/i.test(target)) {
      const sec = parseInt(target.match(/(\d+)/)?.[1] || '3')
      this.scenarioBuilder.addStep({ action: 'wait', value: sec })
    } else if (/메시지|message/i.test(target)) {
      const text = target.replace(/메시지|message/i, '').trim() || '...'
      this.scenarioBuilder.addStep({ action: 'message', text, value: 3 })
    } else {
      // 천체 이동으로 간주
      this.scenarioBuilder.addStep({ action: 'navigate', target, distance_rad: 5.0, transition_time: 4 })
    }

    const summary = this.scenarioBuilder.summarize()
    const msg = `추가됨! 현재 시나리오:\n${summary}\n\n"시나리오 실행"으로 실행하거나 계속 추가하세요.`
    this.history.push({ role: 'assistant', content: msg })
    return { response: msg }
  }

  // ── Intent 핸들링 (Fast Path) ──────────────────────────────────────────

  private async _handleIntent(intent: { tool: string; args: Record<string, unknown> }): Promise<ChatResult> {
    // 시나리오 템플릿 실행
    if (intent.tool === '_template') {
      const templateName = String(intent.args.template || '')
      const template = SCENARIO_TEMPLATES[templateName]
      if (!template) {
        const msg = `알 수 없는 템플릿: ${templateName}`
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg, error: msg }
      }
      const params = (intent.args.params as Record<string, unknown>) || {}
      const steps = template.generate(params)
      const exec = await this._executeToolDirect('cinematic_sequence', { steps, auto_hide_gui: true })
      const summary = exec.status === 'ok'
        ? `**${template.name}** 시나리오 실행 완료 (${steps.length}단계).`
        : `**${template.name}** 실패: ${(exec.result as any)?.message || 'error'}`
      this.history.push({ role: 'assistant', content: summary })
      return { response: summary, toolCalls: [{ name: `template:${templateName}`, arguments: params, result: exec.result, status: exec.status }] }
    }

    // 시나리오 빌더 커맨드
    if (intent.tool === '_scenario_start') {
      this.scenarioBuilder.clear()
      const msg = '시나리오 빌더를 시작합니다. 원하는 동작을 하나씩 말씀해주세요.\n예: "화성 추가", "토성 추가", "스크린샷 추가"\n완료되면 "시나리오 실행"이라고 말씀해주세요.'
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }
    if (intent.tool === '_scenario_list') {
      const msg = this.scenarioBuilder.summarize()
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }
    if (intent.tool === '_scenario_execute') {
      if (!this.scenarioBuilder.isActive()) {
        const msg = '시나리오가 비어있습니다. "시나리오 시작"으로 먼저 만들어주세요.'
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const cinematicArgs = this.scenarioBuilder.toCinematicArgs()
      const stepCount = this.scenarioBuilder.getStepCount()
      const exec = await this._executeToolDirect('cinematic_sequence', cinematicArgs)
      this.scenarioBuilder.clear()
      const summary = exec.status === 'ok'
        ? `시나리오 실행 완료! (${stepCount}단계)`
        : `시나리오 실패: ${(exec.result as any)?.message || 'error'}`
      this.history.push({ role: 'assistant', content: summary })
      return { response: summary, toolCalls: [exec] }
    }
    if (intent.tool === '_scenario_clear') {
      this.scenarioBuilder.clear()
      const msg = '시나리오를 초기화했습니다.'
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }

    // RAG: 천체 추천
    if (intent.tool === '_rag_recommend') {
      const category = String(intent.args.category || 'all')
      const count = Number(intent.args.count) || 5
      const items = category === 'all'
        ? this.rag.recommend('all', count)
        : this.rag.recommend(category, count)
      if (items.length === 0) {
        const msg = `"${category}" 카테고리에 해당하는 천체를 찾을 수 없습니다.`
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const list = items.map((obj, i) =>
        `${i + 1}. **${obj.name}** — ${obj.description} ${'★'.repeat(obj.rating)}`
      ).join('\n')
      const msg = `추천 천체 (${category}):\n${list}\n\n번호를 말하면 이동합니다. (예: "1번으로 가줘")`
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }

    // RAG: 번호 선택 → 이동
    if (intent.tool === '_rag_select') {
      const index = Number(intent.args.index)
      const obj = this.rag.getRecommendation(index)
      if (!obj) {
        const msg = `${index}번 항목이 없습니다. 먼저 천체를 추천받아주세요.`
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const exec = await this._executeToolDirect('navigate_to', {
        target: obj.se_name, mode: 'goto', distance_rad: 3.0
      })
      const summary = exec.status === 'ok'
        ? `**${obj.name}**(으)로 이동합니다. ${obj.description}`
        : `이동 실패: ${(exec.result as any)?.message || 'error'}`
      this.history.push({ role: 'assistant', content: summary })
      return { response: summary, toolCalls: [exec] }
    }

    // RAG: 카테고리 투어
    if (intent.tool === '_rag_tour') {
      const category = String(intent.args.category || 'nebula')
      const count = Number(intent.args.count) || 5
      const steps = this.rag.generateTour(category, count)
      if (steps.length === 0) {
        const msg = `"${category}" 투어를 생성할 수 없습니다.`
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const exec = await this._executeToolDirect('cinematic_sequence', {
        steps, auto_hide_gui: true
      })
      const names = steps.map(s => s.message?.split(':')[0] || s.target).join(' → ')
      const summary = exec.status === 'ok'
        ? `**${category} 투어** 실행 완료 (${steps.length}곳): ${names}`
        : `투어 실패: ${(exec.result as any)?.message || 'error'}`
      this.history.push({ role: 'assistant', content: summary })
      return { response: summary, toolCalls: [exec] }
    }

    // RAG: 오늘의 천체
    if (intent.tool === '_rag_daily') {
      const obj = this.rag.dailyPick()
      if (!obj) {
        const msg = 'RAG 데이터가 로드되지 않았습니다.'
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const msg = `오늘의 천체: **${obj.name}** ${'★'.repeat(obj.rating)}\n${obj.description}\n카테고리: ${obj.category} | 태그: ${obj.tags.join(', ')}\n\n"1번으로 가줘"로 이동할 수 있습니다.`
      this.rag.recommend(obj.category, 1) // set lastRecommendations
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }

    // RAG: 천체 검색
    if (intent.tool === '_rag_search') {
      const query = String(intent.args.query || '')
      const items = this.rag.search(query, 5)
      if (items.length === 0) {
        const msg = `"${query}" 검색 결과가 없습니다.`
        this.history.push({ role: 'assistant', content: msg })
        return { response: msg }
      }
      const list = items.map((obj, i) =>
        `${i + 1}. **${obj.name}** [${obj.category}] — ${obj.description}`
      ).join('\n')
      const msg = `검색 결과 "${query}":\n${list}\n\n번호를 말하면 이동합니다.`
      this.history.push({ role: 'assistant', content: msg })
      return { response: msg }
    }

    // 일반 도구 실행
    const exec = await this._executeToolDirect(intent.tool, intent.args)
    const summary = exec.status === 'ok'
      ? `**${intent.tool}** 실행 완료.`
      : `**${intent.tool}** 실패: ${(exec.result as any)?.message || 'error'}`
    this.history.push({ role: 'assistant', content: summary })
    return { response: summary, toolCalls: [exec] }
  }

  // ── 액션 플랜 실행 ───────────────────────────────────────────────────────

  private async _executePlan(plan: ActionPlan): Promise<ToolExecution[]> {
    const results: ToolExecution[] = []
    for (const action of plan.actions) {
      const args = (typeof action.args === 'object' && action.args !== null) ? action.args : {}

      // 특수 액션: 시나리오 템플릿 실행
      if (action.tool === 'run_template') {
        const templateName = String(args.template || '')
        const template = SCENARIO_TEMPLATES[templateName]
        if (!template) {
          results.push({ name: 'run_template', arguments: args, result: { error: `알 수 없는 템플릿: ${templateName}` }, status: 'error' })
          continue
        }
        const params = (args.params as Record<string, unknown>) || {}
        const steps = template.generate(params)
        // cinematic_sequence로 실행
        const exec = await this._executeToolDirect('cinematic_sequence', { steps, auto_hide_gui: true })
        results.push({ name: `run_template(${templateName})`, arguments: params, result: exec.result, status: exec.status })
        continue
      }

      // 특수 액션: 시나리오 빌더 제어
      if (action.tool === 'scenario_add') {
        this.scenarioBuilder.addStep(args as any)
        results.push({ name: 'scenario_add', arguments: args, result: { added: true, total: this.scenarioBuilder.getStepCount() }, status: 'ok' })
        continue
      }
      if (action.tool === 'scenario_execute') {
        if (!this.scenarioBuilder.isActive()) {
          results.push({ name: 'scenario_execute', arguments: {}, result: { error: '시나리오가 비어있습니다' }, status: 'error' })
          continue
        }
        const cinematicArgs = this.scenarioBuilder.toCinematicArgs()
        const exec = await this._executeToolDirect('cinematic_sequence', cinematicArgs)
        this.scenarioBuilder.clear()
        results.push({ name: 'scenario_execute', arguments: cinematicArgs, result: exec.result, status: exec.status })
        continue
      }

      // 일반 도구 실행
      if (!this.toolNames.has(action.tool)) {
        results.push({ name: action.tool, arguments: args, result: { error: `알 수 없는 도구: ${action.tool}` }, status: 'error' })
        continue
      }
      const exec = await this._executeToolDirect(action.tool, args)
      results.push(exec)
    }
    return results
  }

  // ── Tool 실행 ──────────────────────────────────────────────────────────────

  private async _executeToolDirect(name: string, args: Record<string, unknown>): Promise<ToolExecution> {
    const result = await this.mcpClient.executeTool(name, args)
    const inner = result.result as any
    const isOk = result.status === 'ok' && inner?.status !== 'error'
    return {
      name,
      arguments: args,
      result: result.result ?? result,
      status: isOk ? 'ok' : 'error',
    }
  }

  // ── History 관리 ─────────────────────────────────────────────────────────

  trimHistory(max = 30): void {
    if (this.history.length > max) {
      this.history = [this.history[0], ...this.history.slice(-(max - 1))]
    }
  }

  clearHistory(): void {
    this.history = [{ role: 'system', content: SYSTEM_PROMPT }]
  }

  getToolCount(): number { return this.tools.length }
  getProviderName(): string { return this.llm.name }
}
