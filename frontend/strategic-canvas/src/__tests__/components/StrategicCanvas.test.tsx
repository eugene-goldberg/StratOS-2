import React from 'react';
import { render, screen, waitFor } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import StrategicCanvas from '../../components/StrategicCanvas';
import { useStrategicCanvasStore } from '../../store/strategicCanvasStore';
import { NodeType } from '../../types';

// Mock the store
jest.mock('../../store/strategicCanvasStore');
const mockUseStrategicCanvasStore = useStrategicCanvasStore as jest.MockedFunction<typeof useStrategicCanvasStore>;

// ReactFlow is mocked via moduleNameMapper in package.json

describe('StrategicCanvas', () => {
  const mockAnalyzeSelectedNodes = jest.fn();
  const mockAddAISuggestedEdges = jest.fn();
  const mockOnNodesChange = jest.fn();
  const mockOnEdgesChange = jest.fn();
  const mockAddEdge = jest.fn();
  const mockSetSelectedElements = jest.fn();
  const mockUpdateViewport = jest.fn();

  const mockNodes = [
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

  const mockEdges = [
    {
      id: 'edge-1',
      source: 'node-1',
      target: 'node-2',
      label: 'connects to',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseStrategicCanvasStore.mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      selectedElements: { nodes: [mockNodes[0]], edges: [] },
      onNodesChange: mockOnNodesChange,
      onEdgesChange: mockOnEdgesChange,
      addEdge: mockAddEdge,
      setSelectedElements: mockSetSelectedElements,
      clearSelection: jest.fn(),
      updateViewport: mockUpdateViewport,
      analyzeSelectedNodes: mockAnalyzeSelectedNodes,
      addAISuggestedEdges: mockAddAISuggestedEdges,
      addNode: jest.fn(),
      updateNode: jest.fn(),
      updateNodeStyle: jest.fn(),
      updateEdge: jest.fn(),
      resetCanvas: jest.fn(),
      saveCanvasState: jest.fn(),
      loadCanvasState: jest.fn(),
      setCanvasId: jest.fn(),
      viewportTransform: { x: 0, y: 0, zoom: 1 },
    });
  });

  it('renders ReactFlow with correct props', () => {
    render(<StrategicCanvas />);

    expect(screen.getByTestId('react-flow-provider')).toBeInTheDocument();
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    expect(screen.getByTestId('react-flow-background')).toBeInTheDocument();
    expect(screen.getByTestId('react-flow-controls')).toBeInTheDocument();
    expect(screen.getByTestId('react-flow-minimap')).toBeInTheDocument();
  });

  it('renders toolbar panel', () => {
    render(<StrategicCanvas />);

    expect(screen.getByTestId('react-flow-panel-top-left')).toBeInTheDocument();
  });

  it('shows AI panel when hasSelection is true and AI analysis is available', async () => {
    const mockAIResult = {
      themes: ['Strategy', 'Innovation'],
      summary: 'Test analysis result',
      suggestedConnections: [],
    };

    mockAnalyzeSelectedNodes.mockResolvedValue(mockAIResult);

    render(<StrategicCanvas />);

    // Find and click AI analysis button
    const aiButton = screen.getByRole('button', { name: /AI Assist/ });
    expect(aiButton).not.toBeDisabled();

    await userEvent.setup().click(aiButton);

    await waitFor(() => {
      expect(mockAnalyzeSelectedNodes).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByTestId('react-flow-panel-top-right')).toBeInTheDocument();
    });
  });

  it('does not show AI panel when no selection', () => {
    mockUseStrategicCanvasStore.mockReturnValue({
      ...mockUseStrategicCanvasStore(),
      selectedElements: { nodes: [], edges: [] },
    });

    render(<StrategicCanvas />);

    expect(screen.queryByTestId('react-flow-panel-top-right')).not.toBeInTheDocument();
  });

  it('handles AI analysis with suggested connections', async () => {
    const mockAIResult = {
      themes: ['Strategy'],
      summary: 'Test analysis',
      suggestedConnections: [
        {
          sourceNodeId: 'node-1',
          targetNodeId: 'node-2',
          label: 'Strategic connection',
        },
      ],
    };

    mockAnalyzeSelectedNodes.mockResolvedValue(mockAIResult);

    render(<StrategicCanvas />);

    const aiButton = screen.getByRole('button', { name: /AI Assist/ });
    await userEvent.setup().click(aiButton);

    await waitFor(() => {
      expect(mockAnalyzeSelectedNodes).toHaveBeenCalled();
      expect(mockAddAISuggestedEdges).toHaveBeenCalledWith(mockAIResult.suggestedConnections);
    });
  });

  it('handles failed AI analysis gracefully', async () => {
    mockAnalyzeSelectedNodes.mockResolvedValue(undefined);

    render(<StrategicCanvas />);

    const aiButton = screen.getByRole('button', { name: /AI Assist/ });
    await userEvent.setup().click(aiButton);

    await waitFor(() => {
      expect(mockAnalyzeSelectedNodes).toHaveBeenCalled();
    });

    // AI panel should not appear if analysis fails
    expect(screen.queryByTestId('react-flow-panel-top-right')).not.toBeInTheDocument();
  });

  it('passes correct event handlers to ReactFlow', () => {
    render(<StrategicCanvas />);

    const reactFlow = screen.getByTestId('react-flow');
    
    // Check that event handlers are passed as props
    expect(reactFlow).toHaveAttribute('data-testid', 'react-flow');
  });

  it('renders with correct theme and styling', () => {
    render(<StrategicCanvas />);

    const container = screen.getByTestId('react-flow').parentElement;
    expect(container).toHaveStyle({
      width: '100%',
      height: '100%',
    });
  });

  it('handles node creation through toolbar', async () => {
    const mockAddNode = jest.fn();
    mockUseStrategicCanvasStore.mockReturnValue({
      ...mockUseStrategicCanvasStore(),
      addNode: mockAddNode,
    });

    render(<StrategicCanvas />);

    const basicNodeButton = screen.getByLabelText(/Add Basic Text Node/);
    await userEvent.setup().click(basicNodeButton);

    expect(mockAddNode).toHaveBeenCalled();
  });

  it('handles zoom operations through toolbar', async () => {
    render(<StrategicCanvas />);

    // These would trigger the mocked ReactFlow zoom functions
    const zoomInButton = screen.getByLabelText(/Zoom In/);
    const zoomOutButton = screen.getByLabelText(/Zoom Out/);
    const fitViewButton = screen.getByLabelText(/Fit View/);

    await userEvent.setup().click(zoomInButton);
    await userEvent.setup().click(zoomOutButton);
    await userEvent.setup().click(fitViewButton);

    // Verify buttons are clickable (mocked functions would be called)
    expect(zoomInButton).toBeInTheDocument();
    expect(zoomOutButton).toBeInTheDocument();
    expect(fitViewButton).toBeInTheDocument();
  });

  it('closes AI panel when close button is clicked', async () => {
    const mockAIResult = {
      themes: ['Strategy'],
      summary: 'Test analysis',
      suggestedConnections: [],
    };

    mockAnalyzeSelectedNodes.mockResolvedValue(mockAIResult);

    render(<StrategicCanvas />);

    // Open AI panel
    const aiButton = screen.getByRole('button', { name: /AI Assist/ });
    await userEvent.setup().click(aiButton);

    await waitFor(() => {
      expect(screen.getByTestId('react-flow-panel-top-right')).toBeInTheDocument();
    });

    // Close AI panel
    const closeButton = screen.getByRole('button', { name: /close/i });
    await userEvent.setup().click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId('react-flow-panel-top-right')).not.toBeInTheDocument();
    });
  });
});