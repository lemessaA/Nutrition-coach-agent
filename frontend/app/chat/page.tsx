"use client"

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Send, Bot, User, Sparkles } from 'lucide-react'

interface Message {
  id: string
  content: string
  sender: 'user' | 'ai'
  timestamp: Date
  agentType?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your Nutrition Coach AI. I can help you with meal planning, nutrition questions, food analysis, and personalized advice. How can I assist you today?",
      sender: 'ai',
      timestamp: new Date(),
      agentType: 'coaching_agent'
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Make API call to backend
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('API URL:', apiUrl)
      
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: 'default'
        })
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          sender: 'ai',
          timestamp: new Date(),
          agentType: data.agent_type
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error('Failed to get response')
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I'm having trouble connecting right now. Please try again later.",
        sender: 'ai',
        timestamp: new Date(),
        agentType: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getAgentBadgeColor = (agentType?: string) => {
    switch (agentType) {
      case 'meal_planner_agent':
        return 'bg-blue-100 text-blue-800'
      case 'nutrition_knowledge_agent':
        return 'bg-green-100 text-green-800'
      case 'food_analyzer_agent':
        return 'bg-purple-100 text-purple-800'
      case 'coaching_agent':
        return 'bg-orange-100 text-orange-800'
      case 'user_profile_agent':
        return 'bg-red-100 text-red-800'
      case 'market_intelligence_agent':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getAgentDisplayName = (agentType?: string) => {
    switch (agentType) {
      case 'meal_planner_agent':
        return 'Meal Planner'
      case 'nutrition_knowledge_agent':
        return 'Nutrition Expert'
      case 'food_analyzer_agent':
        return 'Food Analyzer'
      case 'coaching_agent':
        return 'Coach'
      case 'user_profile_agent':
        return 'Profile Manager'
      case 'market_intelligence_agent':
        return 'Market Intelligence'
      default:
        return 'AI Assistant'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold gradient-text mb-2">AI Nutrition Coach</h1>
        <p className="text-gray-600">Chat with your personal AI nutrition assistant</p>
      </div>
      <div className="bg-white rounded-lg shadow-lg overflow-hidden card-hover">
        {/* Chat Header */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            <h2 className="text-lg font-semibold">AI Nutrition Coach</h2>
          </div>
        </div>

        {/* Messages Area */}
        <div className="h-[500px] overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] ${
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                } rounded-lg p-3`}
              >
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 mt-1">
                    {message.sender === 'user' ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.sender === 'ai' && message.agentType && (
                      <div className="mt-2">
                        <Badge className={`text-xs ${getAgentBadgeColor(message.agentType)}`}>
                          {getAgentDisplayName(message.agentType)}
                        </Badge>
                      </div>
                    )}
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-900 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about meal plans, nutrition, or food analysis..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Button
            variant="outline"
            onClick={() => setInputMessage("Create a meal plan for weight loss")}
            className="text-sm"
          >
            Meal Plan
          </Button>
          <Button
            variant="outline"
            onClick={() => setInputMessage("How much protein should I eat daily?")}
            className="text-sm"
          >
            Nutrition Q&A
          </Button>
          <Button
            variant="outline"
            onClick={() => setInputMessage("Analyze: chicken breast with rice and vegetables")}
            className="text-sm"
          >
            Analyze Food
          </Button>
          <Button
            variant="outline"
            onClick={() => setInputMessage("I need motivation to stay on track")}
            className="text-sm"
          >
            Get Motivated
          </Button>
        </div>
      </div>
    </div>
  )
}