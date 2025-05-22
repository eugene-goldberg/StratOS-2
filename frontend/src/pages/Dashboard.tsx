import React, { useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  Card, 
  CardContent, 
  CardHeader, 
  Divider,
  Chip,
  Button,
  IconButton,
  LinearProgress,
  Alert,
  Stack
} from '@mui/material';
import {
  Warning as WarningIcon,
  TrendingUp as OpportunityIcon,
  Lightbulb as InsightIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAlertStore } from '../store/alertStore';
import { AlertType, AlertSeverity, AlertStatus } from '../types/alerts';
import { format } from 'date-fns';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { alerts, stats, loadAlerts, loadStats, triggerScan, acknowledgeAlert } = useAlertStore();

  useEffect(() => {
    loadAlerts();
    loadStats();
  }, [loadAlerts, loadStats]);

  const getAlertIcon = (type: AlertType) => {
    switch (type) {
      case AlertType.RISK:
        return <WarningIcon />;
      case AlertType.OPPORTUNITY:
        return <OpportunityIcon />;
      case AlertType.INSIGHT:
        return <InsightIcon />;
      default:
        return <CheckIcon />;
    }
  };

  const getSeverityColor = (severity: AlertSeverity): "error" | "warning" | "success" | "info" => {
    switch (severity) {
      case AlertSeverity.CRITICAL:
        return 'error';
      case AlertSeverity.HIGH:
        return 'error';
      case AlertSeverity.MEDIUM:
        return 'warning';
      default:
        return 'info';
    }
  };

  // Get recent unacknowledged alerts
  const recentAlerts = alerts
    .filter(a => a.status === AlertStatus.NEW || a.status === AlertStatus.VIEWED)
    .slice(0, 5);

  const handleTriggerScan = async () => {
    await triggerScan();
    // Show success message
  };

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
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                AI Alerts & Insights
              </Typography>
              <Box>
                <IconButton size="small" onClick={handleTriggerScan} title="Trigger risk/opportunity scan">
                  <RefreshIcon />
                </IconButton>
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {recentAlerts.length === 0 ? (
              <Alert severity="info">
                No new alerts. System is continuously monitoring for risks and opportunities.
              </Alert>
            ) : (
              <Stack spacing={2}>
                {recentAlerts.map((alert) => (
                  <Card 
                    key={alert.id} 
                    variant="outlined"
                    sx={{ 
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                        <Box sx={{ color: `${getSeverityColor(alert.severity)}.main` }}>
                          {getAlertIcon(alert.alert_type)}
                        </Box>
                        <Box sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="body2" fontWeight="medium">
                              {alert.title}
                            </Typography>
                            <Chip 
                              label={alert.severity} 
                              size="small"
                              color={getSeverityColor(alert.severity)}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            {alert.description.substring(0, 100)}...
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(alert.created_at), 'MMM d, h:mm a')}
                          </Typography>
                          {alert.confidence_score && (
                            <Box sx={{ mt: 1 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={alert.confidence_score} 
                                sx={{ height: 4 }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {alert.confidence_score}% confidence
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
            
            {stats && stats.total_alerts > 5 && (
              <Button 
                fullWidth 
                sx={{ mt: 2 }}
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/analysis')}
              >
                View All {stats.total_alerts} Alerts
              </Button>
            )}
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