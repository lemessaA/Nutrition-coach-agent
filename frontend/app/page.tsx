import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, Brain, Calculator, Heart, MessageSquare, TrendingUp } from 'lucide-react'

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-6xl font-bold gradient-text mb-6 animate-fade-in">
          Nutrition Coach AI
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto animate-slide-up">
          Your personal AI nutrition coach for meal planning, nutrition advice, and building healthy habits.
          Get personalized recommendations powered by advanced AI technology.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up">
          <Link href="/chat">
            <Button size="lg" className="bg-green-600 hover:bg-green-700 btn-glow">
              Start Chatting
            </Button>
          </Link>
          <Link href="/profile">
            <Button variant="outline" size="lg" className="btn-glow">
              Create Profile
            </Button>
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-green-600" />
              AI-Powered Coaching
            </CardTitle>
            <CardDescription>
              Get personalized nutrition advice from our intelligent AI coach
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Advanced AI agents provide personalized meal plans, nutrition insights, and habit coaching tailored to your goals.
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Personalized Meal Plans
            </CardTitle>
            <CardDescription>
              Custom meal plans based on your health profile and goals
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Generate daily or weekly meal plans with recipes, shopping lists, and nutritional information.
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-purple-600" />
              Food Analysis
            </CardTitle>
            <CardDescription>
              Analyze meals and track your nutritional intake
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Get detailed nutritional breakdowns of your meals and track calories, macros, and micronutrients.
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="h-5 w-5 text-red-600" />
              Health Profile
            </CardTitle>
            <CardDescription>
              Comprehensive health profile management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Track your health metrics, set goals, and get personalized nutritional targets.
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-indigo-600" />
              Nutrition Q&A
            </CardTitle>
            <CardDescription>
              Ask questions about nutrition and health
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Get evidence-based answers to your nutrition questions from our knowledge base.
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-orange-600" />
              Progress Tracking
            </CardTitle>
            <CardDescription>
              Monitor your nutrition journey and progress
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Track your nutritional intake, monitor progress toward goals, and get insights.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* How It Works */}
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-green-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold mb-2">Create Profile</h3>
            <p className="text-sm text-gray-600">
              Tell us about your health goals, preferences, and lifestyle
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold mb-2">Get Personalized Plans</h3>
            <p className="text-sm text-gray-600">
              Receive customized meal plans and nutrition recommendations
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-purple-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold mb-2">Track Progress</h3>
            <p className="text-sm text-gray-600">
              Monitor your nutrition intake and track your progress
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-orange-600 font-bold">4</span>
            </div>
            <h3 className="font-semibold mb-2">Achieve Goals</h3>
            <p className="text-sm text-gray-600">
              Reach your health goals with AI-powered guidance and support
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-lg p-8 text-center text-white">
        <h2 className="text-3xl font-bold mb-4">
          Ready to Start Your Nutrition Journey?
        </h2>
        <p className="text-lg mb-6">
          Join thousands of users who have transformed their health with personalized AI nutrition coaching.
        </p>
        <Link href="/chat">
          <Button size="lg" variant="secondary" className="bg-white text-gray-900 hover:bg-gray-100">
            Get Started Free
          </Button>
        </Link>
      </div>
    </div>
  )
}