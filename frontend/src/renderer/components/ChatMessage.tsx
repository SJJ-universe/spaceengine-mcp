import React, { useState, useEffect } from 'react'
import Markdown from 'react-markdown'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import json from 'highlight.js/lib/languages/json'
import bash from 'highlight.js/lib/languages/bash'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import 'highlight.js/styles/github-dark.css'
import type { ChatMessage as ChatMessageType } from '../stores/chat-store'
import { useToastStore } from './Toast'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('json', json)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)

interface Props {
  message: ChatMessageType
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)
  const { addToast } = useToastStore()

  const handleCopy = async () => {
    const text = message.error || message.content
    await navigator.clipboard.writeText(text)
    setCopied(true)
    addToast('클립보드에 복사됨', 'success')
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      <div
        className={`relative max-w-[75%] rounded-xl px-4 py-2.5 text-sm leading-relaxed
          ${isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : message.error
              ? 'bg-red-900/50 text-red-200 border border-red-700 rounded-bl-sm'
              : 'bg-gray-700 text-gray-100 rounded-bl-sm'
          }`}
      >
        {/* 복사 버튼 */}
        <button
          onClick={handleCopy}
          className={`absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100
            p-1 rounded text-[10px] transition-all
            ${isUser ? 'hover:bg-blue-500 text-blue-200' : 'hover:bg-gray-600 text-gray-400'}`}
          title="복사"
        >
          {copied ? '✓' : '📋'}
        </button>

        {message.error ? (
          <div className="flex items-start gap-2">
            <span className="text-red-400 mt-0.5">!</span>
            <span>{message.error}</span>
          </div>
        ) : isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none
            prose-p:my-1 prose-pre:bg-gray-800 prose-pre:text-xs
            prose-code:text-blue-300 prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded">
            <Markdown components={{
              code({ className, children, ...rest }) {
                const match = /language-(\w+)/.exec(className || '')
                const code = String(children).replace(/\n$/, '')
                if (match) {
                  const lang = match[1]
                  const highlighted = hljs.getLanguage(lang)
                    ? hljs.highlight(code, { language: lang }).value
                    : hljs.highlightAuto(code).value
                  return (
                    <code
                      className={`hljs ${className || ''}`}
                      dangerouslySetInnerHTML={{ __html: highlighted }}
                      {...rest}
                    />
                  )
                }
                return <code className={className} {...rest}>{children}</code>
              }
            }}>{message.content}</Markdown>
          </div>
        )}

        <div className="mt-1 text-[10px] opacity-40">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
