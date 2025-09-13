"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Search, Brain, Mic, Coins, FileText } from "lucide-react"
import PDFUpload from "@/components/pdf-upload"
import { motion } from "framer-motion"
import { AuthHeader } from "@/components/auth-header"

export default function HomePage() {
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    setIsLoading(true)
    setError(null)
    setResults([])
    try {
      const response = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })
      if (!response.ok) throw new Error("Failed to fetch results")
      const data = await response.json()
      setResults(data.results || [])
    } catch (err: any) {
      setError(err.message || "Error fetching results")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-purple-800">
      <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="text-white font-bold text-xl">Research Assistant</div>
        <AuthHeader />
      </nav>

      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl font-bold text-white mb-6">Agentic Research Assistant</h1>
          <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Streamline academic research with AI-powered agents that find, summarize, synthesize, and present
            information from papers automatically.
          </p>
        </motion.div>

        {/* Search Bar and Results */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="flex gap-4">
            <Input
              placeholder="Enter research topic (e.g., 'quantum computing ethics')"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 h-12 text-lg bg-white/90 backdrop-blur-sm"
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button
              onClick={handleSearch}
              disabled={isLoading}
              className="h-12 px-8 bg-white text-purple-600 hover:bg-gray-100"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600" />
              ) : (
                <Search className="h-5 w-5 mr-2" />
                )}
              Search
            </Button>
          </div>
          {/* Results Display */}
          {error && <div className="text-red-500 mt-4">{error}</div>}
          {results.length > 0 && (
            <div className="mt-6 bg-white/80 rounded-lg p-4 shadow">
              <h2 className="text-xl font-bold mb-2 text-purple-700">Search Results</h2>
              <ul className="space-y-3">
                {results.map((item, idx) => (
                  <li key={idx} className="border-b pb-2">
                    <div className="font-semibold text-purple-800">{item.title}</div>
                    <div className="text-sm text-gray-700">{item.authors?.join(", ")}</div>
                    <div className="text-gray-600 mt-1">{item.abstract}</div>
                    {item.url && (
                      <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline text-sm">View Paper</a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Feature Cards Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-10">
          <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 transition-all duration-300">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <Brain className="h-6 w-6 text-white" />
                </div>
                <CardTitle>AI Synthesis</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-blue-100">
                Intelligent summarization and synthesis with gap analysis and recommendations
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 transition-all duration-300">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500 rounded-lg">
                  <Mic className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Voice Narration</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-blue-100">
                Natural audio presentation with ElevenLabs voice synthesis
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 transition-all duration-300">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-500 rounded-lg">
                  <FileText className="h-6 w-6 text-white" />
                </div>
                <CardTitle>PDF Analysis</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-blue-100">
                Deep PDF parsing with citation mapping and literature review generation
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 transition-all duration-300">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500 rounded-lg">
                  <Upload className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Plagiarism Check</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-blue-100">
                Advanced plagiarism detection and humanization scoring
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 transition-all duration-300">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-500 rounded-lg">
                  <Coins className="h-6 w-6 text-white" />
                </div>
                <CardTitle>NFT Minting</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-blue-100">
                Monetize research reports through Crossmint NFT integration
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex justify-center gap-4"
        >
          <div className="w-full max-w-md mx-auto">
            <PDFUpload />
          </div>
          <Button
            size="lg"
            variant="outline"
            className="border-white text-white hover:bg-white hover:text-purple-600 bg-transparent"
          >
            View Demo
          </Button>
        </motion.div>
      </div>
    </div>
  )
}
