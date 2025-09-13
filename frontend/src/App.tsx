import React from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

import SearchPage from './components/SearchPage';
import ResultsPage from './components/ResultsPage';
import HistoryPage from './components/HistoryPage';
import Navigation from './components/Navigation';

function App() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <SearchIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Agentic Research Assistant
          </Typography>
          <Navigation />
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/results/:researchId" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </Container>
    </Box>
  );
}

export default App;