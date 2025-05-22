import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReactFlowProvider } from 'reactflow';
import StrategicCanvas from '../StrategicCanvas';
import CanvasToolbar from '../CanvasToolbar';
import { useStrategicCanvasStore } from '../../../store/strategicCanvasStore';
import useCanvasVoiceCommands from '../../../hooks/useCanvasVoiceCommands';

// Mock dependencies
jest.mock('../../../store/strategicCanvasStore');
jest.mock('../../../hooks/useCanvasVoiceCommands');
jest.mock('reactflow', () => ({
  ...jest.requireActual('reactflow'),
  ReactFlow: ({ children }: any) => <div data-testid="react-flow">{children}</div>,
  ReactFlowProvider: ({ children }: any) => <div>{children}</div>,
  Panel: ({ children, position }: any) => <div data-testid={`panel-${position}`}>{children}</div>,
  Background: () => null,
  Controls: () => null,
  MiniMap: () => null,
  useReactFlow: () => ({
    zoomIn: jest.fn(),
    zoomOut: jest.fn(),
    fitView: jest.fn(),
  }),
}));

const mockUseStrategicCanvasStore = useStrategicCanvasStore as jest.MockedFunction<typeof useStrategicCanvasStore>;
const mockUseCanvasVoiceCommands = useCanvasVoiceCommands as jest.MockedFunction<typeof useCanvasVoiceCommands>;

