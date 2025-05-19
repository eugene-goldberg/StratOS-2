import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
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
  LinearProgress,
  Tabs,
  Tab,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  Slider,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  ArrowForward as ArrowForwardIcon,
  Flag as FlagIcon,
  Person as PersonIcon,
  DateRange as DateRangeIcon,
  BarChart as BarChartIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CompareArrows as CompareArrowsIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  MoreVert as MoreIcon,
  Analytics as AnalyticsIcon,
  ViewList as ViewListIcon
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
      id={`planning-tabpanel-${index}`}
      aria-labelledby={`planning-tab-${index}`}
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

// Initiative Status component
const StatusChip = ({ status }: { status: string }) => {
  if (status === 'active') {
    return <Chip label="Active" color="success" size="small" />;
  } else if (status === 'draft') {
    return <Chip label="Draft" color="default" size="small" />;
  } else if (status === 'completed') {
    return <Chip label="Completed" color="info" size="small" />;
  } else if (status === 'abandoned') {
    return <Chip label="Abandoned" color="error" size="small" />;
  }
  return <Chip label={status} size="small" />;
};

const Planning: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [initiativeType, setInitiativeType] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);

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

  const handleInitiativeTypeChange = (event: SelectChangeEvent) => {
    setInitiativeType(event.target.value);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  const toggleCompareMode = () => {
    setCompareMode(!compareMode);
    handleMenuClose();
  };

  const mockPlans = [
    {
      id: 1,
      title: "Growth Strategy 2025-2027",
      status: "active",
      initiatives: 5,
      progress: 35,
      alignmentScore: 8.2
    },
    {
      id: 2,
      title: "Digital Transformation Initiative",
      status: "draft",
      initiatives: 3,
      progress: 0,
      alignmentScore: 7.5
    },
    {
      id: 3,
      title: "Market Expansion Plan",
      status: "active",
      initiatives: 4,
      progress: 60,
      alignmentScore: 8.8
    }
  ];

  const mockInitiatives = [
    {
      id: 1,
      title: "Asia-Pacific Market Expansion",
      type: "Strategic",
      owner: "Sarah Chen",
      startDate: "Jun 2025",
      endDate: "Dec 2026",
      status: "active",
      progress: 40,
      actions: 8,
      risks: 3,
      alignmentScore: 9.2
    },
    {
      id: 2,
      title: "AI Product Integration",
      type: "Transformational",
      owner: "David Wilson",
      startDate: "Jul 2025",
      endDate: "Mar 2026",
      status: "active",
      progress: 25,
      actions: 12,
      risks: 5,
      alignmentScore: 8.5
    },
    {
      id: 3,
      title: "Customer Success Program",
      type: "Tactical",
      owner: "Michael Rodriguez",
      startDate: "Aug 2025",
      endDate: "Aug 2026",
      status: "draft",
      progress: 0,
      actions: 6,
      risks: 2,
      alignmentScore: 7.8
    }
  ];

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Strategic Planning
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<CompareArrowsIcon />}
            onClick={toggleCompareMode}
            color={compareMode ? "secondary" : "primary"}
            sx={{ mr: 1 }}
          >
            {compareMode ? "Exit Compare" : "Compare Plans"}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenDialog}
          >
            New Initiative
          </Button>
          <IconButton
            onClick={handleMenuOpen}
            sx={{ ml: 1 }}
          >
            <MoreIcon />
          </IconButton>
          <Menu
            anchorEl={menuAnchorEl}
            open={Boolean(menuAnchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <AddIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>New Strategic Plan</ListItemText>
            </MenuItem>
            <MenuItem onClick={toggleCompareMode}>
              <ListItemIcon>
                <CompareArrowsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{compareMode ? "Exit Compare Mode" : "Compare Plans"}</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <AnalyticsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Analyze Plan Alignment</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <FilterIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Filter View</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      <Box sx={{ width: '100%', height: 'calc(100% - 50px)' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Planning tabs">
            <Tab label="Strategic Plans" />
            <Tab label="Initiatives" />
            <Tab label="Action Tracker" />
            <Tab label="Resources" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {!compareMode ? (
            <Grid container spacing={3}>
              {mockPlans.map((plan) => (
                <Grid item xs={12} key={plan.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box>
                          <Typography variant="h6">{plan.title}</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, mb: 2 }}>
                            <StatusChip status={plan.status} />
                            <Chip 
                              label={`${plan.initiatives} Initiatives`} 
                              size="small" 
                              variant="outlined" 
                              sx={{ ml: 1 }} 
                            />
                            <Chip 
                              label={`Alignment: ${plan.alignmentScore}/10`} 
                              size="small" 
                              color={plan.alignmentScore > 8 ? "success" : "default"}
                              sx={{ ml: 1 }} 
                            />
                          </Box>
                        </Box>
                        <Box>
                          <IconButton size="small">
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Overall Progress:
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={plan.progress} 
                              sx={{ height: 10, borderRadius: 5 }}
                            />
                          </Box>
                          <Box sx={{ minWidth: 35 }}>
                            <Typography variant="body2" color="text.secondary">{`${plan.progress}%`}</Typography>
                          </Box>
                        </Box>
                      </Box>
                    </CardContent>
                    <CardActions>
                      <Button size="small">View Details</Button>
                      <Button size="small">Manage Initiatives</Button>
                      <Button size="small">Generate Report</Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box>
              <Paper elevation={0} sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Plan Comparison
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Select the plans you want to compare and adjust the criteria weights below
                </Typography>
              </Paper>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardHeader 
                      title="Growth Strategy 2025-2027" 
                      subheader="Selected for comparison"
                      action={
                        <Chip label="Selected" color="primary" size="small" />
                      }
                    />
                    <CardContent>
                      <List dense>
                        <ListItem>
                          <ListItemText 
                            primary="Alignment Score" 
                            secondary="8.2/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Feasibility Score" 
                            secondary="7.5/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Impact Score" 
                            secondary="8.8/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Resource Requirement" 
                            secondary="High"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Risk Level" 
                            secondary="Medium"
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardHeader 
                      title="Market Expansion Plan" 
                      subheader="Selected for comparison"
                      action={
                        <Chip label="Selected" color="primary" size="small" />
                      }
                    />
                    <CardContent>
                      <List dense>
                        <ListItem>
                          <ListItemText 
                            primary="Alignment Score" 
                            secondary="8.8/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Feasibility Score" 
                            secondary="6.9/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Impact Score" 
                            secondary="9.2/10"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Resource Requirement" 
                            secondary="Very High"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Risk Level" 
                            secondary="High"
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card variant="outlined" sx={{ backgroundColor: '#f5f5f5', height: '100%' }}>
                    <CardHeader 
                      title="Comparison Results" 
                      subheader="Weighted analysis"
                    />
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>
                        Recommendation:
                      </Typography>
                      <Typography variant="body2" paragraph sx={{ fontWeight: 'bold' }}>
                        Market Expansion Plan scores 3% higher overall when factoring your criteria weights
                      </Typography>
                      <Typography variant="subtitle2" gutterBottom>
                        Key Differences:
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <ArrowForwardIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Market Expansion has higher impact potential" 
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <ArrowForwardIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Growth Strategy has better feasibility" 
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <ArrowForwardIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary="Market Expansion requires 40% more resources" 
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                    <CardActions>
                      <Button size="small" variant="outlined">Generate Detailed Report</Button>
                    </CardActions>
                  </Card>
                </Grid>
                
                <Grid item xs={12}>
                  <Paper elevation={0} sx={{ p: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Adjust Comparison Criteria Weights
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={4}>
                        <Typography id="alignment-slider" gutterBottom>
                          WHY Alignment: 40%
                        </Typography>
                        <Slider
                          aria-labelledby="alignment-slider"
                          defaultValue={40}
                          step={5}
                          marks
                          min={0}
                          max={100}
                        />
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Typography id="feasibility-slider" gutterBottom>
                          Feasibility: 30%
                        </Typography>
                        <Slider
                          aria-labelledby="feasibility-slider"
                          defaultValue={30}
                          step={5}
                          marks
                          min={0}
                          max={100}
                        />
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Typography id="impact-slider" gutterBottom>
                          Impact Potential: 30%
                        </Typography>
                        <Slider
                          aria-labelledby="impact-slider"
                          defaultValue={30}
                          step={5}
                          marks
                          min={0}
                          max={100}
                        />
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button variant="contained">Recalculate Comparison</Button>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ViewListIcon sx={{ mr: 1 }} />
              <Typography variant="h6">All Initiatives</Typography>
            </Box>
            <Box>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                sx={{ mr: 1 }}
              >
                Filter
              </Button>
              <Button
                variant="outlined"
                startIcon={<SortIcon />}
              >
                Sort
              </Button>
            </Box>
          </Box>
          
          <Grid container spacing={3}>
            {mockInitiatives.map((initiative) => (
              <Grid item xs={12} md={6} lg={4} key={initiative.id}>
                <Card variant="outlined">
                  <CardHeader
                    title={initiative.title}
                    subheader={`${initiative.type} Initiative`}
                    action={
                      <StatusChip status={initiative.status} />
                    }
                  />
                  <CardContent>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={`Owner: ${initiative.owner}`} />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <DateRangeIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={`Timeline: ${initiative.startDate} - ${initiative.endDate}`} />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <FlagIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={`${initiative.actions} Actions (${initiative.progress}% Complete)`} 
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <WarningIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={`${initiative.risks} Identified Risks`} />
                      </ListItem>
                    </List>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        WHY Alignment Score: {initiative.alignmentScore}/10
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={initiative.alignmentScore * 10} 
                        color={initiative.alignmentScore > 8 ? "success" : "primary"}
                        sx={{ height: 8, borderRadius: 5 }}
                      />
                    </Box>
                    {initiative.status === 'active' && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Progress: {initiative.progress}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={initiative.progress} 
                          sx={{ height: 8, borderRadius: 5 }}
                        />
                      </Box>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button size="small">View Details</Button>
                    <Button size="small">Edit</Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Action Tracker will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography>Resources will be displayed here</Typography>
        </TabPanel>
      </Box>

      {/* Dialog for creating new initiative */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create New Strategic Initiative</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mt: 1, mb: 3 }}>
            <Step>
              <StepLabel>Basic Information</StepLabel>
            </Step>
            <Step>
              <StepLabel>Strategic Alignment</StepLabel>
            </Step>
            <Step>
              <StepLabel>Actions & Resources</StepLabel>
            </Step>
          </Stepper>

          {activeStep === 0 && (
            <Box>
              <TextField
                autoFocus
                margin="normal"
                label="Initiative Title"
                fullWidth
                variant="outlined"
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel>Initiative Type</InputLabel>
                <Select
                  value={initiativeType}
                  onChange={handleInitiativeTypeChange}
                  label="Initiative Type"
                >
                  <MenuItem value="strategic">Strategic</MenuItem>
                  <MenuItem value="tactical">Tactical</MenuItem>
                  <MenuItem value="operational">Operational</MenuItem>
                  <MenuItem value="transformational">Transformational</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                margin="normal"
                label="Description"
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                sx={{ mb: 2 }}
              />
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Owner"
                    fullWidth
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <TextField
                    label="Start Date"
                    type="month"
                    fullWidth
                    variant="outlined"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <TextField
                    label="End Date"
                    type="month"
                    fullWidth
                    variant="outlined"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>
            </Box>
          )}

          {activeStep === 1 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Strategic Alignment
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Connect this initiative to strategic goals and explain alignment with company WHY
              </Typography>
              
              <FormControl fullWidth variant="outlined" sx={{ mb: 3 }}>
                <InputLabel>Linked Strategic Goal</InputLabel>
                <Select
                  label="Linked Strategic Goal"
                  value=""
                >
                  <MenuItem value="goal1">Achieve 25% market share by Q4 2025</MenuItem>
                  <MenuItem value="goal2">Launch 3 innovative product lines within 18 months</MenuItem>
                  <MenuItem value="goal3">Increase customer retention to 85%</MenuItem>
                </Select>
              </FormControl>
              
              <Typography variant="subtitle2" gutterBottom>
                Purpose Alignment
              </Typography>
              <TextField
                margin="normal"
                label="How does this initiative support our purpose?"
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                sx={{ mb: 2 }}
                helperText="Purpose: To empower businesses with strategic clarity and data-driven insights for sustainable growth and meaningful impact."
              />
              
              <Typography variant="subtitle2" gutterBottom>
                Vision Alignment
              </Typography>
              <TextField
                margin="normal"
                label="How does this initiative move us toward our vision?"
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                sx={{ mb: 2 }}
                helperText="Vision: By 2030, to be the indispensable AI-powered strategic partner for 10,000 leadership teams worldwide."
              />
              
              <Typography variant="subtitle2" gutterBottom>
                Values Alignment
              </Typography>
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel>Select Relevant Values</InputLabel>
                <Select
                  multiple
                  label="Select Relevant Values"
                  value={[]}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                >
                  <MenuItem value="Integrity">Integrity</MenuItem>
                  <MenuItem value="Innovation">Innovation</MenuItem>
                  <MenuItem value="Excellence">Excellence</MenuItem>
                  <MenuItem value="Collaboration">Collaboration</MenuItem>
                  <MenuItem value="Customer Focus">Customer Focus</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}

          {activeStep === 2 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Key Actions & Resources
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Define the critical actions needed to execute this initiative
              </Typography>
              
              <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Key Actions
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <CheckIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Conduct market research in target regions" 
                      secondary="Owner: Research Team | Due: August 2025"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Develop partnership strategy" 
                      secondary="Owner: Business Development | Due: September 2025"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AddIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={<Button size="small">Add Another Action</Button>}
                    />
                  </ListItem>
                </List>
              </Paper>
              
              <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Required Resources
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <BarChartIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Financial: $250,000 initial budget" 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <PersonIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Human: 3 FTE for first 6 months" 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AddIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={<Button size="small">Add Another Resource</Button>}
                    />
                  </ListItem>
                </List>
              </Paper>
              
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Key Risks & Mitigation
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <ErrorIcon fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Regulatory challenges in new markets" 
                      secondary="Mitigation: Partner with local legal experts"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <WarningIcon fontSize="small" color="warning" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Potential resource constraints" 
                      secondary="Mitigation: Phased approach with clear milestones"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AddIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={<Button size="small">Add Another Risk</Button>}
                    />
                  </ListItem>
                </List>
              </Paper>
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
            <Button onClick={handleCloseDialog} variant="contained">
              Create Initiative
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Planning;