import React, { useState, useEffect } from 'react'
import { useToastStore } from './Toast'

interface Props {
  onClose: () => void
}

export function LLMSettings({ onClose }: Props) {
  const [provider, setProvider] = useState('groq')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  const [models, setModels] = useState<string[]>([])
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const { addToast } = useToastStore()

  useEffect(() => {
    window.api.llmGetProvider().then((p: any) => {
      setProvider(p.type)
      setModel(p.model)
    })
  }, [])

  // Provider 전환 시 기본 모델로 리셋 + 모델 목록 로드
  useEffect(() => {
    const defaults: Record<string, string> = {
      ollama: 'exaone3.5:7.8b',
      groq: 'llama-3.3-70b-versatile',
      gemini: 'gemini-2.0-flash',
    }
    setModel(defaults[provider] || '')
    window.api.llmListModels(provider).then((res) => {
      if (res.status === 'ok') setModels(res.models)
      else setModels([])
    })
  }, [provider])

  const handleTest = async () => {
    setTesting(true)
    setStatus('')
    try {
      const result = await window.api.llmTestConnection(provider, {
        apiKey: provider !== 'ollama' ? apiKey : undefined,
        model: model || undefined,
      })
      if (result.status === 'ok') {
        setStatus(`테스트 성공: ${result.message}`)
        addToast('연결 테스트 성공', 'success')
      } else {
        setStatus(`테스트 실패: ${result.message}`)
        addToast('연결 테스트 실패', 'error')
      }
    } catch (err) {
      setStatus(`오류: ${err}`)
    } finally {
      setTesting(false)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    setStatus('')
    try {
      const result = await window.api.llmSetProvider(provider, {
        apiKey: provider !== 'ollama' ? apiKey : undefined,
        model: model || undefined,
      })
      if (result.status === 'ok') {
        setStatus(`연결됨: ${result.provider} (${result.model}) — 툴 콜링: ${result.supportsToolCalling ? '지원' : '미지원'}`)
        addToast(`${result.provider} 연결 완료`, 'success')
      } else {
        setStatus(`오류: ${result.message}`)
        addToast('연결 실패', 'error')
      }
    } catch (err) {
      setStatus(`오류: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-[480px] bg-gray-800 rounded-xl border border-gray-600 shadow-2xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold text-white">LLM 설정</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">&times;</button>
        </div>

        <div className="p-4 space-y-4">
          {/* Provider 선택 */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">제공자</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'ollama', label: 'Ollama (로컬)', desc: 'API 키 불필요, 툴콜 미지원' },
                { id: 'groq', label: 'Groq (무료)', desc: '무료·빠름·툴콜 지원!' },
                { id: 'gemini', label: 'Gemini (무료)', desc: '무료 250회/일' },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={`p-2 rounded-lg border text-left text-xs transition-colors ${
                    provider === p.id
                      ? 'border-blue-500 bg-blue-500/10 text-blue-300'
                      : 'border-gray-600 hover:border-gray-500 text-gray-400'
                  }`}
                >
                  <div className="font-medium">{p.label}</div>
                  <div className="text-[10px] mt-0.5 opacity-70">{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* API Key (Groq/Gemini만) */}
          {provider !== 'ollama' && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                API 키 ({provider === 'groq' ? 'console.groq.com' : 'aistudio.google.com'})
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={`${provider} API 키 입력...`}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-[10px] text-gray-500 mt-1">
                {provider === 'groq'
                  ? '무료: console.groq.com → API Keys (카드 불필요)'
                  : '무료: aistudio.google.com → Get API Key'}
              </p>
            </div>
          )}

          {/* 모델 선택 */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">모델</label>
            {models.length > 0 ? (
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              >
                {models.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="모델 이름 입력..."
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
          </div>

          {/* 버튼 */}
          <div className="flex gap-2">
            <button
              onClick={handleTest}
              disabled={testing || (provider !== 'ollama' && !apiKey)}
              className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              {testing ? '테스트 중...' : '연결 테스트'}
            </button>
            <button
              onClick={handleConnect}
              disabled={loading || (provider !== 'ollama' && !apiKey)}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? '연결 중...' : '연결 및 저장'}
            </button>
          </div>

          {/* 상태 */}
          {status && (
            <div className={`text-xs p-2 rounded-lg ${status.startsWith('오류') || status.startsWith('테스트 실패') ? 'bg-red-900/30 text-red-300' : 'bg-green-900/30 text-green-300'}`}>
              {status}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
