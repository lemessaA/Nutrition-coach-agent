import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Utensils, Flame } from 'lucide-react'

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

interface MealPlanCardProps {
    meal: Meal
    mealType: string
    className?: string
}

export default function MealPlanCard({ meal, mealType, className = "" }: MealPlanCardProps) {
    return (
        <Card className={`card-hover ${className}`}>
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="capitalize text-lg">{meal.name}</CardTitle>
                        <p className="text-sm text-gray-600 mt-1">{meal.description}</p>
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
}