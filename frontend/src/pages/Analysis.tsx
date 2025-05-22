import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stepper,
  Step,
  StepLabel,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';
import useAnalysisStore from '../store/analysisStore';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
      style={{ height: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: 3, height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

/* Mock SWOT component - not currently used but kept for future implementation
const SWOTAnalysis = () => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Card variant="outlined" sx={{ height: '100%', bgcolor: '#e3f2fd' }}>
          <CardHeader title="Strengths" />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Proprietary AI technology" 
                  secondary="Our patented algorithms provide 30% better accuracy than competitors"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Strong enterprise client base" 
                  secondary="85% of Fortune 500 tech companies are customers"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Experienced leadership team" 
                  secondary="Executive team with average 15+ years industry experience"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card variant="outlined" sx={{ height: '100%', bgcolor: '#ffebee' }}>
          <CardHeader title="Weaknesses" />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Limited presence in Asia-Pacific" 
                  secondary="Only 8% market penetration in the fastest growing region"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="High customer acquisition cost" 
                  secondary="25% higher CAC than industry average"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Technical debt in legacy systems" 
                  secondary="Core platform requires modernization"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card variant="outlined" sx={{ height: '100%', bgcolor: '#e8f5e9' }}>
          <CardHeader title="Opportunities" />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Expanding into Asia-Pacific market" 
                  secondary="Projected 22% annual growth in enterprise segment"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Strategic partnership with TechCorp" 
                  secondary="Potential to reach 5M new users through integration"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingUpIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Growing demand for AI solutions" 
                  secondary="Market expected to grow 35% annually for next 5 years"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card variant="outlined" sx={{ height: '100%', bgcolor: '#fff8e1' }}>
          <CardHeader title="Threats" />
          <Divider />
          <CardContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Increasing competitive pressure" 
                  secondary="Three new market entrants in the past 6 months"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Regulatory changes in data privacy" 
                  secondary="New compliance requirements increasing operational costs"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrendingDownIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Economic uncertainty" 
                  secondary="Potential budget cuts in enterprise technology spending"
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};
*/

const Analysis: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [analysisType, setAnalysisType] = useState('');
  const [topicContext, setTopicContext] = useState('');
  const [newItemText, setNewItemText] = useState('');

  const {
    activeSwot,
    linkages,
    error,
    createGuidedSwot,
    addSwotItem,
    generateTows,
    discoverLinkages
  } = useAnalysisStore();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setActiveStep(0);
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleAnalysisTypeChange = (event: SelectChangeEvent) => {
    setAnalysisType(event.target.value);
  };

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Analysis
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
        >
          New Analysis
        </Button>
      </Box>

      <Box sx={{ width: '100%', height: 'calc(100% - 50px)' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Analysis tabs">
            <Tab label="SWOT Analysis" />
            <Tab label="S+O Connections" />
            <Tab label="Insights" />
            <Tab label="Scenario Modeling" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {!activeSwot ? (
            <Box textAlign="center">
              <Button variant="contained" onClick={() => createGuidedSwot('AI SWOT Analysis')}>Start AI-Guided SWOT</Button>
              {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            </Box>
          ) : (
            <>
              <Typography variant="h6" gutterBottom>
                {activeSwot.title}
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  label="Add SWOT Item"
                  fullWidth
                  value={newItemText}
                  onChange={(e) => setNewItemText(e.target.value)}
                />
                <Button
                  variant="outlined"
                  onClick={() => {
                    if (newItemText && activeSwot) {
                      addSwotItem(activeSwot.id, {
                        category: 'opportunity',
                        content: newItemText,
                        source: 'ai_generated'
                      });
                      setNewItemText('');
                    }
                  }}
                >
                  Add
                </Button>
              </Box>

              <Grid container spacing={2}>
                {activeSwot.items.map((item) => (
                  <Grid item xs={12} md={6} key={item.id}>
                    <Card variant="outlined">
                      <CardHeader title={item.category.toUpperCase()} />
                      <CardContent>
                        <Typography variant="body2">{item.content}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Button variant="contained" onClick={() => generateTows(activeSwot.id)}>Generate TOWS</Button>
              </Box>

              {activeSwot.tows_strategies && activeSwot.tows_strategies.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>TOWS Strategies</Typography>
                  {activeSwot.tows_strategies.map((strat, idx) => (
                    <Card variant="outlined" key={idx} sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="body2">{strat.strategy || JSON.stringify(strat)}</Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
            <TextField
              label="Topic Context"
              value={topicContext}
              onChange={(e) => setTopicContext(e.target.value)}
              fullWidth
            />
            <Button variant="contained" onClick={() => discoverLinkages('00000000-0000-0000-0000-000000000000', topicContext)}>Discover Linkages</Button>
          </Box>

          {linkages.map((link) => (
            <Card key={link.id} variant="outlined" sx={{ mb: 2 }}>
              <CardHeader title={link.linkage_type} subheader={link.topic_context} />
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>Subjective:</Typography>
                <Typography variant="body2" paragraph>{link.subjective_snippet_text}</Typography>
                <Typography variant="subtitle2" gutterBottom>Objective:</Typography>
                <Typography variant="body2" paragraph>{link.objective_snippet_text}</Typography>
                <Typography variant="subtitle2" color="primary" gutterBottom>AI Insight</Typography>
                <Typography variant="body2" paragraph>{link.ai_summary_of_linkage}</Typography>
                <Typography variant="body2" color="text.secondary">{link.ai_prompt_for_ceo}</Typography>
              </CardContent>
            </Card>
          ))}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Insights will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography>Scenario Modeling will be displayed here</Typography>
        </TabPanel>
      </Box>

      {/* Dialog for creating new analysis */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create New Analysis</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mt: 1, mb: 3 }}>
            <Step>
              <StepLabel>Select Analysis Type</StepLabel>
            </Step>
            <Step>
              <StepLabel>Select Data Sources</StepLabel>
            </Step>
            <Step>
              <StepLabel>Configure Analysis</StepLabel>
            </Step>
          </Stepper>

          {activeStep === 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                What type of analysis would you like to create?
              </Typography>
              <FormControl fullWidth variant="outlined" sx={{ mt: 2 }}>
                <InputLabel>Analysis Type</InputLabel>
                <Select
                  value={analysisType}
                  onChange={handleAnalysisTypeChange}
                  label="Analysis Type"
                >
                  <MenuItem value="swot">SWOT Analysis</MenuItem>
                  <MenuItem value="s-o-connection">Subjective+Objective Connection</MenuItem>
                  <MenuItem value="trend">Trend Analysis</MenuItem>
                  <MenuItem value="scenario">Scenario Modeling</MenuItem>
                  <MenuItem value="risk">Risk Assessment</MenuItem>
                </Select>
              </FormControl>
              {analysisType && (
                <Box sx={{ mt: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {analysisType === 'swot' && 'SWOT Analysis'}
                    {analysisType === 's-o-connection' && 'Subjective+Objective Connection'}
                    {analysisType === 'trend' && 'Trend Analysis'}
                    {analysisType === 'scenario' && 'Scenario Modeling'}
                    {analysisType === 'risk' && 'Risk Assessment'}
                  </Typography>
                  <Typography variant="body2">
                    {analysisType === 'swot' && 'Evaluate your internal Strengths and Weaknesses alongside external Opportunities and Threats. AI will help identify strategic options from these elements.'}
                    {analysisType === 's-o-connection' && 'Discover meaningful connections between your subjective insights and objective data to validate hunches and reveal hidden patterns.'}
                    {analysisType === 'trend' && 'Analyze historical data to identify trends, predict future movements, and understand cyclical patterns in your business metrics.'}
                    {analysisType === 'scenario' && 'Model different future scenarios based on varying assumptions and see how they might impact your business outcomes.'}
                    {analysisType === 'risk' && 'Identify potential risks, assess their likelihood and impact, and develop mitigation strategies.'}
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {activeStep === 1 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Select data sources for your analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Choose both subjective insights and objective data to incorporate
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                Subjective Sources (CEO's Insights)
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">CEO's Log Entries</Typography>
                  <Button size="small">Select All</Button>
                </Box>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="Selected" size="small" color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Thoughts after quarterly executive meeting" 
                      secondary="May 15, 2025"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="Selected" size="small" color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Market expansion opportunity" 
                      secondary="May 12, 2025"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="" size="small" variant="outlined" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Product innovation brainstorm" 
                      secondary="May 8, 2025"
                    />
                  </ListItem>
                </List>
              </Paper>
              
              <Typography variant="subtitle2" gutterBottom>
                Objective Sources (Data)
              </Typography>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Datasets & KPIs</Typography>
                  <Button size="small">Select All</Button>
                </Box>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="Selected" size="small" color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Q1 Financial Results" 
                      secondary="Financial dataset - May 1, 2025"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="Selected" size="small" color="primary" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Customer Satisfaction" 
                      secondary="KPI - Current: 4.2/5"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="" size="small" variant="outlined" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Competitor Pricing Data" 
                      secondary="Market dataset - Apr 10, 2025"
                    />
                  </ListItem>
                </List>
              </Paper>
            </Box>
          )}

          {activeStep === 2 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Configure your analysis
              </Typography>
              
              <TextField
                margin="normal"
                label="Analysis Title"
                fullWidth
                variant="outlined"
                defaultValue={analysisType === 'swot' ? "Enterprise Strategy SWOT" : ""}
                sx={{ mb: 3 }}
              />
              
              <Typography variant="subtitle2" gutterBottom>
                AI Analysis Options
              </Typography>
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, mb: 3 }}>
                {analysisType === 'swot' && (
                  <>
                    <Typography variant="body2" paragraph>
                      The AI will analyze your selected data sources to generate a comprehensive SWOT analysis, identifying key Strengths, Weaknesses, Opportunities and Threats.
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip label="Generate TOWS Strategies" size="small" color="primary" />
                      <Chip label="Include Confidence Scores" size="small" color="primary" />
                      <Chip label="Link to Supporting Evidence" size="small" color="primary" />
                    </Box>
                  </>
                )}
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                <PlayArrowIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="subtitle2" color="primary">
                    Ready to Generate Analysis
                  </Typography>
                  <Typography variant="body2">
                    The AI will combine 2 subjective sources and 2 objective sources to create your SWOT analysis.
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {activeStep > 0 && (
            <Button onClick={handleBack}>
              Back
            </Button>
          )}
          {activeStep < 2 ? (
            <Button onClick={handleNext} variant="contained">
              Next
            </Button>
          ) : (
            <Button onClick={handleCloseDialog} variant="contained" startIcon={<PlayArrowIcon />}>
              Generate Analysis
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Analysis;