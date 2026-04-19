"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { User, Heart, Target, Activity, Save, Calculator, AlertCircle as AlertTriangle } from 'lucide-react'

interface UserProfile {
  email: string
  fullName: string
  age: string
  weight: string
  height: string
  gender: 'male' | 'female' | 'other'
  activityLevel: 'sedentary' | 'lightly_active' | 'moderately_active' | 'very_active' | 'extra_active'
  goal: 'lose_weight' | 'gain_muscle' | 'maintain_health'
  dietaryRestrictions: string[]
  allergies: string[]
  preferences: string[]
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>({
    email: '',
    fullName: '',
    age: '',
    weight: '',
    height: '',
    gender: 'male',
    activityLevel: 'moderately_active',
    goal: 'maintain_health',
    dietaryRestrictions: [],
    allergies: [],
    preferences: []
  })

  const [calculatedTargets, setCalculatedTargets] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [savedProfile, setSavedProfile] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    setProfile(prev => ({ ...prev, [field]: value }))
  }

  const handleArrayInput = (field: 'dietaryRestrictions' | 'allergies' | 'preferences', value: string) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item)
    setProfile(prev => ({ ...prev, [field]: items }))
  }

  const calculateTargets = async () => {
    setIsLoading(true)
    try {
      // Simulate API call to calculate targets
      const mockTargets = {
        bmr: 1650,
        tdee: 2200,
        targetCalories: 2000,
        targetProtein: 120,
        targetCarbs: 250,
        targetFat: 67
      }
      setCalculatedTargets(mockTargets)
    } catch (error) {
      console.error('Error calculating targets:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const saveProfile = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Validate required fields
      if (!profile.age || !profile.weight || !profile.height || !profile.gender || !profile.activityLevel || !profile.goal) {
        throw new Error('Please fill in all required fields (age, weight, height, gender, activity level, and goal)')
      }

      // Make API call to save health profile
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('API URL:', apiUrl)
      
      // First create basic user if needed
      const basicProfile = {
        email: profile.email || 'user@example.com',
        full_name: profile.fullName || 'User'
      }
      
      const userResponse = await fetch(`${apiUrl}/api/v1/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(basicProfile)
      })

      if (!userResponse.ok) {
        throw new Error('Failed to create user profile')
      }

      const userData = await userResponse.json()
      const userId = userData.id

      // Then save health profile
      const healthProfile = {
        age: parseInt(profile.age) || 0,
        weight: parseFloat(profile.weight) || 0,
        height: parseFloat(profile.height) || 0,
        gender: profile.gender,
        activity_level: profile.activityLevel,
        goal: profile.goal,
        dietary_restrictions: profile.dietaryRestrictions,
        allergies: profile.allergies,
        preferences: profile.preferences
      }

      const healthResponse = await fetch(`${apiUrl}/api/v1/profile/${userId}/health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(healthProfile)
      })

      if (healthResponse.ok) {
        const data = await healthResponse.json()
        setSavedProfile(true)
        setTimeout(() => setSavedProfile(false), 3000)
        console.log('Health profile saved:', data)
      } else {
        throw new Error('Failed to save health profile')
      }
    } catch (error) {
      console.error('Error saving profile:', error)
      setError(error.message || 'Failed to save profile')
    } finally {
      setIsLoading(false)
    }
  }

  const activityLevels = [
    { value: 'sedentary', label: 'Sedentary (little or no exercise)' },
    { value: 'lightly_active', label: 'Lightly Active (1-3 days/week)' },
    { value: 'moderately_active', label: 'Moderately Active (3-5 days/week)' },
    { value: 'very_active', label: 'Very Active (6-7 days/week)' },
    { value: 'extra_active', label: 'Extra Active (very hard exercise/physical job)' }
  ]

  const goals = [
    { value: 'lose_weight', label: 'Lose Weight', color: 'bg-red-100 text-red-800' },
    { value: 'gain_muscle', label: 'Gain Muscle', color: 'bg-blue-100 text-blue-800' },
    { value: 'maintain_health', label: 'Maintain Health', color: 'bg-green-100 text-green-800' }
  ]

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold gradient-text mb-2">Health Profile</h1>
        <p className="text-gray-600">Create your personalized nutrition profile</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">Error</span>
          </div>
          <p className="text-red-700 text-sm mt-1">{error}</p>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Profile Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card className="card-hover">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Basic Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="your@email.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.fullName}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    value={profile.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    value={profile.weight}
                    onChange={(e) => handleInputChange('weight', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="70"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    value={profile.height}
                    onChange={(e) => handleInputChange('height', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="175"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={profile.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Activity Level
                  </label>
                  <select
                    value={profile.activityLevel}
                    onChange={(e) => handleInputChange('activityLevel', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {activityLevels.map(level => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Goals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Health Goal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {goals.map(goal => (
                  <div
                    key={goal.value}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      profile.goal === goal.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleInputChange('goal', goal.value)}
                  >
                    <Badge className={goal.color}>
                      {goal.label}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Dietary Preferences */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Dietary Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dietary Restrictions (comma-separated)
                </label>
                <input
                  type="text"
                  value={profile.dietaryRestrictions.join(', ')}
                  onChange={(e) => handleArrayInput('dietaryRestrictions', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="vegetarian, gluten-free, dairy-free"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Allergies (comma-separated)
                </label>
                <input
                  type="text"
                  value={profile.allergies.join(', ')}
                  onChange={(e) => handleArrayInput('allergies', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="nuts, shellfish, soy"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Food Preferences (comma-separated)
                </label>
                <input
                  type="text"
                  value={profile.preferences.join(', ')}
                  onChange={(e) => handleArrayInput('preferences', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="chicken, fish, rice, pasta"
                />
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              onClick={calculateTargets}
              disabled={isLoading || !profile.age || !profile.weight || !profile.height}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Calculator className="h-4 w-4" />
              Calculate Targets
            </Button>
            <Button
              onClick={saveProfile}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              Save Profile
            </Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Calculated Targets */}
          {calculatedTargets && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Your Targets
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">BMR</span>
                    <span className="font-semibold">{calculatedTargets.bmr} kcal</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">TDEE</span>
                    <span className="font-semibold">{calculatedTargets.tdee} kcal</span>
                  </div>
                  <hr />
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Target Calories</span>
                    <span className="font-semibold text-blue-600">{calculatedTargets.targetCalories} kcal</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Protein</span>
                    <span className="font-semibold">{calculatedTargets.targetProtein}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Carbs</span>
                    <span className="font-semibold">{calculatedTargets.targetCarbs}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Fat</span>
                    <span className="font-semibold">{calculatedTargets.targetFat}g</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* BMI Calculator */}
          {profile.age && profile.weight && profile.height && (
            <Card>
              <CardHeader>
                <CardTitle>BMI Calculator</CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const bmi = parseFloat(profile.weight) / Math.pow(parseFloat(profile.height) / 100, 2)
                  const bmiCategory = bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Normal' : bmi < 30 ? 'Overweight' : 'Obese'
                  const categoryColor = bmi < 18.5 ? 'text-blue-600' : bmi < 25 ? 'text-green-600' : bmi < 30 ? 'text-orange-600' : 'text-red-600'
                  
                  return (
                    <div className="space-y-2">
                      <div className="text-center">
                        <div className="text-2xl font-bold">{bmi.toFixed(1)}</div>
                        <div className={`text-sm font-medium ${categoryColor}`}>{bmiCategory}</div>
                      </div>
                    </div>
                  )
                })()}
              </CardContent>
            </Card>
          )}

          {/* Success Message */}
          {savedProfile && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="text-center text-green-800">
                  <div className="text-lg font-semibold mb-1">Profile Saved!</div>
                  <div className="text-sm">Your profile has been successfully saved.</div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}