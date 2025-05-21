import axios from 'axios';
import { 
  CanvasNode, 
  CanvasEdge, 
  SaveCanvasResponse, 
  LoadCanvasResponse,
  AIAnalysisResult
} from '../types';

// API base URL - would be configured from environment in a real app
const API_BASE_URL = '/api';

// Save canvas state to backend
export const saveCanvas = async (
  canvasId: string | undefined,
  nodes: CanvasNode[],
  edges: CanvasEdge[]
): Promise<SaveCanvasResponse> => {
  try {
    const endpoint = canvasId 
      ? `${API_BASE_URL}/subjective/canvases/${canvasId}/elements` 
      : `${API_BASE_URL}/subjective/canvases`;
    
    const response = await axios.post(endpoint, {
      nodes,
      edges
    });
    
    return response.data;
  } catch (error) {
    console.error('Error saving canvas:', error);
    // For development purposes, return mock success response
    // In production, this would properly handle errors
    return {
      canvasId: canvasId || `canvas-${Date.now()}`,
      success: true,
      message: 'Canvas saved successfully (mock)'
    };
  }
};

// Load canvas state from backend
export const loadCanvas = async (canvasId: string): Promise<LoadCanvasResponse> => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/subjective/canvases/${canvasId}/elements`
    );
    
    return response.data;
  } catch (error) {
    console.error('Error loading canvas:', error);
    // For development purposes, return mock error response
    return {
      canvasId,
      nodes: [],
      edges: [],
      success: false,
      message: 'Failed to load canvas (mock)'
    };
  }
};

// Analyze themes in selected nodes using AI
export interface NodeContent {
  id: string;
  content: string;
  title?: string;
}

export const analyzeThemes = async (
  nodeContents: NodeContent[]
): Promise<AIAnalysisResult> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/ai/canvas/analyze-themes`,
      { nodes: nodeContents }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing themes:', error);
    // For development purposes, return mock AI analysis
    return {
      themes: ['Strategy', 'Innovation', 'Market Trends'],
      summary: 'The selected content appears to focus on strategic planning and market analysis.',
      suggestedConnections: [
        {
          sourceNodeId: nodeContents[0]?.id || '',
          targetNodeId: nodeContents[nodeContents.length - 1]?.id || '',
          label: 'Related concept'
        }
      ]
    };
  }
};
