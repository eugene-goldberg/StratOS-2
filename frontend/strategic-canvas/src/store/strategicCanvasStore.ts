import { create } from 'zustand';
import { 
  CanvasState, 
  CanvasNode, 
  CanvasEdge, 
  NodeType,
  NodeData,
  AIAnalysisResult
} from '../types';
import { 
  Node, 
  Edge, 
  NodeChange, 
  EdgeChange, 
  applyNodeChanges, 
  applyEdgeChanges, 
  Connection,
  XYPosition
} from 'reactflow';
import { saveCanvas, loadCanvas, analyzeThemes } from '../services/strategicCanvasService';

interface StrategicCanvasStore extends CanvasState {
  // Node operations
  addNode: (type: NodeType, position: XYPosition, data: NodeData) => void;
  updateNode: (nodeId: string, data: Partial<NodeData>) => void;
  updateNodeStyle: (nodeId: string, style: React.CSSProperties) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  
  // Edge operations
  addEdge: (connection: Connection, label?: string) => void;
  updateEdge: (edgeId: string, data: Partial<CanvasEdge>) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  
  // Selection operations
  setSelectedElements: (nodes: CanvasNode[], edges: CanvasEdge[]) => void;
  clearSelection: () => void;
  
  // Canvas operations
  updateViewport: (x: number, y: number, zoom: number) => void;
  resetCanvas: () => void;
  
  // Persistence operations
  saveCanvasState: () => Promise<string | undefined>;
  loadCanvasState: (canvasId: string) => Promise<boolean>;
  setCanvasId: (id: string) => void;
  
  // AI operations
  analyzeSelectedNodes: () => Promise<AIAnalysisResult | undefined>;
  addAISuggestedEdges: (suggestedConnections: AIAnalysisResult['suggestedConnections']) => void;
}

const initialState: CanvasState = {
  nodes: [],
  edges: [],
  selectedElements: { nodes: [], edges: [] },
  viewportTransform: { x: 0, y: 0, zoom: 1 },
};

export const useStrategicCanvasStore = create<StrategicCanvasStore>((set, get) => ({
  ...initialState,
  
  // Node operations
  addNode: (type, position, data) => {
    const newNode: CanvasNode = {
      id: `node-${Date.now()}`,
      type,
      position,
      data,
      draggable: true,
      selectable: true,
    };
    
    set((state) => ({
      nodes: [...state.nodes, newNode],
    }));
  },
  
  updateNode: (nodeId, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) => 
        node.id === nodeId 
          ? { ...node, data: { ...node.data, ...data } } 
          : node
      ),
    }));
  },
  
  updateNodeStyle: (nodeId, style) => {
    set((state) => ({
      nodes: state.nodes.map((node) => 
        node.id === nodeId 
          ? { ...node, style: { ...node.style, ...style } } 
          : node
      ),
    }));
  },
  
  onNodesChange: (changes) => {
    set((state) => ({
      nodes: applyNodeChanges(changes, state.nodes) as CanvasNode[],
    }));
  },
  
  // Edge operations
  addEdge: (connection, label) => {
    const newEdge: CanvasEdge = {
      id: `edge-${Date.now()}`,
      source: connection.source || '',
      target: connection.target || '',
      sourceHandle: connection.sourceHandle,
      targetHandle: connection.targetHandle,
      label,
    };
    
    set((state) => ({
      edges: [...state.edges, newEdge],
    }));
  },
  
  updateEdge: (edgeId, data) => {
    set((state) => ({
      edges: state.edges.map((edge) => 
        edge.id === edgeId 
          ? { ...edge, ...data } 
          : edge
      ),
    }));
  },
  
  onEdgesChange: (changes) => {
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges) as CanvasEdge[],
    }));
  },
  
  // Selection operations
  setSelectedElements: (nodes, edges) => {
    set({
      selectedElements: { nodes, edges },
    });
  },
  
  clearSelection: () => {
    set({
      selectedElements: { nodes: [], edges: [] },
    });
  },
  
  // Canvas operations
  updateViewport: (x, y, zoom) => {
    set({
      viewportTransform: { x, y, zoom },
    });
  },
  
  resetCanvas: () => {
    set(initialState);
  },
  
  // Persistence operations
  saveCanvasState: async () => {
    const { nodes, edges, canvasId } = get();
    try {
      const response = await saveCanvas(canvasId, nodes, edges);
      if (response.success) {
        set({ canvasId: response.canvasId });
        return response.canvasId;
      }
      return undefined;
    } catch (error) {
      console.error('Failed to save canvas:', error);
      return undefined;
    }
  },
  
  loadCanvasState: async (canvasId) => {
    try {
      const response = await loadCanvas(canvasId);
      if (response.success) {
        set({
          nodes: response.nodes,
          edges: response.edges,
          canvasId: response.canvasId,
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to load canvas:', error);
      return false;
    }
  },
  
  setCanvasId: (id) => {
    set({ canvasId: id });
  },
  
  // AI operations
  analyzeSelectedNodes: async () => {
    const { selectedElements } = get();
    const selectedTextNodes = selectedElements.nodes.filter(
      node => node.data.content && typeof node.data.content === 'string'
    );
    
    if (selectedTextNodes.length === 0) {
      return undefined;
    }
    
    const nodeContents = selectedTextNodes.map(node => ({
      id: node.id,
      content: node.data.content,
      title: node.data.title
    }));
    
    try {
      return await analyzeThemes(nodeContents);
    } catch (error) {
      console.error('Failed to analyze themes:', error);
      return undefined;
    }
  },
  
  addAISuggestedEdges: (suggestedConnections) => {
    if (!suggestedConnections || suggestedConnections.length === 0) {
      return;
    }
    
    const newEdges = suggestedConnections.map(connection => ({
      id: `ai-edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      source: connection.sourceNodeId,
      target: connection.targetNodeId,
      label: connection.label,
      isAISuggested: true,
      style: { strokeDasharray: '5,5', stroke: '#0060FF', opacity: 0.6 },
    }));
    
    set((state) => ({
      edges: [...state.edges, ...newEdges],
    }));
  },
}));
