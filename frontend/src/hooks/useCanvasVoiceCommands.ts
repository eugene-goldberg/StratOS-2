import { useRef, useCallback, useState } from 'react';
import axios from 'axios';
import { Node, Edge } from 'reactflow';
import { useStrategicCanvasStore } from '../store/strategicCanvasStore';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface VoiceCommandResult {
  success: boolean;
  action?: string;
  message?: string;
  node?: any;
  edge?: any;
  node_ids?: string[];
  node_title?: string;
  position?: { x: number; y: number };
  old_title?: string;
  new_title?: string;
  node_titles?: string[];
  analysis?: any;
  compound?: boolean;
  results?: VoiceCommandResult[];
  requires_user_input?: boolean;
  error?: string;
}

interface UseCanvasVoiceCommandsOptions {
  canvasId: string;
  onCommandComplete?: (result: VoiceCommandResult) => void;
  onError?: (error: string) => void;
}

export const useCanvasVoiceCommands = ({
  canvasId,
  onCommandComplete,
  onError
}: UseCanvasVoiceCommandsOptions) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  // const mediaRecorder = useRef<MediaRecorder | null>(null);
  // const audioChunks = useRef<Blob[]>([]);
  const recognition = useRef<any>(null);
  
  // Get canvas state from store
  const {
    nodes,
    // edges,
    selectedElements,
    addNode,
    addEdge,
    updateNode,
    deleteNode,
    setNodes
  } = useStrategicCanvasStore();
  
  // Initialize speech recognition
  const initializeSpeechRecognition = useCallback(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = true;
      recognition.current.lang = 'en-US';
      
      recognition.current.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscript(finalTranscript || interimTranscript);
        
        if (finalTranscript) {
          // Process the final transcript
          processVoiceCommand(finalTranscript);
        }
      };
      
      recognition.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        if (onError) {
          onError(`Speech recognition error: ${event.error}`);
        }
      };
      
      recognition.current.onend = () => {
        setIsRecording(false);
      };
      
      return true;
    }
    return false;
  }, []);
  
  // Process voice command via API
  const processVoiceCommand = useCallback(async (command: string) => {
    setIsProcessing(true);
    
    try {
      // Prepare current nodes data for context
      const currentNodes = nodes.map(node => ({
        id: (node as any).id,
        data: {
          label: (node as any).data.title || '' // Use title instead of non-existent label
        },
        position: (node as any).position,
        type: (node as any).type
      }));
      
      // Get selected node IDs
      const selectedNodeIds = selectedElements.nodes.map((node: any) => node.id);
      
      // Send to API
      const response = await axios.post(
        `${API_BASE_URL}/api/canvas-ai/voice-command`,
        {
          canvas_id: canvasId,
          voice_command: command,
          current_nodes: currentNodes,
          selected_node_ids: selectedNodeIds
        }
      );
      
      const result: VoiceCommandResult = response.data;
      
      // Execute the command based on the action
      if (result.success) {
        await executeCanvasAction(result);
      }
      
      // Notify completion
      if (onCommandComplete) {
        onCommandComplete(result);
      }
      
    } catch (error) {
      console.error('Error processing voice command:', error);
      if (onError) {
        onError('Failed to process voice command');
      }
    } finally {
      setIsProcessing(false);
      setTranscript('');
    }
  }, [canvasId, nodes, selectedElements, onCommandComplete, onError]);
  
  // Execute canvas action based on API response
  const executeCanvasAction = useCallback(async (result: VoiceCommandResult) => {
    if (!result.success) return;
    
    switch (result.action) {
      case 'add_node':
        if (result.node) {
          // Use proper node type structure
          addNode(
            result.node.type || 'basic',
            result.node.position || { x: 0, y: 0 },
            {
              title: result.node.title,
              content: result.node.content || ''
            }
          );
        }
        break;
      
      case 'connect_nodes':
        if (result.edge) {
          // Use the connection object format required by addEdge
          addEdge(
            {
              source: result.edge.source,
              target: result.edge.target,
              sourceHandle: null,
              targetHandle: null
            },
            result.edge.label
          );
        }
        break;
      
      case 'delete_node':
        if (result.node_ids && deleteNode) {
          result.node_ids.forEach(id => deleteNode(id));
        } else if (result.node_title) {
          // Find node by title and delete
          const nodeToDelete = nodes.find(n => 
            (n as any).data.title?.toLowerCase() === result.node_title?.toLowerCase()
          );
          if (nodeToDelete && deleteNode) {
            deleteNode((nodeToDelete as any).id);
          }
        }
        break;
      
      case 'move_node':
        if (result.node_title && result.position) {
          const nodeToMove = nodes.find(n => 
            (n as any).data.title?.toLowerCase() === result.node_title?.toLowerCase()
          );
          if (nodeToMove && setNodes) {
            const updatedNodes = nodes.map(n => {
              if ((n as any).id === (nodeToMove as any).id) {
                return {
                  ...n,
                  position: result.position!
                };
              }
              return n;
            });
            setNodes(updatedNodes);
          }
        }
        break;
      
      case 'update_node':
        if (result.old_title && result.new_title) {
          const nodeToUpdate = nodes.find(n => 
            (n as any).data.title?.toLowerCase() === result.old_title?.toLowerCase()
          );
          if (nodeToUpdate) {
            updateNode((nodeToUpdate as any).id, {
              // Use proper structure based on NodeData type
              title: result.new_title,
              content: (nodeToUpdate as any).data.content || ''
            });
          }
        }
        break;
      
      case 'group_nodes':
        // Group nodes functionality would be implemented here
        console.log('Group nodes:', result.node_titles);
        break;
      
      case 'analyze_canvas':
        // Analysis results are in result.analysis
        console.log('Canvas analysis:', result.analysis);
        break;
    }
    
    // Handle compound commands
    if (result.compound && result.results) {
      for (const subResult of result.results) {
        await executeCanvasAction(subResult);
      }
    }
  }, [nodes, addNode, addEdge, deleteNode, updateNode, setNodes]);
  
  // Start voice recording
  const startVoiceCommand = useCallback(() => {
    if (!recognition.current) {
      const initialized = initializeSpeechRecognition();
      if (!initialized) {
        if (onError) {
          onError('Speech recognition not supported in this browser');
        }
        return;
      }
    }
    
    setIsRecording(true);
    setTranscript('');
    recognition.current.start();
  }, [initializeSpeechRecognition, onError]);
  
  // Stop voice recording
  const stopVoiceCommand = useCallback(() => {
    if (recognition.current && isRecording) {
      recognition.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);
  
  // Cancel voice recording
  const cancelVoiceCommand = useCallback(() => {
    if (recognition.current && isRecording) {
      recognition.current.abort();
      setIsRecording(false);
      setTranscript('');
    }
  }, [isRecording]);
  
  // Process a text command directly (without voice)
  const processTextCommand = useCallback(async (command: string) => {
    await processVoiceCommand(command);
  }, [processVoiceCommand]);
  
  return {
    isRecording,
    isProcessing,
    transcript,
    startVoiceCommand,
    stopVoiceCommand,
    cancelVoiceCommand,
    processTextCommand
  };
};

export default useCanvasVoiceCommands;