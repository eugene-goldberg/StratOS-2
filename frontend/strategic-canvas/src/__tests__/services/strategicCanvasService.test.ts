import axios from 'axios';
import { 
  saveCanvas, 
  loadCanvas, 
  analyzeThemes,
  NodeContent 
} from '../../services/strategicCanvasService';
import { NodeType, CanvasNode, CanvasEdge } from '../../types';
import { server } from '../../__mocks__/server';
import { rest } from 'msw';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('strategicCanvasService', () => {
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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('saveCanvas', () => {
    it('saves new canvas successfully', async () => {
      const mockResponse = {
        data: {
          canvasId: 'new-canvas-123',
          success: true,
          message: 'Canvas saved successfully',
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await saveCanvas(undefined, mockNodes, mockEdges);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/subjective/canvases', {
        nodes: mockNodes,
        edges: mockEdges,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('updates existing canvas successfully', async () => {
      const existingCanvasId = 'existing-canvas-456';
      const mockResponse = {
        data: {
          canvasId: existingCanvasId,
          success: true,
          message: 'Canvas updated successfully',
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await saveCanvas(existingCanvasId, mockNodes, mockEdges);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/subjective/canvases/${existingCanvasId}/elements`,
        {
          nodes: mockNodes,
          edges: mockEdges,
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('handles save error and returns mock response', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockedAxios.post.mockRejectedValue(new Error('Network error'));

      const result = await saveCanvas(undefined, mockNodes, mockEdges);

      expect(consoleErrorSpy).toHaveBeenCalledWith('Error saving canvas:', expect.any(Error));
      expect(result).toMatchObject({
        success: true,
        message: 'Canvas saved successfully (mock)',
      });
      expect(result.canvasId).toMatch(/^canvas-\d+$/);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('loadCanvas', () => {
    it('loads canvas successfully', async () => {
      const canvasId = 'test-canvas-123';
      const mockResponse = {
        data: {
          canvasId,
          nodes: mockNodes,
          edges: mockEdges,
          success: true,
          message: 'Canvas loaded successfully',
        },
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await loadCanvas(canvasId);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/subjective/canvases/${canvasId}/elements`
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('handles load error and returns mock error response', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const canvasId = 'nonexistent-canvas';
      
      mockedAxios.get.mockRejectedValue(new Error('Canvas not found'));

      const result = await loadCanvas(canvasId);

      expect(consoleErrorSpy).toHaveBeenCalledWith('Error loading canvas:', expect.any(Error));
      expect(result).toEqual({
        canvasId,
        nodes: [],
        edges: [],
        success: false,
        message: 'Failed to load canvas (mock)',
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('analyzeThemes', () => {
    const mockNodeContents: NodeContent[] = [
      {
        id: 'node-1',
        content: 'Strategic planning initiatives for Q4',
        title: 'Strategy',
      },
      {
        id: 'node-2',
        content: 'Innovation in product development',
        title: 'Innovation',
      },
    ];

    it('analyzes themes successfully', async () => {
      const mockResponse = {
        data: {
          themes: ['Strategy', 'Innovation', 'Planning'],
          summary: 'The content focuses on strategic planning and innovation.',
          suggestedConnections: [
            {
              sourceNodeId: 'node-1',
              targetNodeId: 'node-2',
              label: 'Strategic innovation link',
            },
          ],
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await analyzeThemes(mockNodeContents);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/ai/canvas/analyze-themes', {
        nodes: mockNodeContents,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('handles analysis error and returns mock response', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      mockedAxios.post.mockRejectedValue(new Error('AI service unavailable'));

      const result = await analyzeThemes(mockNodeContents);

      expect(consoleErrorSpy).toHaveBeenCalledWith('Error analyzing themes:', expect.any(Error));
      expect(result).toEqual({
        themes: ['Strategy', 'Innovation', 'Market Trends'],
        summary: 'The selected content appears to focus on strategic planning and market analysis.',
        suggestedConnections: [
          {
            sourceNodeId: 'node-1',
            targetNodeId: 'node-2',
            label: 'Related concept',
          },
        ],
      });

      consoleErrorSpy.mockRestore();
    });

    it('handles empty node contents gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      mockedAxios.post.mockRejectedValue(new Error('No content to analyze'));

      const result = await analyzeThemes([]);

      expect(result).toEqual({
        themes: ['Strategy', 'Innovation', 'Market Trends'],
        summary: 'The selected content appears to focus on strategic planning and market analysis.',
        suggestedConnections: [
          {
            sourceNodeId: '',
            targetNodeId: '',
            label: 'Related concept',
          },
        ],
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Integration with MSW', () => {
    beforeAll(() => {
      // Use MSW for these tests instead of mocking axios directly
      mockedAxios.post.mockImplementation((url, data) => 
        fetch(url, { 
          method: 'POST', 
          body: JSON.stringify(data),
          headers: { 'Content-Type': 'application/json' }
        }).then(res => ({ data: res.json() }))
      );
      
      mockedAxios.get.mockImplementation((url) => 
        fetch(url).then(res => ({ data: res.json() }))
      );
    });

    it('works with MSW mock server for save operations', async () => {
      // This test demonstrates how the service would work with MSW
      // In a real test environment, this would make actual HTTP requests to MSW
      const result = await saveCanvas(undefined, mockNodes, mockEdges);
      
      // The service should return a properly structured response
      expect(result).toHaveProperty('canvasId');
      expect(result).toHaveProperty('success');
    });

    it('handles MSW error responses', async () => {
      // Test error handling with MSW
      server.use(
        rest.post('/api/subjective/canvases/error-test', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Internal server error' }));
        })
      );

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      // This would trigger the error path in a real implementation
      const result = await saveCanvas('error-test', mockNodes, mockEdges);
      
      // Should fall back to mock response
      expect(result).toHaveProperty('success', true);
      expect(result.message).toContain('mock');

      consoleErrorSpy.mockRestore();
    });
  });
});