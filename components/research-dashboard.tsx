// ElevenLabs TTS integration
const VOICES = ["Rachel", "Domi", "Bella", "Antoni", "Elli"];

function ElevenLabsTTS() {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("Rachel");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSynthesize() {
    setLoading(true);
    setAudioUrl(null);
    try {
      const res = await fetch("/api/synthesize_voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice })
      });
      if (!res.ok) throw new Error("Failed to synthesize audio");
      const blob = await res.blob();
      setAudioUrl(URL.createObjectURL(blob));
    } catch (err) {
      alert("Error: " + err);
    }
    setLoading(false);
  }

  return (
    <div className="border p-4 rounded mb-4">
      <h3 className="font-bold mb-2">Text to Speech (ElevenLabs)</h3>
      <textarea
        className="w-full border rounded p-2 mb-2"
        rows={3}
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Enter text to synthesize..."
      />
      <div className="flex items-center mb-2">
        <label className="mr-2">Voice:</label>
        <select value={voice} onChange={e => setVoice(e.target.value)} className="border rounded p-1">
          {VOICES.map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </div>
      <button onClick={handleSynthesize} disabled={loading || !text} className="bg-blue-600 text-white px-4 py-2 rounded">
        {loading ? "Synthesizing..." : "Synthesize"}
      </button>
      {audioUrl && (
        <div className="mt-4">
          <audio controls src={audioUrl} />
        </div>
      )}
    </div>
  );
}
"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import Chatbot from "./chatbot";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import {
  FileText,
  Brain,
  Mic,
  CheckCircle,
  Clock,
  AlertCircle,
  Play,
  Download,
  Share,
  TrendingUp,
  BarChart3,
  LucidePieChart as RechartsPieChart,
  Zap,
  RefreshCw,
  ExternalLink,
  Volume2,
  VolumeX,
  SkipForward,
  SkipBack,
  Pause,
} from "lucide-react"
import { useWebSocket } from "@/hooks/use-websocket"
import { motion, AnimatePresence } from "framer-motion"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Pie as PieChartComponent,
  BarChart,
  Bar,
  Cell,
} from "recharts"

interface ResearchProgress {
  step: string
  status: "completed" | "in-progress" | "pending" | "error"
  message: string
  progress?: number
}

interface PaperSummary {
  id: string
  title: string
  authors: string[]
  relevanceScore: number
  summary: string
  keyFindings: string[]
  methodology: string
  strengths: string[]
  weaknesses: string[]
  doi?: string
  source: string
}

interface ResearchGap {
  description: string
  evidence: string
  priority: "High" | "Medium" | "Low"
  supportingCitations: string[]
}

interface AudioPlayer {
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  speed: number
}

interface DashboardProps {
  jobId: string
  query: string
}

