import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Typography,
  Box,
  Chip,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Collapse,
  TextField,
  Button,
  Alert,
  Paper,
  ListItem,
  ListItemText,
  ListItemIcon,
  List
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Lightbulb as LightbulbIcon,
  Tag as TagIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { LogEntry, LogEntryUpdate } from '../../services/logService';
import { useLogStore } from '../../store/logStore';

interface LogEntryCardProps {
  entry: LogEntry;
  userId: string;
  onDelete?: (entryId: string) => void;
  onEdit?: (entryId: string) => void;
  onAddToCanvas?: (entryId: string) => void;
}

export const LogEntryCard: React.FC<LogEntryCardProps> = ({
  entry,
  userId,
  onDelete,
  onEdit,
  onAddToCanvas
}) => {
  // State
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(entry.content);
  const [showAiInsights, setShowAiInsights] = useState(false);
  
  // Get actions from store
  const { updateEntry, deleteEntry, isLoading } = useLogStore();
  
  // Format date
  const formattedDate = formatDistanceToNow(new Date(entry.created_at), { addSuffix: true });
  
  // Has AI analysis?
  const hasAiAnalysis = entry.ai_generated_tags?.length > 0 || 
                         entry.ai_summary || 
                         entry.ai_insights?.length > 0;
  
  // Handle menu open
  const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };
  
  // Handle menu close
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  // Handle edit
  const handleEdit = () => {
    setIsEditing(true);
    handleMenuClose();
  };
  
  // Handle save edit
  const handleSaveEdit = async () => {
    if (editedContent.trim() === entry.content.trim()) {
      setIsEditing(false);
      return;
    }
    
    const updateData: LogEntryUpdate = {
      content: editedContent.trim()
    };
    
    await updateEntry(entry.id, updateData);
    setIsEditing(false);
    
    if (onEdit) {
      onEdit(entry.id);
    }
  };
  
  // Handle cancel edit
  const handleCancelEdit = () => {
    setEditedContent(entry.content);
    setIsEditing(false);
  };
  
  // Handle delete
  const handleDelete = async () => {
    await deleteEntry(entry.id);
    handleMenuClose();
    
    if (onDelete) {
      onDelete(entry.id);
    }
  };
  
  // Handle add to canvas
  const handleAddToCanvas = () => {
    if (onAddToCanvas) {
      onAddToCanvas(entry.id);
    }
    handleMenuClose();
  };
  
  // Toggle AI insights
  const toggleAiInsights = () => {
    setShowAiInsights(!showAiInsights);
  };
  
  // Determine entry type label and color
  const getEntryTypeLabel = () => {
    switch (entry.entry_type) {
      case 'idea':
        return { label: 'Idea', color: 'success' };
      case 'observation':
        return { label: 'Observation', color: 'info' };
      case 'concern':
        return { label: 'Concern', color: 'warning' };
      case 'reflection':
        return { label: 'Reflection', color: 'secondary' };
      case 'question':
        return { label: 'Question', color: 'primary' };
      default:
        return { label: 'Note', color: 'default' };
    }
  };
  
  const entryTypeInfo = getEntryTypeLabel();
  
  return (
    <Card variant="outlined">
      <CardHeader
        title={
          entry.ai_summary || 
          (entry.content.length > 60 ? 
            `${entry.content.substring(0, 60)}...` : 
            entry.content)
        }
        subheader={formattedDate}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Chip 
              label={entryTypeInfo.label} 
              color={entryTypeInfo.color as any} 
              size="small" 
              sx={{ mr: 1 }}
            />
            <IconButton 
              aria-label="settings" 
              onClick={handleMenuClick}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        }
      />
      
      <CardContent>
        {isEditing ? (
          <TextField
            fullWidth
            multiline
            rows={4}
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            variant="outlined"
          />
        ) : (
          <Typography variant="body1" paragraph>
            {entry.content}
          </Typography>
        )}
        
        {/* Tags */}
        {(entry.tags.length > 0 || entry.ai_generated_tags?.length > 0) && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {/* User-defined tags */}
            {entry.tags.map((tag) => (
              <Chip
                key={tag.id}
                label={tag.name}
                size="small"
                icon={<TagIcon fontSize="small" />}
                clickable
              />
            ))}
            
            {/* AI-generated tags */}
            {entry.ai_generated_tags?.map((tag, index) => (
              <Chip
                key={`ai-${index}`}
                label={tag}
                size="small"
                variant="outlined"
                color="primary"
                icon={<LightbulbIcon fontSize="small" />}
                clickable
              />
            ))}
          </Box>
        )}
        
        {/* AI Insights Section */}
        {hasAiAnalysis && (
          <>
            <Divider sx={{ my: 2 }} />
            
            <Box 
              sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                cursor: 'pointer'
              }}
              onClick={toggleAiInsights}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <LightbulbIcon color="primary" fontSize="small" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="primary">
                  AI Analysis
                </Typography>
              </Box>
              
              <IconButton size="small">
                {showAiInsights ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            
            <Collapse in={showAiInsights}>
              <Box sx={{ mt: 2, pl: 1 }}>
                {/* AI Summary */}
                {entry.ai_summary && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Summary
                    </Typography>
                    <Typography variant="body2">
                      {entry.ai_summary}
                    </Typography>
                  </Box>
                )}
                
                {/* AI Insights */}
                {entry.ai_insights && entry.ai_insights.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Strategic Insights
                    </Typography>
                    <List dense>
                      {entry.ai_insights.map((insight, index) => (
                        <ListItem key={index} sx={{ pl: 0 }}>
                          <ListItemIcon sx={{ minWidth: 24 }}>
                            <LightbulbIcon fontSize="small" color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={insight} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </Box>
            </Collapse>
          </>
        )}
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between' }}>
        {isEditing ? (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              size="small" 
              startIcon={<CancelIcon />}
              onClick={handleCancelEdit}
            >
              Cancel
            </Button>
            <Button 
              variant="contained"
              size="small" 
              color="primary"
              startIcon={<SaveIcon />}
              onClick={handleSaveEdit}
              disabled={isLoading}
            >
              Save
            </Button>
          </Box>
        ) : (
          <Box>
            <Button size="small" onClick={handleEdit}>
              Edit
            </Button>
            <Button size="small" onClick={handleAddToCanvas}>
              Add to Canvas
            </Button>
          </Box>
        )}
      </CardActions>
      
      {/* Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleAddToCanvas}>
          <ListItemIcon>
            <DescriptionIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Add to Canvas</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default LogEntryCard;