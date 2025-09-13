import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Slider,
  Alert,
  CircularProgress,
  Box,
  Chip,
  Stack,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useResearch } from '../context/ResearchContext';
import { ResearchQuery } from '../types/research';

const availableSources = [
  { value: 'arxiv', label: 'ArXiv' },
  { value: 'pubmed', label: 'PubMed' },
  { value: 'crossref', label: 'CrossRef' },
  { value: 'doaj', label: 'DOAJ' },
];

export default function SearchPage() {
  const navigate = useNavigate();
  const { searchPapers, isLoading, error, clearError, currentResult } = useResearch();

  const [query, setQuery] = useState('');
  const [maxPapers, setMaxPapers] = useState(10);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [includePreprints, setIncludePreprints] = useState(true);
  const [language, setLanguage] = useState('en');

  const handleSearch = async () => {
    if (!query.trim()) {
      return;
    }

    clearError();

    const searchQuery: ResearchQuery = {
      query: query.trim(),
      max_papers: maxPapers,
      sources: selectedSources.length > 0 ? selectedSources : undefined,
      include_preprints: includePreprints,
      language,
    };

    try {
      await searchPapers(searchQuery);
      if (currentResult) {
        navigate(`/results/${currentResult.research_id}`);
      }
    } catch (err) {
      // Error is handled by context
    }
  };

  const handleSourceToggle = (source: string) => {
    setSelectedSources(prev => 
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    );
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !isLoading) {
      handleSearch();
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Academic Research Assistant
      </Typography>
      <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
        Multi-agent system for comprehensive research analysis
      </Typography>

      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Grid container spacing={3}>
          {/* Main search query */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Research Query"
              placeholder="Enter your research question or keywords..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              variant="outlined"
              multiline
              rows={3}
              helperText="Describe what you want to research. Be specific for better results."
            />
          </Grid>

          {/* Maximum papers slider */}
          <Grid item xs={12} md={6}>
            <Typography gutterBottom>
              Maximum Papers: {maxPapers}
            </Typography>
            <Slider
              value={maxPapers}
              onChange={(_, value) => setMaxPapers(value as number)}
              min={1}
              max={50}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 10, label: '10' },
                { value: 25, label: '25' },
                { value: 50, label: '50' },
              ]}
              disabled={isLoading}
            />
          </Grid>

          {/* Language selection */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={language}
                label="Language"
                onChange={(e) => setLanguage(e.target.value)}
                disabled={isLoading}
              >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="es">Spanish</MenuItem>
                <MenuItem value="fr">French</MenuItem>
                <MenuItem value="de">German</MenuItem>
                <MenuItem value="zh">Chinese</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Data sources */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Data Sources (leave empty for all sources)
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {availableSources.map((source) => (
                <Chip
                  key={source.value}
                  label={source.label}
                  onClick={() => handleSourceToggle(source.value)}
                  color={selectedSources.includes(source.value) ? 'primary' : 'default'}
                  variant={selectedSources.includes(source.value) ? 'filled' : 'outlined'}
                  disabled={isLoading}
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Grid>

          {/* Include preprints */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includePreprints}
                  onChange={(e) => setIncludePreprints(e.target.checked)}
                  disabled={isLoading}
                />
              }
              label="Include preprints and non-peer-reviewed papers"
            />
          </Grid>

          {/* Error display */}
          {error && (
            <Grid item xs={12}>
              <Alert severity="error" onClose={clearError}>
                {error}
              </Alert>
            </Grid>
          )}

          {/* Search button */}
          <Grid item xs={12}>
            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
              startIcon={isLoading ? <CircularProgress size={20} /> : <SearchIcon />}
              sx={{ py: 2 }}
            >
              {isLoading ? 'Analyzing...' : 'Start Research'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Loading indicator */}
      {isLoading && (
        <Paper elevation={2} sx={{ p: 3, mt: 3, textAlign: 'center' }}>
          <CircularProgress sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Research in Progress
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Our AI agents are searching, summarizing, and synthesizing research papers...
            This may take a few minutes.
          </Typography>
        </Paper>
      )}

      {/* Quick start tips */}
      <Paper elevation={1} sx={{ p: 3, mt: 3, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          💡 Quick Tips
        </Typography>
        <Typography variant="body2" component="div">
          <ul>
            <li>Use specific keywords and research questions for better results</li>
            <li>Try queries like "machine learning bias detection" or "climate change mitigation strategies"</li>
            <li>The system will find papers, create summaries, and identify patterns across research</li>
            <li>Results include consensus findings, conflicts, and research gaps</li>
          </ul>
        </Typography>
      </Paper>
    </Box>
  );
}