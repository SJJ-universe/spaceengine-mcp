/**
 * CelestialRAG — 천체 카탈로그 검색, 추천, 투어 생성
 *
 * 3계층 카탈로그 구조:
 * - Core (~600): 주요 천체 (별, 행성, 성운, 은하 등)
 * - Extended (~19K): 확장 카탈로그 (미구현, 향후 추가)
 *
 * 검색 알고리즘: 토큰 기반 점수 매칭 (외부 의존성 없음)
 * - 이름 정확 매치: 10점, 별칭 매치: 8점, 태그 매치: 5점
 * - 설명 매치: 2점, 카테고리 매치: 3점
 * - rating 가중치: score * (1 + rating * 0.1)
 */

// ── 인터페이스 ────────────────────────────────────────────────────────────────

export interface CelestialObject {
  id: string
  name: string
  se_name: string        // SpaceEngine Select 명령에 사용되는 정확한 이름
  aliases: string[]      // 대체 이름 (한국어, 카탈로그 번호 등)
  category: 'solar_system' | 'star' | 'exoplanet' | 'nebula' | 'galaxy' | 'black_hole' | 'cluster' | 'other'
  subcategory: string    // 예: 'planet', 'moon', 'red_supergiant', 'globular', 'comet'
  parent: string | null  // 부모 천체
  tags: string[]         // 검색 가능한 태그
  description: string    // 한국어 간략 설명
  rating: number         // 1-5 시각적 인상 점수
}

export interface TourStep {
  target: string         // 천체의 se_name
  action: 'navigate'
  distance_rad?: number
  transition_time?: number
  wait_time?: number
  message?: string       // 천체 설명
}

// ── 한국어 매핑 ───────────────────────────────────────────────────────────────

/** 한국어 → 카테고리/서브카테고리 매핑 */
const KO_CATEGORY_MAP: Record<string, string> = {
  '성운': 'nebula',
  '은하': 'galaxy',
  '행성': 'planet',
  '별': 'star',
  '항성': 'star',
  '성단': 'cluster',
  '블랙홀': 'black_hole',
  '외계행성': 'exoplanet',
  '혜성': 'comet',
  '위성': 'moon',
  '소행성': 'asteroid',
  '왜소행성': 'dwarf_planet',
  '초신성': 'supernova',
  '펄서': 'pulsar',
  '태양계': 'solar_system',
}

/** 한국어 → 태그 매핑 */
const KO_TAG_MAP: Record<string, string> = {
  '거대': 'giant',
  '거성': 'supergiant',
  '왜성': 'dwarf',
  '고리': 'rings',
  '생명': 'habitable',
  '아름다운': 'beautiful',
  '유명한': 'famous',
  '가까운': 'nearby',
}

// ── CelestialRAG 클래스 ──────────────────────────────────────────────────────

export class CelestialRAG {
  private core: CelestialObject[] = []
  private extended: CelestialObject[] = []
  private searchIndex: Map<string, CelestialObject[]> = new Map()
  private loaded = false
  private lastRecommendations: CelestialObject[] = []

  // ── 카탈로그 로드 ─────────────────────────────────────────────────────────

  /**
   * 카탈로그 데이터를 로드하고 검색 인덱스를 구축한다.
   * 초기화 시 한 번만 호출.
   */
  async load(): Promise<void> {
    if (this.loaded) return

    // Core 카탈로그 로드
    try {
      const coreData = await import('./data/celestial-core.json')
      // ESM default export 또는 직접 배열 모두 처리
      this.core = (coreData.default ?? coreData) as CelestialObject[]
    } catch (err) {
      console.warn('[CelestialRAG] celestial-core.json 로드 실패, 빈 카탈로그로 동작:', err)
      this.core = []
    }

    // Extended 카탈로그 로드 (아직 존재하지 않을 수 있음)
    try {
      const extData = await import('./data/celestial-extended.json')
      this.extended = (extData.default ?? extData) as CelestialObject[]
    } catch {
      // Extended 카탈로그가 없으면 무시 — 향후 추가 예정
      this.extended = []
    }

    this.buildIndex()
    this.loaded = true
    console.log(
      `[CelestialRAG] 로드 완료: core=${this.core.length}, extended=${this.extended.length}`
    )
  }

