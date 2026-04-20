"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Calendar,
  Clock,
  Users,
  ChefHat,
  Target,
  TrendingUp,
  Utensils,
  Flame,
  Loader2,
  AlertCircle,
  RefreshCw,
} from "lucide-react"
import { useUser } from "@/lib/user-context"

interface Nutrition {
  calories: number
  protein: number
  carbs: number
  fat: number
}

interface Meal {
  name: string
  description?: string
  ingredients?: string[]
  instructions?: string[]
  nutrition: Nutrition
  prep_time?: string
}

interface DailyMealsBundle {
  breakfast: Meal
  lunch: Meal
  dinner: Meal
  snack: Meal
  daily_totals?: Nutrition
}

interface MealPlan {
  id: number
  user_id: number
  plan_type: string
  plan_date: string
  meals: { meals: DailyMealsBundle; daily_totals?: Nutrition } | Record<string, unknown>
  total_calories?: number
  total_protein?: number
  total_carbs?: number
  total_fat?: number
  created_at: string
}

type WeeklyPlanMap = Record<string, DailyMealsBundle>

function extractDaily(plan: MealPlan): DailyMealsBundle | null {
  const raw = plan.meals as Record<string, unknown> | null
  if (!raw) return null
  const inner = ((raw.meals as unknown) as DailyMealsBundle) ?? ((raw as unknown) as DailyMealsBundle)
  if (!inner || !inner.breakfast) return null
  return inner
}

