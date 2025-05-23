import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Tab,
  Tabs,
  Paper,
  CircularProgress,
  Alert,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Add as AddIcon,
  Dashboard as DashboardIcon,
  List as ListIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { usePlanningStore } from '../../store/planningStore';
import ResourceList from './ResourceList';
import ResourceForm from './ResourceForm';
import ResourceAllocation from './ResourceAllocation';
import ResourceUtilization from './ResourceUtilization';
import { Resource, ResourceCreate, ResourceUpdate } from '../../services/planningService';

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
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const ResourcesTab: React.FC = () => {
  const {
    initiatives,
    resourceUtilization,
    resourceConflicts,
    isLoading,
    error,
    loadPlans,
    createResource,
    updateResource,
    deleteResource,
    allocateResource,
    releaseResourceAllocation,
    loadResourceUtilization,
    checkResourceConflicts
  } = usePlanningStore();

  const [tabValue, setTabValue] = useState(0);
  const [openForm, setOpenForm] = useState(false);
  const [openAllocation, setOpenAllocation] = useState(false);
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [selectedInitiative, setSelectedInitiative] = useState<string>('');
  const [filterResourceType, setFilterResourceType] = useState<string>('');

  useEffect(() => {
    loadPlans();
    loadResourceUtilization();
  }, [loadPlans, loadResourceUtilization]);

  // Get all resources from all initiatives
  const allResources = initiatives.flatMap(i => i.resources || []);
  
  // Filter resources based on selected type
  const filteredResources = filterResourceType 
    ? allResources.filter(r => r.type === filterResourceType)
    : allResources;

  // Filter resources based on selected initiative
  const initiativeResources = selectedInitiative
    ? initiatives.find(i => i.id === selectedInitiative)?.resources || []
    : filteredResources;

  const handleSaveResource = async (data: ResourceCreate | ResourceUpdate) => {
    if (selectedResource) {
      // Update existing resource
      if (!selectedInitiative) return;
      await updateResource(selectedInitiative, selectedResource.id, data as ResourceUpdate);
    } else {
      // Create new resource
      if (!selectedInitiative) {
        alert('Please select an initiative first');
        return;
      }
      await createResource(selectedInitiative, data as ResourceCreate);
    }
    setOpenForm(false);
    setSelectedResource(null);
    loadResourceUtilization();
  };

  const handleDeleteResource = async (resourceId: string) => {
    if (!selectedInitiative) return;
    if (window.confirm('Are you sure you want to delete this resource?')) {
      await deleteResource(selectedInitiative, resourceId);
      loadResourceUtilization();
    }
  };

  const handleAllocateResource = async (data: any) => {
    await allocateResource(data);
    setOpenAllocation(false);
    setSelectedResource(null);
  };

  const handleReleaseAllocation = async (allocationId: string) => {
    if (window.confirm('Are you sure you want to release this allocation?')) {
      await releaseResourceAllocation(allocationId);
    }
  };

  const handleEditResource = (resource: Resource) => {
    setSelectedResource(resource);
    // Find which initiative this resource belongs to
    const initiative = initiatives.find(i => i.resources.some(r => r.id === resource.id));
    if (initiative) {
      setSelectedInitiative(initiative.id);
    }
    setOpenForm(true);
  };

  const handleAllocateClick = (resource: Resource) => {
    setSelectedResource(resource);
    setOpenAllocation(true);
  };

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Resource Management</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => {
              loadPlans();
              loadResourceUtilization();
            }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setSelectedResource(null);
              setOpenForm(true);
            }}
            disabled={!selectedInitiative && tabValue === 0}
          >
            Add Resource
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper elevation={0} sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Filter by Initiative</InputLabel>
              <Select
                value={selectedInitiative}
                onChange={(e) => {
                  setSelectedInitiative(e.target.value);
                  if (e.target.value) {
                    checkResourceConflicts(e.target.value);
                  }
                }}
                label="Filter by Initiative"
              >
                <MenuItem value="">
                  <em>All Initiatives</em>
                </MenuItem>
                {initiatives.map(init => (
                  <MenuItem key={init.id} value={init.id}>
                    {init.title}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Filter by Type</InputLabel>
              <Select
                value={filterResourceType}
                onChange={(e) => setFilterResourceType(e.target.value)}
                label="Filter by Type"
              >
                <MenuItem value="">
                  <em>All Types</em>
                </MenuItem>
                <MenuItem value="financial">Financial</MenuItem>
                <MenuItem value="human">Human</MenuItem>
                <MenuItem value="technology">Technology</MenuItem>
                <MenuItem value="physical">Physical</MenuItem>
                <MenuItem value="time">Time</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab icon={<ListIcon />} label="Resource List" />
          <Tab icon={<DashboardIcon />} label="Utilization Dashboard" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <ResourceList
            resources={initiativeResources}
            onEdit={handleEditResource}
            onDelete={handleDeleteResource}
            onAllocate={handleAllocateClick}
          />
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <ResourceUtilization
          utilization={resourceUtilization}
          conflicts={selectedInitiative ? resourceConflicts : []}
        />
      </TabPanel>

      {/* Dialogs */}
      <ResourceForm
        open={openForm}
        resource={selectedResource}
        onClose={() => {
          setOpenForm(false);
          setSelectedResource(null);
        }}
        onSave={handleSaveResource}
      />

      <ResourceAllocation
        open={openAllocation}
        resource={selectedResource}
        initiatives={initiatives}
        onClose={() => {
          setOpenAllocation(false);
          setSelectedResource(null);
        }}
        onAllocate={handleAllocateResource}
        onRelease={handleReleaseAllocation}
      />
    </Box>
  );
};

export default ResourcesTab;