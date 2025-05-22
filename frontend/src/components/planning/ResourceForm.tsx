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
  Chip,
  InputAdornment,
  Typography,
  FormHelperText,
  Stack
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Resource, ResourceCreate, ResourceUpdate } from '../../services/planningService';

interface ResourceFormProps {
  open: boolean;
  resource?: Resource | null;
  onClose: () => void;
  onSave: (data: ResourceCreate | ResourceUpdate) => void;
}

const resourceTypes = [
  { value: 'financial', label: 'Financial', unit: 'USD' },
  { value: 'human', label: 'Human', unit: 'hours' },
  { value: 'technology', label: 'Technology', unit: 'units' },
  { value: 'physical', label: 'Physical', unit: 'units' },
  { value: 'time', label: 'Time', unit: 'days' },
  { value: 'other', label: 'Other', unit: '' }
];

const ResourceForm: React.FC<ResourceFormProps> = ({ open, resource, onClose, onSave }) => {
  const [formData, setFormData] = useState<ResourceCreate>({
    name: '',
    type: 'financial',
    quantity: undefined,
    unit: 'USD',
    cost: undefined,
    total_quantity: undefined,
    availability_start: undefined,
    availability_end: undefined,
    cost_per_unit: undefined,
    tags: [],
    constraints: ''
  });

  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (resource) {
      setFormData({
        name: resource.name,
        type: resource.type,
        quantity: resource.quantity,
        unit: resource.unit,
        cost: resource.cost,
        total_quantity: resource.total_quantity,
        availability_start: resource.availability_start,
        availability_end: resource.availability_end,
        cost_per_unit: resource.cost_per_unit,
        tags: resource.tags || [],
        constraints: resource.constraints || ''
      });
    } else {
      setFormData({
        name: '',
        type: 'financial',
        quantity: undefined,
        unit: 'USD',
        cost: undefined,
        total_quantity: undefined,
        availability_start: undefined,
        availability_end: undefined,
        cost_per_unit: undefined,
        tags: [],
        constraints: ''
      });
    }
  }, [resource]);

  const handleChange = (field: keyof ResourceCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when field is changed
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }

    // Auto-calculate total cost if both quantity and cost_per_unit are set
    if (field === 'total_quantity' || field === 'cost_per_unit') {
      const quantity = field === 'total_quantity' ? value : formData.total_quantity;
      const costPerUnit = field === 'cost_per_unit' ? value : formData.cost_per_unit;
      
      if (quantity && costPerUnit) {
        setFormData(prev => ({ ...prev, cost: quantity * costPerUnit }));
      }
    }
  };

  const handleTypeChange = (type: string) => {
    const selectedType = resourceTypes.find(t => t.value === type);
    setFormData(prev => ({
      ...prev,
      type: type as any,
      unit: selectedType?.unit || ''
    }));
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: (prev.tags || []).filter(t => t !== tag)
    }));
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Resource name is required';
    }

    if (!formData.type) {
      newErrors.type = 'Resource type is required';
    }

    if (formData.total_quantity !== undefined && formData.total_quantity <= 0) {
      newErrors.total_quantity = 'Total quantity must be greater than 0';
    }

    if (formData.cost_per_unit !== undefined && formData.cost_per_unit < 0) {
      newErrors.cost_per_unit = 'Cost per unit cannot be negative';
    }

    if (formData.availability_start && formData.availability_end) {
      const start = new Date(formData.availability_start);
      const end = new Date(formData.availability_end);
      if (start >= end) {
        newErrors.availability_end = 'End date must be after start date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSave(formData);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{resource ? 'Edit Resource' : 'Add New Resource'}</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Resource Name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                error={!!errors.name}
                helperText={errors.name}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth required error={!!errors.type}>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => handleTypeChange(e.target.value)}
                  label="Type"
                >
                  {resourceTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.type && <FormHelperText>{errors.type}</FormHelperText>}
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Total Quantity"
                value={formData.total_quantity || ''}
                onChange={(e) => handleChange('total_quantity', e.target.value ? Number(e.target.value) : undefined)}
                error={!!errors.total_quantity}
                helperText={errors.total_quantity || 'The total amount available'}
                InputProps={{
                  endAdornment: formData.unit && (
                    <InputAdornment position="end">{formData.unit}</InputAdornment>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Unit of Measure"
                value={formData.unit || ''}
                onChange={(e) => handleChange('unit', e.target.value)}
                helperText="e.g., hours, days, units, USD"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Cost per Unit"
                value={formData.cost_per_unit || ''}
                onChange={(e) => handleChange('cost_per_unit', e.target.value ? Number(e.target.value) : undefined)}
                error={!!errors.cost_per_unit}
                helperText={errors.cost_per_unit}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>
                }}
              />
            </Grid>

            <Grid item xs={12}>
              {formData.cost !== undefined && (
                <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Estimated Cost
                  </Typography>
                  <Typography variant="h6">
                    ${formData.cost.toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Grid>

            <Grid item xs={12}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <DateTimePicker
                      label="Available From"
                      value={formData.availability_start ? new Date(formData.availability_start) : null}
                      onChange={(value) => handleChange('availability_start', value ? (value as Date).toISOString() : undefined)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          helperText="When the resource becomes available"
                        />
                      )}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <DateTimePicker
                      label="Available Until"
                      value={formData.availability_end ? new Date(formData.availability_end) : null}
                      onChange={(value) => handleChange('availability_end', value ? (value as Date).toISOString() : undefined)}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          error={!!errors.availability_end}
                          helperText={errors.availability_end || "When the resource is no longer available"}
                        />
                      )}
                    />
                  </Grid>
                </Grid>
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Constraints or Notes"
                value={formData.constraints || ''}
                onChange={(e) => handleChange('constraints', e.target.value)}
                helperText="Any limitations, dependencies, or special requirements"
              />
            </Grid>

            <Grid item xs={12}>
              <Box>
                <TextField
                  fullWidth
                  label="Tags"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="Add tags for categorization"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <Button size="small" onClick={handleAddTag}>Add</Button>
                      </InputAdornment>
                    )
                  }}
                />
                {formData.tags && formData.tags.length > 0 && (
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap">
                    {formData.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        onDelete={() => handleRemoveTag(tag)}
                        size="small"
                      />
                    ))}
                  </Stack>
                )}
              </Box>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          {resource ? 'Update' : 'Create'} Resource
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ResourceForm;