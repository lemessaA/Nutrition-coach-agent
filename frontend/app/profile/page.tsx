"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  User,
  Heart,
  Target,
  Activity,
  Save,
  Calculator,
  AlertCircle as AlertTriangle,
  CheckCircle2,
  LogOut,
  LogIn,
  Loader2,
  X,
  Store,
  ShoppingBasket,
} from "lucide-react"
import { useUser, type UserRole } from "@/lib/user-context"
import { cn } from "@/lib/utils"
import { SignInDialog } from "@/components/SignInDialog"
import { marketplaceAPI } from "@/services/api"

type Gender = "male" | "female" | "other"
type ActivityLevel =
  | "sedentary"
  | "lightly_active"
  | "moderately_active"
  | "very_active"
  | "extra_active"
type Goal = "lose_weight" | "gain_muscle" | "maintain_health"

interface ProfileForm {
  email: string
  fullName: string
  age: string
  weight: string
  height: string
  gender: Gender
  activityLevel: ActivityLevel
  goal: Goal
  dietaryRestrictions: string[]
  allergies: string[]
  preferences: string[]
}

const ACTIVITY_LEVELS: { value: ActivityLevel; label: string; multiplier: number }[] = [
  { value: "sedentary", label: "Sedentary (little or no exercise)", multiplier: 1.2 },
  { value: "lightly_active", label: "Lightly active (1-3 days/week)", multiplier: 1.375 },
  { value: "moderately_active", label: "Moderately active (3-5 days/week)", multiplier: 1.55 },
  { value: "very_active", label: "Very active (6-7 days/week)", multiplier: 1.725 },
  { value: "extra_active", label: "Extra active (very hard training)", multiplier: 1.9 },
]

const GOALS: { value: Goal; label: string; color: string; description: string }[] = [
  {
    value: "lose_weight",
    label: "Lose weight",
    color: "bg-red-100 text-red-800 border-red-200",
    description: "Caloric deficit (~20% below TDEE)",
  },
  {
    value: "gain_muscle",
    label: "Gain muscle",
    color: "bg-blue-100 text-blue-800 border-blue-200",
    description: "Caloric surplus (~15% above TDEE)",
  },
  {
    value: "maintain_health",
    label: "Maintain",
    color: "bg-green-100 text-green-800 border-green-200",
    description: "Maintenance calories (= TDEE)",
  },
]

const emptyForm: ProfileForm = {
  email: "",
  fullName: "",
  age: "",
  weight: "",
  height: "",
  gender: "male",
  activityLevel: "moderately_active",
  goal: "maintain_health",
  dietaryRestrictions: [],
  allergies: [],
  preferences: [],
}

function computeTargets(form: ProfileForm) {
  const age = parseFloat(form.age)
  const weight = parseFloat(form.weight)
  const height = parseFloat(form.height)
  if (!age || !weight || !height) return null
  // Mifflin-St Jeor
  let bmr = 10 * weight + 6.25 * height - 5 * age
  bmr += form.gender === "male" ? 5 : form.gender === "female" ? -161 : -78
  const mult =
    ACTIVITY_LEVELS.find((a) => a.value === form.activityLevel)?.multiplier ?? 1.55
  const tdee = bmr * mult
  const goalMult =
    form.goal === "lose_weight" ? 0.8 : form.goal === "gain_muscle" ? 1.15 : 1
  const targetCalories = tdee * goalMult
  // macro split: 30% protein / 40% carbs / 30% fat
  const targetProtein = (targetCalories * 0.3) / 4
  const targetCarbs = (targetCalories * 0.4) / 4
  const targetFat = (targetCalories * 0.3) / 9
  return {
    bmr: Math.round(bmr),
    tdee: Math.round(tdee),
    targetCalories: Math.round(targetCalories),
    targetProtein: Math.round(targetProtein),
    targetCarbs: Math.round(targetCarbs),
    targetFat: Math.round(targetFat),
  }
}

