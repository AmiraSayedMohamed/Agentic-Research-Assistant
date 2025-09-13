import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Box,
  TextField,
  InputAdornment,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteIcon from '@mui/icons-material/Delete';
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { useResearch } from '../context/ResearchContext';
import { ResearchHistoryEntry } from '../types/research';
import { researchService } from '../services/researchService';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { history, loadHistory } = useResearch();
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filteredHistory, setFilteredHistory] = useState<ResearchHistoryEntry[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        await loadHistory();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [loadHistory]);

  useEffect(() => {
    // Filter history based on search term
    if (!searchTerm.trim()) {
      setFilteredHistory(history);
    } else {
      const filtered = history.filter(entry =>
        entry.query.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredHistory(filtered);
    }
  }, [history, searchTerm]);

  const handleDeleteEntry = async (researchId: string) => {
    try {
      await researchService.deleteResearchEntry(researchId);
      await loadHistory(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete entry');
    }
  };

  const handleEntryClick = (entry: ResearchHistoryEntry) => {
    if (entry.status === 'completed') {
      navigate(`/results/${entry.research_id}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <CircularProgress size={24} />;
      default:
        return <HistoryIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatProcessingTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  if (isLoading && history.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="h6">Loading research history...</Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Research History
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        View and manage your previous research queries and results.
      </Typography>

      {/* Search field */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search your research history..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      {/* Error display */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* History list */}
      <Paper elevation={3}>
        {filteredHistory.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            {history.length === 0 ? (
              <>
                <HistoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  No research history yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Start your first research to see results here.
                </Typography>
              </>
            ) : (
              <>
                <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  No matching results
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Try a different search term.
                </Typography>
              </>
            )}
          </Box>
        ) : (
          <List>
            {filteredHistory.map((entry, index) => (
              <React.Fragment key={entry.research_id}>
                <ListItem
                  button={entry.status === 'completed'}
                  onClick={() => handleEntryClick(entry)}
                  sx={{
                    cursor: entry.status === 'completed' ? 'pointer' : 'default',
                    '&:hover': entry.status === 'completed' ? {
                      backgroundColor: 'action.hover',
                    } : {},
                  }}
                >
                  <ListItemIcon>
                    {getStatusIcon(entry.status)}
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle1" component="span">
                          {entry.query}
                        </Typography>
                        <Chip
                          label={entry.status}
                          size="small"
                          color={getStatusColor(entry.status) as any}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" component="div">
                          {formatDate(entry.created_at)}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Papers: {entry.papers_count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Time: {formatProcessingTime(entry.processing_time)}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                  
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteEntry(entry.research_id);
                      }}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                
                {index < filteredHistory.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* Statistics */}
      {history.length > 0 && (
        <Paper elevation={1} sx={{ p: 3, mt: 3, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            Statistics
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="h4" color="primary">
                {history.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Queries
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" color="success.main">
                {history.filter(h => h.status === 'completed').length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Completed
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" color="info.main">
                {history.reduce((sum, h) => sum + h.papers_count, 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Papers Analyzed
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" color="secondary.main">
                {history.length > 0 ? 
                  formatProcessingTime(
                    history.reduce((sum, h) => sum + h.processing_time, 0) / history.length
                  ) : '0s'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg. Processing Time
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}
    </Box>
  );
}