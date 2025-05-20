import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  TextField,
  InputAdornment,
  Divider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  LinearProgress,
  Snackbar,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  CloudUpload as UploadIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import useObjectiveDataStore from '../store/objectiveDataStore';
import useNorthStarStore from '../store/northStarStore';

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
      id={`objdata-tabpanel-${index}`}
      aria-labelledby={`objdata-tab-${index}`}
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

const ObjectiveData: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState<'kpi' | 'dataset'>('kpi');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenDialog = (type: 'kpi' | 'dataset') => {
    setDialogType(type);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setKpiName('');
    setKpiCurrent('');
    setKpiTarget('');
    setKpiUnit('');
    setDatasetName('');
    setDatasetDesc('');
    setDatasetFile(null);
    setTags([]);
    setTagInput('');
    setSelectedGoals([]);
  };

  const handleCategoryChange = (event: SelectChangeEvent) => {
    setCategory(event.target.value);
  };

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const value = tagInput.trim();
      if (value && !tags.includes(value)) {
        setTags([...tags, value]);
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleGoalsChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value as string[];
    setSelectedGoals(value);
  };

  const handleViewDetails = async (id: string) => {
    await getDataset(id);
    setDetailOpen(true);
  };

  const handleCloseDetail = () => setDetailOpen(false);

  const handleConfirmDelete = (id: string) => {
    setConfirmDeleteId(id);
  };

  const handleDelete = async () => {
    if (confirmDeleteId) {
      await deleteDataset(confirmDeleteId);
      setConfirmDeleteId(null);
    }
  };

  const handleSubmit = async () => {
    if (dialogType === 'kpi') {
      await createKPI({
        name: kpiName,
        category,
        current_value: parseFloat(kpiCurrent),
        target_value: kpiTarget ? parseFloat(kpiTarget) : undefined,
        unit: kpiUnit || undefined
      });
    } else if (datasetFile) {
      await uploadDataset(
        datasetFile,
        datasetName,
        category,
        datasetDesc,
        tags,
        selectedGoals
      );
    }
    handleCloseDialog();
  };

  const {
    kpis,
    datasets,
    loadKPIs,
    loadDatasets,
    createKPI,
    uploadDataset,
    deleteDataset,
    getDataset,
    isLoading,
    uploading,
    uploadProgress,
    error
  } = useObjectiveDataStore();
  const { strategicGoals, loadStrategicGoals } = useNorthStarStore();

  const [kpiName, setKpiName] = useState('');
  const [kpiCurrent, setKpiCurrent] = useState('');
  const [kpiTarget, setKpiTarget] = useState('');
  const [kpiUnit, setKpiUnit] = useState('');

  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [datasetFile, setDatasetFile] = useState<File | null>(null);

  useEffect(() => {
    loadKPIs();
    loadDatasets();
    loadStrategicGoals();
  }, [loadKPIs, loadDatasets, loadStrategicGoals]);

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Objective Data
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => handleOpenDialog('dataset')}
            sx={{ mr: 1 }}
          >
            Upload Data
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog('kpi')}
          >
            Add KPI
          </Button>
        </Box>
      </Box>

      <Box sx={{ width: '100%', height: 'calc(100% - 50px)' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Objective Data tabs">
            <Tab label="Key Performance Indicators" />
            <Tab label="Datasets" />
            <Tab label="Data Sources" />
            <Tab label="Analytics" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <TextField
              placeholder="Search KPIs..."
              variant="outlined"
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ width: '300px' }}
            />
            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
            >
              Filter
            </Button>
          </Box>

          <TableContainer component={Paper} elevation={0} sx={{ mb: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>KPI Name</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Current Value</TableCell>
                  <TableCell>Target</TableCell>
                  <TableCell>Trend</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {kpis.map((kpi) => (
                  <TableRow key={kpi.id}>
                    <TableCell>{kpi.name}</TableCell>
                    <TableCell>
                      <Chip label={kpi.category} size="small" />
                    </TableCell>
                    <TableCell>{kpi.current_value}</TableCell>
                    <TableCell>{kpi.target_value}</TableCell>
                    <TableCell>
                      {kpi.trend === 'up' && <Chip label="↑" size="small" color="success" />}
                      {kpi.trend === 'down' && <Chip label="↓" size="small" color="error" />}
                      {kpi.trend === 'stable' && <Chip label="→" size="small" color="default" />}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleConfirmDelete(dataset.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1" gutterBottom>
              KPI Insights
            </Typography>
            <IconButton size="small">
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Revenue Growth Trending Below Target
                  </Typography>
                  <Typography variant="body2">
                    Current growth rate of 12.5% is below the target of 15%. Historical data suggests a correlation with marketing spend.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Employee Retention Declining
                  </Typography>
                  <Typography variant="body2">
                    The 5% drop in retention rate over the last quarter warrants attention. Exit interviews highlight compensation concerns.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Market Share Growth Opportunity
                  </Typography>
                  <Typography variant="body2">
                    Current 18% market share has potential to reach 22% target with increased focus on the enterprise segment.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <TextField
              placeholder="Search datasets..."
              variant="outlined"
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ width: '300px' }}
            />
            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
            >
              Filter
            </Button>
          </Box>

          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Dataset Name</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Upload Date</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading && (
                  <TableRow>
                    <TableCell colSpan={7}>Loading...</TableCell>
                  </TableRow>
                )}
                {datasets.map((dataset) => (
                  <TableRow key={dataset.id}>
                    <TableCell>
                      <Button size="small" onClick={() => handleViewDetails(dataset.id)}>
                        {dataset.name}
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Chip label={dataset.category} size="small" />
                    </TableCell>
                    <TableCell>{dataset.data_format}</TableCell>
                    <TableCell>{dataset.import_date ? new Date(dataset.import_date).toLocaleDateString() : ''}</TableCell>
                    <TableCell>
                      {dataset.metadata?.size_bytes ? `${(dataset.metadata.size_bytes/1024).toFixed(1)} KB` : ''}
                    </TableCell>
                    <TableCell>{dataset.metadata?.processing_status || ''}</TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleConfirmDelete(dataset.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Data Sources will be displayed here</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography>Data Analytics will be displayed here</Typography>
        </TabPanel>
      </Box>

      {/* Dialog for adding KPI or uploading dataset */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'kpi' ? 'Add New KPI' : 'Upload Dataset'}
        </DialogTitle>
        <DialogContent>
          {dialogType === 'kpi' ? (
            <>
              <TextField
                autoFocus
                margin="dense"
                label="KPI Name"
                fullWidth
                variant="outlined"
                value={kpiName}
                onChange={(e) => setKpiName(e.target.value)}
                sx={{ mb: 2, mt: 1 }}
              />
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel>Category</InputLabel>
                <Select
                  value={category}
                  onChange={handleCategoryChange}
                  label="Category"
                >
                  <MenuItem value="Financial">Financial</MenuItem>
                  <MenuItem value="Customer">Customer</MenuItem>
                  <MenuItem value="Market">Market</MenuItem>
                  <MenuItem value="Operations">Operations</MenuItem>
                  <MenuItem value="HR">Human Resources</MenuItem>
                </Select>
              </FormControl>
              <TextField
                margin="dense"
                label="Current Value"
                fullWidth
                variant="outlined"
                value={kpiCurrent}
                onChange={(e) => setKpiCurrent(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Target Value"
                fullWidth
                variant="outlined"
                value={kpiTarget}
                onChange={(e) => setKpiTarget(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Unit (e.g., %, $)"
                fullWidth
                variant="outlined"
                value={kpiUnit}
                onChange={(e) => setKpiUnit(e.target.value)}
              />
            </>
          ) : (
            <>
              <TextField
                autoFocus
                margin="dense"
                label="Dataset Name"
                fullWidth
                variant="outlined"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                sx={{ mb: 2, mt: 1 }}
              />
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel>Category</InputLabel>
                <Select
                  value={category}
                  onChange={handleCategoryChange}
                  label="Category"
                >
                  <MenuItem value="Financial">Financial</MenuItem>
                  <MenuItem value="Customer">Customer</MenuItem>
                  <MenuItem value="Market">Market</MenuItem>
                  <MenuItem value="Competitor">Competitor</MenuItem>
                  <MenuItem value="Marketing">Marketing</MenuItem>
                </Select>
              </FormControl>
              <TextField
                margin="dense"
                label="Description"
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                value={datasetDesc}
                onChange={(e) => setDatasetDesc(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Add Tag"
                fullWidth
                variant="outlined"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                sx={{ mb: 1 }}
              />
              <Box sx={{ mb: 2 }}>
                {tags.map((t) => (
                  <Chip key={t} label={t} onDelete={() => handleRemoveTag(t)} sx={{ mr: 0.5, mb: 0.5 }} />
                ))}
              </Box>
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel>Link Strategic Goals</InputLabel>
                <Select
                  multiple
                  value={selectedGoals}
                  onChange={handleGoalsChange}
                  label="Link Strategic Goals"
                  renderValue={(selected) =>
                    strategicGoals
                      .filter((g) => selected.includes(g.id))
                      .map((g) => g.title)
                      .join(', ')
                  }
                >
                  {strategicGoals.map((goal) => (
                    <MenuItem key={goal.id} value={goal.id}>
                      {goal.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="outlined"
                component="label"
                startIcon={<UploadIcon />}
                fullWidth
              >
                Choose File
                <input type="file" hidden onChange={(e) => setDatasetFile(e.target.files ? e.target.files[0] : null)} />
              </Button>
              {uploading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress variant="determinate" value={uploadProgress} />
                </Box>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {dialogType === 'kpi' ? 'Add KPI' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={detailOpen} onClose={handleCloseDetail} maxWidth="sm" fullWidth>
        <DialogTitle>Dataset Details</DialogTitle>
        <DialogContent>
          {selectedDataset && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {selectedDataset.name}
              </Typography>
              <Typography variant="body2" gutterBottom>
                {selectedDataset.description}
              </Typography>
              <Typography variant="body2">
                Status: {selectedDataset.metadata?.processing_status}
              </Typography>
              <Typography variant="body2">
                Uploaded: {selectedDataset.import_date ? new Date(selectedDataset.import_date).toLocaleString() : ''}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetail}>Close</Button>
        </DialogActions>
      </Dialog>
      <Dialog open={Boolean(confirmDeleteId)} onClose={() => setConfirmDeleteId(null)}>
        <DialogTitle>Delete Dataset?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setConfirmDeleteId(null)}>Cancel</Button>
          <Button color="error" onClick={handleDelete}>Delete</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={Boolean(error)} autoHideDuration={6000}>
        <Alert severity="error" sx={{ width: "100%" }}>{error}</Alert>
      </Snackbar>
    </Box>
  );
export default ObjectiveData;