  /**
   * 모든 천체에 대해 검색 인덱스를 구축한다.
   * 이름, 별칭, 태그, 설명, 카테고리, 서브카테고리를 토큰화하여 역인덱스 생성.
   */
  private buildIndex(): void {
    this.searchIndex.clear()
    const allObjects = [...this.core, ...this.extended]

    for (const obj of allObjects) {
      const tokens = new Set<string>()

      // 이름 토큰화
      this.tokenize(obj.name).forEach(t => tokens.add(t))
      this.tokenize(obj.se_name).forEach(t => tokens.add(t))

      // 별칭 토큰화 (Extended 카탈로그에는 aliases가 없을 수 있음)
      if (obj.aliases) {
        for (const alias of obj.aliases) {
          this.tokenize(alias).forEach(t => tokens.add(t))
        }
      }

      // 태그 토큰화
      if (obj.tags) {
        for (const tag of obj.tags) {
          tokens.add(tag.toLowerCase())
        }
      }

      // 설명 토큰화
      if (obj.description) {
        this.tokenize(obj.description).forEach(t => tokens.add(t))
      }

      // 카테고리/서브카테고리 추가
      tokens.add(obj.category.toLowerCase())
      if (obj.subcategory) tokens.add(obj.subcategory.toLowerCase())

      // 인덱스에 추가
      for (const token of tokens) {
        if (token.length < 1) continue
        const list = this.searchIndex.get(token)
        if (list) {
          list.push(obj)
        } else {
          this.searchIndex.set(token, [obj])
        }
      }
    }
  }

