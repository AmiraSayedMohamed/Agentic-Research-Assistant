import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Box,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Link,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArticleIcon from '@mui/icons-material/Article';
import FindInPageIcon from '@mui/icons-material/FindInPage';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import PresentationIcon from '@mui/icons-material/Presentation';
import DownloadIcon from '@mui/icons-material/Download';
import { useResearch } from '../context/ResearchContext';
import { Paper as PaperType, PaperSummary, SynthesisTheme } from '../types/research';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ResultsPage() {
  const { researchId } = useParams<{ researchId: string }>();
  const { currentResult } = useResearch();
  const [tabValue, setTabValue] = useState(0);

  if (!currentResult) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6">No research results found</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Please start a new search to view results.
        </Typography>
      </Paper>
    );
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const renderPaperCard = (paper: PaperType) => (
    <Card key={paper.id} sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" component="h3" gutterBottom>
          {paper.title}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Authors:</strong> {paper.authors.map(author => author.name).join(', ')}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Source:</strong> {paper.source.toUpperCase()} | 
          <strong> Published:</strong> {new Date(paper.published_date).getFullYear()}
          {paper.citation_count && (
            <> | <strong>Citations:</strong> {paper.citation_count}</>
          )}
        </Typography>

        <Typography variant="body2" sx={{ mt: 2, mb: 2 }}>
          {paper.abstract}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            startIcon={<ArticleIcon />}
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            View Paper
          </Button>
          {paper.pdf_url && (
            <Button
              size="small"
              startIcon={<DownloadIcon />}
              href={paper.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              PDF
            </Button>
          )}
          <Chip label={paper.source.toUpperCase()} size="small" variant="outlined" />
        </Box>
      </CardContent>
    </Card>
  );

  const renderSummaryCard = (summary: PaperSummary) => (
    <Accordion key={summary.paper_id} sx={{ mb: 1 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="h6">{summary.title}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              <strong>Objective:</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              {summary.objective}
            </Typography>

            <Typography variant="subtitle2" gutterBottom>
              <strong>Methodology:</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              {summary.methodology}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              <strong>Key Findings:</strong>
            </Typography>
            <List dense>
              {summary.key_findings.map((finding, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <FindInPageIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={finding} />
                </ListItem>
              ))}
            </List>

            <Typography variant="subtitle2" gutterBottom>
              <strong>Conclusions:</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              {summary.conclusions}
            </Typography>

            {summary.limitations && (
              <>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Limitations:</strong>
                </Typography>
                <Typography variant="body2" paragraph>
                  {summary.limitations}
                </Typography>
              </>
            )}
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Authors: {summary.authors.join(', ')}
          </Typography>
          {summary.confidence_score && (
            <Chip
              label={`Confidence: ${(summary.confidence_score * 100).toFixed(0)}%`}
              size="small"
              color={summary.confidence_score > 0.7 ? 'success' : summary.confidence_score > 0.4 ? 'warning' : 'error'}
            />
          )}
        </Box>
      </AccordionDetails>
    </Accordion>
  );

  const renderThemeCard = (theme: SynthesisTheme) => (
    <Card key={theme.theme} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="h3">
            {theme.theme}
          </Typography>
          <Chip
            label={`${theme.evidence_strength} evidence`}
            size="small"
            color={theme.evidence_strength === 'strong' ? 'success' : theme.evidence_strength === 'moderate' ? 'warning' : 'default'}
          />
        </Box>
        
        <Typography variant="body2" paragraph>
          {theme.description}
        </Typography>
        
        <Typography variant="caption" color="text.secondary">
          Supported by {theme.supporting_papers.length} papers
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Research Results
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Query: "{currentResult.query.query}"
        </Typography>
        <Grid container spacing={2}>
          <Grid item>
            <Chip label={`${currentResult.papers_found.length} Papers Found`} color="primary" />
          </Grid>
          <Grid item>
            <Chip label={`${currentResult.paper_summaries.length} Summaries`} color="secondary" />
          </Grid>
          <Grid item>
            <Chip
              label={`Processing Time: ${currentResult.processing_time_seconds.toFixed(1)}s`}
              variant="outlined"
            />
          </Grid>
          <Grid item>
            <Chip
              label={`Confidence: ${((currentResult.synthesis_report.synthesis_confidence || 0.5) * 100).toFixed(0)}%`}
              color="success"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper elevation={2}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab icon={<AnalyticsIcon />} label="Synthesis" iconPosition="start" />
          <Tab icon={<FindInPageIcon />} label="Paper Summaries" iconPosition="start" />
          <Tab icon={<ArticleIcon />} label="Original Papers" iconPosition="start" />
          <Tab icon={<PresentationIcon />} label="Formatted Report" iconPosition="start" />
        </Tabs>

        {/* Synthesis Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Executive Summary */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Executive Summary
                  </Typography>
                  <Typography variant="body1">
                    {currentResult.synthesis_report.executive_summary}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Main Themes */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Main Themes
              </Typography>
              {currentResult.synthesis_report.main_themes.map(renderThemeCard)}
            </Grid>

            {/* Consensus & Conflicts */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Key Findings
              </Typography>
              
              {currentResult.synthesis_report.consensus_findings.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom color="success.main">
                      Consensus Findings
                    </Typography>
                    {currentResult.synthesis_report.consensus_findings.map((finding, index) => (
                      <Typography key={index} variant="body2" paragraph>
                        • {finding}
                      </Typography>
                    ))}
                  </CardContent>
                </Card>
              )}

              {currentResult.synthesis_report.conflicting_results.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom color="warning.main">
                      Conflicting Results
                    </Typography>
                    {currentResult.synthesis_report.conflicting_results.map((conflict, index) => (
                      <Typography key={index} variant="body2" paragraph>
                        • {conflict}
                      </Typography>
                    ))}
                  </CardContent>
                </Card>
              )}

              {currentResult.synthesis_report.research_gaps.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom color="info.main">
                      Research Gaps
                    </Typography>
                    {currentResult.synthesis_report.research_gaps.map((gap, index) => (
                      <Box key={index} sx={{ mb: 2 }}>
                        <Typography variant="body2" paragraph>
                          <strong>{gap.gap_description}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Impact: {gap.potential_impact}
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              )}
            </Grid>

            {/* Methodology Analysis */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Methodology Analysis
                  </Typography>
                  <Typography variant="body1">
                    {currentResult.synthesis_report.methodology_analysis}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Paper Summaries Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Individual Paper Summaries
          </Typography>
          {currentResult.paper_summaries.map(renderSummaryCard)}
        </TabPanel>

        {/* Original Papers Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Found Papers
          </Typography>
          {currentResult.papers_found.map(renderPaperCard)}
        </TabPanel>

        {/* Formatted Report Tab */}
        <TabPanel value={tabValue} index={3}>
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              Formatted Research Report
            </Typography>
            <Box
              component="pre"
              sx={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
              }}
            >
              {currentResult.formatted_report}
            </Box>
          </Paper>
        </TabPanel>
      </Paper>
    </Box>
  );
}