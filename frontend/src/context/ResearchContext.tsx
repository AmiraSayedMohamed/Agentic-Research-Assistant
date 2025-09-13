import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ResearchContextType, ResearchState, ResearchQuery, ResearchResult, ResearchHistoryEntry } from '../types/research';
import { researchService } from '../services/researchService';

// Initial state
const initialState: ResearchState = {
  isLoading: false,
  currentResult: null,
  history: [],
  error: null,
};

// Action types
type ResearchAction =
  | { type: 'SEARCH_START' }
  | { type: 'SEARCH_SUCCESS'; payload: ResearchResult }
  | { type: 'SEARCH_ERROR'; payload: string }
  | { type: 'LOAD_HISTORY_SUCCESS'; payload: ResearchHistoryEntry[] }
  | { type: 'CLEAR_ERROR' }
  | { type: 'CLEAR_RESULT' };

// Reducer
function researchReducer(state: ResearchState, action: ResearchAction): ResearchState {
  switch (action.type) {
    case 'SEARCH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'SEARCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        currentResult: action.payload,
        error: null,
      };
    case 'SEARCH_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
      };
    case 'LOAD_HISTORY_SUCCESS':
      return {
        ...state,
        history: action.payload,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'CLEAR_RESULT':
      return {
        ...state,
        currentResult: null,
      };
    default:
      return state;
  }
}

// Create context
const ResearchContext = createContext<ResearchContextType | undefined>(undefined);

// Provider component
interface ResearchProviderProps {
  children: ReactNode;
}

export function ResearchProvider({ children }: ResearchProviderProps) {
  const [state, dispatch] = useReducer(researchReducer, initialState);

  const searchPapers = async (query: ResearchQuery) => {
    dispatch({ type: 'SEARCH_START' });
    try {
      const result = await researchService.conductResearch(query);
      dispatch({ type: 'SEARCH_SUCCESS', payload: result });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      dispatch({ type: 'SEARCH_ERROR', payload: errorMessage });
    }
  };

  const loadHistory = async () => {
    try {
      const history = await researchService.getResearchHistory();
      dispatch({ type: 'LOAD_HISTORY_SUCCESS', payload: history });
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const clearResult = () => {
    dispatch({ type: 'CLEAR_RESULT' });
  };

  const contextValue: ResearchContextType = {
    ...state,
    searchPapers,
    loadHistory,
    clearError,
    clearResult,
  };

  return (
    <ResearchContext.Provider value={contextValue}>
      {children}
    </ResearchContext.Provider>
  );
}

// Custom hook
export function useResearch() {
  const context = useContext(ResearchContext);
  if (context === undefined) {
    throw new Error('useResearch must be used within a ResearchProvider');
  }
  return context;
}