function ChipInput({
  label,
  placeholder,
  items,
  onChange,
}: {
  label: string
  placeholder: string
  items: string[]
  onChange: (next: string[]) => void
}) {
  const [draft, setDraft] = useState("")
  const addDraft = () => {
    const v = draft.trim()
    if (!v) return
    if (items.map((i) => i.toLowerCase()).includes(v.toLowerCase())) {
      setDraft("")
      return
    }
    onChange([...items, v])
    setDraft("")
  }
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <div className="flex flex-wrap gap-2 rounded-md border border-gray-300 bg-white p-2 focus-within:border-green-500 focus-within:ring-2 focus-within:ring-green-200">
        {items.map((item) => (
          <span
            key={item}
            className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"
          >
            {item}
            <button
              type="button"
              onClick={() => onChange(items.filter((x) => x !== item))}
              className="text-green-700 hover:text-green-900"
              aria-label={`Remove ${item}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault()
              addDraft()
            } else if (e.key === "Backspace" && !draft && items.length) {
              onChange(items.slice(0, -1))
            }
          }}
          onBlur={addDraft}
          placeholder={items.length ? "" : placeholder}
          className="flex-1 min-w-[120px] border-none bg-transparent p-1 text-sm outline-none"
        />
      </div>
      <p className="mt-1 text-[11px] text-gray-500">Press Enter or comma to add</p>
    </div>
  )
}

export default function ProfilePage() {
  const {
    userId,
    email,
    fullName,
    apiUrl,
    ready,
    setUser,
    setProfile,
    clearUser,
    role,
    isSeller,
    setRole,
  } = useUser()
  const [form, setForm] = useState<ProfileForm>(emptyForm)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [signInOpen, setSignInOpen] = useState(false)

  const calculatedTargets = useMemo(() => computeTargets(form), [form])

  const loadExistingProfile = useCallback(
    async (uid: number) => {
      setLoading(true)
      try {
        const [userRes, healthRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/profile/${uid}`),
          fetch(`${apiUrl}/api/v1/profile/${uid}/health`),
        ])
        if (userRes.ok) {
          const u = await userRes.json()
          setForm((prev) => ({
            ...prev,
            email: u.email ?? prev.email,
            fullName: u.full_name ?? prev.fullName,
          }))
        }
        if (healthRes.ok) {
          const h = await healthRes.json()
          setForm((prev) => ({
            ...prev,
            age: h.age?.toString() ?? "",
            weight: h.weight?.toString() ?? "",
            height: h.height?.toString() ?? "",
            gender: (h.gender as Gender) ?? prev.gender,
            activityLevel:
              (h.activity_level as ActivityLevel) ?? prev.activityLevel,
            goal: (h.goal as Goal) ?? prev.goal,
            dietaryRestrictions: Array.isArray(h.dietary_restrictions)
              ? h.dietary_restrictions
              : [],
            allergies: Array.isArray(h.allergies) ? h.allergies : [],
            preferences: Array.isArray(h.preferences) ? h.preferences : [],
          }))
          setProfile(h)
        }
      } catch (err) {
        console.error("Failed to load profile", err)
      } finally {
        setLoading(false)
      }
    },
    [apiUrl, setProfile]
  )

  useEffect(() => {
    if (!ready) return
    if (userId) {
      setForm((prev) => ({
        ...prev,
        email: email ?? prev.email,
        fullName: fullName ?? prev.fullName,
      }))
      loadExistingProfile(userId)
    }
  }, [ready, userId, email, fullName, loadExistingProfile])

  const update = <K extends keyof ProfileForm>(field: K, value: ProfileForm[K]) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  const validate = (): string | null => {
    if (!form.age || !form.weight || !form.height)
      return "Please fill in age, weight and height."
    const a = parseFloat(form.age)
    const w = parseFloat(form.weight)
    const h = parseFloat(form.height)
    if (a <= 0 || a > 120) return "Age looks off."
    if (w <= 0 || w > 400) return "Weight looks off."
    if (h <= 0 || h > 260) return "Height looks off (use centimeters)."
    return null
  }

  const handleSave = async () => {
    setError(null)
    const v = validate()
    if (v) {
      setError(v)
      return
    }
    setSaving(true)
    try {
      let currentUserId = userId
      let currentEmail = form.email || email || ""

      if (!currentUserId) {
        const fallbackEmail =
          currentEmail ||
          `guest-${Date.now()}@nutrition-coach.local`
        const userRes = await fetch(`${apiUrl}/api/v1/profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: fallbackEmail,
            full_name: form.fullName || "User",
          }),
        })
        if (!userRes.ok) {
          const detail = await userRes.json().catch(() => ({}))
          throw new Error(detail.detail || "Could not create account")
        }
        const userData = await userRes.json()
        currentUserId = userData.id
        currentEmail = userData.email
        setUser({
          userId: userData.id,
          email: userData.email,
          fullName: userData.full_name,
          role: userData.role,
        })
      }

      const healthPayload = {
        age: parseInt(form.age, 10),
        weight: parseFloat(form.weight),
        height: parseFloat(form.height),
        gender: form.gender,
        activity_level: form.activityLevel,
        goal: form.goal,
        dietary_restrictions: form.dietaryRestrictions,
        allergies: form.allergies,
        preferences: form.preferences,
      }

      let healthRes = await fetch(
        `${apiUrl}/api/v1/profile/${currentUserId}/health`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(healthPayload),
        }
      )

      // If profile already exists, backend returns 400 -> fall back to PUT
      if (healthRes.status === 400) {
        healthRes = await fetch(
          `${apiUrl}/api/v1/profile/${currentUserId}/health`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(healthPayload),
          }
        )
      }

      if (!healthRes.ok) {
        const detail = await healthRes.json().catch(() => ({}))
        throw new Error(detail.detail || "Could not save health profile")
      }

      const health = await healthRes.json()
      setProfile(health)
      setUser({
        userId: currentUserId!,
        email: currentEmail,
        fullName: form.fullName || fullName || null,
      })
      setSuccess(true)
      window.setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save profile"
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const bmi = useMemo(() => {
    const w = parseFloat(form.weight)
    const h = parseFloat(form.height)
    if (!w || !h) return null
    const value = w / Math.pow(h / 100, 2)
    let category = "Normal"
    let color = "text-green-600"
    if (value < 18.5) {
      category = "Underweight"
      color = "text-blue-600"
    } else if (value >= 25 && value < 30) {
      category = "Overweight"
      color = "text-orange-600"
    } else if (value >= 30) {
      category = "Obese"
      color = "text-red-600"
    }
    return { value: +value.toFixed(1), category, color }
  }, [form.weight, form.height])

  return (
    <div className="container mx-auto max-w-4xl px-4 py-6 sm:py-8 animate-fade-in">
      <div className="mb-6 text-center">
        <h1 className="text-2xl sm:text-3xl font-bold gradient-text mb-1">
          Health Profile
        </h1>
        <p className="text-sm sm:text-base text-gray-600">
          {userId
            ? "Update your profile to keep recommendations in sync"
            : "Create your personalized nutrition profile"}
        </p>
      </div>

      {ready && !userId && (
        <div className="mb-6 flex flex-col gap-3 rounded-xl border border-green-200 bg-green-50 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-2 text-green-900">
            <LogIn className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Already have a profile?</p>
              <p className="text-sm text-green-800">
                Sign in with your email to load your saved targets and preferences.
              </p>
            </div>
          </div>
          <Button
            type="button"
            onClick={() => setSignInOpen(true)}
            className="bg-green-600 hover:bg-green-700 shrink-0"
          >
            <LogIn className="mr-2 h-4 w-4" />
            Sign in
          </Button>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-start gap-2 text-red-800">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
          <div className="flex items-start gap-2 text-green-800">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Saved!</p>
              <p className="text-sm">
                Your profile is saved.{" "}
                <Link href="/meal-plan" className="underline font-medium">
                  Generate a meal plan
                </Link>{" "}
                or{" "}
                <Link href="/chat" className="underline font-medium">
                  ask the coach
                </Link>
                .
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="card-hover">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Basic information
              </CardTitle>
              <CardDescription>Used to personalize your coach</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    autoComplete="email"
                    value={form.email}
                    onChange={(e) => update("email", e.target.value)}
                    disabled={!!userId}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200 disabled:bg-gray-50"
                    placeholder="your@email.com"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Full name
                  </label>
                  <input
                    type="text"
                    autoComplete="name"
                    value={form.fullName}
                    onChange={(e) => update("fullName", e.target.value)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div className="grid gap-4 grid-cols-2 sm:grid-cols-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Age
                  </label>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    max={120}
                    value={form.age}
                    onChange={(e) => update("age", e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    inputMode="decimal"
                    min={1}
                    value={form.weight}
                    onChange={(e) => update("weight", e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                    placeholder="70"
                  />
                </div>
                <div className="col-span-2 sm:col-span-1">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    inputMode="decimal"
                    min={1}
                    value={form.height}
                    onChange={(e) => update("height", e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                    placeholder="175"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Gender
                  </label>
                  <select
                    value={form.gender}
                    onChange={(e) => update("gender", e.target.value as Gender)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Activity level
                  </label>
                  <select
                    value={form.activityLevel}
                    onChange={(e) =>
                      update("activityLevel", e.target.value as ActivityLevel)
                    }
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-200"
                  >
                    {ACTIVITY_LEVELS.map((lvl) => (
                      <option key={lvl.value} value={lvl.value}>
                        {lvl.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Health goal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-3">
                {GOALS.map((goal) => {
                  const selected = form.goal === goal.value
                  return (
                    <button
                      type="button"
                      key={goal.value}
                      onClick={() => update("goal", goal.value)}
                      className={cn(
                        "rounded-xl border p-4 text-left transition-all",
                        selected
                          ? "border-green-500 bg-green-50 ring-2 ring-green-100"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      )}
                    >
                      <Badge className={goal.color}>{goal.label}</Badge>
                      <p className="mt-2 text-xs text-gray-600">{goal.description}</p>
                    </button>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Dietary preferences
              </CardTitle>
              <CardDescription>
                These help the coach avoid foods that don't work for you
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ChipInput
                label="Dietary restrictions"
                placeholder="vegetarian, gluten-free..."
                items={form.dietaryRestrictions}
                onChange={(v) => update("dietaryRestrictions", v)}
              />
              <ChipInput
                label="Allergies"
                placeholder="nuts, shellfish, soy..."
                items={form.allergies}
                onChange={(v) => update("allergies", v)}
              />
              <ChipInput
                label="Food preferences"
                placeholder="chicken, fish, rice..."
                items={form.preferences}
                onChange={(v) => update("preferences", v)}
              />
            </CardContent>
          </Card>

          <div className="sticky bottom-0 -mx-4 flex flex-wrap gap-3 border-t border-gray-200 bg-white/90 px-4 py-3 backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:p-0">
            <Button
              onClick={handleSave}
              disabled={saving || loading}
              className="flex-1 sm:flex-none bg-green-600 hover:bg-green-700"
            >
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  {userId ? "Update profile" : "Save profile"}
                </>
              )}
            </Button>
            {userId && (
              <Button
                variant="outline"
                onClick={() => {
                  clearUser()
                  setForm(emptyForm)
                }}
                className="flex-1 sm:flex-none"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-4 lg:sticky lg:top-20 lg:h-fit">
          <Card className="card-hover">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Calculator className="h-4 w-4" />
                Your estimated targets
              </CardTitle>
              <CardDescription className="text-xs">
                Live from Mifflin-St Jeor equation
              </CardDescription>
            </CardHeader>
            <CardContent>
              {calculatedTargets ? (
                <div className="space-y-2 text-sm">
                  <Row label="BMR" value={`${calculatedTargets.bmr} kcal`} />
                  <Row label="TDEE" value={`${calculatedTargets.tdee} kcal`} />
                  <hr />
                  <Row
                    label="Target calories"
                    value={`${calculatedTargets.targetCalories} kcal`}
                    emphasize
                  />
                  <Row label="Protein" value={`${calculatedTargets.targetProtein} g`} />
                  <Row label="Carbs" value={`${calculatedTargets.targetCarbs} g`} />
                  <Row label="Fat" value={`${calculatedTargets.targetFat} g`} />
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  Fill in age, weight and height to see targets.
                </p>
              )}
            </CardContent>
          </Card>

          {bmi && (
            <Card className="card-hover">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-4 w-4" />
                  BMI
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold">{bmi.value}</div>
                  <div className={cn("text-sm font-medium", bmi.color)}>
                    {bmi.category}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {userId && (
            <SellerRoleCard
              userId={userId}
              role={role}
              isSeller={isSeller}
              onRoleChange={(newRole) => setRole(newRole)}
            />
          )}
        </div>
      </div>

      <SignInDialog
        open={signInOpen}
        onClose={() => setSignInOpen(false)}
      />
    </div>
  )
}

function Row({
  label,
  value,
  emphasize,
}: {
  label: string
  value: string
  emphasize?: boolean
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-600">{label}</span>
      <span
        className={cn(
          "font-semibold",
          emphasize ? "text-blue-600" : "text-gray-900"
        )}
      >
        {value}
      </span>
    </div>
  )
}

function SellerRoleCard({
  userId,
  role,
  isSeller,
  onRoleChange,
}: {
  userId: number
  role: UserRole
  isSeller: boolean
  onRoleChange: (role: UserRole) => void
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateRole = async (next: UserRole) => {
    setLoading(true)
    setError(null)
    try {
      const updated = (await marketplaceAPI.updateRole(userId, next)) as {
        role?: string
      }
      const resolved = updated?.role as UserRole | undefined
      onRoleChange(resolved === "seller" || resolved === "both" ? resolved : next)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update role")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="card-hover">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Store className="h-4 w-4" />
          Seller account
        </CardTitle>
        <CardDescription className="text-xs">
          Sell food with nutrition info to buyers on the marketplace.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Current role</span>
          <Badge
            variant={isSeller ? "default" : "secondary"}
            className="capitalize"
          >
            {role}
          </Badge>
        </div>

        {error && (
          <p className="flex items-center gap-1 text-xs text-red-600">
            <AlertTriangle className="h-3.5 w-3.5" />
            {error}
          </p>
        )}

        {!isSeller ? (
          <Button
            onClick={() => updateRole("seller")}
            disabled={loading}
            className="w-full gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Store className="h-4 w-4" />
            )}
            Become a seller
          </Button>
        ) : (
          <div className="space-y-2">
            <Link href="/marketplace/sell" className="block">
              <Button className="w-full gap-2">
                <Store className="h-4 w-4" />
                Open seller dashboard
              </Button>
            </Link>
            <Button
              variant="outline"
              onClick={() => updateRole("buyer")}
              disabled={loading}
              className="w-full gap-2 text-muted-foreground"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ShoppingBasket className="h-4 w-4" />
              )}
              Switch back to buyer only
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
