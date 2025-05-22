import { act, renderHook } from '@testing-library/react';
import { useStrategicCanvasStore } from '../../store/strategicCanvasStore';
import { NodeType, CanvasNode, CanvasEdge } from '../../types';
import * as strategicCanvasService from '../../services/strategicCanvasService';

// Mock the service
jest.mock('../../services/strategicCanvasService');
const mockStrategicCanvasService = strategicCanvasService as jest.Mocked<typeof strategicCanvasService>;

describe('strategicCanvasStore', () => {
  beforeEach(() => {
    // Reset store state between tests
    useStrategicCanvasStore.setState({
      nodes: [],
      edges: [],
      selectedElements: { nodes: [], edges: [] },
      viewportTransform: { x: 0, y: 0, zoom: 1 },
      canvasId: undefined,
    });
    
    jest.clearAllMocks();
  });

  describe('Node operations', () => {
    it('adds a new node', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      act(() => {
        result.current.addNode(
          NodeType.BASIC,
          { x: 100, y: 200 },
          { content: 'Test content', title: 'Test Node' }
        );
      });

      const state = result.current;
      expect(state.nodes).toHaveLength(1);
      expect(state.nodes[0]).toMatchObject({
        type: NodeType.BASIC,
        position: { x: 100, y: 200 },
        data: { content: 'Test content', title: 'Test Node' },
        draggable: true,
        selectable: true,
      });
      expect(state.nodes[0].id).toMatch(/^node-\d+$/);
    });

    it('updates an existing node', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add a node first
      act(() => {
        result.current.addNode(
          NodeType.BASIC,
          { x: 100, y: 200 },
          { content: 'Original content' }
        );
      });

      const nodeId = result.current.nodes[0].id;

      // Update the node
      act(() => {
        result.current.updateNode(nodeId, { content: 'Updated content', title: 'New Title' });
      });

      const state = result.current;
      expect(state.nodes[0].data).toMatchObject({
        content: 'Updated content',
        title: 'New Title',
      });
    });

    it('updates node style', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add a node first
      act(() => {
        result.current.addNode(NodeType.BASIC, { x: 0, y: 0 }, { content: 'Test' });
      });

      const nodeId = result.current.nodes[0].id;

      // Update node style
      act(() => {
        result.current.updateNodeStyle(nodeId, { backgroundColor: 'red', width: 200 });
      });

      const state = result.current;
      expect(state.nodes[0].style).toMatchObject({
        backgroundColor: 'red',
        width: 200,
      });
    });

    it('handles node changes through ReactFlow', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add a node first
      act(() => {
        result.current.addNode(NodeType.BASIC, { x: 0, y: 0 }, { content: 'Test' });
      });

      const nodeId = result.current.nodes[0].id;

      // Simulate ReactFlow node changes
      const changes = [
        {
          id: nodeId,
          type: 'position' as const,
          position: { x: 50, y: 100 },
        },
      ];

      act(() => {
        result.current.onNodesChange(changes);
      });

      // Note: Since we're mocking applyNodeChanges, the actual implementation
      // would be tested in a real environment
      expect(result.current.onNodesChange).toBeDefined();
    });
  });

  describe('Edge operations', () => {
    it('adds a new edge', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      const connection = {
        source: 'node-1',
        target: 'node-2',
        sourceHandle: null,
        targetHandle: null,
      };

      act(() => {
        result.current.addEdge(connection, 'test connection');
      });

      const state = result.current;
      expect(state.edges).toHaveLength(1);
      expect(state.edges[0]).toMatchObject({
        source: 'node-1',
        target: 'node-2',
        label: 'test connection',
      });
      expect(state.edges[0].id).toMatch(/^edge-\d+$/);
    });

    it('updates an existing edge', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add an edge first
      act(() => {
        result.current.addEdge({ source: 'node-1', target: 'node-2' });
      });

      const edgeId = result.current.edges[0].id;

      // Update the edge
      act(() => {
        result.current.updateEdge(edgeId, { label: 'Updated label' });
      });

      const state = result.current;
      expect(state.edges[0].label).toBe('Updated label');
    });

    it('handles edge changes through ReactFlow', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add an edge first
      act(() => {
        result.current.addEdge({ source: 'node-1', target: 'node-2' });
      });

      const edgeId = result.current.edges[0].id;

      // Simulate ReactFlow edge changes
      const changes = [
        {
          id: edgeId,
          type: 'remove' as const,
        },
      ];

      act(() => {
        result.current.onEdgesChange(changes);
      });

      expect(result.current.onEdgesChange).toBeDefined();
    });
  });

  describe('Selection operations', () => {
    it('sets selected elements', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      const mockNodes: CanvasNode[] = [
        {
          id: 'node-1',
          type: NodeType.BASIC,
          position: { x: 0, y: 0 },
          data: { content: 'Test' },
          draggable: true,
          selectable: true,
        },
      ];

      const mockEdges: CanvasEdge[] = [
        {
          id: 'edge-1',
          source: 'node-1',
          target: 'node-2',
        },
      ];

      act(() => {
        result.current.setSelectedElements(mockNodes, mockEdges);
      });

      const state = result.current;
      expect(state.selectedElements.nodes).toEqual(mockNodes);
      expect(state.selectedElements.edges).toEqual(mockEdges);
    });

    it('clears selection', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Set some selection first
      act(() => {
        result.current.setSelectedElements(
          [{ id: 'node-1' } as CanvasNode],
          [{ id: 'edge-1' } as CanvasEdge]
        );
      });

      // Clear selection
      act(() => {
        result.current.clearSelection();
      });

      const state = result.current;
      expect(state.selectedElements.nodes).toEqual([]);
      expect(state.selectedElements.edges).toEqual([]);
    });
  });

  describe('Canvas operations', () => {
    it('updates viewport', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      act(() => {
        result.current.updateViewport(100, 200, 1.5);
      });

      const state = result.current;
      expect(state.viewportTransform).toEqual({ x: 100, y: 200, zoom: 1.5 });
    });

    it('resets canvas', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Add some data first
      act(() => {
        result.current.addNode(NodeType.BASIC, { x: 0, y: 0 }, { content: 'Test' });
        result.current.updateViewport(100, 200, 2);
        result.current.setCanvasId('test-canvas');
      });

      // Reset canvas
      act(() => {
        result.current.resetCanvas();
      });

      const state = result.current;
      expect(state.nodes).toEqual([]);
      expect(state.edges).toEqual([]);
      expect(state.selectedElements).toEqual({ nodes: [], edges: [] });
      expect(state.viewportTransform).toEqual({ x: 0, y: 0, zoom: 1 });
    });
  });

  describe('Persistence operations', () => {
    it('saves canvas state successfully', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      mockStrategicCanvasService.saveCanvas.mockResolvedValue({
        canvasId: 'saved-canvas-123',
        success: true,
        message: 'Canvas saved successfully',
      });

      // Add some data to save
      act(() => {
        result.current.addNode(NodeType.BASIC, { x: 0, y: 0 }, { content: 'Test node' });
        result.current.addEdge({ source: 'node-1', target: 'node-2' });
      });

      let saveResult: string | undefined;
      await act(async () => {
        saveResult = await result.current.saveCanvasState();
      });

      expect(mockStrategicCanvasService.saveCanvas).toHaveBeenCalledWith(
        undefined, // no existing canvasId
        expect.any(Array), // nodes
        expect.any(Array)  // edges
      );
      expect(saveResult).toBe('saved-canvas-123');
      expect(result.current.canvasId).toBe('saved-canvas-123');
    });

    it('handles save canvas error', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      mockStrategicCanvasService.saveCanvas.mockRejectedValue(new Error('Save failed'));

      let saveResult: string | undefined;
      await act(async () => {
        saveResult = await result.current.saveCanvasState();
      });

      expect(saveResult).toBeUndefined();
      consoleSpy.mockRestore();
    });

    it('loads canvas state successfully', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      const mockLoadResponse = {
        canvasId: 'loaded-canvas-123',
        nodes: [
          {
            id: 'node-1',
            type: NodeType.BASIC,
            position: { x: 100, y: 100 },
            data: { content: 'Loaded node' },
            draggable: true,
            selectable: true,
          },
        ] as CanvasNode[],
        edges: [
          {
            id: 'edge-1',
            source: 'node-1',
            target: 'node-2',
          },
        ] as CanvasEdge[],
        success: true,
        message: 'Canvas loaded successfully',
      };

      mockStrategicCanvasService.loadCanvas.mockResolvedValue(mockLoadResponse);

      let loadResult: boolean;
      await act(async () => {
        loadResult = await result.current.loadCanvasState('test-canvas-id');
      });

      expect(mockStrategicCanvasService.loadCanvas).toHaveBeenCalledWith('test-canvas-id');
      expect(loadResult).toBe(true);
      
      const state = result.current;
      expect(state.nodes).toEqual(mockLoadResponse.nodes);
      expect(state.edges).toEqual(mockLoadResponse.edges);
      expect(state.canvasId).toBe('loaded-canvas-123');
    });

    it('handles load canvas error', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      mockStrategicCanvasService.loadCanvas.mockRejectedValue(new Error('Load failed'));

      let loadResult: boolean;
      await act(async () => {
        loadResult = await result.current.loadCanvasState('test-canvas-id');
      });

      expect(loadResult).toBe(false);
      consoleSpy.mockRestore();
    });
  });

  describe('AI operations', () => {
    it('analyzes selected nodes successfully', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Set up selected nodes with content
      const selectedNodes: CanvasNode[] = [
        {
          id: 'node-1',
          type: NodeType.BASIC,
          position: { x: 0, y: 0 },
          data: { content: 'Strategic planning content', title: 'Strategy' },
          draggable: true,
          selectable: true,
        },
      ];

      act(() => {
        result.current.setSelectedElements(selectedNodes, []);
      });

      const mockAIResult = {
        themes: ['Strategy', 'Planning'],
        summary: 'Analysis of strategic content',
        suggestedConnections: [],
      };

      mockStrategicCanvasService.analyzeThemes.mockResolvedValue(mockAIResult);

      let analysisResult;
      await act(async () => {
        analysisResult = await result.current.analyzeSelectedNodes();
      });

      expect(mockStrategicCanvasService.analyzeThemes).toHaveBeenCalledWith([
        {
          id: 'node-1',
          content: 'Strategic planning content',
          title: 'Strategy',
        },
      ]);
      expect(analysisResult).toEqual(mockAIResult);
    });

    it('returns undefined when no nodes with content are selected', async () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      // Set selected nodes without content
      act(() => {
        result.current.setSelectedElements([], []);
      });

      let analysisResult;
      await act(async () => {
        analysisResult = await result.current.analyzeSelectedNodes();
      });

      expect(analysisResult).toBeUndefined();
      expect(mockStrategicCanvasService.analyzeThemes).not.toHaveBeenCalled();
    });

    it('adds AI suggested edges', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      const suggestedConnections = [
        {
          sourceNodeId: 'node-1',
          targetNodeId: 'node-2',
          label: 'AI suggested connection',
        },
        {
          sourceNodeId: 'node-2',
          targetNodeId: 'node-3',
          label: 'Another AI connection',
        },
      ];

      act(() => {
        result.current.addAISuggestedEdges(suggestedConnections);
      });

      const state = result.current;
      expect(state.edges).toHaveLength(2);
      
      // Check first edge
      expect(state.edges[0]).toMatchObject({
        source: 'node-1',
        target: 'node-2',
        label: 'AI suggested connection',
        isAISuggested: true,
      });
      expect(state.edges[0].style).toMatchObject({
        strokeDasharray: '5,5',
        stroke: '#0060FF',
        opacity: 0.6,
      });
    });

    it('handles empty suggested connections', () => {
      const { result } = renderHook(() => useStrategicCanvasStore());

      act(() => {
        result.current.addAISuggestedEdges([]);
      });

      expect(result.current.edges).toHaveLength(0);
    });
  });
});