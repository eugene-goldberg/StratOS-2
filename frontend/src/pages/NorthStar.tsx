import React, { useState } from 'react';
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
  DialogActions
} from '@mui/material';
import { Edit as EditIcon, Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';

const NorthStar: React.FC = () => {
  const [editMode, setEditMode] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState<'value' | 'goal'>('value');

  const handleEditToggle = () => {
    setEditMode(!editMode);
  };

  const handleAddItem = (type: 'value' | 'goal') => {
    setDialogType(type);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

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
                defaultValue="To empower businesses with strategic clarity and data-driven insights for sustainable growth and meaningful impact."
                sx={{ mb: 2 }}
              />
            ) : (
              <Typography variant="h6" paragraph>
                To empower businesses with strategic clarity and data-driven insights for sustainable growth and meaningful impact.
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
                defaultValue="By 2030, to be the indispensable AI-powered strategic partner for 10,000 leadership teams worldwide, helping them navigate complexity and achieve their boldest ambitions."
                sx={{ mb: 2 }}
              />
            ) : (
              <Typography variant="h6" paragraph>
                By 2030, to be the indispensable AI-powered strategic partner for 10,000 leadership teams worldwide, helping them navigate complexity and achieve their boldest ambitions.
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

            {['Integrity', 'Innovation', 'Excellence', 'Collaboration', 'Customer Focus'].map((value, index) => (
              <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                <CardHeader
                  title={value}
                  action={
                    editMode && (
                      <IconButton aria-label="delete" size="small">
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
                        defaultValue="This is a description of the value and what it means to our organization."
                      />
                    ) : (
                      "This is a description of the value and what it means to our organization."
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

            {['Achieve 25% market share by Q4 2025', 'Launch 3 innovative product lines within 18 months', 'Increase customer retention to 85%'].map((goal, index) => (
              <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                <CardHeader
                  title={goal}
                  subheader="2023-2025"
                  action={
                    editMode && (
                      <IconButton aria-label="delete" size="small">
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
                          defaultValue="This strategic goal will help us strengthen our market position and drive sustainable growth."
                        />
                      ) : (
                        "This strategic goal will help us strengthen our market position and drive sustainable growth."
                      )}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Key Metrics:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip label="Revenue Growth" size="small" />
                      <Chip label="Market Share" size="small" />
                      <Chip label="Customer Acquisition" size="small" />
                    </Box>
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
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
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
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Key Metrics (comma separated)"
                fullWidth
                variant="outlined"
                placeholder="e.g., Revenue Growth, Market Share"
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCloseDialog} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NorthStar;