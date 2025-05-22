import { rest } from 'msw';
import { 
  SaveCanvasResponse, 
  LoadCanvasResponse, 
  AIAnalysisResult,
  CanvasNode,
  CanvasEdge,
  NodeType 
} from '../types';

const API_BASE_URL = '/api';

// Mock canvas data
const mockNodes: CanvasNode[] = [
  {
    id: 'node-1',
    type: NodeType.BASIC,
    position: { x: 100, y: 100 },
    data: { content: 'Test node 1', title: 'Node 1' },
    draggable: true,
    selectable: true,
  },
  {
    id: 'node-2',
    type: NodeType.CEO_LOG,
    position: { x: 300, y: 200 },
    data: { 
      content: 'CEO log entry', 
      title: 'CEO Log',
      logId: 'log-1',
      date: '2024-01-01'
    },
    draggable: true,
    selectable: true,
  },
];

const mockEdges: CanvasEdge[] = [
  {
    id: 'edge-1',
    source: 'node-1',
    target: 'node-2',
    label: 'connects to',
  },
];

export const handlers = [
  // Save canvas
  rest.post(`${API_BASE_URL}/subjective/canvases`, (req, res, ctx) => {
    const response: SaveCanvasResponse = {
      canvasId: `canvas-${Date.now()}`,
      success: true,
      message: 'Canvas saved successfully',
    };
    return res(ctx.json(response));
  }),

  // Update existing canvas
  rest.post(`${API_BASE_URL}/subjective/canvases/:canvasId/elements`, (req, res, ctx) => {
    const { canvasId } = req.params;
    const response: SaveCanvasResponse = {
      canvasId: canvasId as string,
      success: true,
      message: 'Canvas updated successfully',
    };
    return res(ctx.json(response));
  }),

  // Load canvas
  rest.get(`${API_BASE_URL}/subjective/canvases/:canvasId/elements`, (req, res, ctx) => {
    const { canvasId } = req.params;
    const response: LoadCanvasResponse = {
      canvasId: canvasId as string,
      nodes: mockNodes,
      edges: mockEdges,
      success: true,
      message: 'Canvas loaded successfully',
    };
    return res(ctx.json(response));
  }),

  // AI theme analysis
  rest.post(`${API_BASE_URL}/ai/canvas/analyze-themes`, (req, res, ctx) => {
    const response: AIAnalysisResult = {
      themes: ['Strategy', 'Innovation', 'Leadership'],
      summary: 'The selected content focuses on strategic leadership and innovation initiatives.',
      suggestedConnections: [
        {
          sourceNodeId: 'node-1',
          targetNodeId: 'node-2',
          label: 'Strategic alignment',
        },
      ],
    };
    return res(ctx.json(response));
  }),

  // Error cases
  rest.post(`${API_BASE_URL}/subjective/canvases/error-test`, (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ message: 'Internal server error' }));
  }),

  rest.get(`${API_BASE_URL}/subjective/canvases/not-found/elements`, (req, res, ctx) => {
    return res(ctx.status(404), ctx.json({ message: 'Canvas not found' }));
  }),
];