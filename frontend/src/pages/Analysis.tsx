import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Divider,
  Chip,
  IconButton,
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
  ArrowForward as ArrowForwardIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Help as HelpIcon,
  Share as ShareIcon,
  Save as SaveIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';

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

// Mock SWOT component
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

const Analysis: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [analysisType, setAnalysisType] = useState('');

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
          <Box sx={{ mb: 3 }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">Enterprise Strategy SWOT</Typography>
                  <Typography variant="subtitle2" color="text.secondary">
                    Created: May 10, 2025 | Last updated: May 15, 2025
                  </Typography>
                </Box>
                <Box>
                  <Button
                    variant="outlined"
                    startIcon={<ShareIcon />}
                    sx={{ mr: 1 }}
                  >
                    Share
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                  >
                    Refresh
                  </Button>
                </Box>
              </Box>
            </Paper>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            This SWOT analysis was generated by combining CEO's subjective insights with objective data. Click on any item to see the supporting evidence.
          </Alert>

          <SWOTAnalysis />

          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              TOWS Strategies
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Strategic options generated by combining SWOT elements
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="S-O Strategy: Asia-Pacific Expansion" />
                  <CardContent>
                    <Typography variant="body2">
                      Leverage our proprietary AI technology and strong enterprise client base to rapidly expand into the Asia-Pacific market, targeting the fastest-growing sectors.
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<ArrowForwardIcon />}>
                      Create Initiative
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="W-O Strategy: Strategic Partnership Program" />
                  <CardContent>
                    <Typography variant="body2">
                      Establish a partnership with TechCorp to overcome our limited presence in Asia-Pacific and reduce customer acquisition costs through joint marketing.
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<ArrowForwardIcon />}>
                      Create Initiative
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Subjective + Objective Connections
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Exploring relationships between CEO insights and objective data
            </Typography>
          </Box>

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardHeader 
                  title="CEO Observation + Market Data Connection" 
                  subheader="High Confidence (85%)"
                  action={
                    <IconButton>
                      <HelpIcon />
                    </IconButton>
                  }
                />
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, mr: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>CEO Log Entry (May 8, 2025):</Typography>
                      <Typography variant="body2">
                        "I can't stop thinking about how we could integrate AI capabilities into our core product line. The demos I saw at the industry conference last week were impressive, and I believe we could develop something even more powerful with our domain expertise."
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip size="small" label="Product Innovation" sx={{ mr: 1 }} />
                        <Chip size="small" label="AI Integration" />
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', px: 2 }}>
                      <LinkIcon color="primary" sx={{ fontSize: 40 }} />
                    </Box>
                    <Box sx={{ flex: 1, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, ml: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>Market Research Data:</Typography>
                      <Typography variant="body2">
                        "AI-enhanced products in our industry have shown a 42% higher adoption rate and 23% premium pricing power compared to traditional offerings. The market for AI-integrated solutions is projected to grow at 35% CAGR over the next 5 years."
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip size="small" label="Market Trends" sx={{ mr: 1 }} />
                        <Chip size="small" label="Pricing Analysis" />
                      </Box>
                    </Box>
                  </Box>
                  <Box sx={{ p: 2, backgroundColor: '#e3f2fd', borderRadius: 1 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      AI-Generated Insight:
                    </Typography>
                    <Typography variant="body2">
                      The CEO's intuition about AI integration is strongly supported by market data showing exceptional growth and pricing power for AI-enhanced products. This represents a high-value opportunity that aligns both with executive vision and market trends.
                    </Typography>
                  </Box>
                </CardContent>
                <CardActions>
                  <Button size="small" startIcon={<ArrowForwardIcon />}>
                    Add to Strategic Canvas
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          </Grid>
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