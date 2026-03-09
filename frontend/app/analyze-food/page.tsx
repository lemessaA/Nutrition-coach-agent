"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, Utensils, Scale, Flame, Activity, AlertCircle, RefreshCw } from 'lucide-react'

interface NutritionData {
    calories: number
    protein: number
    carbs: number
    fat: number
    [key: string]: any
}

interface AnalysisResult {
    food_item?: string
    meal_description?: string
    calories?: number
    protein?: number
    carbs?: number
    fat?: number
    fiber?: number
    sugar?: number
    sodium?: number
    health_benefits?: string[]
    concerns?: string[]
    meal_quality_score?: number
    suggestions_for_improvement?: string[]
}

interface ComparisonFood {
    food_input: string
    nutrition: NutritionData
}

interface ComparisonResult {
    comparison: {
        foods: ComparisonFood[]
        insights?: string[]
        comparison_timestamp?: string
    }
}

export default function AnalyzeFoodPage() {
    const [activeTab, setActiveTab] = useState('single')

    // Input states
    const [singleFoodInput, setSingleFoodInput] = useState('')
    const [mealInput, setMealInput] = useState('')
    const [compareInput1, setCompareInput1] = useState('')
    const [compareInput2, setCompareInput2] = useState('')

    // Loading & Error states
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Result states
    const [singleResult, setSingleResult] = useState<AnalysisResult | null>(null)
    const [mealResult, setMealResult] = useState<AnalysisResult | null>(null)
    const [compareResult, setCompareResult] = useState<ComparisonResult | null>(null)

    const USER_ID = 1 // Hardcoded for prototype

    const handleAnalyze = async (endpoint: string, payload: any, resultSetter: Function) => {
        setIsLoading(true)
        setError(null)
        resultSetter(null)

        try {
            // Different endpoints have different parameter requirements
            let url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/${endpoint}`
            let requestBody = payload

            if (endpoint === 'analyze-food') {
                url += `?user_id=${USER_ID}`
            } else if (endpoint === 'analyze-meal') {
                url += `?meal_description=${encodeURIComponent(payload.meal_description)}&user_id=${USER_ID}`
                requestBody = undefined // Query params only
            } else if (endpoint === 'compare-foods') {
                url += `?user_id=${USER_ID}`
                requestBody = payload.foods // Expects a flat array of strings
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: requestBody ? JSON.stringify(requestBody) : undefined
            })

            if (!response.ok) {
                const errData = await response.json()
                throw new Error(errData.detail || 'Analysis failed')
            }

            const data = await response.json()

            // The API wraps responses in different property names depending on the endpoint
            if (endpoint === 'analyze-food') {
                // analyze-food returns the result DIRECTLY, not wrapped in an 'analysis' object
                // Wait, looking at the backend, it returns FoodAnalysisResponse directly
                resultSetter(data)
            } else if (endpoint === 'analyze-meal') {
                resultSetter(data.analysis)
            } else if (endpoint === 'compare-foods') {
                resultSetter(data)
            }

        } catch (err: any) {
            console.error(`Error with ${endpoint}:`, err)
            setError(err.message || 'An error occurred during analysis.')
        } finally {
            setIsLoading(false)
        }
    }

    const renderNutritionBadges = (item: any) => {
        if (!item) return null
        return (
            <div className="flex flex-wrap gap-2 mt-4">
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200 px-3 py-1">
                    <Flame className="w-4 h-4 mr-1.5" /> {item.calories || 0} kcal
                </Badge>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200 px-3 py-1">
                    Protein: {item.protein || 0}g
                </Badge>
                <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200 px-3 py-1">
                    Carbs: {item.carbs || 0}g
                </Badge>
                <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-200 px-3 py-1">
                    Fat: {item.fat || 0}g
                </Badge>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl animate-fade-in">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold gradient-text mb-2">Food Analyzer</h1>
                <p className="text-gray-600">Break down the nutritional value of any food or meal instantly.</p>
            </div>

            {error && (
                <Card className="border-red-200 bg-red-50 mb-6">
                    <CardContent className="pt-6 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
                        <div className="text-red-800">
                            <h3 className="font-semibold">Error</h3>
                            <p className="text-sm">{error}</p>
                        </div>
                    </CardContent>
                </Card>
            )}

            <Tabs defaultValue="single" value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3 mb-8">
                    <TabsTrigger value="single" className="flex items-center gap-2">
                        <Search className="w-4 h-4" /> Single Food
                    </TabsTrigger>
                    <TabsTrigger value="meal" className="flex items-center gap-2">
                        <Utensils className="w-4 h-4" /> Full Meal
                    </TabsTrigger>
                    <TabsTrigger value="compare" className="flex items-center gap-2">
                        <Scale className="w-4 h-4" /> Compare
                    </TabsTrigger>
                </TabsList>

                {/* --- SINGLE FOOD TAB --- */}
                <TabsContent value="single" className="space-y-6">
                    <Card className="card-hover">
                        <CardHeader>
                            <CardTitle>Analyze a Single Ingredient or Food</CardTitle>
                            <CardDescription>Enter a specific food item (e.g., "1 large banana", "100g chicken breast")</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    placeholder="e.g. 100g salmon"
                                    value={singleFoodInput}
                                    onChange={(e) => setSingleFoodInput(e.target.value)}
                                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={isLoading}
                                />
                                <Button
                                    onClick={() => handleAnalyze('analyze-food', { food_input: singleFoodInput }, setSingleResult)}
                                    disabled={!singleFoodInput.trim() || isLoading}
                                    className="bg-blue-600 hover:bg-blue-700 w-32"
                                >
                                    {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Analyze'}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {singleResult && (
                        <Card className="border-t-4 border-t-blue-500 animate-slide-up">
                            <CardHeader className="bg-gray-50 pb-4">
                                <CardTitle className="text-2xl capitalize">{singleResult.food_item || singleFoodInput}</CardTitle>
                                {renderNutritionBadges(singleResult)}
                            </CardHeader>
                            <CardContent className="pt-6 grid md:grid-cols-2 gap-6">
                                {singleResult.health_benefits && singleResult.health_benefits.length > 0 && (
                                    <div>
                                        <h4 className="font-semibold text-green-700 mb-2 flex items-center gap-2">
                                            <Activity className="w-4 h-4" /> Health Benefits
                                        </h4>
                                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                                            {singleResult.health_benefits.map((benefit, i) => <li key={i}>{benefit}</li>)}
                                        </ul>
                                    </div>
                                )}
                                {singleResult.concerns && singleResult.concerns.length > 0 && (
                                    <div>
                                        <h4 className="font-semibold text-orange-700 mb-2 flex items-center gap-2">
                                            <AlertCircle className="w-4 h-4" /> Things to Note
                                        </h4>
                                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                                            {singleResult.concerns.map((concern, i) => <li key={i}>{concern}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                {/* --- FULL MEAL TAB --- */}
                <TabsContent value="meal" className="space-y-6">
                    <Card className="card-hover">
                        <CardHeader>
                            <CardTitle>Analyze a Complete Meal</CardTitle>
                            <CardDescription>Describe your full meal in detail for a comprehensive breakdown.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Textarea
                                placeholder="e.g. 2 scrambled eggs cooked in butter, 2 slices of whole wheat toast, and a cup of black coffee."
                                value={mealInput}
                                onChange={(e) => setMealInput(e.target.value)}
                                className="mb-4 min-h-[120px]"
                                disabled={isLoading}
                            />
                            <Button
                                onClick={() => handleAnalyze('analyze-meal', { meal_description: mealInput }, setMealResult)}
                                disabled={!mealInput.trim() || isLoading}
                                className="bg-blue-600 hover:bg-blue-700 w-full"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Analyzing Meal...</span>
                                ) : 'Analyze Full Meal'}
                            </Button>
                        </CardContent>
                    </Card>

                    {mealResult && (
                        <Card className="border-t-4 border-t-purple-500 animate-slide-up">
                            <CardHeader className="bg-gray-50 flex flex-row items-start justify-between pb-4">
                                <div>
                                    <CardTitle className="text-xl leading-relaxed max-w-2xl">{mealResult.meal_description || mealInput}</CardTitle>
                                    {renderNutritionBadges(mealResult)}
                                </div>
                                {mealResult.meal_quality_score && (
                                    <div className="text-center bg-white p-3 rounded-xl shadow-sm border">
                                        <div className="text-3xl font-bold text-purple-600">{mealResult.meal_quality_score}</div>
                                        <div className="text-xs text-gray-500 uppercase font-semibold">Quality Score</div>
                                    </div>
                                )}
                            </CardHeader>
                            <CardContent className="pt-6">
                                {mealResult.suggestions_for_improvement && mealResult.suggestions_for_improvement.length > 0 && (
                                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                                        <h4 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                                            <Flame className="w-4 h-4" /> Suggestions for Improvement
                                        </h4>
                                        <ul className="list-disc pl-5 text-sm text-purple-900 space-y-2">
                                            {mealResult.suggestions_for_improvement.map((sug, i) => <li key={i}>{sug}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>

                {/* --- COMPARE FOODS TAB --- */}
                <TabsContent value="compare" className="space-y-6">
                    <Card className="card-hover">
                        <CardHeader>
                            <CardTitle>Compare Two Foods</CardTitle>
                            <CardDescription>See a side-by-side nutritional breakdown to make better choices.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Food 1</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. 1 cup white rice"
                                        value={compareInput1}
                                        onChange={(e) => setCompareInput1(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={isLoading}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Food 2</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. 1 cup brown rice"
                                        value={compareInput2}
                                        onChange={(e) => setCompareInput2(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={isLoading}
                                    />
                                </div>
                            </div>
                            <Button
                                onClick={() => handleAnalyze('compare-foods', { foods: [compareInput1, compareInput2] }, setCompareResult)}
                                disabled={!compareInput1.trim() || !compareInput2.trim() || isLoading}
                                className="bg-blue-600 hover:bg-blue-700 w-full"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Comparing...</span>
                                ) : 'Compare Nutritional Value'}
                            </Button>
                        </CardContent>
                    </Card>

                    {compareResult && compareResult.comparison && compareResult.comparison.foods && (
                        <div className="space-y-6 animate-slide-up">
                            <div className="grid md:grid-cols-2 gap-6">
                                {compareResult.comparison.foods.map((food, idx) => (
                                    <Card key={idx}>
                                        <CardHeader className="pb-2">
                                            <div className="flex justify-between items-center">
                                                <CardTitle className="capitalize text-lg">{food.food_input}</CardTitle>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            {renderNutritionBadges(food.nutrition)}
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {compareResult.comparison.insights && compareResult.comparison.insights.length > 0 && (
                                <Card className="bg-gray-50 border-gray-200">
                                    <CardContent className="pt-6">
                                        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                            <Activity className="w-4 h-4 text-blue-600" /> Key Insights
                                        </h4>
                                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-2">
                                            {compareResult.comparison.insights.map((insight, i) => (
                                                <li key={i}>{insight}</li>
                                            ))}
                                        </ul>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    )
}
