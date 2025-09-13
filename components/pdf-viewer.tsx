"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  FileText,
  Search,
  Download,
  Eye,
  MapPin,
  Highlighter as Highlight,
  ZoomIn,
  ZoomOut,
  RotateCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface PDFSentence {
  id: number
  text: string
  page: number
  bbox: {
    left: number
    top: number
    width: number
    height: number
  }
  similarity_score?: number
}

interface PDFHighlight {
  sentence_id: number
  page: number
  bbox: {
    left: number
    top: number
    width: number
    height: number
  }
  text: string
  type: "citation" | "gap" | "search" | "relevant"
}

interface PDFViewerProps {
  pdfUrl: string
  sentences: PDFSentence[]
  highlights: PDFHighlight[]
  onSentenceClick?: (sentence: PDFSentence) => void
  onHighlightClick?: (highlight: PDFHighlight) => void
}

export default function PDFViewer({
  pdfUrl,
  sentences,
  highlights,
  onSentenceClick,
  onHighlightClick,
}: PDFViewerProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [zoom, setZoom] = useState(1.0)
  const [searchTerm, setSearchTerm] = useState("")
  const [searchResults, setSearchResults] = useState<PDFSentence[]>([])
  const [selectedHighlight, setSelectedHighlight] = useState<PDFHighlight | null>(null)
  const [showMiniMap, setShowMiniMap] = useState(true)

  const pdfViewerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Mock PDF rendering (in real implementation, use react-pdf or PDF.js)
  useEffect(() => {
    // Simulate PDF loading
    setTotalPages(12) // Mock total pages
  }, [pdfUrl])

  const handleSearch = () => {
    if (!searchTerm.trim()) {
      setSearchResults([])
      return
    }

    const results = sentences.filter((sentence) => sentence.text.toLowerCase().includes(searchTerm.toLowerCase()))
    setSearchResults(results)
  }

  const navigateToSentence = (sentence: PDFSentence) => {
    setCurrentPage(sentence.page)
    onSentenceClick?.(sentence)
  }

  const navigateToHighlight = (highlight: PDFHighlight) => {
    setCurrentPage(highlight.page)
    setSelectedHighlight(highlight)
    onHighlightClick?.(highlight)
  }

  const getHighlightColor = (type: string) => {
    switch (type) {
      case "citation":
        return "bg-blue-200 border-blue-400"
      case "gap":
        return "bg-red-200 border-red-400"
      case "search":
        return "bg-yellow-200 border-yellow-400"
      case "relevant":
        return "bg-green-200 border-green-400"
      default:
        return "bg-gray-200 border-gray-400"
    }
  }

  const getHighlightTypeIcon = (type: string) => {
    switch (type) {
      case "citation":
        return <FileText className="h-3 w-3" />
      case "gap":
        return <Eye className="h-3 w-3" />
      case "search":
        return <Search className="h-3 w-3" />
      case "relevant":
        return <Highlight className="h-3 w-3" />
      default:
        return <MapPin className="h-3 w-3" />
    }
  }

  const currentPageHighlights = highlights.filter((h) => h.page === currentPage)
  const currentPageSentences = sentences.filter((s) => s.page === currentPage)

  return (
    <div className="grid lg:grid-cols-4 gap-6 h-screen">
      {/* Sidebar */}
      <div className="lg:col-span-1 space-y-4">
        {/* Search */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="h-5 w-5 text-blue-500" />
              Search PDF
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="Search in document..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              />
              <Button size="sm" onClick={handleSearch}>
                <Search className="h-4 w-4" />
              </Button>
            </div>

            {searchResults.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm text-gray-600">{searchResults.length} results found</p>
                <ScrollArea className="h-32">
                  {searchResults.map((result, index) => (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-2 border rounded cursor-pointer hover:bg-gray-50 mb-2"
                      onClick={() => navigateToSentence(result)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="outline" className="text-xs">
                          Page {result.page}
                        </Badge>
                        {result.similarity_score && (
                          <Badge className="bg-blue-500 text-xs">{(result.similarity_score * 100).toFixed(0)}%</Badge>
                        )}
                      </div>
                      <p className="text-xs text-gray-700 line-clamp-2">{result.text}</p>
                    </motion.div>
                  ))}
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Highlights */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Highlight className="h-5 w-5 text-orange-500" />
              Highlights
            </CardTitle>
            <CardDescription>Citations, gaps, and key findings</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {highlights.map((highlight, index) => (
                  <motion.div
                    key={`${highlight.sentence_id}-${highlight.type}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`p-3 rounded-lg border-l-4 cursor-pointer hover:shadow-md transition-shadow ${getHighlightColor(highlight.type)}`}
                    onClick={() => navigateToHighlight(highlight)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getHighlightTypeIcon(highlight.type)}
                        <Badge variant="outline" className="text-xs capitalize">
                          {highlight.type}
                        </Badge>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        Page {highlight.page}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-3">{highlight.text}</p>
                  </motion.div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Mini Map */}
        {showMiniMap && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <MapPin className="h-5 w-5 text-purple-500" />
                Document Map
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-1">
                {Array.from({ length: totalPages }).map((_, index) => {
                  const pageNum = index + 1
                  const pageHighlights = highlights.filter((h) => h.page === pageNum)
                  const isCurrentPage = pageNum === currentPage

                  return (
                    <motion.div
                      key={pageNum}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      className={`
                        relative h-8 border rounded cursor-pointer transition-all
                        ${isCurrentPage ? "border-blue-500 bg-blue-100" : "border-gray-300 bg-white hover:bg-gray-50"}
                      `}
                      onClick={() => setCurrentPage(pageNum)}
                    >
                      <div className="text-xs text-center pt-1">{pageNum}</div>
                      {pageHighlights.length > 0 && (
                        <div className="absolute top-0 right-0 w-2 h-2 bg-orange-500 rounded-full" />
                      )}
                    </motion.div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Main PDF Viewer */}
      <div className="lg:col-span-3">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-500" />
                PDF Viewer
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-sm font-medium">{Math.round(zoom * 100)}%</span>
                <Button variant="outline" size="sm" onClick={() => setZoom(Math.min(2.0, zoom + 0.1))}>
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Separator orientation="vertical" className="h-6" />
                <Button variant="outline" size="sm">
                  <RotateCw className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 p-0">
            {/* PDF Navigation */}
            <div className="flex items-center justify-between p-4 border-b">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <div className="flex items-center gap-2">
                <span className="text-sm">Page</span>
                <Input
                  type="number"
                  min={1}
                  max={totalPages}
                  value={currentPage}
                  onChange={(e) =>
                    setCurrentPage(Math.min(totalPages, Math.max(1, Number.parseInt(e.target.value) || 1)))
                  }
                  className="w-16 h-8 text-center"
                />
                <span className="text-sm">of {totalPages}</span>
              </div>

              <Button
                variant="outline"
                size="sm"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>

            {/* PDF Content Area */}
            <div className="relative flex-1 overflow-auto bg-gray-100 p-4">
              <div
                ref={pdfViewerRef}
                className="relative mx-auto bg-white shadow-lg"
                style={{
                  transform: `scale(${zoom})`,
                  transformOrigin: "top center",
                  width: "210mm", // A4 width
                  minHeight: "297mm", // A4 height
                }}
              >
                {/* Mock PDF Page */}
                <div className="relative w-full h-full p-8 border">
                  <div className="text-center mb-6">
                    <h1 className="text-2xl font-bold mb-2">Quantum Computing Ethics: A Comprehensive Framework</h1>
                    <p className="text-gray-600">
                      Page {currentPage} of {totalPages}
                    </p>
                  </div>

                  {/* Mock content with highlights */}
                  <div className="space-y-4 text-sm leading-relaxed">
                    {currentPageSentences.map((sentence) => {
                      const highlight = currentPageHighlights.find((h) => h.sentence_id === sentence.id)
                      const isSelected = selectedHighlight?.sentence_id === sentence.id

                      return (
                        <motion.div
                          key={sentence.id}
                          className={`
                            relative p-2 rounded cursor-pointer transition-all
                            ${highlight ? getHighlightColor(highlight.type) : "hover:bg-gray-50"}
                            ${isSelected ? "ring-2 ring-blue-500" : ""}
                          `}
                          onClick={() => navigateToSentence(sentence)}
                          whileHover={{ scale: 1.02 }}
                          style={{
                            position: "absolute",
                            left: `${sentence.bbox.left * 100}%`,
                            top: `${sentence.bbox.top * 100}%`,
                            width: `${sentence.bbox.width * 100}%`,
                            minHeight: `${sentence.bbox.height * 100}%`,
                          }}
                        >
                          <p className="text-justify">{sentence.text}</p>
                          {highlight && (
                            <div className="absolute top-1 right-1">{getHighlightTypeIcon(highlight.type)}</div>
                          )}
                        </motion.div>
                      )
                    })}

                    {/* Fallback content when no sentences available */}
                    {currentPageSentences.length === 0 && (
                      <div className="text-gray-500 text-center py-8">
                        <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>PDF content loading...</p>
                        <p className="text-sm">Page {currentPage} content will appear here</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Highlight Overlays */}
                <AnimatePresence>
                  {currentPageHighlights.map((highlight) => (
                    <motion.div
                      key={`overlay-${highlight.sentence_id}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 0.3 }}
                      exit={{ opacity: 0 }}
                      className={`absolute pointer-events-none ${getHighlightColor(highlight.type)}`}
                      style={{
                        left: `${highlight.bbox.left * 100}%`,
                        top: `${highlight.bbox.top * 100}%`,
                        width: `${highlight.bbox.width * 100}%`,
                        height: `${highlight.bbox.height * 100}%`,
                      }}
                    />
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
