import React, { useCallback, useState } from 'react';
import { Box, Paper, Typography, IconButton, Divider, Tooltip } from '@mui/material';
import {
  AddCircleOutline,
  TextFields,
  Timeline,
  Delete,
  ZoomIn,
  ZoomOut,
  FitScreen,
  Undo,
  Redo,
  Psychology,
  Save,
  ColorLens,
  Image as ImageIcon,
  DataUsage,
  Assessment,
  BugReport,
  Lightbulb,
} from '@mui/icons-material';
import { useStrategicCanvasStore } from '../store/strategicCanvasStore';
import { NodeType, BaseNodeData } from '../types';
import { useReactFlow } from 'reactflow';

interface CanvasToolbarProps {
  onAIAnalysisClick: () => void;
  hasSelection: boolean;
}

const CanvasToolbar: React.FC<CanvasToolbarProps> = ({
  onAIAnalysisClick,
  hasSelection,
}) => {
  const { addNode, selectedElements } = useStrategicCanvasStore();
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const [colorPickerOpen, setColorPickerOpen] = useState(false);

  // Add a new node to the canvas
  const handleAddNode = useCallback(
    (type: NodeType) => {
      // Calculate position in the center of the current viewport
      const reactFlowBounds = document.querySelector('.react-flow')?.getBoundingClientRect();
      const position = {
        x: (reactFlowBounds?.width || 800) / 2,
        y: (reactFlowBounds?.height || 600) / 2,
      };

      // Create default data based on node type
      let data: BaseNodeData = {
        content: '',
      };

      // Add the node
      addNode(type, position, data);
    },
    [addNode]
  );

  return (
    <Paper
      elevation={3}
      sx={{
        p: 1,
        borderRadius: 2,
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        maxWidth: '48px',
        '& .MuiIconButton-root': {
          p: 1,
        },
      }}
    >
      {/* Selection Tool - Always active */}
      <Tooltip title="Select Tool (Active)" placement="right">
        <Box
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            borderRadius: '50%',
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            alignSelf: 'center',
          }}
        >
          <IconButton size="small" color="inherit" disableRipple>
            <FitScreen fontSize="small" />
          </IconButton>
        </Box>
      </Tooltip>

      <Divider />

      {/* Node Creation Tools */}
      <Tooltip title="Add Basic Text Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.BASIC)} color="primary">
          <TextFields />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add CEO Log Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.CEO_LOG)} color="primary">
          <Assessment />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add Data Snippet Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.DATA_SNIPPET)} color="primary">
          <DataUsage />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add SWOT Strength Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.SWOT_S)} color="success">
          <AddCircleOutline />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add SWOT Weakness Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.SWOT_W)} color="error">
          <BugReport />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add SWOT Opportunity Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.SWOT_O)} color="info">
          <Lightbulb />
        </IconButton>
      </Tooltip>

      <Tooltip title="Add Image Node" placement="right">
        <IconButton onClick={() => handleAddNode(NodeType.IMAGE)} color="primary">
          <ImageIcon />
        </IconButton>
      </Tooltip>

      <Divider />

      {/* Edge Tool */}
      <Tooltip title="Connect Nodes" placement="right">
        <IconButton color="primary">
          <Timeline />
        </IconButton>
      </Tooltip>

      <Divider />

      {/* Canvas Operations */}
      <Tooltip title="Zoom In" placement="right">
        <IconButton onClick={() => zoomIn()} color="primary">
          <ZoomIn />
        </IconButton>
      </Tooltip>

      <Tooltip title="Zoom Out" placement="right">
        <IconButton onClick={() => zoomOut()} color="primary">
          <ZoomOut />
        </IconButton>
      </Tooltip>

      <Tooltip title="Fit View" placement="right">
        <IconButton onClick={() => fitView()} color="primary">
          <FitScreen />
        </IconButton>
      </Tooltip>

      <Divider />

      {/* Edit Operations */}
      <Tooltip title="Undo" placement="right">
        <IconButton color="primary">
          <Undo />
        </IconButton>
      </Tooltip>

      <Tooltip title="Redo" placement="right">
        <IconButton color="primary">
          <Redo />
        </IconButton>
      </Tooltip>

      <Tooltip title="Delete Selected" placement="right">
        <IconButton color="error" disabled={!hasSelection}>
          <Delete />
        </IconButton>
      </Tooltip>

      <Divider />

      {/* AI Operations */}
      <Tooltip title="AI Assist" placement="right">
        <IconButton
          onClick={onAIAnalysisClick}
          color="primary"
          disabled={!hasSelection}
        >
          <Psychology />
        </IconButton>
      </Tooltip>

      <Divider />

      {/* Save Operation */}
      <Tooltip title="Save Canvas" placement="right">
        <IconButton color="primary">
          <Save />
        </IconButton>
      </Tooltip>
    </Paper>
  );
};

export default CanvasToolbar;