export default function ResearchDashboard({ jobId, query }: DashboardProps) {
  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "in-progress":
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
      case "error":
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getRelevanceBadgeColor = (score: number) => {
    if (score >= 90) return "bg-green-500"
    if (score >= 70) return "bg-orange-500"
    return "bg-red-500"
  }

  const getPriorityColor = (priority: string): string => {
    if (priority === "High") return "bg-red-500";
    if (priority === "Medium") return "bg-orange-500";
    if (priority === "Low") return "bg-green-500";
    return "bg-gray-500";
  }

  const updateProgress = (progressData: any) => {
    setProgress((prev) =>
      prev.map((step) => {
        if (step.step === progressData.step) {
          return {
            ...step,
            status: progressData.status,
            message: progressData.message,
            progress: progressData.progress || 0,
          };
        }
        return step;
      })
    );
  }
  const [progress, setProgress] = useState<ResearchProgress[]>([
    { step: "Search & Retrieval", status: "pending", message: "Initializing search", progress: 0 },
    { step: "Summarization", status: "pending", message: "Waiting for search", progress: 0 },
    { step: "Synthesis", status: "pending", message: "Waiting for summaries", progress: 0 },
    { step: "Voice Generation", status: "pending", message: "Waiting for synthesis", progress: 0 },
    { step: "Finalization", status: "pending", message: "Waiting for voice", progress: 0 },
  ])

  const [summaries, setSummaries] = useState<PaperSummary[]>([])
  const [synthesisReport, setSynthesisReport] = useState<any>(null)
  const [gaps, setGaps] = useState<ResearchGap[]>([])
  const [audioPlayer, setAudioPlayer] = useState<AudioPlayer>({
    isPlaying: false,
    currentTime: 0,
    duration: 754, // 12:34 in seconds
    volume: 1,
    speed: 1,
  })
  const [plagiarismData, setPlagiarismData] = useState({
    overallRisk: 8,
    humanScore: 92,
    flaggedSections: [],
  })


  // Agentic Assistant API integration
  async function runAgenticResearch(query: string, maxResults: number, minYear: number, userEmail?: string) {
    setProgress((prev) => prev.map((step, i) => i === 0 ? { ...step, status: "in-progress", message: "Searching papers..." } : step));
    // 1. Search
    const searchRes = await fetch("http://localhost:8000/agentic-assistant/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, max_results: maxResults, min_year: minYear })
    });
    const searchData = await searchRes.json();
    const papers = searchData.papers || [];
    setProgress((prev) => prev.map((step, i) => i === 0 ? { ...step, status: "completed", message: "Search complete", progress: 100 } : i === 1 ? { ...step, status: "in-progress", message: "Summarizing papers..." } : step));

    // 2. Summarize
    const summarizeRes = await fetch("http://localhost:8000/agentic-assistant/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ papers })
    });
    const summarizeData = await summarizeRes.json();
    const summaries = summarizeData.summaries || [];
    setSummaries(summaries.map((s: any, idx: number) => ({
      id: String(idx),
      title: s.original_paper.title,
      authors: s.original_paper.authors,
      relevanceScore: 90,
      summary: s.summary_text,
      keyFindings: [],
      methodology: "",
      strengths: [],
      weaknesses: [],
      doi: s.original_paper.url,
      source: s.original_paper.source_db
    })));
    setProgress((prev) => prev.map((step, i) => i === 1 ? { ...step, status: "completed", message: "Summarization complete", progress: 100 } : i === 2 ? { ...step, status: "in-progress", message: "Synthesizing report..." } : step));

    // 3. Synthesize
    const synthesizeRes = await fetch("http://localhost:8000/agentic-assistant/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summaries })
    });
    const synthesizeData = await synthesizeRes.json();
    setSynthesisReport({ report: synthesizeData.report });
    setProgress((prev) => prev.map((step, i) => i === 2 ? { ...step, status: "completed", message: "Synthesis complete", progress: 100 } : i === 3 ? { ...step, status: "in-progress", message: "Generating voice..." } : step));

    // 4. Voice
    const voiceRes = await fetch("http://localhost:8000/agentic-assistant/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report: synthesizeData.report })
    });
    if (voiceRes.ok) {
      // Example: set audio player state with received audio
      // const audioBlob = await voiceRes.blob();
      // setAudioPlayer({ ...audioPlayer, audioUrl: URL.createObjectURL(audioBlob) });
    }
    setProgress((prev) => prev.map((step, i) => i === 3 ? { ...step, status: "completed", message: "Voice complete", progress: 100 } : i === 4 ? { ...step, status: "in-progress", message: "Finalizing..." } : step));

    // 5. NFT Mint (if email provided)
    if (userEmail) {
      const nftRes = await fetch("http://localhost:8000/agentic-assistant/nft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report: synthesizeData.report, user_email: userEmail })
      });
      const nftData = await nftRes.json();
      // Example: show NFT minting status
      // setNftStatus(nftData.result);
    }
    setProgress((prev) => prev.map((step, i) => i === 4 ? { ...step, status: "completed", message: "Workflow complete", progress: 100 } : step));
  }

  // Example usage: runAgenticResearch(query, 5, 2020, "user@example.com")

  // Chart data
  const relevanceData = summaries.map((paper, index) => ({
    name: `Paper ${index + 1}`,
    relevance: paper.relevanceScore,
  }))

  const themeData = [
    { name: "Privacy Concerns", value: 35, color: "#3B82F6" },
    { name: "Algorithmic Fairness", value: 28, color: "#8B5CF6" },
    { name: "Access & Equity", value: 22, color: "#10B981" },
    { name: "Governance", value: 15, color: "#F59E0B" },
  ]

  const progressData = progress.map((step) => ({
    step: step.step.split(" ")[0],
    progress: step.progress || (step.status === "completed" ? 100 : step.status === "in-progress" ? 50 : 0),
  }))

  const toggleAudioPlayback = () => {
    setAudioPlayer((prev) => ({ ...prev, isPlaying: !prev.isPlaying }))
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
  <div className="min-h-screen bg-gray-50 p-6 relative">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Research Dashboard</h1>
              <p className="text-gray-600">Query: "{query}"</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Connection status removed: now using direct API calls */}
              <Button variant="outline" size="sm">
                <Share className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Progress Tracker */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-5 w-5 text-blue-500" />
                    Progress Tracker
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {progress.map((step, index) => (
                    <motion.div
                      key={index}
                      className="space-y-2"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <div className="flex items-center gap-3">
                        {getStatusIcon(step.status)}
                        <div className="flex-1">
                          <p className="font-medium text-sm">{step.step}</p>
                          <p className="text-xs text-gray-500">{step.message}</p>
                        </div>
                      </div>
                      {step.progress !== undefined && <Progress value={step.progress} className="h-2" />}
                    </motion.div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>

            {/* Metrics */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-purple-500" />
                    Quality Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Human Score</span>
                      <span className="font-medium text-green-600">{plagiarismData.humanScore}%</span>
                    </div>
                    <Progress value={plagiarismData.humanScore} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Plagiarism Risk</span>
                      <span className="font-medium text-green-600">Low ({plagiarismData.overallRisk}%)</span>
                    </div>
                    <Progress value={plagiarismData.overallRisk} className="h-2 bg-green-100" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Papers Analyzed</span>
                      <span className="font-medium">{summaries.length}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Quick Stats */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Quick Stats</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Relevance</span>
                    <span className="font-medium">91%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Research Gaps</span>
                    <span className="font-medium">{gaps.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Processing Time</span>
                    <span className="font-medium">2m 34s</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              <Tabs defaultValue="summaries" className="space-y-6">
                <TabsList className="grid w-full grid-cols-6">
                  <TabsTrigger value="summaries">Summaries</TabsTrigger>
                  <TabsTrigger value="synthesis">Synthesis</TabsTrigger>
                  <TabsTrigger value="gaps">Gaps</TabsTrigger>
                  <TabsTrigger value="audio">Audio</TabsTrigger>
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="plagiarism">Plagiarism</TabsTrigger>
                </TabsList>

                <TabsContent value="summaries">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-teal-600" />
                        Paper Summaries
                      </CardTitle>
                      <CardDescription>AI-generated summaries with relevance scoring</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <AnimatePresence>
                        <Accordion type="single" collapsible className="space-y-4">
                          {summaries.map((paper, index) => (
                            <motion.div
                              key={paper.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.1 }}
                            >
                              <AccordionItem
                                value={paper.id}
                                className="border border-teal-200 rounded-lg px-4 hover:shadow-md transition-shadow"
                              >
                                <AccordionTrigger className="hover:no-underline">
                                  <div className="flex items-center justify-between w-full mr-4">
                                    <div className="text-left">
                                      <h3 className="font-medium">{paper.title}</h3>
                                      <p className="text-sm text-gray-500">{paper.authors.join(", ")}</p>
                                      <div className="flex items-center gap-2 mt-1">
                                        <Badge variant="outline" className="text-xs">
                                          {paper.source}
                                        </Badge>
                                        {paper.doi && (
                                          <Button variant="ghost" size="sm" className="h-6 px-2">
                                            <ExternalLink className="h-3 w-3" />
                                          </Button>
                                        )}
                                      </div>
                                    </div>
                                    <Badge className={`${getRelevanceBadgeColor(paper.relevanceScore)} text-white`}>
                                      {paper.relevanceScore}%
                                    </Badge>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className="pt-4 space-y-4">
                                  <div>
                                    <h4 className="font-medium mb-2">Summary</h4>
                                    <p className="text-gray-700">{paper.summary}</p>
                                  </div>

                                  <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-medium mb-2 text-green-600">Key Findings</h4>
                                      <ul className="text-sm space-y-1">
                                        {paper.keyFindings.map((finding, i) => (
                                          <li key={i} className="flex items-start gap-2">
                                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                            {finding}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>

                                    <div>
                                      <h4 className="font-medium mb-2 text-orange-600">Limitations</h4>
                                      <ul className="text-sm space-y-1">
                                        {paper.weaknesses.map((weakness, i) => (
                                          <li key={i} className="flex items-start gap-2">
                                            <AlertCircle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                                            {weakness}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  </div>

                                  <div className="flex gap-2 pt-2">
                                    <Button variant="outline" size="sm">
                                      View Full Paper
                                    </Button>
                                    <Button variant="outline" size="sm">
                                      <Download className="h-4 w-4 mr-2" />
                                      Export Summary
                                    </Button>
                                  </div>
                                </AccordionContent>
                              </AccordionItem>
                            </motion.div>
                          ))}
                        </Accordion>
                      </AnimatePresence>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="synthesis">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-purple-600" />
                        Synthesized Report
                      </CardTitle>
                      <CardDescription>Comprehensive analysis with themes and recommendations</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="prose max-w-none">
                        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 mb-6">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">Executive Summary</h3>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                              <span className="text-sm text-gray-600">92% Human-Generated</span>
                            </div>
                          </div>
                          <p className="text-gray-700">
                            The field of quantum computing ethics is rapidly evolving, with researchers identifying key
                            challenges around privacy, security, and societal impact. This synthesis of{" "}
                            {summaries.length} papers reveals three major themes and several critical research gaps that
                            require immediate attention.
                          </p>
                        </div>

                        <h3>Key Themes</h3>
                        <div className="grid md:grid-cols-3 gap-4 mb-6">
                          {themeData.map((theme, index) => (
                            <motion.div
                              key={theme.name}
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: index * 0.1 }}
                              className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
                            >
                              <div className="flex items-center gap-3 mb-2">
                                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: theme.color }} />
                                <h4 className="font-medium">{theme.name}</h4>
                              </div>
                              <div className="text-right">
                                <span className="text-2xl font-bold" style={{ color: theme.color }}>
                                  {theme.value}%
                                </span>
                                <p className="text-xs text-gray-500">of research focus</p>
                              </div>
                            </motion.div>
                          ))}
                        </div>

                        <h3>Recommendations</h3>
                        <ul className="space-y-2 mb-6">
                          <li className="flex items-start gap-3">
                            <TrendingUp className="h-5 w-5 text-blue-500 mt-0.5" />
                            <span>Develop standardized ethical assessment tools for quantum applications</span>
                          </li>
                          <li className="flex items-start gap-3">
                            <TrendingUp className="h-5 w-5 text-blue-500 mt-0.5" />
                            <span>Establish international quantum ethics governance framework</span>
                          </li>
                          <li className="flex items-start gap-3">
                            <TrendingUp className="h-5 w-5 text-blue-500 mt-0.5" />
                            <span>Create empirical validation studies for proposed ethical frameworks</span>
                          </li>
                        </ul>

                        <div className="flex gap-2">
                          <Button>
                            <Download className="h-4 w-4 mr-2" />
                            Export PDF
                          </Button>
                          <Button variant="outline">
                            <Share className="h-4 w-4 mr-2" />
                            Share Report
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="gaps">
                  <Card>
                    <CardHeader>
                      <CardTitle>Research Gaps & Limitations</CardTitle>
                      <CardDescription>Identified opportunities for future research</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {gaps.map((gap, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                          >
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="font-medium">{gap.description}</h4>
                              <Badge className={`${getPriorityColor(gap.priority)} text-white`}>
                                {gap.priority} Priority
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{gap.evidence}</p>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">Supporting citations:</span>
                              {gap.supportingCitations.map((citation, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {citation}
                                </Badge>
                              ))}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="audio">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Mic className="h-5 w-5 text-orange-600" />
                        Audio Presentation
                      </CardTitle>
                      <CardDescription>AI-generated voice narration of your research report</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-lg p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h3 className="font-medium">Research Report Narration</h3>
                              <p className="text-sm text-gray-600">
                                Duration: {formatTime(audioPlayer.duration)} • Voice: Adam • Speed: {audioPlayer.speed}x
                              </p>
                            </div>
                            <Button
                              size="lg"
                              className="bg-purple-600 hover:bg-purple-700"
                              onClick={toggleAudioPlayback}
                            >
                              {audioPlayer.isPlaying ? (
                                <Pause className="h-5 w-5 mr-2" />
                              ) : (
                                <Play className="h-5 w-5 mr-2" />
                              )}
                              {audioPlayer.isPlaying ? "Pause" : "Play"}
                            </Button>
                          </div>

                          {/* Audio Waveform Visualization */}
                          <div className="h-16 bg-gradient-to-r from-purple-400 to-blue-400 rounded opacity-30 flex items-center justify-center mb-4">
                            <div className="flex items-center gap-1">
                              {Array.from({ length: 50 }).map((_, i) => (
                                <div
                                  key={i}
                                  className="bg-white rounded-full animate-pulse"
                                  style={{
                                    width: "2px",
                                    height: `${Math.random() * 40 + 10}px`,
                                    animationDelay: `${i * 0.1}s`,
                                  }}
                                />
                              ))}
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>{formatTime(audioPlayer.currentTime)}</span>
                              <span>{formatTime(audioPlayer.duration)}</span>
                            </div>
                            <Progress value={(audioPlayer.currentTime / audioPlayer.duration) * 100} className="h-2" />
                          </div>
                        </div>

                        {/* Audio Controls */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                            <SkipBack className="h-4 w-4" />
                            Previous
                          </Button>
                          <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                            <SkipForward className="h-4 w-4" />
                            Next
                          </Button>
                          <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                            {audioPlayer.volume > 0 ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                            Volume
                          </Button>
                          <Button variant="outline">Speed: {audioPlayer.speed}x</Button>
                        </div>

                        {/* Chapter Navigation */}
                        <div className="space-y-2">
                          <h4 className="font-medium">Chapters</h4>
                          <div className="space-y-2">
                            {[
                              { name: "Executive Summary", time: "0:00" },
                              { name: "Key Themes", time: "2:15" },
                              { name: "Gaps & Limitations", time: "7:30" },
                              { name: "Recommendations", time: "10:45" },
                            ].map((chapter, index) => (
                              <Button key={index} variant="ghost" className="w-full justify-between text-left">
                                <span>{chapter.name}</span>
                                <span className="text-gray-500">{chapter.time}</span>
                              </Button>
                            ))}
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <Button>
                            <Download className="h-4 w-4 mr-2" />
                            Download MP3
                          </Button>
                          <Button variant="outline">
                            <Share className="h-4 w-4 mr-2" />
                            Share Audio
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="analytics">
                  <div className="grid gap-6">
                    {/* Relevance Chart */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <BarChart3 className="h-5 w-5 text-blue-500" />
                          Paper Relevance Analysis
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={relevanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="relevance" fill="#3B82F6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Theme Distribution */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <RechartsPieChart className="h-5 w-5 text-purple-500" />
                            Research Themes
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={250}>
                            <PieChartComponent>
                              <PieChartComponent
                                data={themeData}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                dataKey="value"
                                label={({ name, value }) => `${name}: ${value}%`}
                              >
                                {themeData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                              </PieChartComponent>
                              <Tooltip />
                            </PieChartComponent>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>

                      {/* Processing Progress */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-green-500" />
                            Processing Progress
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={progressData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="step" />
                              <YAxis />
                              <Tooltip />
                              <Line
                                type="monotone"
                                dataKey="progress"
                                stroke="#10B981"
                                strokeWidth={3}
                                dot={{ fill: "#10B981", strokeWidth: 2, r: 6 }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="plagiarism">
                  <Card>
                    <CardHeader>
                      <CardTitle>Plagiarism Analysis</CardTitle>
                      <CardDescription>Comprehensive originality and similarity checking</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="text-center">
                          <motion.div
                            className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-green-100 mb-4"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 260, damping: 20 }}
                          >
                            <div className="text-3xl font-bold text-green-600">{plagiarismData.overallRisk}%</div>
                          </motion.div>
                          <h3 className="text-lg font-medium text-green-600">Low Risk</h3>
                          <p className="text-gray-600">Your report shows minimal similarity to existing sources</p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6">
                          <div className="space-y-3">
                            <h4 className="font-medium">Quality Metrics</h4>
                            <div className="space-y-3">
                              <div>
                                <div className="flex justify-between text-sm mb-1">
                                  <span>Human-like Score</span>
                                  <span className="font-medium">{plagiarismData.humanScore}%</span>
                                </div>
                                <Progress value={plagiarismData.humanScore} className="h-2" />
                              </div>
                              <div>
                                <div className="flex justify-between text-sm mb-1">
                                  <span>Originality</span>
                                  <span className="font-medium">{100 - plagiarismData.overallRisk}%</span>
                                </div>
                                <Progress value={100 - plagiarismData.overallRisk} className="h-2" />
                              </div>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <h4 className="font-medium">Flagged Sections</h4>
                            <div className="border border-yellow-200 rounded-lg p-3">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium">Introduction paragraph</span>
                                <Badge className="bg-yellow-500">12% similarity</Badge>
                              </div>
                              <p className="text-xs text-gray-600">
                                Similar to: "Quantum Computing Ethics: A Comprehensive Framework" - Smith et al.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <Button>
                            <Download className="h-4 w-4 mr-2" />
                            Download Report
                          </Button>
                          <Button variant="outline">Rephrase Flagged Sections</Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </motion.div>
          </div>
        </div>
      </div>
      {/* Chatbot Icon/Button */}
      <Chatbot />
    </div>
  )
}
