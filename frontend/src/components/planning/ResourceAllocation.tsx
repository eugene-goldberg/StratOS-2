import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Slider,
  InputAdornment
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { Resource, ResourceAllocationCreate, Initiative } from '../../services/planningService';
import { format } from 'date-fns';

interface ResourceAllocationProps {
  open: boolean;
  resource: Resource | null;
  initiatives: Initiative[];
  onClose: () => void;
  onAllocate: (data: ResourceAllocationCreate) => void;
  onRelease: (allocationId: string) => void;
}

const ResourceAllocation: React.FC<ResourceAllocationProps> = ({ 
  open, 
  resource, 
  initiatives,
  onClose, 
  onAllocate,
  onRelease 
}) => {
  const [selectedInitiative, setSelectedInitiative] = useState<string>('');
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [allocatedQuantity, setAllocatedQuantity] = useState<number>(0);
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [initiative, setInitiative] = useState<Initiative | null>(null);

  useEffect(() => {
    if (selectedInitiative) {
      const init = initiatives.find(i => i.id === selectedInitiative);
      setInitiative(init || null);
      setSelectedAction(''); // Reset action when initiative changes
    }
  }, [selectedInitiative, initiatives]);

  useEffect(() => {
    // Reset form when dialog opens/closes
    if (!open) {
      setSelectedInitiative('');
      setSelectedAction('');
      setAllocatedQuantity(0);
      setNotes('');
      setErrors({});
    }
  }, [open]);

  const availableQuantity = resource ? 
    (resource.total_quantity || resource.quantity || 0) - (resource.allocated_quantity || 0) : 0;

  const utilizationRate = resource ? 
    ((resource.allocated_quantity || 0) / (resource.total_quantity || resource.quantity || 1)) * 100 : 0;

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!selectedInitiative) {
      newErrors.initiative = 'Please select an initiative';
    }

    if (allocatedQuantity <= 0) {
      newErrors.quantity = 'Allocation quantity must be greater than 0';
    }

    if (allocatedQuantity > availableQuantity) {
      newErrors.quantity = `Cannot allocate more than available quantity (${availableQuantity} ${resource?.unit || ''})`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate() && resource) {
      onAllocate({
        resource_id: resource.id,
        initiative_id: selectedInitiative,
        action_id: selectedAction || undefined,
        allocated_quantity: allocatedQuantity,
        notes: notes || undefined
      });
      onClose();
    }
  };

  if (!resource) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Allocate Resource: {resource.name}</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {/* Resource Overview */}
          <Paper elevation={0} sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Available</Typography>
                <Typography variant="h6">
                  {availableQuantity} {resource.unit || 'units'}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">Current Utilization</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h6">{Math.round(utilizationRate)}%</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={utilizationRate}
                    sx={{ flexGrow: 1 }}
                    color={utilizationRate > 90 ? 'error' : 'primary'}
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Allocation Form */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth required error={!!errors.initiative}>
                <InputLabel>Initiative</InputLabel>
                <Select
                  value={selectedInitiative}
                  onChange={(e) => setSelectedInitiative(e.target.value)}
                  label="Initiative"
                >
                  {initiatives.map(init => (
                    <MenuItem key={init.id} value={init.id}>
                      <Box>
                        <Typography variant="body2">{init.title}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {init.status} • {init.progress || 0}% complete
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.initiative && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                    {errors.initiative}
                  </Typography>
                )}
              </FormControl>
            </Grid>

            {initiative && initiative.actions.length > 0 && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Action (Optional)</InputLabel>
                  <Select
                    value={selectedAction}
                    onChange={(e) => setSelectedAction(e.target.value)}
                    label="Action (Optional)"
                  >
                    <MenuItem value="">
                      <em>None - Allocate to initiative</em>
                    </MenuItem>
                    {initiative.actions.map(action => (
                      <MenuItem key={action.id} value={action.id}>
                        <Box>
                          <Typography variant="body2">{action.title}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {action.status} • {action.owner || 'Unassigned'}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            <Grid item xs={12}>
              <Typography gutterBottom>Quantity to Allocate</Typography>
              <Slider
                value={allocatedQuantity}
                onChange={(_, value) => setAllocatedQuantity(value as number)}
                max={availableQuantity}
                min={0}
                step={1}
                marks
                valueLabelDisplay="on"
                valueLabelFormat={(value) => `${value} ${resource.unit || ''}`}
              />
              <TextField
                fullWidth
                type="number"
                value={allocatedQuantity}
                onChange={(e) => setAllocatedQuantity(Number(e.target.value))}
                error={!!errors.quantity}
                helperText={errors.quantity}
                InputProps={{
                  endAdornment: resource.unit && (
                    <InputAdornment position="end">{resource.unit}</InputAdornment>
                  )
                }}
                sx={{ mt: 2 }}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Notes (Optional)"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any special notes about this allocation"
              />
            </Grid>
          </Grid>

          {/* Current Allocations */}
          {resource.allocations && resource.allocations.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Current Allocations</Typography>
              <TableContainer component={Paper} elevation={0}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Initiative</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell>Allocated</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {resource.allocations.map((allocation) => {
                      const allocInit = initiatives.find(i => i.id === allocation.initiative_id);
                      return (
                        <TableRow key={allocation.id}>
                          <TableCell>
                            <Typography variant="body2">
                              {allocInit?.title || 'Unknown Initiative'}
                            </Typography>
                            {allocation.notes && (
                              <Typography variant="caption" color="text.secondary">
                                {allocation.notes}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            {allocation.allocated_quantity} {resource.unit || ''}
                          </TableCell>
                          <TableCell>
                            {format(new Date(allocation.allocation_date), 'MMM d, yyyy')}
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => onRelease(allocation.id)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {resource.status === 'over_allocated' && (
            <Alert severity="error" sx={{ mt: 2 }}>
              This resource is currently over-allocated. Consider releasing some allocations before adding new ones.
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={availableQuantity <= 0}>
          Allocate Resource
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ResourceAllocation;