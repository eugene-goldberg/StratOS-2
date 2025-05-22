import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import CanvasToolbar from '../../components/CanvasToolbar';
import { useStrategicCanvasStore } from '../../store/strategicCanvasStore';
import { useReactFlow } from 'reactflow';

// Mock the store
jest.mock('../../store/strategicCanvasStore');
const mockUseStrategicCanvasStore = useStrategicCanvasStore as jest.MockedFunction<typeof useStrategicCanvasStore>;

// Mock ReactFlow hook
jest.mock('reactflow');
const mockUseReactFlow = useReactFlow as jest.MockedFunction<typeof useReactFlow>;

describe('CanvasToolbar', () => {
  const mockAddNode = jest.fn();
  const mockOnAIAnalysisClick = jest.fn();
  const mockZoomIn = jest.fn();
  const mockZoomOut = jest.fn();
  const mockFitView = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseStrategicCanvasStore.mockReturnValue({
      addNode: mockAddNode,
      selectedElements: { nodes: [], edges: [] },
      nodes: [],
      edges: [],
      updateNode: jest.fn(),
      updateNodeStyle: jest.fn(),
      onNodesChange: jest.fn(),
      addEdge: jest.fn(),
      updateEdge: jest.fn(),
      onEdgesChange: jest.fn(),
      setSelectedElements: jest.fn(),
      clearSelection: jest.fn(),
      updateViewport: jest.fn(),
      resetCanvas: jest.fn(),
      saveCanvasState: jest.fn(),
      loadCanvasState: jest.fn(),
      setCanvasId: jest.fn(),
      analyzeSelectedNodes: jest.fn(),
      addAISuggestedEdges: jest.fn(),
      viewportTransform: { x: 0, y: 0, zoom: 1 },
    });

    mockUseReactFlow.mockReturnValue({
      zoomIn: mockZoomIn,
      zoomOut: mockZoomOut,
      fitView: mockFitView,
      getNodes: jest.fn(),
      getEdges: jest.fn(),
      setNodes: jest.fn(),
      setEdges: jest.fn(),
      addNodes: jest.fn(),
      addEdges: jest.fn(),
      toObject: jest.fn(),
      setViewport: jest.fn(),
      getViewport: jest.fn(),
      project: jest.fn(),
      screenToFlowPosition: jest.fn(),
      flowToScreenPosition: jest.fn(),
    });
  });

  it('renders all toolbar buttons', () => {
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    // Check for main tool categories
    expect(screen.getByLabelText(/Add Basic Text Node/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Add CEO Log Node/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Add Data Snippet Node/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Zoom In/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Zoom Out/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fit View/)).toBeInTheDocument();
    expect(screen.getByLabelText(/AI Assist/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Save Canvas/)).toBeInTheDocument();
  });

  it('calls addNode when node creation buttons are clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    // Click basic text node button
    const basicNodeButton = screen.getByLabelText(/Add Basic Text Node/);
    await user.click(basicNodeButton);

    expect(mockAddNode).toHaveBeenCalledWith(
      'basic',
      expect.objectContaining({ x: expect.any(Number), y: expect.any(Number) }),
      expect.objectContaining({ content: '' })
    );
  });

  it('calls ReactFlow zoom functions when zoom buttons are clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    // Test zoom in
    await user.click(screen.getByLabelText(/Zoom In/));
    expect(mockZoomIn).toHaveBeenCalled();

    // Test zoom out
    await user.click(screen.getByLabelText(/Zoom Out/));
    expect(mockZoomOut).toHaveBeenCalled();

    // Test fit view
    await user.click(screen.getByLabelText(/Fit View/));
    expect(mockFitView).toHaveBeenCalled();
  });

  it('disables AI assist button when no selection', () => {
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    const aiButton = screen.getByLabelText(/AI Assist/);
    expect(aiButton).toBeDisabled();
  });

  it('enables AI assist button when has selection', () => {
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={true} />
    );

    const aiButton = screen.getByLabelText(/AI Assist/);
    expect(aiButton).not.toBeDisabled();
  });

  it('calls onAIAnalysisClick when AI assist button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={true} />
    );

    const aiButton = screen.getByLabelText(/AI Assist/);
    await user.click(aiButton);

    expect(mockOnAIAnalysisClick).toHaveBeenCalled();
  });

  it('disables delete button when no selection', () => {
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    const deleteButton = screen.getByLabelText(/Delete Selected/);
    expect(deleteButton).toBeDisabled();
  });

  it('enables delete button when has selection', () => {
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={true} />
    );

    const deleteButton = screen.getByLabelText(/Delete Selected/);
    expect(deleteButton).not.toBeDisabled();
  });

  it('adds different node types correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    // Test CEO Log node
    await user.click(screen.getByLabelText(/Add CEO Log Node/));
    expect(mockAddNode).toHaveBeenCalledWith(
      'ceoLog',
      expect.any(Object),
      expect.any(Object)
    );

    // Test Data Snippet node
    await user.click(screen.getByLabelText(/Add Data Snippet Node/));
    expect(mockAddNode).toHaveBeenCalledWith(
      'dataSnippet',
      expect.any(Object),
      expect.any(Object)
    );

    // Test SWOT nodes
    await user.click(screen.getByLabelText(/Add SWOT Strength Node/));
    expect(mockAddNode).toHaveBeenCalledWith(
      'swotS',
      expect.any(Object),
      expect.any(Object)
    );
  });

  it('calculates node position in center of viewport', async () => {
    const user = userEvent.setup();
    
    // Mock getBoundingClientRect for react-flow element
    const mockElement = document.createElement('div');
    mockElement.getBoundingClientRect = jest.fn(() => ({
      width: 1000,
      height: 800,
      top: 0,
      left: 0,
      bottom: 800,
      right: 1000,
      x: 0,
      y: 0,
      toJSON: jest.fn(),
    }));
    
    jest.spyOn(document, 'querySelector').mockReturnValue(mockElement);
    
    render(
      <CanvasToolbar onAIAnalysisClick={mockOnAIAnalysisClick} hasSelection={false} />
    );

    await user.click(screen.getByLabelText(/Add Basic Text Node/));

    expect(mockAddNode).toHaveBeenCalledWith(
      'basic',
      { x: 500, y: 400 }, // Center of 1000x800 viewport
      expect.any(Object)
    );
  });
});