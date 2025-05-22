import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  LinearProgress,
  Tooltip,
  Button,
  Menu,
  MenuItem,
  Stack,
  Alert
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  PeopleAlt as PeopleIcon,
  Computer as TechIcon,
  AttachMoney as MoneyIcon,
  Build as PhysicalIcon,
  Schedule as TimeIcon,
  Category as OtherIcon,
  Assignment as AssignIcon
} from '@mui/icons-material';
import { Resource } from '../../services/planningService';

interface ResourceListProps {
  resources: Resource[];
  onEdit: (resource: Resource) => void;
  onDelete: (resourceId: string) => void;
  onAllocate: (resource: Resource) => void;
}

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'human': return <PeopleIcon />;
    case 'technology': return <TechIcon />;
    case 'financial': return <MoneyIcon />;
    case 'physical': return <PhysicalIcon />;
    case 'time': return <TimeIcon />;
    default: return <OtherIcon />;
  }
};

const getStatusColor = (status: string): "default" | "success" | "warning" | "error" => {
  switch (status) {
    case 'available': return 'success';
    case 'allocated': return 'default';
    case 'partially_allocated': return 'warning';
    case 'over_allocated': return 'error';
    case 'unavailable': return 'default';
    default: return 'default';
  }
};

const ResourceList: React.FC<ResourceListProps> = ({ resources, onEdit, onDelete, onAllocate }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, resource: Resource) => {
    setAnchorEl(event.currentTarget);
    setSelectedResource(resource);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedResource(null);
  };

  const handleEdit = () => {
    if (selectedResource) {
      onEdit(selectedResource);
    }
    handleMenuClose();
  };

  const handleDelete = () => {
    if (selectedResource) {
      onDelete(selectedResource.id);
    }
    handleMenuClose();
  };

  const handleAllocate = () => {
    if (selectedResource) {
      onAllocate(selectedResource);
    }
    handleMenuClose();
  };

  if (resources.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          No resources have been defined for this project yet. Click "Add Resource" to get started.
        </Alert>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper} elevation={0}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Resource</TableCell>
            <TableCell>Type</TableCell>
            <TableCell align="right">Quantity</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Utilization</TableCell>
            <TableCell>Cost</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {resources.map((resource) => (
            <TableRow key={resource.id} hover>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getResourceIcon(resource.type)}
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {resource.name}
                    </Typography>
                    {resource.tags.length > 0 && (
                      <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                        {resource.tags.slice(0, 3).map((tag, index) => (
                          <Chip key={index} label={tag} size="small" variant="outlined" />
                        ))}
                        {resource.tags.length > 3 && (
                          <Typography variant="caption" color="text.secondary">
                            +{resource.tags.length - 3} more
                          </Typography>
                        )}
                      </Stack>
                    )}
                  </Box>
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                  {resource.type}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="body2">
                  {resource.allocated_quantity || 0} / {resource.total_quantity || resource.quantity || 0}
                </Typography>
                {resource.unit && (
                  <Typography variant="caption" color="text.secondary">
                    {resource.unit}
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Chip
                  label={resource.status.replace('_', ' ')}
                  size="small"
                  color={getStatusColor(resource.status)}
                  sx={{ textTransform: 'capitalize' }}
                />
              </TableCell>
              <TableCell>
                <Box sx={{ width: '100%', minWidth: 100 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2">
                      {resource.utilization_rate ? `${Math.round(resource.utilization_rate)}%` : '0%'}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={resource.utilization_rate || 0}
                    color={resource.utilization_rate && resource.utilization_rate > 90 ? 'error' : 'primary'}
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              </TableCell>
              <TableCell>
                {resource.cost_per_unit && (
                  <Typography variant="body2">
                    ${resource.cost_per_unit.toLocaleString()}
                    {resource.unit && ` / ${resource.unit}`}
                  </Typography>
                )}
                {resource.cost && (
                  <Typography variant="caption" color="text.secondary">
                    Total: ${resource.cost.toLocaleString()}
                  </Typography>
                )}
              </TableCell>
              <TableCell align="center">
                <IconButton
                  size="small"
                  onClick={(e) => handleMenuOpen(e, resource)}
                >
                  <MoreVertIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleAllocate}>
          <AssignIcon sx={{ mr: 1 }} fontSize="small" />
          Allocate
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>
    </TableContainer>
  );
};

export default ResourceList;