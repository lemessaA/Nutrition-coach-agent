"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, DollarSign, Users, ShoppingCart, Package, AlertCircle, RefreshCw } from 'lucide-react'

interface MarketData {
    trend_name: string
    description: string
    current_price: number
    price_change: number
    price_change_percentage: number
    market_demand: 'high' | 'medium' | 'low'
    popularity_score: number
    health_benefits: string[]
    market_insights: string[]
    recommendation: string
}

export default function MarketPage() {
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [marketData, setMarketData] = useState<MarketData[]>([])
    const [selectedCategory, setSelectedCategory] = useState('all')

    const categories = [
        { value: 'all', label: 'All Categories' },
        { value: 'organic', label: 'Organic Foods' },
        { value: 'plant-based', label: 'Plant-Based Products' },
        { value: 'supplements', label: 'Nutritional Supplements' },
        { value: 'functional', label: 'Functional Foods' }
    ]

    useEffect(() => {
        fetchMarketData()
    }, [selectedCategory])

    const fetchMarketData = async () => {
        setIsLoading(true)
        setError(null)

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            
            const response = await fetch(`${apiUrl}/api/v1/market-intelligence`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    category: selectedCategory,
                    analysis_type: 'trends'
                })
            })

            if (!response.ok) {
                const errData = await response.json()
                throw new Error(errData.detail || 'Failed to fetch market data')
            }

            const data = await response.json()
            setMarketData(data.market_data || [])
        } catch (err: any) {
            console.error('Error fetching market data:', err)
            setError(err.message || 'Failed to fetch market intelligence')
        } finally {
            setIsLoading(false)
        }
    }

    const getDemandColor = (demand: string) => {
        switch (demand) {
            case 'high': return 'bg-green-100 text-green-800 border-green-200'
            case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
            case 'low': return 'bg-red-100 text-red-800 border-red-200'
            default: return 'bg-gray-100 text-gray-800 border-gray-200'
        }
    }

    const getPriceChangeColor = (change: number) => {
        return change >= 0 ? 'text-green-600' : 'text-red-600'
    }

    const renderMarketCard = (item: MarketData) => (
        <Card className="card-hover">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-lg">{item.trend_name}</CardTitle>
                        <CardDescription className="text-sm">{item.description}</CardDescription>
                    </div>
                    <Badge variant="secondary" className={getDemandColor(item.market_demand)}>
                        {item.market_demand.toUpperCase()} DEMAND
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <DollarSign className="w-5 h-5 text-green-600" />
                            <span className="text-2xl font-bold">${item.current_price.toFixed(2)}</span>
                        </div>
                        <div className={`flex items-center gap-1 ${getPriceChangeColor(item.price_change)}`}>
                            {item.price_change >= 0 ? (
                                <TrendingUp className="w-4 h-4" />
                            ) : (
                                <TrendingUp className="w-4 h-4 rotate-180" />
                            )}
                            <span className="font-semibold">
                                {item.price_change >= 0 ? '+' : ''}{item.price_change_percentage.toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                            <Users className="w-6 h-6 mx-auto text-blue-600 mb-1" />
                            <div className="text-sm text-blue-700">Popularity Score</div>
                            <div className="text-xl font-bold text-blue-900">{item.popularity_score}</div>
                        </div>
                        <div className="text-center p-3 bg-purple-50 rounded-lg">
                            <Package className="w-6 h-6 mx-auto text-purple-600 mb-1" />
                            <div className="text-sm text-purple-700">Market Demand</div>
                            <div className="text-xl font-bold text-purple-900 capitalize">{item.market_demand}</div>
                        </div>
                    </div>

                    {item.health_benefits && item.health_benefits.length > 0 && (
                        <div className="border-t pt-4">
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <Package className="w-4 h-4 text-green-600" /> Health Benefits
                            </h4>
                            <div className="flex flex-wrap gap-1">
                                {item.health_benefits.map((benefit, idx) => (
                                    <Badge key={idx} variant="secondary" className="bg-green-100 text-green-800 border-green-200 text-xs">
                                        {benefit}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    )}

                    {item.market_insights && item.market_insights.length > 0 && (
                        <div className="border-t pt-4">
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-blue-600" /> Market Insights
                            </h4>
                            <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                                {item.market_insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {item.recommendation && (
                        <div className="border-t pt-4">
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                                <ShoppingCart className="w-4 h-4 text-orange-600" /> Recommendation
                            </h4>
                            <div className="bg-orange-50 p-3 rounded-lg border border-orange-100">
                                <p className="text-sm text-orange-900">{item.recommendation}</p>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl animate-fade-in">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold gradient-text mb-2">Market Intelligence</h1>
                <p className="text-gray-600">Nutrition market trends and insights for informed decisions</p>
            </div>

            {error && (
                <Card className="border-red-200 bg-red-50 mb-6">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
                            <div className="text-red-800">
                                <h3 className="font-semibold">Error</h3>
                                <p className="text-sm">{error}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="mb-6">
                <div className="flex flex-wrap gap-2 mb-4">
                    {categories.map((category) => (
                        <Button
                            key={category.value}
                            variant={selectedCategory === category.value ? "default" : "outline"}
                            onClick={() => setSelectedCategory(category.value)}
                            className="mb-2"
                        >
                            {category.label}
                        </Button>
                    ))}
                </div>
                <Button
                    onClick={fetchMarketData}
                    disabled={isLoading}
                    className="bg-blue-600 hover:bg-blue-700"
                >
                    {isLoading ? (
                        <span className="flex items-center gap-2">
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Analyzing Market...
                        </span>
                    ) : (
                        <span className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Analyze Trends
                        </span>
                    )}
                </Button>
            </div>

            {marketData.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {marketData.map((item, idx) => (
                        <div key={idx} className="animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
                            {renderMarketCard(item)}
                        </div>
                    ))}
                </div>
            ) : (
                <Card className="text-center py-12">
                    <CardContent>
                        <Package className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-600 mb-2">No Market Data Available</h3>
                        <p className="text-gray-500 mb-4">Select a category and analyze market trends to get started</p>
                        <Button 
                            onClick={fetchMarketData}
                            disabled={isLoading}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            {isLoading ? 'Analyzing...' : 'Analyze Market Trends'}
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}