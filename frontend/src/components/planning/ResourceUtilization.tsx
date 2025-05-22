import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Stack,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import { ResourceUtilization as ResourceUtilizationType, ResourceConflict } from '../../services/planningService';

interface ResourceUtilizationProps {
  utilization: ResourceUtilizationType | null;
  conflicts: ResourceConflict[];
  onResolveConflict?: (conflict: ResourceConflict) => void;
}

const COLORS: Record<string, string> = {
  financial: '#0088FE',
  human: '#00C49F',
  technology: '#FFBB28',
  physical: '#FF8042',
  time: '#8884D8',
  other: '#82CA9D'
};

const ResourceUtilization: React.FC<ResourceUtilizationProps> = ({ 
  utilization, 
  conflicts,
  onResolveConflict 
}) => {
  if (!utilization) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          No resource utilization data available. Add resources to initiatives to see utilization metrics.
        </Alert>
      </Box>
    );
  }

  // Prepare data for pie chart
  const pieData = Object.entries(utilization.utilization_by_type).map(([type, data]) => ({
    name: type.charAt(0).toUpperCase() + type.slice(1),
    value: data.allocated,
    total: data.total,
    percentage: data.total > 0 ? Math.round((data.allocated / data.total) * 100) : 0
  }));

  // Prepare data for bar chart
  const barData = utilization.resources
    .filter(r => r.utilization_rate !== undefined)
    .sort((a, b) => (b.utilization_rate || 0) - (a.utilization_rate || 0))
    .slice(0, 10) // Top 10 most utilized
    .map(r => ({
      name: r.name.length > 20 ? r.name.substring(0, 20) + '...' : r.name,
      utilization: r.utilization_rate || 0,
      status: r.status
    }));

  const overAllocatedCount = utilization.over_allocated_resources;
  const totalResourceCount = utilization.total_resources;
  const overallUtilization = totalResourceCount > 0 
    ? Math.round((utilization.allocated_resources / totalResourceCount) * 100) 
    : 0;

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Resources
              </Typography>
              <Typography variant="h4">
                {totalResourceCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all types
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Overall Utilization
              </Typography>
              <Typography variant="h4">
                {overallUtilization}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={overallUtilization}
                sx={{ mt: 1 }}
                color={overallUtilization > 90 ? 'error' : 'primary'}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Allocated Resources
              </Typography>
              <Typography variant="h4">
                {utilization.allocated_resources}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Chip 
                  size="small" 
                  label={`${utilization.total_resources - utilization.allocated_resources} available`}
                  color="success"
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ borderColor: overAllocatedCount > 0 ? 'error.main' : 'success.main', borderWidth: 1, borderStyle: 'solid' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Over-allocated
              </Typography>
              <Typography variant="h4" color={overAllocatedCount > 0 ? 'error' : 'success'}>
                {overAllocatedCount}
              </Typography>
              {overAllocatedCount > 0 ? (
                <Chip 
                  size="small" 
                  label="Action required" 
                  color="error" 
                  icon={<WarningIcon />}
                  sx={{ mt: 1 }}
                />
              ) : (
                <Chip 
                  size="small" 
                  label="All good" 
                  color="success" 
                  icon={<CheckIcon />}
                  sx={{ mt: 1 }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Utilization by Type */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Resource Distribution by Type
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase()] || COLORS.other} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Top Utilized Resources */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Most Utilized Resources
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData} margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="utilization" fill="#8884d8">
                  {barData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.utilization > 90 ? '#f44336' : entry.utilization > 70 ? '#ff9800' : '#4caf50'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Resource Conflicts ({conflicts.length})
          </Typography>
          <List>
            {conflicts.map((conflict, index) => (
              <React.Fragment key={conflict.resource_id}>
                <ListItem>
                  <ListItemIcon>
                    <ErrorIcon color="error" />
                  </ListItemIcon>
                  <ListItemText
                    primary={conflict.resource_name}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="error">
                          {conflict.conflict_type.replace('_', ' ').toUpperCase()}
                        </Typography>
                        {conflict.conflict_type === 'over_allocation' && (
                          <Typography variant="body2">
                            Over-allocated by {conflict.over_allocated_by} {conflict.total_quantity && `units`}
                          </Typography>
                        )}
                        {conflict.conflict_type === 'early_allocation' && (
                          <Typography variant="body2">
                            Allocated before availability date: {conflict.availability_start}
                          </Typography>
                        )}
                        {conflict.conflict_type === 'late_allocation' && (
                          <Typography variant="body2">
                            Allocated after availability ends: {conflict.availability_end}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  {onResolveConflict && (
                    <Button
                      size="small"
                      onClick={() => onResolveConflict(conflict)}
                    >
                      Resolve
                    </Button>
                  )}
                </ListItem>
                {index < conflicts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Insights */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Resource Insights
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Alert severity={overAllocatedCount > 0 ? 'warning' : 'success'}>
              {overAllocatedCount > 0 
                ? `${overAllocatedCount} resources are over-allocated and need immediate attention.`
                : 'All resources are within allocation limits.'}
            </Alert>
          </Grid>
          <Grid item xs={12} md={6}>
            <Alert severity={overallUtilization > 85 ? 'warning' : 'info'}>
              {overallUtilization > 85
                ? 'Resource utilization is high. Consider adding more resources or adjusting allocations.'
                : overallUtilization < 50
                ? 'Resource utilization is low. You may have excess capacity.'
                : 'Resource utilization is at a healthy level.'}
            </Alert>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default ResourceUtilization;