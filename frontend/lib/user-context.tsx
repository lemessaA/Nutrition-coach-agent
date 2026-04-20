"use client"

import React, { createContext, useCallback, useContext, useEffect, useState } from "react"

type HealthProfile = {
  age?: number
  weight?: number
  height?: number
  gender?: "male" | "female" | "other"
  activity_level?: string
  goal?: string
  dietary_restrictions?: string[]
  allergies?: string[]
  preferences?: string[]
  bmr?: number
  tdee?: number
  target_calories?: number
  target_protein?: number
  target_carbs?: number
  target_fat?: number
}

type UserState = {
  userId: number | null
  email: string | null
  fullName: string | null
  profile: HealthProfile | null
}

type UserContextValue = UserState & {
  setUser: (u: { userId: number; email?: string | null; fullName?: string | null }) => void
  setProfile: (p: HealthProfile | null) => void
  clearUser: () => void
  apiUrl: string
  ready: boolean
}

const STORAGE_KEY = "nutrition-coach.user"

const defaultState: UserState = {
  userId: null,
  email: null,
  fullName: null,
  profile: null,
}

const UserContext = createContext<UserContextValue | undefined>(undefined)

function loadFromStorage(): UserState {
  if (typeof window === "undefined") return defaultState
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultState
    const parsed = JSON.parse(raw)
    return {
      userId: typeof parsed.userId === "number" ? parsed.userId : null,
      email: parsed.email ?? null,
      fullName: parsed.fullName ?? null,
      profile: parsed.profile ?? null,
    }
  } catch {
    return defaultState
  }
}

function saveToStorage(state: UserState) {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // ignore (quota / private mode)
  }
}

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<UserState>(defaultState)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setState(loadFromStorage())
    setReady(true)
  }, [])

  useEffect(() => {
    if (ready) saveToStorage(state)
  }, [state, ready])

  const setUser: UserContextValue["setUser"] = useCallback((u) => {
    setState((prev) => ({
      ...prev,
      userId: u.userId,
      email: u.email ?? prev.email,
      fullName: u.fullName ?? prev.fullName,
    }))
  }, [])

  const setProfile: UserContextValue["setProfile"] = useCallback((p) => {
    setState((prev) => ({ ...prev, profile: p }))
  }, [])

  const clearUser = useCallback(() => {
    setState(defaultState)
    if (typeof window !== "undefined") window.localStorage.removeItem(STORAGE_KEY)
  }, [])

  const apiUrl =
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
    "http://localhost:8000"

  const value: UserContextValue = {
    ...state,
    setUser,
    setProfile,
    clearUser,
    apiUrl,
    ready,
  }

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>
}

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext)
  if (!ctx) {
    throw new Error("useUser must be used within a UserProvider")
  }
  return ctx
}

export type { HealthProfile }
