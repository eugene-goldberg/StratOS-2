import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Switch,
  FormControlLabel,
  FormGroup,
  Tabs,
  Tab,
  Card,
  CardContent,
  IconButton,
  Chip
} from '@mui/material';
import {
  Person as PersonIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  VpnKey as ApiKeyIcon,
  Storage as StorageIcon,
  DataUsage as DataUsageIcon,
  AccessTime as AccessTimeIcon,
  Delete as DeleteIcon,
  Save as SaveIcon
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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
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

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure your StratOS experience and manage system settings
        </Typography>
      </Box>

      <Box sx={{ width: '100%', height: 'calc(100% - 80px)' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Settings tabs">
            <Tab icon={<PersonIcon />} label="Account" />
            <Tab icon={<SecurityIcon />} label="Security" />
            <Tab icon={<NotificationsIcon />} label="Notifications" />
            <Tab icon={<ApiKeyIcon />} label="API & Integrations" />
            <Tab icon={<DataUsageIcon />} label="Data Management" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper elevation={0} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Profile Information
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <TextField
                  label="Full Name"
                  variant="outlined"
                  fullWidth
                  defaultValue="Alex Morgan"
                  margin="normal"
                />
                
                <TextField
                  label="Email Address"
                  variant="outlined"
                  fullWidth
                  defaultValue="alex.morgan@example.com"
                  margin="normal"
                />
                
                <TextField
                  label="Job Title"
                  variant="outlined"
                  fullWidth
                  defaultValue="Chief Executive Officer"
                  margin="normal"
                />
                
                <TextField
                  label="Company"
                  variant="outlined"
                  fullWidth
                  defaultValue="TechInnovate Solutions"
                  margin="normal"
                />
                
                <TextField
                  label="Time Zone"
                  variant="outlined"
                  fullWidth
                  defaultValue="(GMT-08:00) Pacific Time"
                  select
                  SelectProps={{ native: true }}
                  margin="normal"
                >
                  <option value="PT">(GMT-08:00) Pacific Time</option>
                  <option value="MT">(GMT-07:00) Mountain Time</option>
                  <option value="CT">(GMT-06:00) Central Time</option>
                  <option value="ET">(GMT-05:00) Eastern Time</option>
                </TextField>
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="contained" startIcon={<SaveIcon />}>
                    Save Changes
                  </Button>
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper elevation={0} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Preferences
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <FormGroup>
                  <FormControlLabel 
                    control={<Switch defaultChecked />} 
                    label="Enable voice interactions" 
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mb: 2 }}>
                    Allow StratOS to respond to voice commands and provide verbal responses
                  </Typography>
                  
                  <FormControlLabel 
                    control={<Switch defaultChecked />} 
                    label="Show AI insights on dashboard" 
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mb: 2 }}>
                    Display AI-generated insights and alerts on your main dashboard
                  </Typography>
                  
                  <FormControlLabel 
                    control={<Switch defaultChecked />} 
                    label="Automatic tagging of CEO Log entries" 
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mb: 2 }}>
                    Let AI automatically tag and categorize your log entries
                  </Typography>
                </FormGroup>
                
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Theme Preference
                </Typography>
                <FormGroup>
                  <FormControlLabel 
                    control={<Switch />} 
                    label="Dark Mode" 
                  />
                </FormGroup>
              </Paper>
              
              <Paper elevation={0} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Account Management
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Data Storage" 
                      secondary="1.2 GB used of 10 GB" 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AccessTimeIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Account Created" 
                      secondary="March 15, 2025" 
                    />
                  </ListItem>
                </List>
                
                <Box sx={{ mt: 2 }}>
                  <Button color="error" startIcon={<DeleteIcon />}>
                    Delete Account
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper elevation={0} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Password Management
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <TextField
                  label="Current Password"
                  type="password"
                  variant="outlined"
                  fullWidth
                  margin="normal"
                />
                
                <TextField
                  label="New Password"
                  type="password"
                  variant="outlined"
                  fullWidth
                  margin="normal"
                />
                
                <TextField
                  label="Confirm New Password"
                  type="password"
                  variant="outlined"
                  fullWidth
                  margin="normal"
                />
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="contained">
                    Update Password
                  </Button>
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper elevation={0} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Two-Factor Authentication
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <FormGroup>
                  <FormControlLabel 
                    control={<Switch defaultChecked />} 
                    label="Enable Two-Factor Authentication" 
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mb: 2 }}>
                    Add an extra layer of security to your account by requiring a code in addition to your password
                  </Typography>
                </FormGroup>
                
                <Box sx={{ mt: 2 }}>
                  <Button variant="outlined" sx={{ mr: 2 }}>
                    Configure 2FA
                  </Button>
                  <Button variant="outlined" color="error">
                    Reset 2FA
                  </Button>
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12}>
              <Paper elevation={0} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Session Management
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <Typography variant="subtitle2" gutterBottom>
                  Active Sessions
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1">
                            This Device
                          </Typography>
                          <Chip label="Current" color="success" size="small" />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          MacBook Pro • San Francisco, CA
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Last active: Just now
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1">
                            iPhone 15 Pro
                          </Typography>
                          <IconButton size="small">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          iOS App • San Francisco, CA
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Last active: 2 hours ago
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1">
                            Windows PC
                          </Typography>
                          <IconButton size="small">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Chrome • New York, NY
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Last active: Yesterday
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="outlined" color="error">
                    Log Out All Other Devices
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Notification settings will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography>API & Integration settings will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <Typography>Data management settings will be displayed here</Typography>
        </TabPanel>
      </Box>
    </Box>
  );
};

export default Settings;