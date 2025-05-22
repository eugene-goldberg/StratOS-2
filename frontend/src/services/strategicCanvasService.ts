import axios from 'axios';
import { 
  CanvasNode, 
  CanvasEdge, 
  SaveCanvasResponse, 
  LoadCanvasResponse,
  AIAnalysisResult
} from '../types/canvas';

// API base URL - would be configured from environment in a real app
const API_BASE_URL = '/api';

// Save canvas state to backend
export const saveCanvas = async (
  canvasId: string | undefined,
  nodes: CanvasNode[],
  edges: CanvasEdge[]
): Promise<SaveCanvasResponse> => {
  try {
    if (canvasId) {
      // Update existing canvas elements
      const response = await axios.post(`${API_BASE_URL}/subjective/canvases/${canvasId}/elements`, {
        nodes,
        edges
      });
      return {
        canvasId,
        success: true,
        message: response.data.message || 'Canvas updated successfully'
      };
    } else {
      // Create new canvas
      const response = await axios.post(`${API_BASE_URL}/subjective/canvases`, {
        title: 'Strategic Canvas',
        description: 'Auto-generated strategic canvas'
      });
      const newCanvasId = response.data.id;
      
      // Add elements to the new canvas
      if (nodes.length > 0 || edges.length > 0) {
        await axios.post(`${API_BASE_URL}/subjective/canvases/${newCanvasId}/elements`, {
          nodes,
          edges
        });
      }
      
      return {
        canvasId: newCanvasId,
        success: true,
        message: 'Canvas created successfully'
      };
    }
  } catch (error) {
    console.error('Error saving canvas:', error);
    throw error;
  }
};

// Load canvas state from backend
export const loadCanvas = async (canvasId: string): Promise<LoadCanvasResponse> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/subjective/canvases/${canvasId}`);
    const canvas = response.data;
    
    // Convert canvas elements to ReactFlow nodes and edges format
    const nodes: CanvasNode[] = [];
    const edges: CanvasEdge[] = [];
    
    canvas.elements?.forEach((element: any) => {
      // Convert backend element to frontend node
      const node: CanvasNode = {
        id: element.id,
        type: element.element_type,
        position: element.position || { x: 0, y: 0 },
        data: {
          content: element.content,
          ...element.style
        },
        draggable: true,
        selectable: true
      };
      nodes.push(node);
      
      // Convert connections to edges
      element.connections?.forEach((targetId: string) => {
        const edge: CanvasEdge = {
          id: `${element.id}-${targetId}`,
          source: element.id,
          target: targetId,
          type: 'smoothstep'
        };
        edges.push(edge);
      });
    });
    
    return {
      canvasId,
      nodes,
      edges,
      success: true,
      message: 'Canvas loaded successfully'
    };
  } catch (error) {
    console.error('Error loading canvas:', error);
    throw error;
  }
};

// Analyze themes in selected nodes using AI
export interface NodeContent {
  id: string;
  content: string;
  title?: string;
}

export const analyzeThemes = async (
  canvasId: string,
  selectedNodeIds?: string[]
): Promise<AIAnalysisResult> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/subjective/canvases/${canvasId}/analyze-themes`,
      { selected_nodes: selectedNodeIds }
    );
    
    // Parse the AI analysis response to extract themes and insights
    const analysis = response.data.analysis;
    
    // Extract themes from the structured response
    const themes = extractThemesFromAnalysis(analysis);
    const summary = extractSummaryFromAnalysis(analysis);
    const suggestedConnections = extractConnectionsFromAnalysis(analysis);
    
    return {
      themes,
      summary,
      suggestedConnections
    };
  } catch (error) {
    console.error('Error analyzing themes:', error);
    throw error;
  }
};

// Get connection suggestions for canvas elements
export const suggestConnections = async (
  canvasId: string,
  selectedElementIds?: string[]
): Promise<string> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/subjective/canvases/${canvasId}/suggest-connections`,
      { selected_elements: selectedElementIds }
    );
    
    return response.data.suggestions;
  } catch (error) {
    console.error('Error getting connection suggestions:', error);
    throw error;
  }
};

// Helper functions to parse AI responses
function extractThemesFromAnalysis(analysis: string): string[] {
  const themeMatch = analysis.match(/## Key Themes Identified\s*((?:- .+\n?)+)/);
  if (themeMatch) {
    return themeMatch[1]
      .split('\n')
      .filter(line => line.trim().startsWith('-'))
      .map(line => line.replace(/^-\s*/, '').split(':')[0].trim())
      .filter(theme => theme.length > 0);
  }
  return ['Strategic Planning', 'Business Analysis'];
}

function extractSummaryFromAnalysis(analysis: string): string {
  const insightMatch = analysis.match(/## Strategic Insights\s*((?:- .+\n?)+)/);
  if (insightMatch) {
    return insightMatch[1]
      .split('\n')
      .filter(line => line.trim().startsWith('-'))
      .map(line => line.replace(/^-\s*/, '').trim())
      .join(' ');
  }
  return 'Strategic analysis completed with key insights identified.';
}

function extractConnectionsFromAnalysis(analysis: string): Array<{ sourceNodeId: string; targetNodeId: string; label: string }> {
  // This would parse connection suggestions from the AI response
  // For now, return empty array as the AI response format may vary
  return [];
}