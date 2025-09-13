import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Tabs,
  Tab,
  Box,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import HistoryIcon from '@mui/icons-material/History';

export default function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const getCurrentTab = () => {
    if (location.pathname === '/') return 0;
    if (location.pathname === '/history') return 1;
    if (location.pathname.startsWith('/results')) return 0;
    return 0;
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    switch (newValue) {
      case 0:
        navigate('/');
        break;
      case 1:
        navigate('/history');
        break;
    }
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Tabs
        value={getCurrentTab()}
        onChange={handleTabChange}
        textColor="inherit"
        indicatorColor="secondary"
      >
        <Tab
          icon={<SearchIcon />}
          label="Search"
          iconPosition="start"
          sx={{ color: 'white' }}
        />
        <Tab
          icon={<HistoryIcon />}
          label="History"
          iconPosition="start"
          sx={{ color: 'white' }}
        />
      </Tabs>
    </Box>
  );
}