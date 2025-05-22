import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Typography,
  Collapse,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  SubdirectoryArrowRight as SubGoalIcon,
  Timeline as TimelineIcon,
  TrendingUp as MetricsIcon,
} from '@mui/icons-material';
import { StrategicGoal } from '../../services/northStarService';
import { useNorthStarStore } from '../../store/northStarStore';

interface GoalNodeProps {
  goal: StrategicGoal;
  level: number;
  allGoals: StrategicGoal[];
  onEdit: (goal: StrategicGoal) => void;
  onDelete: (goalId: string) => void;
  onAddSubGoal: (parentGoalId: string) => void;
}

const GoalNode: React.FC<GoalNodeProps> = ({ 
  goal, 
  level, 
  allGoals,
  onEdit, 
  onDelete, 
  onAddSubGoal 
}) => {
  const [expanded, setExpanded] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEdit = () => {
    handleMenuClose();
    onEdit(goal);
  };

  const handleDelete = () => {
    handleMenuClose();
    onDelete(goal.id);
  };

  const handleAddSubGoal = () => {
    handleMenuClose();
    onAddSubGoal(goal.id);
  };

  const hasSubGoals = goal.sub_goals && goal.sub_goals.length > 0;

  return (
    <Box sx={{ ml: level * 4 }}>
      <Card 
        variant="outlined" 
        sx={{ 
          mb: 2,
          borderLeft: level > 0 ? '3px solid' : 'none',
          borderLeftColor: level > 0 ? 'primary.main' : 'transparent',
          '&:hover': {
            boxShadow: 2,
          }
        }}
      >
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {hasSubGoals && (
                <IconButton
                  size="small"
                  onClick={() => setExpanded(!expanded)}
                  sx={{ p: 0.5 }}
                >
                  {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              )}
              <Typography variant="h6" component="div">
                {goal.title}
              </Typography>
            </Box>
          }
          subheader={goal.time_frame}
          action={
            <IconButton
              size="small"
              onClick={handleMenuOpen}
            >
              <MoreVertIcon />
            </IconButton>
          }
          sx={{ pb: 1 }}
        />
        <CardContent sx={{ pt: 0 }}>
          <Typography variant="body2" color="text.secondary" paragraph>
            {goal.description}
          </Typography>
          
          {goal.metrics && goal.metrics.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                <MetricsIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  Key Metrics:
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {goal.metrics.map((metric, index) => (
                  <Chip key={index} label={metric} size="small" />
                ))}
              </Box>
            </Box>
          )}
          
          {(goal.target_value || goal.current_value) && (
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              {goal.current_value !== undefined && (
                <Typography variant="body2">
                  Current: <strong>{goal.current_value}</strong>
                </Typography>
              )}
              {goal.target_value !== undefined && (
                <Typography variant="body2">
                  Target: <strong>{goal.target_value}</strong>
                </Typography>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Goal</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleAddSubGoal}>
          <ListItemIcon>
            <SubGoalIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Add Sub-Goal</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete Goal</ListItemText>
        </MenuItem>
      </Menu>

      {hasSubGoals && (
        <Collapse in={expanded}>
          <Box sx={{ mt: 1 }}>
            {goal.sub_goals!.map((subGoal) => (
              <GoalNode
                key={subGoal.id}
                goal={subGoal}
                level={level + 1}
                allGoals={allGoals}
                onEdit={onEdit}
                onDelete={onDelete}
                onAddSubGoal={onAddSubGoal}
              />
            ))}
          </Box>
        </Collapse>
      )}
    </Box>
  );
};

interface HierarchicalGoalTreeProps {
  goals: StrategicGoal[];
  onAddGoal: () => void;
}

const HierarchicalGoalTree: React.FC<HierarchicalGoalTreeProps> = ({ goals, onAddGoal }) => {
  const { updateStrategicGoal, deleteStrategicGoal } = useNorthStarStore();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<StrategicGoal | null>(null);
  const [parentGoalId, setParentGoalId] = useState<string>('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    time_frame: '',
    metrics: '',
    target_value: '',
    current_value: '',
    parent_goal_id: '',
  });

  // Get only top-level goals (no parent)
  const topLevelGoals = goals.filter(g => !g.parent_goal_id);

  const handleEdit = (goal: StrategicGoal) => {
    setSelectedGoal(goal);
    setFormData({
      title: goal.title,
      description: goal.description,
      time_frame: goal.time_frame || '',
      metrics: goal.metrics?.join(', ') || '',
      target_value: goal.target_value?.toString() || '',
      current_value: goal.current_value?.toString() || '',
      parent_goal_id: goal.parent_goal_id || '',
    });
    setEditDialogOpen(true);
  };

  const handleAddSubGoal = (parentId: string) => {
    setParentGoalId(parentId);
    onAddGoal();
  };

  const handleDelete = async (goalId: string) => {
    if (window.confirm('Are you sure you want to delete this goal and all its sub-goals?')) {
      try {
        await deleteStrategicGoal(goalId);
      } catch (error) {
        console.error('Failed to delete goal:', error);
      }
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedGoal) return;

    try {
      const updateData: Partial<StrategicGoal> = {
        title: formData.title,
        description: formData.description,
        time_frame: formData.time_frame || undefined,
        metrics: formData.metrics ? formData.metrics.split(',').map(m => m.trim()) : undefined,
        target_value: formData.target_value ? parseFloat(formData.target_value) : undefined,
        current_value: formData.current_value ? parseFloat(formData.current_value) : undefined,
        parent_goal_id: formData.parent_goal_id || undefined,
      };

      await updateStrategicGoal(selectedGoal.id, updateData);
      setEditDialogOpen(false);
      setSelectedGoal(null);
    } catch (error) {
      console.error('Failed to update goal:', error);
    }
  };

  const handleFieldChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" color="primary">
          Strategic Goals Hierarchy
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onAddGoal}
        >
          Add Goal
        </Button>
      </Box>

      {topLevelGoals.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            No strategic goals yet. Click "Add Goal" to create your first goal.
          </Typography>
        </Box>
      ) : (
        topLevelGoals.map((goal) => (
          <GoalNode
            key={goal.id}
            goal={goal}
            level={0}
            allGoals={goals}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onAddSubGoal={handleAddSubGoal}
          />
        ))
      )}

      {/* Edit Goal Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Strategic Goal</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Goal Title"
            value={formData.title}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => handleFieldChange('description', e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Time Frame"
            value={formData.time_frame}
            onChange={(e) => handleFieldChange('time_frame', e.target.value)}
            placeholder="e.g., 2024-2025"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Key Metrics (comma separated)"
            value={formData.metrics}
            onChange={(e) => handleFieldChange('metrics', e.target.value)}
            placeholder="e.g., Revenue Growth, Market Share"
            sx={{ mb: 2 }}
          />
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Current Value"
              type="number"
              value={formData.current_value}
              onChange={(e) => handleFieldChange('current_value', e.target.value)}
              sx={{ flex: 1 }}
            />
            <TextField
              label="Target Value"
              type="number"
              value={formData.target_value}
              onChange={(e) => handleFieldChange('target_value', e.target.value)}
              sx={{ flex: 1 }}
            />
          </Box>
          <FormControl fullWidth>
            <InputLabel>Parent Goal</InputLabel>
            <Select
              value={formData.parent_goal_id}
              onChange={(e: SelectChangeEvent) => handleFieldChange('parent_goal_id', e.target.value)}
              label="Parent Goal"
            >
              <MenuItem value="">
                <em>None (Top Level)</em>
              </MenuItem>
              {goals
                .filter(g => g.id !== selectedGoal?.id)
                .map((goal) => (
                  <MenuItem key={goal.id} value={goal.id}>
                    {goal.title}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HierarchicalGoalTree;