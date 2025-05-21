import React, { useCallback, useRef, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  ReactFlowProvider,
  NodeTypes,
  EdgeTypes,
  OnConnect,
  Connection,
  useReactFlow,
  NodeDragHandler,
  NodeMouseHandler,
  EdgeMouseHandler,
  SelectionDragHandler,
  PanelPosition,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useStrategicCanvasStore } from '../store/strategicCanvasStore';
import { CanvasNode, CanvasEdge, NodeType } from '../types';
import { nodeTypes } from './nodes';
import CanvasToolbar from './CanvasToolbar';
import AIAssistPanel from './AIAssistPanel';

import { Box, Paper, useTheme } from '@mui/material';

const StrategicCanvas: React.FC = () => {
  const theme = useTheme();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState<any>(null);
  
  // Access store state and actions
  const {
    nodes,
    edges,
    selectedElements,
    onNodesChange,
    onEdgesChange,
    addEdge,
    setSelectedElements,
    clearSelection,
    updateViewport,
    analyzeSelectedNodes,
    addAISuggestedEdges,
  } = useStrategicCanvasStore();

  // Handle connections between nodes
  const onConnect: OnConnect = useCallback(
    (connection) => {
      addEdge(connection);
    },
    [addEdge]
  );

  // Handle node selection
  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      const selectedNode = node as CanvasNode;
      setSelectedElements([selectedNode], []);
    },
    [setSelectedElements]
  );

  // Handle edge selection
  const onEdgeClick: EdgeMouseHandler = useCallback(
    (_, edge) => {
      const selectedEdge = edge as CanvasEdge;
      setSelectedElements([], [selectedEdge]);
    },
    [setSelectedElements]
  );

  // Handle selection change
  const onSelectionChange = useCallback(
    ({ nodes, edges }: { nodes: any[], edges: any[] }) => {
      setSelectedElements(
        nodes as CanvasNode[],
        edges as CanvasEdge[]
      );
    },
    [setSelectedElements]
  );

  // Handle viewport change
  const onMove = useCallback(
    (_: any, viewport: any) => {
      updateViewport(viewport.x, viewport.y, viewport.zoom);
    },
    [updateViewport]
  );

  // Handle AI analysis
  const handleAIAnalysis = useCallback(async () => {
    const result = await analyzeSelectedNodes();
    if (result) {
      setAiAnalysisResult(result);
      setShowAIPanel(true);
      
      // Add suggested connections if available
      if (result.suggestedConnections && result.suggestedConnections.length > 0) {
        addAISuggestedEdges(result.suggestedConnections);
      }
    }
  }, [analyzeSelectedNodes, addAISuggestedEdges]);

  // Handle closing AI panel
  const handleCloseAIPanel = () => {
    setShowAIPanel(false);
    setAiAnalysisResult(null);
  };

  return (
    <Box
      sx={{
        width: '100%',
        height: '100vh',
        bgcolor: theme.palette.background.default,
      }}
    >
      <ReactFlowProvider>
        <Box ref={reactFlowWrapper} sx={{ width: '100%', height: '100%' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onSelectionChange={onSelectionChange}
            onMove={onMove}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            defaultViewport={{ x: 0, y: 0, zoom: 1 }}
            selectNodesOnDrag
            multiSelectionKeyCode="Shift"
            panActivationKeyCode="Space"
            zoomActivationKeyCode="Meta"
          >
            <Background color="#aaa" gap={16} />
            <Controls />
            <MiniMap
              nodeStrokeColor={(n) => {
                if (n.type === NodeType.BASIC) return '#0060FF';
                if (n.type === NodeType.CEO_LOG) return '#00E8C9';
                return '#1A2232';
              }}
              nodeColor={(n) => {
                if (n.type === NodeType.BASIC) return '#F5F8FF';
                if (n.type === NodeType.CEO_LOG) return '#E6FFF9';
                return '#F5F8FF';
              }}
              maskColor="#F5F8FF50"
            />
            
            {/* Toolbar Panel */}
            <Panel position="top-left">
              <CanvasToolbar 
                onAIAnalysisClick={handleAIAnalysis}
                hasSelection={selectedElements.nodes.length > 0}
              />
            </Panel>
            
            {/* AI Assist Panel */}
            {showAIPanel && aiAnalysisResult && (
              <Panel position="top-right">
                <AIAssistPanel 
                  result={aiAnalysisResult}
                  onClose={handleCloseAIPanel}
                />
              </Panel>
            )}
          </ReactFlow>
        </Box>
      </ReactFlowProvider>
    </Box>
  );
};

export default StrategicCanvas;
