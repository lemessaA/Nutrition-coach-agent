// API service for centralized backend communication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic API request function
export async function apiRequest<T = any>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
    body?: any
    params?: Record<string, string>
    headers?: Record<string, string>
  } = {}
): Promise<T> {
  const url = new URL(`${API_BASE_URL}/api/v1/${endpoint}`)
  
  // Add query parameters
  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      url.searchParams.append(key, value)
    })
  }

  const response = await fetch(url.toString(), {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || `API request failed: ${response.statusText}`)
  }

  return response.json()
}

// Chat API
export const chatAPI = {
  sendMessage: async (message: string, sessionId: string = 'default') => {
    return apiRequest('chat', {
      method: 'POST',
      body: {
        message,
        session_id: sessionId
      }
    })
  }
}

// Profile API
export const profileAPI = {
  createUser: async (userData: { email: string; full_name: string }) => {
    return apiRequest('profile', {
      method: 'POST',
      body: userData
    })
  },

  getUser: async (userId: number) => {
    return apiRequest(`profile/${userId}`, {
      method: 'GET'
    })
  },

  createHealthProfile: async (userId: number, profileData: any) => {
    return apiRequest(`profile/${userId}/health`, {
      method: 'POST',
      body: profileData
    })
  },

  getHealthProfile: async (userId: number) => {
    return apiRequest(`profile/${userId}/health`, {
      method: 'GET'
    })
  },

  updateHealthProfile: async (userId: number, profileData: any) => {
    return apiRequest(`profile/${userId}/health`, {
      method: 'PUT',
      body: profileData
    })
  }
}

// Meal Plan API
export const mealPlanAPI = {
  generateMealPlan: async (userId: number, planData: {
    plan_type: 'daily' | 'weekly'
    preferences?: Record<string, any>
    dietary_restrictions?: string[]
    target_calories?: number
  }) => {
    return apiRequest('meal-plan', {
      method: 'POST',
      params: { user_id: userId.toString() },
      body: planData
    })
  },

  getMealPlan: async (userId: number, planType: string = 'daily') => {
    return apiRequest('meal-plan', {
      method: 'GET',
      params: { 
        user_id: userId.toString(),
        plan_type: planType
      }
    })
  },

  getMealPlanById: async (planId: number) => {
    return apiRequest(`meal-plan/${planId}`, {
      method: 'GET'
    })
  },

  deleteMealPlan: async (planId: number) => {
    return apiRequest(`meal-plan/${planId}`, {
      method: 'DELETE'
    })
  }
}

// Food Analysis API
export const foodAnalysisAPI = {
  analyzeFood: async (userId: number, foodInput: string) => {
    return apiRequest('analyze-food', {
      method: 'POST',
      params: { user_id: userId.toString() },
      body: { food_input: foodInput }
    })
  },

  analyzeMeal: async (userId: number, mealDescription: string) => {
    return apiRequest('analyze-meal', {
      method: 'POST',
      params: { 
        user_id: userId.toString(),
        meal_description: mealDescription
      }
    })
  },

  compareFoods: async (userId: number, foods: string[]) => {
    return apiRequest('compare-foods', {
      method: 'POST',
      params: { user_id: userId.toString() },
      body: { foods }
    })
  }
}

// Market Intelligence API
export const marketAPI = {
  getMarketData: async (category: string = 'all', analysisType: string = 'trends') => {
    return apiRequest('market-intelligence', {
      method: 'POST',
      body: {
        category,
        analysis_type: analysisType
      }
    })
  },

  getPriceHistory: async (item: string, timeframe: string = '30d') => {
    return apiRequest('market-intelligence/price-history', {
      method: 'GET',
      params: { 
        item,
        timeframe
      }
    })
  },

  getRecommendations: async (budget: number, preferences: string[]) => {
    return apiRequest('market-intelligence/recommendations', {
      method: 'POST',
      body: {
        budget,
        preferences
      }
    })
  }
}

// User Management API
export const userAPI = {
  updateProfile: async (userId: number, userData: any) => {
    return apiRequest(`profile/${userId}`, {
      method: 'PUT',
      body: userData
    })
  },

  deleteAccount: async (userId: number) => {
    return apiRequest(`profile/${userId}`, {
      method: 'DELETE'
    })
  },

  getPreferences: async (userId: number) => {
    return apiRequest(`profile/${userId}/preferences`, {
      method: 'GET'
    })
  },

  updatePreferences: async (userId: number, preferences: any) => {
    return apiRequest(`profile/${userId}/preferences`, {
      method: 'PUT',
      body: preferences
    })
  }
}

// Health Metrics API
export const healthAPI = {
  getMetrics: async (userId: number, timeframe: string = '30d') => {
    return apiRequest('health-metrics', {
      method: 'GET',
      params: { 
        user_id: userId.toString(),
        timeframe
      }
    })
  },

  trackProgress: async (userId: number, progressData: {
    weight?: number
    measurements?: Record<string, number>
    goals?: Record<string, any>
  }) => {
    return apiRequest('health-metrics/progress', {
      method: 'POST',
      params: { user_id: userId.toString() },
      body: progressData
    })
  },

  getHistory: async (userId: number, metric: string, limit: number = 10) => {
    return apiRequest('health-metrics/history', {
      method: 'GET',
      params: { 
        user_id: userId.toString(),
        metric,
        limit: limit.toString()
      }
    })
  }
}

// Error handling utility
export const handleAPIError = (error: any, customMessage?: string) => {
  console.error('API Error:', error)
  
  if (error.message) {
    return error.message
  }
  
  if (typeof error === 'string') {
    return error
  }
  
  return customMessage || 'An unexpected error occurred'
}

// Response type guards
export const isValidAPIResponse = <T>(response: any): response is T => {
  return response !== null && typeof response === 'object' && !('error' in response)
}

export const extractErrorMessage = (error: any): string => {
  if (error?.detail) {
    return error.detail
  }
  
  if (error?.message) {
    return error.message
  }
  
  return 'An unexpected error occurred'
}

// Utility for API response logging
export const logAPIResponse = (endpoint: string, response: any) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`API Response [${endpoint}]:`, response)
  }
}