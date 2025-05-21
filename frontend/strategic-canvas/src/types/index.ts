// Types for the Strategic Canvas UI component

import { Node, Edge, NodeChange, EdgeChange, Connection } from 'reactflow';

// Node types
export enum NodeType {
  BASIC = 'basic',
  CEO_LOG = 'ceoLog',
  DATA_SNIPPET = 'dataSnippet',
  SWOT_S = 'swotS',
  SWOT_W = 'swotW',
  SWOT_O = 'swotO',
  SWOT_T = 'swotT',
  RISK = 'risk',
  OPPORTUNITY = 'opportunity',
  IMAGE = 'image',
}

// Base node data interface
export interface BaseNodeData {
  title?: string;
  content: string;
}

// CEO Log node data
export interface CEOLogNodeData extends BaseNodeData {
  logId: string;
  date: string;
}

// Data Snippet node data
export interface DataSnippetNodeData extends BaseNodeData {
  dataSourceId: string;
  dataType: 'chart' | 'metric' | 'text';
  dataValue?: any;
}

// SWOT node data
export interface SWOTNodeData extends BaseNodeData {
  category: 'strength' | 'weakness' | 'opportunity' | 'threat';
}

// Risk/Opportunity node data
export interface RiskOpportunityNodeData extends BaseNodeData {
  impact: 'low' | 'medium' | 'high';
  likelihood: 'low' | 'medium' | 'high';
}

// Image node data
export interface ImageNodeData extends BaseNodeData {
  imageUrl: string;
  altText?: string;
}

// Union type for all node data
export type NodeData = 
  | BaseNodeData 
  | CEOLogNodeData 
  | DataSnippetNodeData 
  | SWOTNodeData 
  | RiskOpportunityNodeData
  | ImageNodeData;

// Custom node with additional properties
export interface CanvasNode extends Node<NodeData> {
  type: NodeType;
  style?: React.CSSProperties;
}

// Custom edge with additional properties  
export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  label?: string;
  style?: React.CSSProperties;
  isAISuggested?: boolean;
}

// Canvas state
export interface CanvasState {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  selectedElements: { nodes: CanvasNode[], edges: CanvasEdge[] };
  canvasId?: string;
  viewportTransform: {
    x: number;
    y: number;
    zoom: number;
  };
}

// AI Analysis result
export interface AIAnalysisResult {
  themes: string[];
  summary: string;
  suggestedConnections?: {
    sourceNodeId: string;
    targetNodeId: string;
    label?: string;
  }[];
}

// API service response types
export interface SaveCanvasResponse {
  canvasId: string;
  success: boolean;
  message?: string;
}

export interface LoadCanvasResponse {
  canvasId: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  success: boolean;
  message?: string;
}
