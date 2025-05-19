import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  IconButton,
  TextField,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  FormatShapes as ShapesIcon,
  TextFields as TextIcon,
  Image as ImageIcon,
  Link as LinkIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Mic as MicIcon
} from '@mui/icons-material';

// This would be replaced with an actual canvas library implementation
const MockCanvas = () => {
  return (
    <Box
      sx={{
        height: '100%',
        width: '100%',
        backgroundColor: '#f9f9f9',
        border: '1px solid #e0e0e0',
        borderRadius: 1,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Mock canvas elements */}
      <Box
        sx={{
          position: 'absolute',
          top: '50px',
          left: '100px',
          padding: 2,
          backgroundColor: '#bbdefb',
          borderRadius: 1,
          boxShadow: 1,
          maxWidth: '200px'
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">Market Expansion</Typography>
        <Typography variant="body2">Explore opportunities in Asia Pacific region</Typography>
      </Box>
      
      <Box
        sx={{
          position: 'absolute',
          top: '150px',
          left: '400px',
          padding: 2,
          backgroundColor: '#c8e6c9',
          borderRadius: 1,
          boxShadow: 1,
          maxWidth: '200px'
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">Customer Segment</Typography>
        <Typography variant="body2">Enterprise clients with 1000+ employees</Typography>
      </Box>
      
      <Box
        sx={{
          position: 'absolute',
          top: '250px',
          left: '200px',
          padding: 2,
          backgroundColor: '#ffecb3',
          borderRadius: 1,
          boxShadow: 1,
          maxWidth: '200px'
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">Competitive Advantage</Typography>
        <Typography variant="body2">Proprietary AI technology with 30% better accuracy</Typography>
      </Box>
      
      {/* Mock connection lines */}
      <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
        <line x1="150" y1="100" x2="400" y2="170" stroke="#999" strokeWidth="2" />
        <line x1="160" y1="110" x2="220" y2="250" stroke="#999" strokeWidth="2" />
        <line x1="450" y1="190" x2="320" y2="270" stroke="#999" strokeWidth="2" />
      </svg>
    </Box>
  );
};

const StrategicCanvas: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAddElement = (type: string) => {
    setAnchorEl(null);
    // Logic to add element would go here
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const toggleVoiceListener = () => {
    setIsListening(!isListening);
    // Voice command logic would go here
  };

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1">
          Strategic Canvas
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            sx={{ mr: 1 }}
          >
            Save
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleMenuClick}
          >
            Add Element
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => handleAddElement('text')}>
              <ListItemIcon>
                <TextIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Text Note</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAddElement('shape')}>
              <ListItemIcon>
                <ShapesIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Shape</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAddElement('image')}>
              <ListItemIcon>
                <ImageIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Image</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleAddElement('link')}>
              <ListItemIcon>
                <LinkIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Connection</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      <Paper elevation={0} sx={{ p: 1, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <TextField
              variant="outlined"
              size="small"
              fullWidth
              label="Canvas Title"
              defaultValue="Product Strategy Brainstorm"
            />
          </Grid>
          <Grid item>
            <Tooltip title="Voice Commands">
              <IconButton 
                color={isListening ? "secondary" : "default"}
                onClick={toggleVoiceListener}
              >
                <MicIcon />
              </IconButton>
            </Tooltip>
          </Grid>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Grid item>
            <Tooltip title="Undo">
              <IconButton size="small">
                <UndoIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Redo">
              <IconButton size="small">
                <RedoIcon />
              </IconButton>
            </Tooltip>
          </Grid>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Grid item>
            <Tooltip title="Zoom In">
              <IconButton size="small">
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Zoom Out">
              <IconButton size="small">
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
          </Grid>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Grid item>
            <Tooltip title="Delete Selected">
              <IconButton size="small">
                <DeleteIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="More Options">
              <IconButton size="small">
                <MoreIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <MockCanvas />
      </Box>

      {/* Dialog for adding new elements */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Add Text Note</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            variant="outlined"
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Content"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCloseDialog} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategicCanvas;