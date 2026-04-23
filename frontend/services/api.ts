import { getPublicApiUrl } from "@/lib/public-api-url"

// API service for centralized backend communication
const API_BASE_URL = getPublicApiUrl()

// Generic API request function
export async function apiRequest<T = any>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
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

// ---------------------------------------------------------------------------
// Marketplace (food seller / buyer e-commerce)
// ---------------------------------------------------------------------------

export type ListingNutrition = {
  calories?: number | null
  protein?: number | null
  carbs?: number | null
  fat?: number | null
  fiber?: number | null
  sugar?: number | null
  sodium?: number | null
}

export type FoodListing = ListingNutrition & {
  id: number
  seller_id: number
  seller_name?: string | null
  name: string
  description?: string | null
  image_url?: string | null
  price: number
  unit: string
  stock: number
  is_active: boolean
  serving_size?: string | null
  tags: string[]
  created_at: string
  updated_at?: string | null
}

export type OrderItem = {
  id: number
  listing_id: number
  name_snapshot: string
  unit_price: number
  quantity: number
  listing_image_url?: string | null
  listing_nutrition?: ListingNutrition | null
  listing_tags: string[]
}

export type OrderStatus = 'pending' | 'confirmed' | 'fulfilled' | 'cancelled'

export type MarketplaceOrder = {
  id: number
  buyer_id: number
  seller_id: number
  buyer_name?: string | null
  seller_name?: string | null
  status: OrderStatus
  total_price: number
  notes?: string | null
  nutrient_target?: ListingNutrition | null
  items: OrderItem[]
  created_at: string
  updated_at?: string | null
}

export type ListingSearchFilters = {
  q?: string
  tags?: string[]
  min_protein?: number
  max_sugar?: number
  min_fiber?: number
  max_calories?: number
  max_price?: number
  in_stock_only?: boolean
  sort_by?: 'newest' | 'protein_per_dollar' | 'price_asc' | 'price_desc'
  limit?: number
  offset?: number
}

function buildListingSearchParams(filters: ListingSearchFilters = {}): Record<string, string> {
  const params: Record<string, string> = {}
  if (filters.q) params.q = filters.q
  if (filters.tags && filters.tags.length) params.tags = filters.tags.join(',')
  if (filters.min_protein != null) params.min_protein = String(filters.min_protein)
  if (filters.max_sugar != null) params.max_sugar = String(filters.max_sugar)
  if (filters.min_fiber != null) params.min_fiber = String(filters.min_fiber)
  if (filters.max_calories != null) params.max_calories = String(filters.max_calories)
  if (filters.max_price != null) params.max_price = String(filters.max_price)
  if (filters.in_stock_only != null) params.in_stock_only = String(filters.in_stock_only)
  if (filters.sort_by) params.sort_by = filters.sort_by
  if (filters.limit != null) params.limit = String(filters.limit)
  if (filters.offset != null) params.offset = String(filters.offset)
  return params
}

export const marketplaceAPI = {
  // Listings
  searchListings: async (filters: ListingSearchFilters = {}): Promise<FoodListing[]> => {
    return apiRequest('marketplace/listings', {
      method: 'GET',
      params: buildListingSearchParams(filters),
    })
  },

  getListing: async (listingId: number): Promise<FoodListing> => {
    return apiRequest(`marketplace/listings/${listingId}`, { method: 'GET' })
  },

  getSellerListings: async (
    sellerId: number,
    includeInactive: boolean = true
  ): Promise<FoodListing[]> => {
    return apiRequest(`marketplace/sellers/${sellerId}/listings`, {
      method: 'GET',
      params: { include_inactive: String(includeInactive) },
    })
  },

  createListing: async (
    sellerId: number,
    data: Partial<FoodListing> & { name: string; price: number }
  ): Promise<FoodListing> => {
    return apiRequest('marketplace/listings', {
      method: 'POST',
      params: { seller_id: String(sellerId) },
      body: data,
    })
  },

  updateListing: async (
    sellerId: number,
    listingId: number,
    data: Partial<FoodListing>
  ): Promise<FoodListing> => {
    return apiRequest(`marketplace/listings/${listingId}`, {
      method: 'PUT',
      params: { seller_id: String(sellerId) },
      body: data,
    })
  },

  deleteListing: async (sellerId: number, listingId: number) => {
    return apiRequest(`marketplace/listings/${listingId}`, {
      method: 'DELETE',
      params: { seller_id: String(sellerId) },
    })
  },

  // Orders
  createOrder: async (
    buyerId: number,
    body: {
      items: { listing_id: number; quantity: number }[]
      notes?: string
      nutrient_target?: ListingNutrition
    }
  ): Promise<MarketplaceOrder[]> => {
    return apiRequest('marketplace/orders', {
      method: 'POST',
      params: { buyer_id: String(buyerId) },
      body,
    })
  },

  listOrders: async (
    userId: number,
    role: 'buyer' | 'seller' = 'buyer',
    status?: OrderStatus
  ): Promise<MarketplaceOrder[]> => {
    const params: Record<string, string> = {
      user_id: String(userId),
      role,
    }
    if (status) params.status = status
    return apiRequest('marketplace/orders', { method: 'GET', params })
  },

  getOrder: async (userId: number, orderId: number): Promise<MarketplaceOrder> => {
    return apiRequest(`marketplace/orders/${orderId}`, {
      method: 'GET',
      params: { user_id: String(userId) },
    })
  },

  updateOrderStatus: async (
    userId: number,
    orderId: number,
    status: OrderStatus
  ): Promise<MarketplaceOrder> => {
    return apiRequest(`marketplace/orders/${orderId}/status`, {
      method: 'PATCH',
      params: { user_id: String(userId) },
      body: { status },
    })
  },

  // Role management
  updateRole: async (userId: number, role: 'buyer' | 'seller' | 'both') => {
    return apiRequest(`profile/${userId}/role`, {
      method: 'PATCH',
      body: { role },
    })
  },

  // Listing image upload (multipart/form-data -> returns absolute URL to use in image_url)
  uploadImage: async (
    file: File
  ): Promise<{ url: string; path: string; filename: string; size: number; content_type: string }> => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE_URL}/api/v1/marketplace/uploads`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}))
      throw new Error(detail.detail || `Upload failed: ${res.statusText}`)
    }
    return res.json()
  },
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