describe('Canvas Voice Commands Integration', () => {
  const mockNodes = [
    { id: 'node1', data: { label: 'Strategy' }, position: { x: 0, y: 0 }, type: 'basic' },
    { id: 'node2', data: { label: 'Goals' }, position: { x: 200, y: 0 }, type: 'basic' },
  ];
  
  const mockStoreState = {
    nodes: mockNodes,
    edges: [],
    selectedElements: { nodes: [], edges: [] },
    onNodesChange: jest.fn(),
    onEdgesChange: jest.fn(),
    addEdge: jest.fn(),
    setSelectedElements: jest.fn(),
    updateViewport: jest.fn(),
    analyzeSelectedNodes: jest.fn(),
    addAISuggestedEdges: jest.fn(),
    addNode: jest.fn(),
  };
  
  const mockVoiceCommands = {
    isRecording: false,
    isProcessing: false,
    transcript: '',
    startVoiceCommand: jest.fn(),
    stopVoiceCommand: jest.fn(),
    cancelVoiceCommand: jest.fn(),
    processTextCommand: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseStrategicCanvasStore.mockReturnValue(mockStoreState);
    mockUseCanvasVoiceCommands.mockReturnValue(mockVoiceCommands);
  });
  
  describe('StrategicCanvas Voice Integration', () => {
    it('should render voice command UI elements', () => {
      render(<StrategicCanvas />);
      
      // Check that the canvas toolbar is rendered with voice controls
      const toolbar = screen.getByTestId('panel-top-left');
      expect(toolbar).toBeInTheDocument();
    });
    
    it('should show transcript when recording', () => {
      mockUseCanvasVoiceCommands.mockReturnValue({
        ...mockVoiceCommands,
        isRecording: true,
        transcript: 'add a node called Innovation',
      });
      
      render(<StrategicCanvas />);
      
      // Check for transcript display
      expect(screen.getByText('add a node called Innovation')).toBeInTheDocument();
    });
    
    it('should show listening indicator when recording without transcript', () => {
      mockUseCanvasVoiceCommands.mockReturnValue({
        ...mockVoiceCommands,
        isRecording: true,
        transcript: '',
      });
      
      render(<StrategicCanvas />);
      
      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });
    
    it('should display command feedback messages', async () => {
      const { rerender } = render(<StrategicCanvas />);
      
      // Simulate command completion with message
      mockUseCanvasVoiceCommands.mockReturnValue({
        ...mockVoiceCommands,
        isRecording: false,
      });
      
      // Mock the onCommandComplete callback being called
      const onCommandComplete = mockUseCanvasVoiceCommands.mock.calls[0][0].onCommandComplete;
      onCommandComplete({ 
        success: true, 
        message: "Added node 'Innovation'" 
      });
      
      rerender(<StrategicCanvas />);
      
      await waitFor(() => {
        expect(screen.getByText("Added node 'Innovation'")).toBeInTheDocument();
      });
    });
    
    it('should display error messages', async () => {
      const { rerender } = render(<StrategicCanvas />);
      
      // Mock the onError callback being called
      const onError = mockUseCanvasVoiceCommands.mock.calls[0][0].onError;
      onError('Speech recognition not supported');
      
      rerender(<StrategicCanvas />);
      
      await waitFor(() => {
        expect(screen.getByText('Speech recognition not supported')).toBeInTheDocument();
      });
    });
  });
  
  describe('CanvasToolbar Voice Button', () => {
    it('should render voice command button when handler is provided', () => {
      const handleVoiceToggle = jest.fn();
      
      render(
        <CanvasToolbar
          onAIAnalysisClick={jest.fn()}
          hasSelection={false}
          isVoiceRecording={false}
          onVoiceCommandToggle={handleVoiceToggle}
        />
      );
      
      const voiceButton = screen.getByLabelText('Start Voice Command');
      expect(voiceButton).toBeInTheDocument();
    });
    
    it('should not render voice button when handler is not provided', () => {
      render(
        <CanvasToolbar
          onAIAnalysisClick={jest.fn()}
          hasSelection={false}
        />
      );
      
      const voiceButton = screen.queryByLabelText('Start Voice Command');
      expect(voiceButton).not.toBeInTheDocument();
    });
    
    it('should toggle voice recording on button click', async () => {
      const handleVoiceToggle = jest.fn();
      const user = userEvent.setup();
      
      render(
        <CanvasToolbar
          onAIAnalysisClick={jest.fn()}
          hasSelection={false}
          isVoiceRecording={false}
          onVoiceCommandToggle={handleVoiceToggle}
        />
      );
      
      const voiceButton = screen.getByLabelText('Start Voice Command');
      await user.click(voiceButton);
      
      expect(handleVoiceToggle).toHaveBeenCalled();
    });
    
    it('should show stop recording state', () => {
      render(
        <CanvasToolbar
          onAIAnalysisClick={jest.fn()}
          hasSelection={false}
          isVoiceRecording={true}
          onVoiceCommandToggle={jest.fn()}
        />
      );
      
      const voiceButton = screen.getByLabelText('Stop Voice Command');
      expect(voiceButton).toBeInTheDocument();
      
      // Check for pulsing animation style
      const iconButton = voiceButton.closest('button');
      expect(iconButton).toHaveStyle({ animation: expect.stringContaining('pulse') });
    });
  });
  
  describe('Voice Command Flow', () => {
    it('should handle complete voice command flow', async () => {
      const { rerender } = render(<StrategicCanvas />);
      
      // Start voice recording
      const handleVoiceToggle = mockUseCanvasVoiceCommands.mock.calls[0][0].onVoiceCommandToggle;
      
      // Simulate clicking voice button (would be done through toolbar)
      mockUseCanvasVoiceCommands.mockReturnValue({
        ...mockVoiceCommands,
        isRecording: true,
        transcript: 'create a node called Product Strategy',
      });
      
      rerender(<StrategicCanvas />);
      
      // Verify recording state
      expect(screen.getByText('create a node called Product Strategy')).toBeInTheDocument();
      
      // Simulate command completion
      mockUseCanvasVoiceCommands.mockReturnValue({
        ...mockVoiceCommands,
        isRecording: false,
        transcript: '',
      });
      
      const onCommandComplete = mockUseCanvasVoiceCommands.mock.calls[0][0].onCommandComplete;
      onCommandComplete({
        success: true,
        action: 'add_node',
        message: "Added node 'Product Strategy'",
      });
      
      rerender(<StrategicCanvas />);
      
      // Verify feedback
      await waitFor(() => {
        expect(screen.getByText("Added node 'Product Strategy'")).toBeInTheDocument();
      });
    });
  });
  
  describe('Voice Commands Accessibility', () => {
    it('should have proper ARIA labels for voice controls', () => {
      render(
        <CanvasToolbar
          onAIAnalysisClick={jest.fn()}
          hasSelection={false}
          isVoiceRecording={false}
          onVoiceCommandToggle={jest.fn()}
        />
      );
      
      const voiceButton = screen.getByLabelText('Start Voice Command');
      expect(voiceButton).toHaveAttribute('aria-label');
    });
    
    it('should announce voice command status changes', async () => {
      const { rerender } = render(<StrategicCanvas />);
      
      // Check for alert role in feedback messages
      const onCommandComplete = mockUseCanvasVoiceCommands.mock.calls[0][0].onCommandComplete;
      onCommandComplete({
        success: true,
        message: 'Voice command completed',
      });
      
      rerender(<StrategicCanvas />);
      
      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toHaveTextContent('Voice command completed');
      });
    });
  });
});