export default function MealPlanPage() {
  const { userId, profile, apiUrl, ready } = useUser()
  const [activeTab, setActiveTab] = useState("current")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPlan, setCurrentPlan] = useState<MealPlan | null>(null)
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlanMap | null>(null)

  const fetchCurrentMealPlan = useCallback(async () => {
    if (!userId) return
    try {
      const res = await fetch(
        `${apiUrl}/api/v1/meal-plan?user_id=${userId}&plan_type=daily&limit=1`
      )
      if (res.ok) {
        const data: MealPlan[] = await res.json()
        if (Array.isArray(data) && data.length > 0) setCurrentPlan(data[0])
      }
    } catch (err) {
      console.error("Failed to fetch meal plan", err)
    }
  }, [apiUrl, userId])

  useEffect(() => {
    if (!ready) return
    if (userId) fetchCurrentMealPlan()
  }, [ready, userId, fetchCurrentMealPlan])

  const generateMealPlan = async (planType: "daily" | "weekly") => {
    if (!userId) {
      setError("Please create a profile first.")
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      if (planType === "daily") {
        const res = await fetch(
          `${apiUrl}/api/v1/meal-plan?user_id=${userId}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              plan_type: "daily",
              preferences: {
                high_protein: profile?.goal === "gain_muscle",
              },
              dietary_restrictions: profile?.dietary_restrictions ?? [],
              target_calories: profile?.target_calories ?? 2000,
            }),
          }
        )
        if (!res.ok) {
          const detail = await res.json().catch(() => ({}))
          throw new Error(detail.detail || "Failed to generate meal plan")
        }
        const data: MealPlan = await res.json()
        setCurrentPlan(data)
        setActiveTab("current")
      } else {
        const res = await fetch(
          `${apiUrl}/api/v1/meal-plan/${userId}/generate-weekly`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ high_protein: profile?.goal === "gain_muscle" }),
          }
        )
        if (!res.ok) {
          const detail = await res.json().catch(() => ({}))
          throw new Error(detail.detail || "Failed to generate weekly plan")
        }
        const data = await res.json()
        const weekly = (data.weekly_plan ?? data) as WeeklyPlanMap
        setWeeklyPlan(weekly)
        setActiveTab("weekly")
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unexpected error"
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  if (ready && !userId) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-10 animate-fade-in">
        <Card className="text-center">
          <CardContent className="py-10">
            <ChefHat className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <h2 className="mb-2 text-lg font-semibold">
              Set up your profile first
            </h2>
            <p className="mb-5 text-sm text-gray-600">
              Meal plans are tailored to your goals and activity level. Create a
              profile and we'll build one for you.
            </p>
            <Link href="/profile">
              <Button className="bg-green-600 hover:bg-green-700">
                Create profile
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-6 sm:py-8 animate-fade-in">
      <div className="mb-6 text-center">
        <h1 className="text-2xl sm:text-3xl font-bold gradient-text mb-1">
          Meal Planner
        </h1>
        <p className="text-sm sm:text-base text-gray-600">
          Personalized meal plans tailored to your health goals
        </p>
      </div>

      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="flex items-start gap-3 pt-6">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
            <div className="text-red-800">
              <h3 className="font-semibold">Error</h3>
              <p className="text-sm">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-6 grid w-full grid-cols-3 gap-1">
          <TabsTrigger value="current" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <Calendar className="h-4 w-4" />
            <span className="hidden xs:inline sm:inline">Current</span>
            <span className="xs:hidden sm:hidden">Now</span>
          </TabsTrigger>
          <TabsTrigger value="generate" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <ChefHat className="h-4 w-4" />
            Generate
          </TabsTrigger>
          <TabsTrigger value="weekly" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <Users className="h-4 w-4" />
            Weekly
          </TabsTrigger>
        </TabsList>

        <TabsContent value="current" className="space-y-6">
          {currentPlan ? (
            <DailyView plan={currentPlan} profile={profile} />
          ) : (
            <EmptyState
              icon={<Calendar className="h-12 w-12" />}
              title="No current meal plan"
              description="Generate your first personalized meal plan to get started"
              action={
                <Button
                  onClick={() => setActiveTab("generate")}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Generate meal plan
                </Button>
              }
            />
          )}
        </TabsContent>

        <TabsContent value="generate" className="space-y-6">
          <Card className="card-hover">
            <CardHeader>
              <CardTitle>Generate a new plan</CardTitle>
              <CardDescription>
                Create a personalized plan based on your profile
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                <Button
                  onClick={() => generateMealPlan("daily")}
                  disabled={isLoading}
                  className="h-20 flex-col gap-1 bg-blue-600 text-white hover:bg-blue-700"
                >
                  <ChefHat className="h-6 w-6" />
                  <span className="text-sm">
                    {isLoading ? "Generating..." : "Daily plan"}
                  </span>
                </Button>
                <Button
                  onClick={() => generateMealPlan("weekly")}
                  disabled={isLoading}
                  className="h-20 flex-col gap-1 bg-green-600 text-white hover:bg-green-700"
                >
                  <Users className="h-6 w-6" />
                  <span className="text-sm">
                    {isLoading ? "Generating..." : "Weekly plan"}
                  </span>
                </Button>
              </div>
              {profile && (
                <div className="mt-4 rounded-lg bg-gray-50 p-4 text-sm text-gray-600">
                  <h4 className="mb-2 font-semibold text-gray-900">
                    Your profile
                  </h4>
                  <div className="grid grid-cols-2 gap-y-1">
                    <span>Goal</span>
                    <span className="text-right capitalize">
                      {profile.goal?.replace("_", " ")}
                    </span>
                    <span>Activity</span>
                    <span className="text-right capitalize">
                      {profile.activity_level?.replace("_", " ")}
                    </span>
                    <span>Target calories</span>
                    <span className="text-right">
                      {profile.target_calories ?? "—"} kcal
                    </span>
                  </div>
                </div>
              )}
              {isLoading && (
                <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Cooking up your plan...
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="weekly" className="space-y-6">
          {weeklyPlan ? (
            <WeeklyView plan={weeklyPlan} />
          ) : (
            <EmptyState
              icon={<Users className="h-12 w-12" />}
              title="No weekly plan yet"
              description="Generate a 7-day plan to see your full week at a glance"
              action={
                <Button
                  onClick={() => generateMealPlan("weekly")}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Generate weekly plan
                    </>
                  )}
                </Button>
              }
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode
  title: string
  description: string
  action?: React.ReactNode
}) {
  return (
    <Card className="py-10 text-center">
      <CardContent>
        <div className="mx-auto mb-4 text-gray-400">{icon}</div>
        <h3 className="mb-2 text-lg font-semibold text-gray-700">{title}</h3>
        <p className="mb-4 text-sm text-gray-500">{description}</p>
        {action}
      </CardContent>
    </Card>
  )
}

function DailyView({
  plan,
  profile,
}: {
  plan: MealPlan
  profile: ReturnType<typeof useUser>["profile"]
}) {
  const daily = extractDaily(plan)
  if (!daily) {
    return (
      <Card>
        <CardContent className="pt-6 text-sm text-gray-600">
          This plan's data seems malformed. Try generating a new one.
        </CardContent>
      </Card>
    )
  }

  const totals =
    daily.daily_totals ??
    ({
      calories: plan.total_calories ?? 0,
      protein: plan.total_protein ?? 0,
      carbs: plan.total_carbs ?? 0,
      fat: plan.total_fat ?? 0,
    } as Nutrition)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Target className="h-8 w-8 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Daily targets</h3>
                <p className="text-xs text-blue-700">Based on your profile</p>
              </div>
            </div>
            <dl className="mt-4 space-y-1.5 text-sm">
              <Stat label="Calories" value={`${profile?.target_calories ?? "—"} kcal`} />
              <Stat label="Protein" value={`${profile?.target_protein ?? "—"} g`} />
              <Stat label="Carbs" value={`${profile?.target_carbs ?? "—"} g`} />
              <Stat label="Fat" value={`${profile?.target_fat ?? "—"} g`} />
            </dl>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div>
                <h3 className="font-semibold text-green-900">This plan</h3>
                <p className="text-xs text-green-700">
                  What you'll consume today
                </p>
              </div>
            </div>
            <dl className="mt-4 space-y-1.5 text-sm">
              <Stat label="Calories" value={`${totals.calories} kcal`} />
              <Stat label="Protein" value={`${totals.protein} g`} />
              <Stat label="Carbs" value={`${totals.carbs} g`} />
              <Stat label="Fat" value={`${totals.fat} g`} />
            </dl>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <MealCard meal={daily.breakfast} type="Breakfast" />
        <MealCard meal={daily.lunch} type="Lunch" />
        <MealCard meal={daily.dinner} type="Dinner" />
        <MealCard meal={daily.snack} type="Snack" />
      </div>
    </div>
  )
}

function MealCard({ meal, type }: { meal: Meal; type: string }) {
  return (
    <Card className="card-hover">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="truncate text-base capitalize sm:text-lg">
              {meal.name}
            </CardTitle>
            {meal.description && (
              <CardDescription className="text-xs sm:text-sm">
                {meal.description}
              </CardDescription>
            )}
          </div>
          <Badge variant="secondary" className="shrink-0 bg-blue-100 text-blue-800">
            {type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {meal.prep_time && (
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <Clock className="h-4 w-4" />
              {meal.prep_time}
            </div>
          )}

          {meal.ingredients && meal.ingredients.length > 0 && (
            <details className="rounded-md bg-gray-50 p-3 text-sm md:open">
              <summary className="cursor-pointer font-semibold">
                <Utensils className="mr-2 inline h-4 w-4" /> Ingredients
              </summary>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-700">
                {meal.ingredients.map((i, idx) => (
                  <li key={idx}>{i}</li>
                ))}
              </ul>
            </details>
          )}

          {meal.instructions && meal.instructions.length > 0 && (
            <details className="rounded-md bg-gray-50 p-3 text-sm">
              <summary className="cursor-pointer font-semibold">
                Instructions
              </summary>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-gray-700">
                {meal.instructions.map((i, idx) => (
                  <li key={idx}>{i}</li>
                ))}
              </ol>
            </details>
          )}

          <div className="flex flex-wrap gap-1.5 border-t pt-3">
            <Badge className="bg-orange-100 text-orange-800">
              <Flame className="mr-1 h-3 w-3" />
              {meal.nutrition.calories} kcal
            </Badge>
            <Badge className="bg-blue-100 text-blue-800">
              P {meal.nutrition.protein}g
            </Badge>
            <Badge className="bg-green-100 text-green-800">
              C {meal.nutrition.carbs}g
            </Badge>
            <Badge className="bg-yellow-100 text-yellow-800">
              F {meal.nutrition.fat}g
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function WeeklyView({ plan }: { plan: WeeklyPlanMap }) {
  const days = Object.entries(plan).filter(
    ([k, v]) => k !== "shopping_list" && v && typeof v === "object"
  )
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-xl font-bold gradient-text sm:text-2xl">
          7-Day Meal Plan
        </h3>
        <p className="text-sm text-gray-600">
          Your personalized weekly nutrition plan
        </p>
      </div>
      {days.map(([day, meals]) => (
        <Card key={day} className="card-hover">
          <CardHeader className="pb-3">
            <CardTitle className="capitalize text-base sm:text-lg">{day}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {(["breakfast", "lunch", "dinner", "snack"] as const).map(
                (mealType) => {
                  const meal = (meals as DailyMealsBundle)[mealType]
                  if (!meal) return null
                  return (
                    <div
                      key={mealType}
                      className="rounded-lg border border-gray-200 p-3 text-sm"
                    >
                      <div className="mb-1 text-[11px] font-semibold uppercase text-gray-500">
                        {mealType}
                      </div>
                      <p className="mb-1.5 line-clamp-2 font-medium text-gray-900">
                        {meal.name}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        <Badge className="bg-orange-100 text-orange-800 text-[10px]">
                          {meal.nutrition.calories} kcal
                        </Badge>
                        <Badge className="bg-blue-100 text-blue-800 text-[10px]">
                          {meal.nutrition.protein}g P
                        </Badge>
                      </div>
                    </div>
                  )
                }
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  )
}
