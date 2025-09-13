import axios from 'axios';
import { ResearchQuery, ResearchResult, ResearchHistoryEntry } from '../types/research';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes timeout for research operations
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const researchService = {
  // Conduct full research workflow
  async conductResearch(query: ResearchQuery): Promise<ResearchResult> {
    try {
      const response = await api.post('/research', query);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Research request failed');
      }
      throw error;
    }
  },

  // Search papers only
  async searchPapers(query: ResearchQuery): Promise<{ papers: any[] }> {
    try {
      const response = await api.post('/search-papers', query);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Paper search failed');
      }
      throw error;
    }
  },

  // Summarize specific paper
  async summarizePaper(paperId: string): Promise<any> {
    try {
      const response = await api.post('/summarize-paper', null, {
        params: { paper_id: paperId }
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Paper summarization failed');
      }
      throw error;
    }
  },

  // Synthesize research across papers
  async synthesizeResearch(paperIds: string[]): Promise<any> {
    try {
      const response = await api.post('/synthesize-research', paperIds);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Research synthesis failed');
      }
      throw error;
    }
  },

  // Get research history
  async getResearchHistory(): Promise<ResearchHistoryEntry[]> {
    try {
      const response = await api.get('/research-history');
      return response.data.history || [];
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to load research history');
      }
      throw error;
    }
  },

  // Delete research entry
  async deleteResearchEntry(queryId: string): Promise<void> {
    try {
      await api.delete(`/research-history/${queryId}`);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to delete research entry');
      }
      throw error;
    }
  },

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Health check failed');
      }
      throw error;
    }
  },

  // Get system info
  async getSystemInfo(): Promise<any> {
    try {
      const response = await api.get('/');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to get system info');
      }
      throw error;
    }
  },
};