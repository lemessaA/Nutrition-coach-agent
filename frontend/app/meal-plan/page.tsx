"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar, Clock, Users, ChefHat, Target, TrendingUp, Utensils, Flame } from 'lucide-react'

interface Meal {
    name: string
    description: string
    ingredients: string[]
    instructions: string[]
    nutrition: {
        calories: number
        protein: number
        carbs: number
        fat: number
    }
    prep_time: string
}

interface MealPlan {
    id: number
    user_id: number
    plan_type: string
    plan_date: string
    meals: {
        meals: {
            breakfast: Meal
            lunch: Meal
            dinner: Meal
            snack: Meal
        }
        daily_totals: {
            calories: number
            protein: number
            carbs: number
            fat: number
        }
    }
    total_calories: number
    total_protein: number
    total_carbs: number
    total_fat: number
    created_at: string
}

export default function MealPlanPage() {
    const [activeTab, setActiveTab] = useState('current')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [currentPlan, setCurrentPlan] = useState<MealPlan | null>(null)
    const [weeklyPlan, setWeeklyPlan] = useState<MealPlan | null>(null)
    const [userProfile, setUserProfile] = useState<any>(null)

    const USER_ID = 18 // Use the weight loss test user we created

    useEffect(() => {
        fetchUserProfile()
        fetchCurrentMealPlan()
    }, [])

    const fetchUserProfile = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/api/v1/profile/${USER_ID}/health`)
            
            if (response.ok) {
                const data = await response.json()
                setUserProfile(data)
            }
        } catch (err) {
            console.error('Error fetching user profile:', err)
        }
    }

    const fetchCurrentMealPlan = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const response = await fetch(`${apiUrl}/api/v1/meal-plan?user_id=${USER_ID}&plan_type=daily`)
            
            if (response.ok) {
                const data = await response.json()
                if (data && data.length > 0) {
                    setCurrentPlan(data[0])
                }
            }
        } catch (err) {
            console.error('Error fetching current meal plan:', err)
        }
    }

    const generateMealPlan = async (planType: 'daily' | 'weekly') => {
        setIsLoading(true)
        setError(null)

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const targetCalories = userProfile?.target_calories || 2000
            
            const response = await fetch(`${apiUrl}/api/v1/meal-plan?user_id=${USER_ID}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plan_type: planType,
                    preferences: { high_protein: userProfile?.goal === 'gain_muscle' },
                    dietary_restrictions: userProfile?.dietary_restrictions || [],
                    target_calories: targetCalories
                })
            })

            if (response.ok) {
                const data = await response.json()
                if (planType === 'daily') {
                    setCurrentPlan(data)
                } else {
                    setWeeklyPlan(data)
                }
            } else {
                throw new Error('Failed to generate meal plan')
            }
        } catch (err: any) {
            console.error('Error generating meal plan:', err)
            setError(err.message || 'Failed to generate meal plan')
        } finally {
            setIsLoading(false)
        }
    }

    const renderMealCard = (meal: Meal, mealType: string) => (
        <Card className="card-hover">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="capitalize text-lg">{meal.name}</CardTitle>
                        <CardDescription className="text-sm">{meal.description}</CardDescription>
                    </div>
                    <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        {mealType}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        <span>{meal.prep_time}</span>
                    </div>
                    
                    <div>
                        <h4 className="font-semibold mb-2 flex items-center gap-2">
                            <Utensils className="w-4 h-4" /> Ingredients
                        </h4>
                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                            {meal.ingredients.map((ingredient, idx) => (
                                <li key={idx}>{ingredient}</li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-semibold mb-2">Instructions</h4>
                        <ol className="list-decimal pl-5 text-sm text-gray-600 space-y-1">
                            {meal.instructions.map((instruction, idx) => (
                                <li key={idx}>{instruction}</li>
                            ))}
                        </ol>
                    </div>

                    <div className="flex flex-wrap gap-2 pt-3 border-t">
                        <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200 px-3 py-1">
                            <Flame className="w-3 h-3 mr-1" /> {meal.nutrition.calories} kcal
                        </Badge>
                        <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200 px-3 py-1">
                            Protein: {meal.nutrition.protein}g
                        </Badge>
                        <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200 px-3 py-1">
                            Carbs: {meal.nutrition.carbs}g
                        </Badge>
                        <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-200 px-3 py-1">
                            Fat: {meal.nutrition.fat}g
                        </Badge>
                    </div>
                </div>
            </CardContent>
        </Card>
    )

    const renderDailyPlan = (plan: MealPlan) => (
        <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4 mb-6">
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <Target className="w-8 h-8 text-blue-600" />
                            <div>
                                <h3 className="font-semibold text-blue-900">Daily Targets</h3>
                                <p className="text-sm text-blue-700">Based on your profile</p>
                            </div>
                        </div>
                        <div className="mt-4 space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-blue-700">Calories:</span>
                                <span className="font-semibold">{plan.total_calories}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-blue-700">Protein:</span>
                                <span className="font-semibold">{plan.total_protein}g</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-blue-700">Carbs:</span>
                                <span className="font-semibold">{plan.total_carbs}g</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-blue-700">Fat:</span>
                                <span className="font-semibold">{plan.total_fat}g</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-50 to-emerald-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-3">
                            <TrendingUp className="w-8 h-8 text-green-600" />
                            <div>
                                <h3 className="font-semibold text-green-900">Daily Totals</h3>
                                <p className="text-sm text-green-700">What you'll consume today</p>
                            </div>
                        </div>
                        <div className="mt-4 space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-green-700">Total Calories:</span>
                                <span className="font-semibold">{plan.meals.meals.daily_totals.calories}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-green-700">Total Protein:</span>
                                <span className="font-semibold">{plan.meals.meals.daily_totals.protein}g</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-green-700">Total Carbs:</span>
                                <span className="font-semibold">{plan.meals.meals.daily_totals.carbs}g</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-green-700">Total Fat:</span>
                                <span className="font-semibold">{plan.meals.meals.daily_totals.fat}g</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
                {renderMealCard(plan.meals.meals.breakfast, 'Breakfast')}
                {renderMealCard(plan.meals.meals.lunch, 'Lunch')}
            </div>
            <div className="grid md:grid-cols-2 gap-6">
                {renderMealCard(plan.meals.meals.dinner, 'Dinner')}
                {renderMealCard(plan.meals.meals.snack, 'Snack')}
            </div>
        </div>
    )

    const renderWeeklyPlan = (plan: MealPlan) => (
        <div className="space-y-6">
            <div className="text-center mb-6">
                <h3 className="text-2xl font-bold gradient-text">7-Day Meal Plan</h3>
                <p className="text-gray-600">Your personalized weekly nutrition plan</p>
            </div>
            
            {Object.keys(plan.meals.meals).map((day) => (
                <Card key={day} className="card-hover">
                    <CardHeader>
                        <CardTitle className="capitalize text-lg">{day}</CardTitle>
                        <CardDescription>Daily meals and nutrition</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-2 gap-4">
                            {Object.entries(plan.meals.meals[day as keyof typeof plan.meals.meals]).map(([mealType, meal]: [string, any]) => (
                                <div key={mealType} className="border rounded-lg p-3">
                                    <h4 className="font-semibold capitalize mb-2">{mealType}</h4>
                                    <p className="text-sm text-gray-600 mb-2">{meal.name}</p>
                                    <div className="flex flex-wrap gap-1">
                                        <Badge variant="secondary" className="text-xs">
                                            {meal.nutrition.calories} kcal
                                        </Badge>
                                        <Badge variant="secondary" className="text-xs">
                                            {meal.nutrition.protein}g protein
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl animate-fade-in">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold gradient-text mb-2">Meal Planner</h1>
                <p className="text-gray-600">Personalized meal plans tailored to your health goals</p>
            </div>

            {error && (
                <Card className="border-red-200 bg-red-50 mb-6">
                    <CardContent className="pt-6">
                        <div className="text-red-800">
                            <h3 className="font-semibold">Error</h3>
                            <p className="text-sm">{error}</p>
                        </div>
                    </CardContent>
                </Card>
            )}

            <Tabs defaultValue="current" value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3 mb-8">
                    <TabsTrigger value="current" className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" /> Current Plan
                    </TabsTrigger>
                    <TabsTrigger value="generate" className="flex items-center gap-2">
                        <ChefHat className="w-4 h-4" /> Generate
                    </TabsTrigger>
                    <TabsTrigger value="weekly" className="flex items-center gap-2">
                        <Users className="w-4 h-4" /> Weekly View
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="current" className="space-y-6">
                    {currentPlan ? (
                        renderDailyPlan(currentPlan)
                    ) : (
                        <Card className="text-center py-12">
                            <CardContent>
                                <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                                <h3 className="text-lg font-semibold text-gray-600 mb-2">No Current Meal Plan</h3>
                                <p className="text-gray-500 mb-4">Generate your first personalized meal plan to get started</p>
                                <Button 
                                    onClick={() => setActiveTab('generate')}
                                    className="bg-blue-600 hover:bg-blue-700"
                                >
                                    Generate Meal Plan
                                </Button>
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                <TabsContent value="generate" className="space-y-6">
                    <Card className="card-hover">
                        <CardHeader>
                            <CardTitle>Generate New Meal Plan</CardTitle>
                            <CardDescription>Create a personalized meal plan based on your profile</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid md:grid-cols-2 gap-4">
                                <Button
                                    onClick={() => generateMealPlan('daily')}
                                    disabled={isLoading}
                                    className="bg-blue-600 hover:bg-blue-700 h-20 flex flex-col items-center justify-center gap-2"
                                >
                                    <ChefHat className="w-6 h-6" />
                                    <span>{isLoading ? 'Generating...' : 'Daily Plan'}</span>
                                </Button>
                                <Button
                                    onClick={() => generateMealPlan('weekly')}
                                    disabled={isLoading}
                                    className="bg-green-600 hover:bg-green-700 h-20 flex flex-col items-center justify-center gap-2"
                                >
                                    <Users className="w-6 h-6" />
                                    <span>{isLoading ? 'Generating...' : 'Weekly Plan'}</span>
                                </Button>
                            </div>
                            {userProfile && (
                                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                                    <h4 className="font-semibold mb-2">Your Profile</h4>
                                    <div className="text-sm text-gray-600 space-y-1">
                                        <p>Goal: {userProfile.goal}</p>
                                        <p>Activity Level: {userProfile.activity_level}</p>
                                        <p>Target Calories: {userProfile.target_calories}</p>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="weekly" className="space-y-6">
                    {weeklyPlan ? (
                        renderWeeklyPlan(weeklyPlan)
                    ) : (
                        <Card className="text-center py-12">
                            <CardContent>
                                <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                                <h3 className="text-lg font-semibold text-gray-600 mb-2">No Weekly Plan</h3>
                                <p className="text-gray-500 mb-4">Generate a weekly meal plan to see your full week</p>
                                <Button 
                                    onClick={() => setActiveTab('generate')}
                                    className="bg-green-600 hover:bg-green-700"
                                >
                                    Generate Weekly Plan
                                </Button>
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    )
}