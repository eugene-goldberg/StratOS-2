import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert
} from '@mui/material';
import { Edit as EditIcon, Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useNorthStarStore } from '../store/northStarStore';
import { Value, StrategicGoal } from '../services/strategicFoundationService';
import { v4 as uuidv4 } from 'uuid';

const NorthStar: React.FC = () => {
  const [editMode, setEditMode] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState<'value' | 'goal'>('value');
  const [dialogData, setDialogData] = useState({
    name: '',
    description: '',
    timeFrame: '',
    metrics: ''
  });

  const {
    data,
    isLoading,
    error,
    loadNorthStar,
    updateNorthStar
  } = useNorthStarStore();

  const [purpose, setPurpose] = useState('');
  const [vision, setVision] = useState('');
  const [values, setValues] = useState<Value[]>([]);
  const [goals, setGoals] = useState<StrategicGoal[]>([]);

  useEffect(() => {
    loadNorthStar();
  }, [loadNorthStar]);

  useEffect(() => {
    if (data) {
      setPurpose(data.purpose.statement);
      setVision(data.vision.statement);
      setValues(data.values);
      setGoals(data.strategic_goals);
    }
  }, [data]);

  const handleEditToggle = async () => {
    if (editMode) {
      await updateNorthStar({
        purpose,
        vision,
        values,
        strategic_goals: goals
      });
    }
    setEditMode(!editMode);
  };

  const handleAddItem = (type: 'value' | 'goal') => {
    setDialogType(type);
    setDialogData({ name: '', description: '', timeFrame: '', metrics: '' });
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleDialogSave = () => {
    if (dialogType === 'value') {
      setValues([...values, { id: uuidv4(), name: dialogData.name, description: dialogData.description }]);
    } else {
      setGoals([
        ...goals,
        {
          id: uuidv4(),
          title: dialogData.name,
          description: dialogData.description,
          time_frame: dialogData.timeFrame,
          metrics: dialogData.metrics
            ? dialogData.metrics.split(',').map((m) => m.trim()).filter((m) => m)
            : []
        }
      ]);
    }
    setOpenDialog(false);
  };

  const handleValueChange = (index: number, field: 'name' | 'description', value: string) => {
    setValues((vals) => vals.map((v, i) => (i === index ? { ...v, [field]: value } : v)));
  };

  const handleGoalChange = (
    index: number,
    field: 'title' | 'description' | 'time_frame' | 'metrics',
    value: string
  ) => {
    setGoals((gs) =>
      gs.map((g, i) =>
        i === index
          ? {
              ...g,
              [field]:
                field === 'metrics'
                  ? value.split(',').map((m) => m.trim()).filter((m) => m)
                  : value
            }
          : g
      )
    );
  };

  if (isLoading && !data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Our North Star
        </Typography>
        <Button
          variant={editMode ? "contained" : "outlined"}
          color={editMode ? "secondary" : "primary"}
          onClick={handleEditToggle}
          startIcon={<EditIcon />}
        >
          {editMode ? "Save Changes" : "Edit"}
        </Button>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* Purpose & Vision Section */}
        <Grid item xs={12}>
          <Paper elevation={0} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom color="primary">
              Purpose
            </Typography>
            {editMode ? (
              <TextField
                fullWidth
                multiline
                variant="outlined"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                sx={{ mb: 2 }}
              />
            ) : (
              <Typography variant="h6" paragraph>
                {purpose}
              </Typography>
            )}

            <Typography variant="h5" gutterBottom color="primary" sx={{ mt: 3 }}>
              Vision
            </Typography>
            {editMode ? (
              <TextField
                fullWidth
                multiline
                variant="outlined"
                value={vision}
                onChange={(e) => setVision(e.target.value)}
                sx={{ mb: 2 }}
              />
            ) : (
              <Typography variant="h6" paragraph>
                {vision}
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Values Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" color="primary">
                Our Values
              </Typography>
              {editMode && (
                <IconButton color="primary" onClick={() => handleAddItem('value')}>
                  <AddIcon />
                </IconButton>
              )}
            </Box>
            <Divider sx={{ mb: 2 }} />

            {values.map((valueItem, index) => (
              <Card key={valueItem.id} variant="outlined" sx={{ mb: 2 }}>
                <CardHeader
                  title={
                    editMode ? (
                      <TextField
                        fullWidth
                        variant="outlined"
                        value={valueItem.name}
                        onChange={(e) => handleValueChange(index, 'name', e.target.value)}
                      />
                    ) : (
                      valueItem.name
                    )
                  }
                  action={
                    editMode && (
                      <IconButton aria-label="delete" size="small" onClick={() => setValues(values.filter((_, i) => i !== index))}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )
                  }
                />
                <CardContent>
                  <Typography variant="body2" color="text.secondary">
                    {editMode ? (
                      <TextField
                        fullWidth
                        multiline
                        variant="outlined"
                        size="small"
                        value={valueItem.description}
                        onChange={(e) => handleValueChange(index, 'description', e.target.value)}
                      />
                    ) : (
                      valueItem.description
                    )}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Paper>
        </Grid>

        {/* Strategic Goals Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" color="primary">
                Strategic Goals
              </Typography>
              {editMode && (
                <IconButton color="primary" onClick={() => handleAddItem('goal')}>
                  <AddIcon />
                </IconButton>
              )}
            </Box>
            <Divider sx={{ mb: 2 }} />

            {goals.map((goal, index) => (
              <Card key={goal.id} variant="outlined" sx={{ mb: 2 }}>
                <CardHeader
                  title={
                    editMode ? (
                      <TextField
                        fullWidth
                        variant="outlined"
                        value={goal.title}
                        onChange={(e) => handleGoalChange(index, 'title', e.target.value)}
                      />
                    ) : (
                      goal.title
                    )
                  }
                  subheader={goal.time_frame}
                  action={
                    editMode && (
                      <IconButton aria-label="delete" size="small" onClick={() => setGoals(goals.filter((_, i) => i !== index))}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )
                  }
                />
                <CardContent>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {editMode ? (
                        <TextField
                          fullWidth
                          multiline
                          variant="outlined"
                          size="small"
                          value={goal.description}
                          onChange={(e) => handleGoalChange(index, 'description', e.target.value)}
                        />
                      ) : (
                        goal.description
                      )}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Key Metrics:
                    </Typography>
                    {editMode ? (
                      <TextField
                        fullWidth
                        variant="outlined"
                        size="small"
                        value={goal.metrics ? goal.metrics.join(', ') : ''}
                        onChange={(e) => handleGoalChange(index, 'metrics', e.target.value)}
                      />
                    ) : (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {goal.metrics && goal.metrics.map((m) => (
                          <Chip key={m} label={m} size="small" />
                        ))}
                      </Box>
                    )}
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Paper>
        </Grid>
      </Grid>

      {/* Dialog for adding new value or goal */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Add New {dialogType === 'value' ? 'Value' : 'Strategic Goal'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={dialogType === 'value' ? 'Value Name' : 'Goal Title'}
            fullWidth
            variant="outlined"
            value={dialogData.name}
            onChange={(e) => setDialogData({ ...dialogData, name: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={dialogData.description}
            onChange={(e) => setDialogData({ ...dialogData, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          {dialogType === 'goal' && (
            <>
              <TextField
                margin="dense"
                label="Time Frame"
                fullWidth
                variant="outlined"
                placeholder="e.g., 2023-2025"
                value={dialogData.timeFrame}
                onChange={(e) => setDialogData({ ...dialogData, timeFrame: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Key Metrics (comma separated)"
                fullWidth
                variant="outlined"
                placeholder="e.g., Revenue Growth, Market Share"
                value={dialogData.metrics}
                onChange={(e) => setDialogData({ ...dialogData, metrics: e.target.value })}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleDialogSave} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
export default NorthStar;
