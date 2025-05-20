import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  IconButton,
  Divider,
  Chip,
  Tabs,
  Tab,
  Menu,
  MenuItem,
  InputAdornment,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent
} from '@mui/material';
import {
  Add as AddIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import LogEntryCreator from '../components/subjective/LogEntryCreator';
import LogEntryCard from '../components/subjective/LogEntryCard';
import VoiceInputButton from '../components/subjective/VoiceInputButton';
import { useLogStore } from '../store/logStore';
import { LogEntryType } from '../services/logService';
import { useAuthStore } from '../store/authStore';

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
      id={`log-tabpanel-${index}`}
      aria-labelledby={`log-tab-${index}`}
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

const CEOLog: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id || '';

  // State
  const [tabValue, setTabValue] = useState(0);
  const [filterMenuAnchorEl, setFilterMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [sortMenuAnchorEl, setSortMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [showNewEntryDialog, setShowNewEntryDialog] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [entryTypeFilter, setEntryTypeFilter] = useState<string | null>(null);
  
  // Get state and actions from store
  const { 
    entries, 
    isLoading, 
    error, 
    loadEntries, 
    loadMoreEntries, 
    filters, 
    setEntryTypeFilter, 
    setTagFilter,
    setSearchQuery,
    clearFilters
  } = useLogStore();
  
  // Load entries on mount
  useEffect(() => {
    loadEntries(userId, true);
    
    // Cleanup function
    return () => {
      // Reset store when unmounting
      clearFilters();
    };
  }, [loadEntries, userId, clearFilters]);
  
  // Load more entries when tab changes
  useEffect(() => {
    if (tabValue === 0) {
      loadEntries(userId, true);
    } else if (tabValue === 1) {
      // Recent tab - this could be the same as All but with a different sort
      loadEntries(userId, true);
    } else if (tabValue === 2) {
      // Favorites tab - this would filter for favorited entries
      // For now, just load all entries
      loadEntries(userId, true);
    } else if (tabValue === 3) {
      // By Tag tab - this would show a different layout focused on tags
      // For now, just load all entries
      loadEntries(userId, true);
    }
  }, [tabValue, loadEntries, userId]);
  
  // Tab change handler
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Filter menu handlers
  const handleFilterClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setFilterMenuAnchorEl(event.currentTarget);
  };
  
  const handleFilterClose = () => {
    setFilterMenuAnchorEl(null);
  };
  
  const handleFilterSelect = (type: string | null) => {
    setEntryTypeFilter(type);
    setFilterMenuAnchorEl(null);
    
    // Update store filter
    if (type === 'all') {
      setEntryTypeFilter(null);
    } else {
      setEntryTypeFilter(type);
    }
    
    // Reload entries with new filter
    loadEntries(userId, true);
  };
  
  // Sort menu handlers
  const handleSortClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setSortMenuAnchorEl(event.currentTarget);
  };
  
  const handleSortClose = () => {
    setSortMenuAnchorEl(null);
  };
  
  // Search handler
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };
  
  // View mode toggle
  const toggleViewMode = () => {
    setViewMode(viewMode === 'list' ? 'grid' : 'list');
  };
  
  // Handle new entry button click
  const handleNewEntryClick = () => {
    setShowNewEntryDialog(true);
  };
  
  // Close new entry dialog
  const handleCloseNewEntryDialog = () => {
    setShowNewEntryDialog(false);
  };
  
  // Handle entry created
  const handleEntryCreated = (entryId: string) => {
    handleCloseNewEntryDialog();
    // Reload entries to show the new one
    loadEntries(userId, true);
  };
  
  // Handle entry deleted
  const handleEntryDeleted = (entryId: string) => {
    // No need to reload, the store already removed it
  };
  
  // Handle add to canvas
  const handleAddToCanvas = (entryId: string) => {
    // This would navigate to the canvas page or open a dialog
    console.log('Add to canvas:', entryId);
  };
  
  // Filter for the current tab
  const getFilteredEntries = () => {
    if (tabValue === 0) {
      // All entries - already filtered by the store
      return entries;
    } else if (tabValue === 1) {
      // Recent entries - sort by date (already done by API)
      return entries;
    } else if (tabValue === 2) {
      // Favorites tab
      // Mock implementation - in a real app this would use a "favorited" flag
      return entries.filter(entry => entry.id.charAt(0) === 'a');
    } else if (tabValue === 3) {
      // By Tag tab - no additional filtering needed here
      return entries;
    }
    return entries;
  };
  
  const filteredEntries = getFilteredEntries();
  
  // No entries state
  const showNoEntries = !isLoading && filteredEntries.length === 0;
  
  // Get entry type label
  const getEntryTypeLabel = (type: string | null) => {
    if (!type || type === 'all') return 'All Types';
    
    switch (type) {
      case LogEntryType.IDEA:
        return 'Ideas';
      case LogEntryType.OBSERVATION:
        return 'Observations';
      case LogEntryType.CONCERN:
        return 'Concerns';
      case LogEntryType.REFLECTION:
        return 'Reflections';
      case LogEntryType.QUESTION:
        return 'Questions';
      default:
        return 'Notes';
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          CEO's Log
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <VoiceInputButton 
            userId={userId}
            onEntryCreated={handleEntryCreated}
          />
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleNewEntryClick}
          >
            New Entry
          </Button>
        </Box>
      </Box>

      {/* Tabs and Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="CEO Log tabs">
            <Tab label="All Entries" />
            <Tab label="Recent" />
            <Tab label="Favorites" />
            <Tab label="By Tag" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {/* Toolbar */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <TextField
              placeholder="Search log entries..."
              variant="outlined"
              size="small"
              value={filters.searchQuery}
              onChange={handleSearchChange}
              sx={{ width: '50%' }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton
                onClick={toggleViewMode}
                color="inherit"
              >
                {viewMode === 'list' ? <ViewModuleIcon /> : <ViewListIcon />}
              </IconButton>
              
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={handleFilterClick}
                endIcon={
                  filters.entryType ? 
                    <Chip 
                      label={getEntryTypeLabel(filters.entryType)} 
                      size="small" 
                      onDelete={() => handleFilterSelect('all')}
                    /> : 
                    <ExpandMoreIcon />
                }
              >
                Filter
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<SortIcon />}
                onClick={handleSortClick}
              >
                Sort
              </Button>
              
              {/* Filter Menu */}
              <Menu
                anchorEl={filterMenuAnchorEl}
                open={Boolean(filterMenuAnchorEl)}
                onClose={handleFilterClose}
              >
                <MenuItem onClick={() => handleFilterSelect('all')}>
                  All Types
                </MenuItem>
                <MenuItem onClick={() => handleFilterSelect(LogEntryType.IDEA)}>
                  Ideas
                </MenuItem>
                <MenuItem onClick={() => handleFilterSelect(LogEntryType.OBSERVATION)}>
                  Observations
                </MenuItem>
                <MenuItem onClick={() => handleFilterSelect(LogEntryType.CONCERN)}>
                  Concerns
                </MenuItem>
                <MenuItem onClick={() => handleFilterSelect(LogEntryType.REFLECTION)}>
                  Reflections
                </MenuItem>
                <MenuItem onClick={() => handleFilterSelect(LogEntryType.QUESTION)}>
                  Questions
                </MenuItem>
              </Menu>
              
              {/* Sort Menu */}
              <Menu
                anchorEl={sortMenuAnchorEl}
                open={Boolean(sortMenuAnchorEl)}
                onClose={handleSortClose}
              >
                <MenuItem onClick={handleSortClose}>
                  Newest First
                </MenuItem>
                <MenuItem onClick={handleSortClose}>
                  Oldest First
                </MenuItem>
                <MenuItem onClick={handleSortClose}>
                  Recently Updated
                </MenuItem>
              </Menu>
            </Box>
          </Box>

          {/* Quick Entry Form */}
          <Box sx={{ mb: 3 }}>
            <LogEntryCreator 
              userId={userId}
              variant="compact"
              onEntryCreated={handleEntryCreated}
            />
          </Box>
          
          {/* Loading State */}
          {isLoading && filteredEntries.length === 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
          
          {/* Error State */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {/* No Entries State */}
          {showNoEntries && (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                No log entries found
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {filters.entryType || filters.tag ? 
                  "Try changing your filters or create a new entry." : 
                  "Start by creating your first log entry."}
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<AddIcon />}
                onClick={handleNewEntryClick}
              >
                Create New Entry
              </Button>
            </Paper>
          )}
          
          {/* Entries List/Grid */}
          {!showNoEntries && (
            <Grid container spacing={viewMode === 'grid' ? 3 : 2}>
              {filteredEntries.map((entry) => (
                <Grid item xs={12} md={viewMode === 'grid' ? 6 : 12} key={entry.id}>
                  <LogEntryCard
                    entry={entry}
                    userId={userId}
                    onDelete={handleEntryDeleted}
                    onAddToCanvas={handleAddToCanvas}
                  />
                </Grid>
              ))}
            </Grid>
          )}
          
          {/* Load More Button */}
          {!isLoading && filteredEntries.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Button 
                variant="outlined" 
                onClick={() => loadMoreEntries(userId)}
                disabled={isLoading || !useLogStore.getState().pagination.hasMore}
              >
                {isLoading ? 'Loading...' : 'Load More'}
              </Button>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography>Recent entries will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Favorite entries will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography>Entries organized by tag will be displayed here</Typography>
        </TabPanel>
      </Box>
      
      {/* New Entry Dialog */}
      <Dialog 
        open={showNewEntryDialog} 
        onClose={handleCloseNewEntryDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>New Log Entry</DialogTitle>
        <DialogContent dividers>
          <LogEntryCreator 
            userId={userId}
            initialFocus={true}
            onEntryCreated={handleEntryCreated}
            showTypeTabs={true}
            strategicElements={{
              purposeVision: true,
              values: [
                { id: "1", name: "Integrity" },
                { id: "2", name: "Innovation" },
                { id: "3", name: "Excellence" },
                { id: "4", name: "Collaboration" },
                { id: "5", name: "Customer Focus" }
              ],
              goals: [
                { id: "1", title: "Achieve 25% market share by Q4 2025" },
                { id: "2", title: "Launch 3 innovative product lines within 18 months" },
                { id: "3", title: "Increase customer retention to 85%" }
              ]
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseNewEntryDialog}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CEOLog;