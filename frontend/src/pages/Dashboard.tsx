import React from 'react';
import { Box, Typography, Grid, Paper, Card, CardContent, CardHeader, Divider } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        CEO's Strategic Cockpit
      </Typography>
      
      <Grid container spacing={3}>
        {/* KPI Overview */}
        <Grid item xs={12} md={8}>
          <Paper elevation={0} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Key Performance Indicators
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {['Revenue', 'Customer Satisfaction', 'Market Share', 'Employee Engagement'].map((metric) => (
                <Grid item xs={12} sm={6} md={3} key={metric}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {metric}
                      </Typography>
                      <Typography variant="h5" component="div">
                        {Math.floor(Math.random() * 100)}%
                      </Typography>
                      <Typography variant="body2" color={Math.random() > 0.5 ? "success.main" : "error.main"}>
                        {Math.random() > 0.5 ? "↑" : "↓"} {Math.floor(Math.random() * 10)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
        
        {/* AI Alerts */}
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              AI Alerts & Insights
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="error.main" gutterBottom>
                  High Priority
                </Typography>
                <Typography variant="body1">
                  Marketing campaign performance below projection by 15%
                </Typography>
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography color="warning.main" gutterBottom>
                  Medium Priority
                </Typography>
                <Typography variant="body1">
                  Competitor launched new product in East region
                </Typography>
              </CardContent>
            </Card>
            <Card variant="outlined">
              <CardContent>
                <Typography color="success.main" gutterBottom>
                  Opportunity
                </Typography>
                <Typography variant="body1">
                  Customer feedback suggests strong interest in premium offering
                </Typography>
              </CardContent>
            </Card>
          </Paper>
        </Grid>
        
        {/* Quick Access */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Recent Strategic Canvas Sessions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {['Market Expansion Strategy', 'Q3 Innovation Planning', 'Talent Development Framework'].map((canvas) => (
              <Card variant="outlined" sx={{ mb: 1 }} key={canvas}>
                <CardHeader 
                  title={canvas}
                  subheader={`Last edited: ${new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}`}
                />
              </Card>
            ))}
          </Paper>
        </Grid>
        
        {/* CEO's Log */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Recent CEO's Log Entries
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {['Thoughts on market positioning', 'Notes from leadership offsite', 'Reflection on quarterly results'].map((entry) => (
              <Card variant="outlined" sx={{ mb: 1 }} key={entry}>
                <CardHeader 
                  title={entry}
                  subheader={`Created: ${new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}`}
                />
              </Card>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;