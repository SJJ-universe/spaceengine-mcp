import React, { useEffect, useState } from 'react'
import { ChatView } from './components/ChatView'
import { SEStatusBar } from './components/SEStatusBar'
import { QuickActions } from './components/QuickActions'
import { SEStatePanel } from './components/SEStatePanel'
import { CommandPalette } from './components/CommandPalette'
import { LLMSettings } from './components/LLMSettings'
import { SessionList } from './components/SessionList'
import { ToastContainer } from './components/Toast'
import { useSEStore } from './stores/se-store'
import { useChatStore } from './stores/chat-store'

export default function App() {
  const { setMcpStatus, setLlmStatus } = useSEStore()
  const { loadSessions } = useChatStore()
  const [rightPanelOpen, setRightPanelOpen] = useState(true)
  const [llmSettingsOpen, setLlmSettingsOpen] = useState(false)

  useEffect(() => {
    loadSessions()
    const checkStatus = async () => {
      try {
        const health = await window.api.mcpHealth()
        setMcpStatus(!!health, health?.version, health?.tools_count)
      } catch {
        setMcpStatus(false)
      }
      try {
        const llm = await window.api.llmStatus()
        setLlmStatus(llm.connected, llm.provider)
      } catch {
        setLlmStatus(false)
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [setMcpStatus, setLlmStatus])

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      <SEStatusBar
        onToggleRight={() => setRightPanelOpen((p) => !p)}
        onOpenLLMSettings={() => setLlmSettingsOpen(true)}
      />

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-60 bg-gray-800 border-r border-gray-700 overflow-y-auto flex-shrink-0">
          <SessionList />
          <div className="border-t border-gray-700" />
          <QuickActions />
        </aside>

        <main className="flex-1 flex flex-col min-w-0">
          <ChatView />
        </main>

        {rightPanelOpen && (
          <aside className="w-72 bg-gray-800 border-l border-gray-700 overflow-y-auto flex-shrink-0">
            <SEStatePanel />
          </aside>
        )}
      </div>

      <CommandPalette />
      <ToastContainer />
      {llmSettingsOpen && <LLMSettings onClose={() => setLlmSettingsOpen(false)} />}
    </div>
  )
}
