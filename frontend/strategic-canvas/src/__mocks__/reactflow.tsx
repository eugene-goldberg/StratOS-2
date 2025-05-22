import React from 'react';

// Mock ReactFlow components and hooks
const ReactFlow: React.FC<any> = ({ children, ...props }) => {
  // Filter out React-specific props that aren't valid DOM attributes
  const { 
    nodes, edges, nodeTypes, onNodesChange, onEdgesChange, onConnect, 
    onNodeClick, onEdgeClick, onSelectionChange, onMove, fitView, 
    snapToGrid, snapGrid, defaultViewport, selectNodesOnDrag, 
    multiSelectionKeyCode, panActivationKeyCode, zoomActivationKeyCode,
    ...domProps 
  } = props;
  
  return (
    <div data-testid="react-flow" {...domProps}>
      {children}
    </div>
  );
};

export const ReactFlowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div data-testid="react-flow-provider">{children}</div>
);

export const Background: React.FC<any> = (props) => (
  <div data-testid="react-flow-background" {...props} />
);

export const Controls: React.FC<any> = (props) => (
  <div data-testid="react-flow-controls" {...props} />
);

export const MiniMap: React.FC<any> = (props) => {
  const { nodeStrokeColor, nodeColor, maskColor, ...domProps } = props;
  return <div data-testid="react-flow-minimap" {...domProps} />;
};

export const Panel: React.FC<{ children: React.ReactNode; position: string; [key: string]: any }> = ({ children, position, ...props }) => (
  <div data-testid={`react-flow-panel-${position}`} {...props}>
    {children}
  </div>
);

export { ReactFlow };

// Mock hooks
export const useReactFlow = () => ({
  getNodes: jest.fn(() => []),
  getEdges: jest.fn(() => []),
  setNodes: jest.fn(),
  setEdges: jest.fn(),
  addNodes: jest.fn(),
  addEdges: jest.fn(),
  toObject: jest.fn(),
  setViewport: jest.fn(),
  getViewport: jest.fn(() => ({ x: 0, y: 0, zoom: 1 })),
  fitView: jest.fn(),
  project: jest.fn(),
  screenToFlowPosition: jest.fn(),
  flowToScreenPosition: jest.fn(),
  zoomIn: jest.fn(),
  zoomOut: jest.fn(),
});

export const useNodesState = (initialNodes: any) => [
  initialNodes,
  jest.fn(),
  jest.fn(),
];

export const useEdgesState = (initialEdges: any) => [
  initialEdges,
  jest.fn(),
  jest.fn(),
];

// Mock utility functions
export const applyNodeChanges = jest.fn((changes: any, nodes: any) => nodes);
export const applyEdgeChanges = jest.fn((changes: any, edges: any) => edges);

// Mock types and enums
export const Position = {
  Top: 'top',
  Right: 'right',
  Bottom: 'bottom',
  Left: 'left',
};

export const MarkerType = {
  Arrow: 'arrow',
  ArrowClosed: 'arrowclosed',
};

export default ReactFlow;