  /**
   * 문자열을 소문자 토큰 배열로 분할한다.
   * 영문, 숫자, 한글 모두 처리.
   */
  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .split(/[\s,.\-_|/()]+/)
      .filter(t => t.length > 0)
  }

  // ── 검색 ──────────────────────────────────────────────────────────────────

  /**
   * 전체 텍스트 검색 — 이름, 별칭, 태그, 설명 전부 검색.
   * 점수 기반으로 정렬하여 상위 N개 반환.
   */
  search(query: string, limit = 10): CelestialObject[] {
    if (!this.loaded || query.trim().length === 0) return []

    const allObjects = [...this.core, ...this.extended]
    const scores = new Map<string, number>()

    // 한국어 → 영어 매핑 적용
    const expandedQuery = this.expandKoreanQuery(query)
    const queryTokens = this.tokenize(expandedQuery)
    const queryLower = query.toLowerCase().trim()

    for (const obj of allObjects) {
      let score = 0

      // 1. 이름 정확 매치 (10점)
      if (obj.name.toLowerCase() === queryLower || obj.se_name.toLowerCase() === queryLower) {
        score += 10
      }

      // 2. 별칭 정확 매치 (8점)
      if (obj.aliases) {
        for (const alias of obj.aliases) {
          if (alias.toLowerCase() === queryLower) {
            score += 8
            break
          }
        }
      }

      // 토큰 기반 점수
      for (const token of queryTokens) {
        // 이름 부분 매치
        if (obj.name.toLowerCase().includes(token) || obj.se_name.toLowerCase().includes(token)) {
          score += 6
        }

        // 별칭 부분 매치
        if (obj.aliases) {
          for (const alias of obj.aliases) {
            if (alias.toLowerCase().includes(token)) {
              score += 4
              break
            }
          }
        }

        // 태그 매치 (5점)
        if (obj.tags?.some(t => t.toLowerCase() === token)) {
          score += 5
        }

        // 카테고리 매치 (3점)
        if (obj.category === token || obj.subcategory === token) {
          score += 3
        }

        // 설명 매치 (2점)
        if (obj.description?.toLowerCase().includes(token)) {
          score += 2
        }
      }

      // rating 가중치 적용
      if (score > 0) {
        score *= (1 + (obj.rating ?? 0) * 0.1)
        scores.set(obj.id, score)
      }
    }

    // 점수 기준 정렬
    return allObjects
      .filter(obj => (scores.get(obj.id) ?? 0) > 0)
      .sort((a, b) => (scores.get(b.id) ?? 0) - (scores.get(a.id) ?? 0))
      .slice(0, limit)
  }

  /**
   * 한국어 검색어를 영어 카테고리/태그로 확장한다.
   * 예: "아름다운 성운" → "아름다운 성운 beautiful nebula"
   */
  private expandKoreanQuery(query: string): string {
    const parts = [query]

    for (const [ko, en] of Object.entries(KO_CATEGORY_MAP)) {
      if (query.includes(ko)) {
        parts.push(en)
      }
    }

    for (const [ko, en] of Object.entries(KO_TAG_MAP)) {
      if (query.includes(ko)) {
        parts.push(en)
      }
    }

    return parts.join(' ')
  }

  // ── 카테고리 추천 ─────────────────────────────────────────────────────────

  /**
   * 카테고리 기반 추천.
   * 해당 카테고리에서 랜덤 선택 후 rating 높은 순으로 정렬.
   * 한국어 카테고리명도 지원 (예: "성운" → nebula).
   */
  recommend(category: string, count = 5): CelestialObject[] {
    if (!this.loaded) return []

    // 한국어 → 영어 카테고리 변환
    const resolvedCategory = KO_CATEGORY_MAP[category] ?? category.toLowerCase()
    const allObjects = [...this.core, ...this.extended]

    // 'all' — 전체 카테고리에서 랜덤 추천
    if (resolvedCategory === 'all') {
      const shuffled = this.shuffle([...allObjects])
      shuffled.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
      const result = shuffled.slice(0, count)
      this.lastRecommendations = result
      return result
    }

    // 카테고리 또는 서브카테고리 매칭
    const candidates = allObjects.filter(
      obj => obj.category === resolvedCategory || obj.subcategory === resolvedCategory
    )

    if (candidates.length === 0) return []

    // 셔플 후 rating 기준 상위 선택
    const shuffled = this.shuffle([...candidates])
    const selected = shuffled.slice(0, Math.max(count * 2, candidates.length))
    selected.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
    const result = selected.slice(0, count)

    // 마지막 추천 결과 저장 (인덱스 기반 접근용)
    this.lastRecommendations = result
    return result
  }

  // ── 태그 검색 ─────────────────────────────────────────────────────────────

  /**
   * 태그 기반 검색 (예: "habitable", "supergiant", "ringed").
   * 한국어 태그도 지원 (예: "고리" → ringed).
   */
  searchByTag(tag: string, limit = 10): CelestialObject[] {
    if (!this.loaded) return []

    // 한국어 → 영어 태그 변환
    const resolvedTag = KO_TAG_MAP[tag] ?? tag.toLowerCase()
    const allObjects = [...this.core, ...this.extended]

    return allObjects
      .filter(obj => obj.tags?.some(t => t.toLowerCase() === resolvedTag))
      .sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
      .slice(0, limit)
  }

  // ── 추천 인덱스 접근 ──────────────────────────────────────────────────────

  /**
   * 마지막 추천 결과에서 인덱스로 천체를 가져온다.
   * "3번으로 가줘" 같은 사용자 요청 처리용.
   * @param index 1-based 인덱스
   */
  getRecommendation(index: number): CelestialObject | null {
    // 1-based → 0-based 변환
    const zeroIndex = index - 1
    if (zeroIndex < 0 || zeroIndex >= this.lastRecommendations.length) return null
    return this.lastRecommendations[zeroIndex]
  }

  /**
   * 마지막 추천 결과 목록 반환.
   */
  getLastRecommendations(): CelestialObject[] {
    return [...this.lastRecommendations]
  }

  // ── 투어 생성 ─────────────────────────────────────────────────────────────

  /**
   * cinematic_sequence 도구용 투어 스텝을 생성한다.
   * 카테고리에서 rating 높은 천체를 선택하여 순차 탐방 경로를 만든다.
   */
  generateTour(category: string, count = 5): TourStep[] {
    const objects = this.recommend(category, count)
    if (objects.length === 0) return []

    const steps: TourStep[] = []

    for (const obj of objects) {
      steps.push({
        target: obj.se_name,
        action: 'navigate',
        distance_rad: 3.0,
        transition_time: 5,
        wait_time: 4,
        message: `${obj.name}: ${obj.description}`,
      })
    }

    return steps
  }

  // ── 오늘의 천체 ───────────────────────────────────────────────────────────

  /**
   * "오늘의 천체" — 날짜 기반 시드로 매일 다른 천체를 추천.
   * 같은 날에는 항상 같은 결과를 반환한다.
   */
  dailyPick(): CelestialObject | null {
    if (!this.loaded || this.core.length === 0) return null

    // 날짜를 시드로 사용 (YYYYMMDD)
    const now = new Date()
    const seed = now.getFullYear() * 10000 + (now.getMonth() + 1) * 100 + now.getDate()

    // rating 3 이상인 천체만 후보로 (시각적으로 인상적인 것)
    const candidates = this.core.filter(obj => (obj.rating ?? 0) >= 3)
    if (candidates.length === 0) return this.core[0]

    // 시드 기반 인덱스 선택 (간단한 해싱)
    const index = this.simpleHash(seed) % candidates.length
    return candidates[index]
  }

  /**
   * 간단한 정수 해싱 (날짜 시드용).
   * 외부 라이브러리 없이 충분히 균일한 분포를 제공한다.
   */
  private simpleHash(n: number): number {
    let h = n
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = (h >> 16) ^ h
    return Math.abs(h)
  }

  // ── 통계 ──────────────────────────────────────────────────────────────────

  /**
   * 카탈로그 통계 반환.
   */
  getStats(): { core: number; extended: number; categories: Record<string, number> } {
    const categories: Record<string, number> = {}
    const allObjects = [...this.core, ...this.extended]

    for (const obj of allObjects) {
      categories[obj.category] = (categories[obj.category] ?? 0) + 1
    }

    return {
      core: this.core.length,
      extended: this.extended.length,
      categories,
    }
  }

  /**
   * 로드 완료 여부.
   */
  isLoaded(): boolean {
    return this.loaded
  }

  // ── 유틸리티 ──────────────────────────────────────────────────────────────

  /**
   * Fisher-Yates 셔플 (in-place).
   */
  private shuffle<T>(arr: T[]): T[] {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[arr[i], arr[j]] = [arr[j], arr[i]]
    }
    return arr
  }
}
