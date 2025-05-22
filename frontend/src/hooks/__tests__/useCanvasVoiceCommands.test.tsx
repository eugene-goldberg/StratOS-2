import { renderHook, act } from '@testing-library/react';
import axios from 'axios';
import { useCanvasVoiceCommands } from '../useCanvasVoiceCommands';
import { useStrategicCanvasStore } from '../../store/strategicCanvasStore';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock the store
jest.mock('../../store/strategicCanvasStore');
const mockUseStrategicCanvasStore = useStrategicCanvasStore as jest.MockedFunction<typeof useStrategicCanvasStore>;

// Mock SpeechRecognition
const mockSpeechRecognition = {
  start: jest.fn(),
  stop: jest.fn(),
  abort: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  continuous: false,
  interimResults: false,
  lang: '',
  onresult: null as any,
  onerror: null as any,
  onend: null as any,
};

// Add SpeechRecognition to window
(global as any).window.webkitSpeechRecognition = jest.fn(() => mockSpeechRecognition);

describe('useCanvasVoiceCommands', () => {
  const mockCanvasId = 'test-canvas-123';
  const mockOnCommandComplete = jest.fn();
  const mockOnError = jest.fn();
  
  // Mock store state
  const mockNodes = [
    { id: 'node1', data: { label: 'Test Node 1' }, position: { x: 0, y: 0 }, type: 'basic' },
    { id: 'node2', data: { label: 'Test Node 2' }, position: { x: 100, y: 100 }, type: 'basic' },
  ];
  
  const mockAddNode = jest.fn();
  const mockAddEdge = jest.fn();
  const mockUpdateNode = jest.fn();
  const mockDeleteNode = jest.fn();
  const mockSetNodes = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset mock store
    mockUseStrategicCanvasStore.mockReturnValue({
      nodes: mockNodes,
      edges: [],
      selectedElements: [],
      addNode: mockAddNode,
      addEdge: mockAddEdge,
      updateNode: mockUpdateNode,
      deleteNode: mockDeleteNode,
      setNodes: mockSetNodes,
      onNodesChange: jest.fn(),
      onEdgesChange: jest.fn(),
      setSelectedElements: jest.fn(),
      updateViewport: jest.fn(),
      analyzeSelectedNodes: jest.fn(),
      addAISuggestedEdges: jest.fn(),
    });
    
    // Reset SpeechRecognition mock
    mockSpeechRecognition.onresult = null;
    mockSpeechRecognition.onerror = null;
    mockSpeechRecognition.onend = null;
  });
  
  describe('initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      expect(result.current.isRecording).toBe(false);
      expect(result.current.isProcessing).toBe(false);
      expect(result.current.transcript).toBe('');
    });
  });
  
  describe('voice recording', () => {
    it('should start voice recording when startVoiceCommand is called', () => {
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      act(() => {
        result.current.startVoiceCommand();
      });
      
      expect(mockSpeechRecognition.start).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(true);
    });
    
    it('should stop voice recording when stopVoiceCommand is called', () => {
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      // Start recording first
      act(() => {
        result.current.startVoiceCommand();
      });
      
      // Then stop
      act(() => {
        result.current.stopVoiceCommand();
      });
      
      expect(mockSpeechRecognition.stop).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(false);
    });
    
    it('should handle speech recognition errors', () => {
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      act(() => {
        result.current.startVoiceCommand();
      });
      
      // Simulate error
      act(() => {
        if (mockSpeechRecognition.onerror) {
          mockSpeechRecognition.onerror({ error: 'network' });
        }
      });
      
      expect(mockOnError).toHaveBeenCalledWith('Speech recognition error: network');
      expect(result.current.isRecording).toBe(false);
    });
  });
  
  describe('voice command processing', () => {
    it('should process add node command successfully', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          success: true,
          action: 'add_node',
          node: {
            title: 'New Strategy',
            type: 'concept',
            position: { x: 0, y: 0 },
          },
          message: "Added node 'New Strategy'",
        },
      });
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      await act(async () => {
        await result.current.processTextCommand('add a node called New Strategy');
      });
      
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/canvas-ai/voice-command'),
        expect.objectContaining({
          canvas_id: mockCanvasId,
          voice_command: 'add a node called New Strategy',
        })
      );
      
      expect(mockAddNode).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'concept',
          data: {
            label: 'New Strategy',
            content: '',
          },
        })
      );
      
      expect(mockOnCommandComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          action: 'add_node',
          message: "Added node 'New Strategy'",
        })
      );
    });
    
    it('should process connect nodes command successfully', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          success: true,
          action: 'connect_nodes',
          edge: {
            source: 'node1',
            target: 'node2',
            type: 'relates_to',
          },
          message: "Connected 'Test Node 1' to 'Test Node 2'",
        },
      });
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      await act(async () => {
        await result.current.processTextCommand('connect Test Node 1 to Test Node 2');
      });
      
      expect(mockAddEdge).toHaveBeenCalledWith(
        expect.objectContaining({
          source: 'node1',
          target: 'node2',
          type: 'relates_to',
        })
      );
    });
    
    it('should process delete node command successfully', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          success: true,
          action: 'delete_node',
          node_title: 'Test Node 1',
          message: "Delete node 'Test Node 1'",
        },
      });
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      await act(async () => {
        await result.current.processTextCommand('delete node Test Node 1');
      });
      
      expect(mockDeleteNode).toHaveBeenCalledWith('node1');
    });
    
    it('should handle command processing errors', async () => {
      mockedAxios.post.mockRejectedValueOnce(new Error('Network error'));
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      await act(async () => {
        await result.current.processTextCommand('any command');
      });
      
      expect(mockOnError).toHaveBeenCalledWith('Failed to process voice command');
    });
  });
  
  describe('compound commands', () => {
    it('should process compound commands with multiple actions', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          success: true,
          compound: true,
          results: [
            {
              success: true,
              action: 'add_node',
              node: { title: 'Node A', type: 'concept', position: { x: 0, y: 0 } },
            },
            {
              success: true,
              action: 'add_node',
              node: { title: 'Node B', type: 'concept', position: { x: 100, y: 0 } },
            },
          ],
          message: 'Executed 2 commands',
        },
      });
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      await act(async () => {
        await result.current.processTextCommand('create Node A and then create Node B');
      });
      
      expect(mockAddNode).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('speech recognition flow', () => {
    it('should update transcript during speech recognition', () => {
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      act(() => {
        result.current.startVoiceCommand();
      });
      
      // Simulate interim result
      act(() => {
        if (mockSpeechRecognition.onresult) {
          mockSpeechRecognition.onresult({
            resultIndex: 0,
            results: [
              {
                0: { transcript: 'add a node' },
                isFinal: false,
                length: 1,
              },
            ],
          });
        }
      });
      
      expect(result.current.transcript).toBe('add a node');
    });
    
    it('should process final transcript automatically', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          success: true,
          action: 'add_node',
          node: { title: 'Test', type: 'concept', position: { x: 0, y: 0 } },
          message: "Added node 'Test'",
        },
      });
      
      const { result } = renderHook(() =>
        useCanvasVoiceCommands({
          canvasId: mockCanvasId,
          onCommandComplete: mockOnCommandComplete,
          onError: mockOnError,
        })
      );
      
      act(() => {
        result.current.startVoiceCommand();
      });
      
      // Simulate final result
      await act(async () => {
        if (mockSpeechRecognition.onresult) {
          mockSpeechRecognition.onresult({
            resultIndex: 0,
            results: [
              {
                0: { transcript: 'add a node called Test' },
                isFinal: true,
                length: 1,
              },
            ],
          });
        }
      });
      
      expect(mockedAxios.post).toHaveBeenCalled();
      expect(mockAddNode).toHaveBeenCalled();
    });
  });
});