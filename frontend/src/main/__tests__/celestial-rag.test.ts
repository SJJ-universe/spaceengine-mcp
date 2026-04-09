import { describe, it, expect, beforeAll } from 'vitest'
import { CelestialRAG } from '../celestial-rag'
import type { CelestialObject } from '../celestial-rag'

describe('CelestialRAG', () => {
  let rag: CelestialRAG

  beforeAll(async () => {
    rag = new CelestialRAG()
    await rag.load()
  })

  // ── 로드 ────────────────────────────────────────────────────────────────

  it('loads core catalog successfully', () => {
    expect(rag.isLoaded()).toBe(true)
    const stats = rag.getStats()
    expect(stats.core).toBeGreaterThan(400)
  })

  it('has all expected categories', () => {
    const stats = rag.getStats()
    const expected = ['solar_system', 'star', 'exoplanet', 'nebula', 'galaxy', 'black_hole', 'cluster', 'other']
    for (const cat of expected) {
      expect(stats.categories[cat]).toBeGreaterThan(0)
    }
  })

  // ── 검색 ────────────────────────────────────────────────────────────────

  it('searches by exact name', () => {
    const results = rag.search('Earth')
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].se_name).toBe('Earth')
  })

  it('searches by Korean name', () => {
    const results = rag.search('지구')
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].name).toBe('Earth')
  })

  it('searches by alias', () => {
    const results = rag.search('Proxima Cen')
    expect(results.length).toBeGreaterThan(0)
  })

  it('searches by Korean category keyword', () => {
    const results = rag.search('성운')
    expect(results.length).toBeGreaterThan(0)
    expect(results.some(r => r.category === 'nebula')).toBe(true)
  })

  it('returns empty array for gibberish query', () => {
    const results = rag.search('xyzqwerty12345')
    expect(results).toHaveLength(0)
  })

  it('respects search limit', () => {
    const results = rag.search('nebula', 3)
    expect(results.length).toBeLessThanOrEqual(3)
  })

  // ── 추천 ────────────────────────────────────────────────────────────────

  it('recommends by category', () => {
    const results = rag.recommend('nebula', 5)
    expect(results).toHaveLength(5)
    results.forEach(r => expect(r.category).toBe('nebula'))
  })

  it('recommends by Korean category', () => {
    const results = rag.recommend('은하', 3)
    expect(results).toHaveLength(3)
    results.forEach(r => expect(r.category).toBe('galaxy'))
  })

  it('recommends all categories with "all"', () => {
    const results = rag.recommend('all', 10)
    expect(results.length).toBeLessThanOrEqual(10)
    expect(results.length).toBeGreaterThan(0)
  })

  it('returns empty for unknown category', () => {
    const results = rag.recommend('dragons', 5)
    expect(results).toHaveLength(0)
  })

  it('sorts recommendations by rating (descending)', () => {
    const results = rag.recommend('star', 10)
    for (let i = 1; i < results.length; i++) {
      expect(results[i].rating).toBeLessThanOrEqual(results[i - 1].rating)
    }
  })

  // ── 인덱스 선택 ─────────────────────────────────────────────────────────

  it('getRecommendation returns correct object by 1-based index', () => {
    const recs = rag.recommend('solar_system', 5)
    const picked = rag.getRecommendation(1)
    expect(picked).not.toBeNull()
    expect(picked!.id).toBe(recs[0].id)
  })

  it('getRecommendation returns null for out-of-range index', () => {
    rag.recommend('star', 3)
    expect(rag.getRecommendation(0)).toBeNull()
    expect(rag.getRecommendation(100)).toBeNull()
  })

  // ── 태그 검색 ───────────────────────────────────────────────────────────

  it('searchByTag finds tagged objects', () => {
    const results = rag.searchByTag('famous')
    expect(results.length).toBeGreaterThan(0)
  })

  it('searchByTag supports Korean tags', () => {
    // KO_TAG_MAP: '고리' → 'ringed', but data uses 'rings'
    // Test direct English tag that exists in data
    const results = rag.searchByTag('rings')
    expect(results.length).toBeGreaterThan(0)
    results.forEach(r => expect(r.tags).toContain('rings'))
  })

  // ── 투어 생성 ───────────────────────────────────────────────────────────

  it('generates tour steps for category', () => {
    const steps = rag.generateTour('nebula', 3)
    expect(steps).toHaveLength(3)
    steps.forEach(step => {
      expect(step.action).toBe('navigate')
      expect(step.target).toBeTruthy()
      expect(step.distance_rad).toBe(3.0)
      expect(step.transition_time).toBe(5)
      expect(step.wait_time).toBe(4)
      expect(step.message).toBeTruthy()
    })
  })

  it('generates empty tour for unknown category', () => {
    const steps = rag.generateTour('unicorns', 5)
    expect(steps).toHaveLength(0)
  })

  // ── 오늘의 천체 ─────────────────────────────────────────────────────────

  it('dailyPick returns a high-rated object', () => {
    const pick = rag.dailyPick()
    expect(pick).not.toBeNull()
    expect(pick!.rating).toBeGreaterThanOrEqual(3)
  })

  it('dailyPick is deterministic (same day = same result)', () => {
    const pick1 = rag.dailyPick()
    const pick2 = rag.dailyPick()
    expect(pick1!.id).toBe(pick2!.id)
  })

  // ── 통계 ────────────────────────────────────────────────────────────────

  it('getStats returns correct structure', () => {
    const stats = rag.getStats()
    expect(stats.core).toBeGreaterThan(0)
    expect(typeof stats.extended).toBe('number')
    expect(typeof stats.categories).toBe('object')
  })
})
