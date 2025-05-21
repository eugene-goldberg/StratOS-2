import React, { memo, useState, useRef, useEffect } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { 
  Paper, 
  Typography, 
  Box, 
  TextField, 
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import { 
  Edit, 
  Check, 
  Description, 
  DataUsage, 
  TrendingUp, 
  TrendingDown,
  Lightbulb, 
  Warning,
  Image as ImageIcon
} from '@mui/icons-material';
import { NodeType, NodeData } from '../../types'; // Corrected path and imports

// Basic Node Component
const BasicNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(data.title || '');
  const [content, setContent] = useState(data.content || '');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = () => {
    // In a real implementation, this would update the node in the store
    setIsEditing(false);
  };

  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 200,
        maxWidth: 300,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.primary.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          p: 1,
        }}
      >
        {isEditing ? (
          <TextField
            ref={inputRef}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            variant="standard"
            size="small"
            fullWidth
            sx={{ 
              input: { 
                color: theme.palette.primary.contrastText,
                fontSize: '0.875rem',
                fontWeight: 'bold',
              }
            }}
          />
        ) : (
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {title || 'Untitled'}
          </Typography>
        )}
        
        <IconButton 
          size="small" 
          color="inherit"
          onClick={() => isEditing ? handleSave() : setIsEditing(true)}
        >
          {isEditing ? <Check fontSize="small" /> : <Edit fontSize="small" />}
        </IconButton>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        {isEditing ? (
          <TextField
            value={content}
            onChange={(e) => setContent(e.target.value)}
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            size="small"
          />
        ) : (
          <Typography variant="body2">
            {content || 'Add content here...'}
          </Typography>
        )}
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// CEO Log Node Component
const CEOLogNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  const ceoLogData = data as any; // In a real implementation, this would be properly typed
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 200,
        maxWidth: 300,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.info.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.info.main,
          color: theme.palette.info.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Description fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'CEO Log Entry'}
          </Typography>
        </Box>
        
        <Typography variant="caption">
          {ceoLogData.date || 'No date'}
        </Typography>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'No content available'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// Data Snippet Node Component
const DataSnippetNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  const dataSnippetData = data as any; // In a real implementation, this would be properly typed
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 200,
        maxWidth: 300,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.secondary.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.secondary.main,
          color: theme.palette.secondary.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <DataUsage fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Data Snippet'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'No data available'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// SWOT Strength Node Component
const SWOTStrengthNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 180,
        maxWidth: 250,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.success.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.success.main,
          color: theme.palette.success.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <TrendingUp fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Strength'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'Add strength here...'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// SWOT Weakness Node Component
const SWOTWeaknessNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 180,
        maxWidth: 250,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.error.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.error.main,
          color: theme.palette.error.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <TrendingDown fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Weakness'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'Add weakness here...'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// SWOT Opportunity Node Component
const SWOTOpportunityNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 180,
        maxWidth: 250,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.info.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.info.main,
          color: theme.palette.info.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Lightbulb fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Opportunity'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'Add opportunity here...'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// SWOT Threat Node Component
const SWOTThreatNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 180,
        maxWidth: 250,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.warning.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.warning.main,
          color: theme.palette.warning.contrastText,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Warning fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Threat'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        <Typography variant="body2">
          {data.content || 'Add threat here...'}
        </Typography>
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// Image Node Component
const ImageNode = memo(({ id, data, selected }: NodeProps<NodeData>) => {
  const theme = useTheme();
  const imageData = data as any; // In a real implementation, this would be properly typed
  
  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        minWidth: 200,
        maxWidth: 300,
        borderRadius: 2,
        border: selected ? `2px solid ${theme.palette.primary.main}` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Node Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          bgcolor: theme.palette.grey[800],
          color: theme.palette.common.white,
          p: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <ImageIcon fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold" noWrap>
            {data.title || 'Image'}
          </Typography>
        </Box>
      </Box>
      
      {/* Node Content */}
      <Box sx={{ p: 1 }}>
        {imageData.imageUrl ? (
          <Box 
            component="img"
            src={imageData.imageUrl}
            alt={imageData.altText || 'Image'}
            sx={{ 
              width: '100%', 
              height: 'auto',
              maxHeight: 200,
              objectFit: 'contain'
            }}
          />
        ) : (
          <Box 
            sx={{ 
              width: '100%', 
              height: 150,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: theme.palette.grey[200],
              color: theme.palette.text.secondary
            }}
          >
            <Typography variant="body2">No image available</Typography>
          </Box>
        )}
      </Box>
      
      {/* Handles for connections */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </Paper>
  );
});

// Export all node types
export const nodeTypes = {
  [NodeType.BASIC]: BasicNode,
  [NodeType.CEO_LOG]: CEOLogNode,
  [NodeType.DATA_SNIPPET]: DataSnippetNode,
  [NodeType.SWOT_S]: SWOTStrengthNode,
  [NodeType.SWOT_W]: SWOTWeaknessNode,
  [NodeType.SWOT_O]: SWOTOpportunityNode,
  [NodeType.SWOT_T]: SWOTThreatNode,
  [NodeType.IMAGE]: ImageNode,
};

export default nodeTypes;
