// TypeScript interfaces for the research assistant

export interface Author {
  name: string;
  affiliation?: string;
  email?: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: Author[];
  abstract: string;
  doi?: string;
  url: string;
  source: 'arxiv' | 'pubmed' | 'doaj' | 'crossref';
  published_date: string;
  citation_count?: number;
  keywords?: string[];
  pdf_url?: string;
}

export interface PaperSummary {
  paper_id: string;
  title: string;
  authors: string[];
  objective: string;
  methodology: string;
  key_findings: string[];
  conclusions: string;
  limitations?: string;
  summary_generated_at: string;
  confidence_score?: number;
}

export interface SynthesisTheme {
  theme: string;
  description: string;
  supporting_papers: string[];
  evidence_strength: 'strong' | 'moderate' | 'weak';
}

export interface ResearchGap {
  gap_description: string;
  related_themes: string[];
  potential_impact: 'high' | 'medium' | 'low';
  suggested_research_directions: string[];
}

export interface SynthesisReport {
  query: string;
  paper_ids: string[];
  total_papers: number;
  executive_summary: string;
  main_themes: SynthesisTheme[];
  consensus_findings: string[];
  conflicting_results: string[];
  research_gaps: ResearchGap[];
  methodology_analysis: string;
  generated_at: string;
  synthesis_confidence?: number;
}

export interface ResearchQuery {
  query: string;
  max_papers?: number;
  date_range?: {
    start_date: string;
    end_date: string;
  };
  sources?: string[];
  include_preprints?: boolean;
  language?: string;
}

export interface ResearchResult {
  query: ResearchQuery;
  papers_found: Paper[];
  paper_summaries: PaperSummary[];
  synthesis_report: SynthesisReport;
  formatted_report: string;
  presentation_format: string;
  processing_time_seconds: number;
  total_tokens_used?: number;
  research_id: string;
  created_at: string;
}

export interface ResearchHistoryEntry {
  research_id: string;
  query: string;
  papers_count: number;
  created_at: string;
  processing_time: number;
  status: 'completed' | 'failed' | 'in_progress';
}

export interface ResearchState {
  isLoading: boolean;
  currentResult: ResearchResult | null;
  history: ResearchHistoryEntry[];
  error: string | null;
}

export interface ResearchContextType extends ResearchState {
  searchPapers: (query: ResearchQuery) => Promise<void>;
  clearError: () => void;
  clearResult: () => void;
  loadHistory: () => Promise<void>;
}