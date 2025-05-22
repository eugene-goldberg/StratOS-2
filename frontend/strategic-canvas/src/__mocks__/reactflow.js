// Mock ReactFlow components and hooks
export const ReactFlow = ({ children, ...props }) => (
  <div data-testid="react-flow" {...props}>
    {children}
  </div>
);

export const ReactFlowProvider = ({ children }) => (
  <div data-testid="react-flow-provider">{children}</div>
);

export const Background = (props) => (
  <div data-testid="react-flow-background" {...props} />
);

export const Controls = (props) => (
  <div data-testid="react-flow-controls" {...props} />
);

export const MiniMap = (props) => (
  <div data-testid="react-flow-minimap" {...props} />
);

export const Panel = ({ children, position, ...props }) => (
  <div data-testid={`react-flow-panel-${position}`} {...props}>
    {children}
  </div>
);

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

export const useNodesState = (initialNodes) => [
  initialNodes,
  jest.fn(),
  jest.fn(),
];

export const useEdgesState = (initialEdges) => [
  initialEdges,
  jest.fn(),
  jest.fn(),
];

// Mock utility functions
export const applyNodeChanges = jest.fn((changes, nodes) => nodes);
export const applyEdgeChanges = jest.fn((changes, edges) => edges);

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