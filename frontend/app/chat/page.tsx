"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Send, Bot, User as UserIcon, Sparkles, Trash2, Loader2 } from "lucide-react"
import { useUser } from "@/lib/user-context"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  timestamp: string
  agentType?: string
}

const STORAGE_KEY = "nutrition-coach.chat"

const WELCOME: Message = {
  id: "welcome",
  content:
    "Hi! I'm your Nutrition Coach AI. Ask me about meal planning, nutrition, food analysis, or your goals. Setting up a profile unlocks personalized advice.",
  sender: "ai",
  timestamp: new Date().toISOString(),
  agentType: "coaching_agent",
}

const QUICK_ACTIONS = [
  { label: "Meal plan", text: "Create a meal plan for weight loss" },
  { label: "Protein needs", text: "How much protein should I eat daily?" },
  { label: "Analyze food", text: "Analyze: chicken breast with rice and vegetables" },
  { label: "Motivation", text: "I need motivation to stay on track" },
  { label: "Macros", text: "Explain macros for muscle gain" },
  { label: "Snack ideas", text: "Healthy snack ideas under 200 kcal" },
]

function getAgentBadgeColor(agentType?: string) {
  switch (agentType) {
    case "meal_planner_agent":
      return "bg-blue-100 text-blue-800"
    case "nutrition_knowledge_agent":
      return "bg-green-100 text-green-800"
    case "food_analyzer_agent":
      return "bg-purple-100 text-purple-800"
    case "coaching_agent":
      return "bg-orange-100 text-orange-800"
    case "user_profile_agent":
      return "bg-red-100 text-red-800"
    case "market_intelligence_agent":
      return "bg-yellow-100 text-yellow-800"
    case "error":
      return "bg-red-100 text-red-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

function getAgentDisplayName(agentType?: string) {
  switch (agentType) {
    case "meal_planner_agent":
      return "Meal Planner"
    case "nutrition_knowledge_agent":
      return "Nutrition Expert"
    case "food_analyzer_agent":
      return "Food Analyzer"
    case "coaching_agent":
      return "Coach"
    case "user_profile_agent":
      return "Profile Manager"
    case "market_intelligence_agent":
      return "Market Intelligence"
    case "error":
      return "Offline"
    default:
      return "AI Assistant"
  }
}

export default function ChatPage() {
  const { userId, apiUrl, ready } = useUser()
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sessionId = useMemo(
    () => (userId ? `user-${userId}` : "guest"),
    [userId]
  )

  useEffect(() => {
    if (!ready) return
    try {
      const raw = window.localStorage.getItem(`${STORAGE_KEY}:${sessionId}`)
      if (raw) {
        const parsed: Message[] = JSON.parse(raw)
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed)
          return
        }
      }
    } catch {
      // ignore
    }
    setMessages([WELCOME])
  }, [sessionId, ready])

  useEffect(() => {
    if (!ready) return
    try {
      window.localStorage.setItem(
        `${STORAGE_KEY}:${sessionId}`,
        JSON.stringify(messages.slice(-100))
      )
    } catch {
      // ignore
    }
  }, [messages, sessionId, ready])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const autoGrow = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [])

  useEffect(() => {
    autoGrow()
  }, [input, autoGrow])

  const sendMessage = async (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || isLoading) return

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      content,
      sender: "user",
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          session_id: sessionId,
          ...(userId ? { user_id: userId } : {}),
        }),
      })
      if (!response.ok) throw new Error("Bad response")
      const data = await response.json()
      const aiMsg: Message = {
        id: `a-${Date.now()}`,
        content: data.response || "(empty response)",
        sender: "ai",
        timestamp: new Date().toISOString(),
        agentType: data.agent_type,
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          content:
            "Sorry, I couldn't reach the AI coach. Check that the backend is running and try again.",
          sender: "ai",
          timestamp: new Date().toISOString(),
          agentType: "error",
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearConversation = () => {
    setMessages([WELCOME])
    try {
      window.localStorage.removeItem(`${STORAGE_KEY}:${sessionId}`)
    } catch {
      // ignore
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col px-3 sm:px-4 py-4 sm:py-6 h-[calc(100dvh-3.5rem)]">
      <div className="mb-3 sm:mb-4 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-xl sm:text-2xl font-bold gradient-text">
            AI Nutrition Coach
          </h1>
          <p className="truncate text-xs sm:text-sm text-gray-600">
            {userId
              ? "Chatting with your personalized assistant"
              : "Tip: create a profile to unlock personalized advice"}
          </p>
        </div>
        {!userId && (
          <Link
            href="/profile"
            className="shrink-0 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-medium text-green-800 hover:bg-green-100"
          >
            Set up profile
          </Link>
        )}
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-black/5">
        <div className="flex items-center justify-between gap-3 bg-gradient-to-r from-green-600 to-blue-600 px-4 py-3 text-white">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            <h2 className="text-base sm:text-lg font-semibold">
              Nutrition Coach
            </h2>
          </div>
          <button
            type="button"
            onClick={clearConversation}
            title="Clear conversation"
            className="rounded-md p-1.5 text-white/90 hover:bg-white/10"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>

        <div className="nice-scroll flex-1 space-y-3 overflow-y-auto px-3 sm:px-4 py-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                "flex",
                m.sender === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[85%] sm:max-w-[75%] rounded-2xl px-3.5 py-2.5 shadow-sm",
                  m.sender === "user"
                    ? "bg-blue-600 text-white rounded-br-md"
                    : "bg-gray-100 text-gray-900 rounded-bl-md"
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 shrink-0">
                    {m.sender === "user" ? (
                      <UserIcon className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="whitespace-pre-wrap break-words text-sm sm:text-[15px] leading-relaxed">
                      {m.content}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      {m.sender === "ai" && m.agentType && (
                        <Badge
                          className={cn(
                            "text-[10px] sm:text-xs",
                            getAgentBadgeColor(m.agentType)
                          )}
                        >
                          {getAgentDisplayName(m.agentType)}
                        </Badge>
                      )}
                      <span className="text-[10px] sm:text-xs opacity-70">
                        {new Date(m.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md bg-gray-100 px-4 py-3 text-gray-900">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
                    <div
                      className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                      style={{ animationDelay: "0.12s" }}
                    />
                    <div
                      className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                      style={{ animationDelay: "0.24s" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t bg-white/80 px-3 sm:px-4 py-3">
          <div className="chip-row mb-2">
            {QUICK_ACTIONS.map((q) => (
              <button
                key={q.label}
                type="button"
                disabled={isLoading}
                onClick={() => sendMessage(q.text)}
                className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:border-green-400 hover:text-green-700 disabled:opacity-50"
              >
                {q.label}
              </button>
            ))}
          </div>
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about meals, nutrition, macros..."
              className="block max-h-40 min-h-[44px] w-full resize-none rounded-2xl border border-gray-300 bg-white px-4 py-2.5 leading-relaxed text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
              disabled={isLoading}
            />
            <Button
              onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="h-11 w-11 shrink-0 rounded-full bg-green-600 hover:bg-green-700"
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
          <p className="mt-1.5 hidden sm:block text-[11px] text-gray-400">
            Press Enter to send, Shift + Enter for a new line
          </p>
        </div>
      </div>
    </div>
  )
}
