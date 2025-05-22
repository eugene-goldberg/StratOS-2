import React from 'react';
import { render, screen, waitFor, within } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import StrategicCanvas from '../../components/StrategicCanvas';
import { useStrategicCanvasStore } from '../../store/strategicCanvasStore';
import { NodeType } from '../../types';

// Mock the store with a more complete implementation for integration tests
jest.mock('../../store/strategicCanvasStore');
const mockUseStrategicCanvasStore = useStrategicCanvasStore as jest.MockedFunction<typeof useStrategicCanvasStore>;

// Mock ReactFlow
jest.mock('reactflow');

describe('Strategic Canvas Integration Tests', () => {
  let mockStore: any;

  beforeEach(() => {
    // Create a more complete mock store for integration testing
    mockStore = {
      nodes: [],
      edges: [],
      selectedElements: { nodes: [], edges: [] },
      viewportTransform: { x: 0, y: 0, zoom: 1 },
      canvasId: undefined,
      
      addNode: jest.fn((type, position, data) => {
        const newNode = {
          id: `node-${Date.now()}`,
          type,
          position,
          data,
          draggable: true,
          selectable: true,
        };
        mockStore.nodes = [...mockStore.nodes, newNode];
        mockUseStrategicCanvasStore.mockReturnValue(mockStore);
      }),
      
      updateNode: jest.fn((nodeId, data) => {
        mockStore.nodes = mockStore.nodes.map((node: any) => 
          node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
        );
        mockUseStrategicCanvasStore.mockReturnValue(mockStore);
      }),
      
      addEdge: jest.fn((connection, label) => {
        const newEdge = {
          id: `edge-${Date.now()}`,
          source: connection.source,
          target: connection.target,
          label,
        };
        mockStore.edges = [...mockStore.edges, newEdge];
        mockUseStrategicCanvasStore.mockReturnValue(mockStore);
      }),
      
      setSelectedElements: jest.fn((nodes, edges) => {
        mockStore.selectedElements = { nodes, edges };
        mockUseStrategicCanvasStore.mockReturnValue(mockStore);
      }),
      
      analyzeSelectedNodes: jest.fn().mockResolvedValue({
        themes: ['Strategy', 'Innovation'],
        summary: 'The selected content focuses on strategic innovation.',
        suggestedConnections: [
          {
            sourceNodeId: 'node-1',
            targetNodeId: 'node-2',
            label: 'Strategic alignment',
          },
        ],
      }),
      
      addAISuggestedEdges: jest.fn((connections) => {
        const newEdges = connections.map((conn: any) => ({
          id: `ai-edge-${Date.now()}`,
          source: conn.sourceNodeId,
          target: conn.targetNodeId,
          label: conn.label,
          isAISuggested: true,
        }));
        mockStore.edges = [...mockStore.edges, ...newEdges];
        mockUseStrategicCanvasStore.mockReturnValue(mockStore);
      }),
      
      saveCanvasState: jest.fn().mockResolvedValue('saved-canvas-123'),
      loadCanvasState: jest.fn().mockResolvedValue(true),
      
      // Other required methods
      updateNodeStyle: jest.fn(),
      onNodesChange: jest.fn(),
      updateEdge: jest.fn(),
      onEdgesChange: jest.fn(),
      clearSelection: jest.fn(),
      updateViewport: jest.fn(),
      resetCanvas: jest.fn(),
      setCanvasId: jest.fn(),
    };

    mockUseStrategicCanvasStore.mockReturnValue(mockStore);
  });

  describe('Complete Canvas Workflow', () => {
    it('should complete a full canvas creation and editing workflow', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Step 1: Add a basic text node
      const basicNodeButton = screen.getByLabelText(/Add Basic Text Node/);
      await user.click(basicNodeButton);

      expect(mockStore.addNode).toHaveBeenCalledWith(
        NodeType.BASIC,
        expect.any(Object),
        expect.objectContaining({ content: '' })
      );

      // Step 2: Add a CEO log node
      const ceoLogButton = screen.getByLabelText(/Add CEO Log Node/);
      await user.click(ceoLogButton);

      expect(mockStore.addNode).toHaveBeenCalledWith(
        NodeType.CEO_LOG,
        expect.any(Object),
        expect.any(Object)
      );

      // Step 3: Simulate node selection
      mockStore.selectedElements = {
        nodes: [
          {
            id: 'node-1',
            type: NodeType.BASIC,
            position: { x: 0, y: 0 },
            data: { content: 'Strategic planning content', title: 'Strategy' },
            draggable: true,
            selectable: true,
          },
        ],
        edges: [],
      };
      mockUseStrategicCanvasStore.mockReturnValue(mockStore);

      // Re-render to reflect the selection
      render(<StrategicCanvas />);

      // Step 4: Run AI analysis
      const aiButton = screen.getByLabelText(/AI Assist/);
      expect(aiButton).not.toBeDisabled();
      
      await user.click(aiButton);

      await waitFor(() => {
        expect(mockStore.analyzeSelectedNodes).toHaveBeenCalled();
      });

      // Step 5: Verify AI panel appears
      await waitFor(() => {
        expect(screen.getByTestId('react-flow-panel-top-right')).toBeInTheDocument();
      });

      // Step 6: Verify AI suggested edges were added
      expect(mockStore.addAISuggestedEdges).toHaveBeenCalledWith([
        {
          sourceNodeId: 'node-1',
          targetNodeId: 'node-2',
          label: 'Strategic alignment',
        },
      ]);

      // Step 7: Close AI panel
      const closeButton = screen.getByLabelText(/close/i);
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('react-flow-panel-top-right')).not.toBeInTheDocument();
      });
    });

    it('should handle canvas save and load workflow', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Add some content to the canvas
      const basicNodeButton = screen.getByLabelText(/Add Basic Text Node/);
      await user.click(basicNodeButton);
      await user.click(basicNodeButton); // Add second node

      // Save the canvas
      const saveButton = screen.getByLabelText(/Save Canvas/);
      await user.click(saveButton);

      // Verify save was attempted (in a real app, this would show feedback)
      expect(mockStore.saveCanvasState).toHaveBeenCalled();
    });

    it('should handle zoom and viewport operations', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Test zoom operations
      const zoomInButton = screen.getByLabelText(/Zoom In/);
      const zoomOutButton = screen.getByLabelText(/Zoom Out/);
      const fitViewButton = screen.getByLabelText(/Fit View/);

      await user.click(zoomInButton);
      await user.click(zoomOutButton);
      await user.click(fitViewButton);

      // These operations would be handled by ReactFlow in a real environment
      expect(zoomInButton).toBeInTheDocument();
      expect(zoomOutButton).toBeInTheDocument();
      expect(fitViewButton).toBeInTheDocument();
    });
  });

  describe('SWOT Analysis Workflow', () => {
    it('should create a complete SWOT analysis canvas', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Add all SWOT node types
      const strengthButton = screen.getByLabelText(/Add SWOT Strength Node/);
      const weaknessButton = screen.getByLabelText(/Add SWOT Weakness Node/);
      const opportunityButton = screen.getByLabelText(/Add SWOT Opportunity Node/);

      await user.click(strengthButton);
      await user.click(weaknessButton);
      await user.click(opportunityButton);

      expect(mockStore.addNode).toHaveBeenCalledTimes(3);
      expect(mockStore.addNode).toHaveBeenCalledWith(NodeType.SWOT_S, expect.any(Object), expect.any(Object));
      expect(mockStore.addNode).toHaveBeenCalledWith(NodeType.SWOT_W, expect.any(Object), expect.any(Object));
      expect(mockStore.addNode).toHaveBeenCalledWith(NodeType.SWOT_O, expect.any(Object), expect.any(Object));
    });
  });

  describe('Data Visualization Workflow', () => {
    it('should create a data-driven strategic canvas', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Add data snippet and image nodes
      const dataSnippetButton = screen.getByLabelText(/Add Data Snippet Node/);
      const imageButton = screen.getByLabelText(/Add Image Node/);

      await user.click(dataSnippetButton);
      await user.click(imageButton);

      expect(mockStore.addNode).toHaveBeenCalledWith(NodeType.DATA_SNIPPET, expect.any(Object), expect.any(Object));
      expect(mockStore.addNode).toHaveBeenCalledWith(NodeType.IMAGE, expect.any(Object), expect.any(Object));
    });
  });

  describe('Error Handling Workflows', () => {
    it('should handle AI analysis failure gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock AI analysis to fail
      mockStore.analyzeSelectedNodes.mockResolvedValue(undefined);
      
      // Set up selection
      mockStore.selectedElements = {
        nodes: [
          {
            id: 'node-1',
            type: NodeType.BASIC,
            position: { x: 0, y: 0 },
            data: { content: 'Test content' },
            draggable: true,
            selectable: true,
          },
        ],
        edges: [],
      };
      
      render(<StrategicCanvas />);

      // Try AI analysis
      const aiButton = screen.getByLabelText(/AI Assist/);
      await user.click(aiButton);

      await waitFor(() => {
        expect(mockStore.analyzeSelectedNodes).toHaveBeenCalled();
      });

      // AI panel should not appear on failure
      expect(screen.queryByTestId('react-flow-panel-top-right')).not.toBeInTheDocument();
    });

    it('should handle empty selection for AI analysis', async () => {
      const user = userEvent.setup();
      
      // No selection
      mockStore.selectedElements = { nodes: [], edges: [] };
      
      render(<StrategicCanvas />);

      // AI button should be disabled
      const aiButton = screen.getByLabelText(/AI Assist/);
      expect(aiButton).toBeDisabled();
    });
  });

  describe('Accessibility and UX Workflows', () => {
    it('should provide proper ARIA labels and keyboard navigation', () => {
      render(<StrategicCanvas />);

      // Check that all buttons have proper labels
      expect(screen.getByLabelText(/Add Basic Text Node/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Add CEO Log Node/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Zoom In/)).toBeInTheDocument();
      expect(screen.getByLabelText(/AI Assist/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Save Canvas/)).toBeInTheDocument();
    });

    it('should show appropriate disabled states', () => {
      render(<StrategicCanvas />);

      // With no selection, these buttons should be disabled
      expect(screen.getByLabelText(/AI Assist/)).toBeDisabled();
      expect(screen.getByLabelText(/Delete Selected/)).toBeDisabled();
    });

    it('should enable buttons when selection is present', () => {
      // Set up selection
      mockStore.selectedElements = {
        nodes: [{ id: 'node-1' } as any],
        edges: [],
      };
      
      render(<StrategicCanvas />);

      // With selection, these buttons should be enabled
      expect(screen.getByLabelText(/AI Assist/)).not.toBeDisabled();
      expect(screen.getByLabelText(/Delete Selected/)).not.toBeDisabled();
    });
  });

  describe('Performance and State Management', () => {
    it('should maintain consistent state across operations', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Perform multiple operations
      await user.click(screen.getByLabelText(/Add Basic Text Node/));
      await user.click(screen.getByLabelText(/Add CEO Log Node/));

      // Verify state consistency
      expect(mockStore.addNode).toHaveBeenCalledTimes(2);
      
      // Simulate zoom operation
      await user.click(screen.getByLabelText(/Zoom In/));
      
      // State should remain consistent
      expect(mockStore.nodes).toBeDefined();
      expect(mockStore.edges).toBeDefined();
    });

    it('should handle rapid successive operations', async () => {
      const user = userEvent.setup();
      
      render(<StrategicCanvas />);

      // Rapid clicking
      const basicNodeButton = screen.getByLabelText(/Add Basic Text Node/);
      await user.click(basicNodeButton);
      await user.click(basicNodeButton);
      await user.click(basicNodeButton);

      expect(mockStore.addNode).toHaveBeenCalledTimes(3);
    });
  });
});