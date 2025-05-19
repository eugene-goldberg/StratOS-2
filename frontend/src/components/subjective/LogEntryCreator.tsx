import React, { useState, useRef, useEffect } from 'react';
import {
  Paper,
  TextField,
  Box,
  Button,
  Chip,
  Typography,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete
} from '@mui/material';
import {
  Send as SendIcon,
  Add as AddIcon,
  LightbulbOutlined as LightbulbIcon,
  CheckCircleOutline as CheckCircleIcon,
  Cancel as CancelIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { useLogStore } from '../../store/logStore';
import { LogEntryCreate, LogEntryType } from '../../services/logService';
import VoiceInputButton from './VoiceInputButton';

interface LogEntryCreatorProps {
  userId: string;
  initialFocus?: boolean;
  onEntryCreated?: (entryId: string) => void;
  showTypeTabs?: boolean;
  variant?: 'expanded' | 'compact';
  showVoiceButton?: boolean;
  strategicElements?: {
    purposeVision?: boolean;
    values?: { id: string; name: string }[];
    goals?: { id: string; title: string }[];
  };
}

export const LogEntryCreator: React.FC<LogEntryCreatorProps> = ({
  userId,
  initialFocus = false,
  onEntryCreated,
  showTypeTabs = true,
  variant = 'expanded',
  showVoiceButton = true,
  strategicElements
}) => {
  // State
  const [content, setContent] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [entryType, setEntryType] = useState<LogEntryType>(LogEntryType.OTHER);
  const [tagInput, setTagInput] = useState('');
  const [linkMenuAnchorEl, setLinkMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [customTagDialogOpen, setCustomTagDialogOpen] = useState(false);
  const [selectedValues, setSelectedValues] = useState<string[]>([]);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  
  // Ref for text field
  const textFieldRef = useRef<HTMLDivElement>(null);
  
  // Get functions from store
  const { isLoading, error, createEntry } = useLogStore();
  
  // Focus text field on mount if initialFocus is true
  useEffect(() => {
    if (initialFocus && textFieldRef.current) {
      const input = textFieldRef.current.querySelector('textarea');
      if (input) {
        input.focus();
      }
    }
  }, [initialFocus]);
  
  // Handle content change
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
  };
  
  // Handle entry type change
  const handleEntryTypeChange = (e: SelectChangeEvent) => {
    setEntryType(e.target.value as LogEntryType);
  };
  
  // Handle submit
  const handleSubmit = async () => {
    if (!content.trim()) return;
    
    // Combine all tags
    const allTags = [
      ...selectedTags,
      ...selectedValues,
      ...selectedGoals.map(g => `Goal: ${g}`)
    ];
    
    // Create entry data
    const entryData: LogEntryCreate = {
      content: content.trim(),
      entry_type: entryType,
      tags: allTags
    };
    
    try {
      const entry = await createEntry(userId, entryData);
      
      // Clear form
      setContent('');
      setSelectedTags([]);
      setSelectedValues([]);
      setSelectedGoals([]);
      
      // Notify parent
      if (onEntryCreated) {
        onEntryCreated(entry.id);
      }
    } catch (error) {
      console.error('Error creating log entry:', error);
    }
  };
  
  // Handle key press (Ctrl+Enter to submit)
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit();
    }
  };
  
  // Handle tag input change
  const handleTagInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTagInput(e.target.value);
  };
  
  // Add custom tag
  const handleAddCustomTag = () => {
    if (tagInput.trim() && !selectedTags.includes(tagInput.trim())) {
      setSelectedTags([...selectedTags, tagInput.trim()]);
      setTagInput('');
    }
    setCustomTagDialogOpen(false);
  };
  
  // Remove tag
  const handleRemoveTag = (tag: string) => {
    setSelectedTags(selectedTags.filter(t => t !== tag));
  };
  
  // Remove value tag
  const handleRemoveValue = (value: string) => {
    setSelectedValues(selectedValues.filter(v => v !== value));
  };
  
  // Remove goal tag
  const handleRemoveGoal = (goal: string) => {
    setSelectedGoals(selectedGoals.filter(g => g !== goal));
  };
  
  // Handle link menu click
  const handleLinkMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setLinkMenuAnchorEl(event.currentTarget);
  };
  
  // Handle link menu close
  const handleLinkMenuClose = () => {
    setLinkMenuAnchorEl(null);
  };
  
  // Link to strategic elements
  const handleLinkToValues = () => {
    setLinkMenuAnchorEl(null);
    // This would open a dialog or dropdown to select values
  };
  
  const handleLinkToGoals = () => {
    setLinkMenuAnchorEl(null);
    // This would open a dialog or dropdown to select goals
  };
  
  const linkMenuOpen = Boolean(linkMenuAnchorEl);
  
  // Compact variant
  if (variant === 'compact') {
    return (
      <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            placeholder="Capture a thought, observation, or question..."
            size="small"
            fullWidth
            value={content}
            onChange={handleContentChange}
            onKeyDown={handleKeyPress}
            ref={textFieldRef}
            InputProps={{
              endAdornment: (
                <IconButton 
                  color="primary" 
                  onClick={handleSubmit}
                  disabled={!content.trim() || isLoading}
                  size="small"
                >
                  {isLoading ? <CircularProgress size={20} /> : <SendIcon />}
                </IconButton>
              )
            }}
          />
          
          {showVoiceButton && (
            <VoiceInputButton 
              userId={userId} 
              size="small" 
              onEntryCreated={onEntryCreated}
            />
          )}
        </Box>
      </Paper>
    );
  }
  
  // Expanded variant (default)
  return (
    <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="medium">
          New Log Entry
        </Typography>
      </Box>
      
      {showTypeTabs && (
        <Box sx={{ mb: 2 }}>
          <FormControl size="small" fullWidth>
            <InputLabel>Entry Type</InputLabel>
            <Select
              value={entryType}
              onChange={handleEntryTypeChange}
              label="Entry Type"
            >
              <MenuItem value={LogEntryType.IDEA}>Idea</MenuItem>
              <MenuItem value={LogEntryType.OBSERVATION}>Observation</MenuItem>
              <MenuItem value={LogEntryType.CONCERN}>Concern</MenuItem>
              <MenuItem value={LogEntryType.REFLECTION}>Reflection</MenuItem>
              <MenuItem value={LogEntryType.QUESTION}>Question</MenuItem>
              <MenuItem value={LogEntryType.OTHER}>Other</MenuItem>
            </Select>
          </FormControl>
        </Box>
      )}
      
      <TextField
        placeholder="What's on your mind? Capture ideas, observations, or questions here..."
        multiline
        rows={4}
        fullWidth
        value={content}
        onChange={handleContentChange}
        onKeyDown={handleKeyPress}
        ref={textFieldRef}
        sx={{ mb: 2 }}
      />
      
      {/* Tags Section */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Tags & Links
          </Typography>
          
          <Box>
            <Tooltip title="Add Custom Tag">
              <IconButton size="small" onClick={() => setCustomTagDialogOpen(true)}>
                <AddIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Link to Strategic Elements">
              <IconButton size="small" onClick={handleLinkMenuClick}>
                <ExpandMoreIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {/* Custom tags */}
          {selectedTags.map(tag => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              onDelete={() => handleRemoveTag(tag)}
            />
          ))}
          
          {/* Value tags */}
          {selectedValues.map(value => (
            <Chip
              key={value}
              label={`Value: ${value}`}
              size="small"
              color="primary"
              variant="outlined"
              onDelete={() => handleRemoveValue(value)}
            />
          ))}
          
          {/* Goal tags */}
          {selectedGoals.map(goal => (
            <Chip
              key={goal}
              label={`Goal: ${goal}`}
              size="small"
              color="secondary"
              variant="outlined"
              onDelete={() => handleRemoveGoal(goal)}
            />
          ))}
          
          {selectedTags.length === 0 && selectedValues.length === 0 && selectedGoals.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              No tags added. AI will suggest tags after submission.
            </Typography>
          )}
        </Box>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <LightbulbIcon fontSize="small" color="disabled" sx={{ mr: 1 }} />
          <Typography variant="caption" color="text.secondary">
            AI will analyze and tag your entry
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {showVoiceButton && (
            <VoiceInputButton 
              userId={userId}
              onEntryCreated={onEntryCreated}
            />
          )}
          
          <Button
            variant="contained"
            color="primary"
            endIcon={<SendIcon />}
            onClick={handleSubmit}
            disabled={!content.trim() || isLoading}
          >
            {isLoading ? 'Submitting...' : 'Submit'}
          </Button>
        </Box>
      </Box>
      
      {/* Link Menu */}
      <Menu
        anchorEl={linkMenuAnchorEl}
        open={linkMenuOpen}
        onClose={handleLinkMenuClose}
      >
        <MenuItem onClick={() => {
          handleLinkMenuClose();
          setCustomTagDialogOpen(true);
        }}>
          <ListItemIcon>
            <AddIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Add Custom Tag</ListItemText>
        </MenuItem>
        
        {strategicElements?.values && strategicElements.values.length > 0 && (
          <MenuItem onClick={() => {
            handleLinkMenuClose();
            // Open values selector
          }}>
            <ListItemIcon>
              <LightbulbIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Link to Values</ListItemText>
          </MenuItem>
        )}
        
        {strategicElements?.goals && strategicElements.goals.length > 0 && (
          <MenuItem onClick={() => {
            handleLinkMenuClose();
            // Open goals selector
          }}>
            <ListItemIcon>
              <CheckCircleIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Link to Strategic Goals</ListItemText>
          </MenuItem>
        )}
      </Menu>
      
      {/* Custom Tag Dialog */}
      <Dialog open={customTagDialogOpen} onClose={() => setCustomTagDialogOpen(false)}>
        <DialogTitle>Add Custom Tag</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Tag Name"
            type="text"
            fullWidth
            value={tagInput}
            onChange={handleTagInputChange}
            variant="outlined"
            placeholder="Enter a tag (e.g., 'Customer Feedback', 'Product Idea')"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCustomTagDialogOpen(false)} color="inherit" startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button onClick={handleAddCustomTag} color="primary" variant="contained" startIcon={<CheckCircleIcon />}>
            Add Tag
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Strategic Values Dialog would go here */}
      
      {/* Strategic Goals Dialog would go here */}
    </Paper>
  );
};

export default LogEntryCreator;