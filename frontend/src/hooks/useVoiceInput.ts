import { useState, useRef, useCallback, useEffect } from 'react';
import { logService, LogEntry } from '../services/logService';
import useLogStore from '../store/logStore';

interface UseVoiceInputOptions {
  userId: string;
  useWebSocket?: boolean;
  audioConfig?: {
    sampleRate: number;
    bitsPerSample: number;
    channels: number;
  };
  chunkDuration?: number; // Duration of each audio chunk in ms
}

interface UseVoiceInputResult {
  isRecording: boolean;
  isTranscribing: boolean;
  recordingError: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<LogEntry | null>;
  cancelRecording: () => void;
}

/**
 * Hook for handling voice input recording and streaming
 */
export const useVoiceInput = ({
  userId,
  useWebSocket = true,
  audioConfig = {
    sampleRate: 16000,
    bitsPerSample: 16,
    channels: 1
  },
  chunkDuration = 1000 // 1 second chunks
}: UseVoiceInputOptions): UseVoiceInputResult => {
  // Get state from log store
  const { 
    isRecording, 
    isTranscribing, 
    recordingError, 
    voiceStreamId,
    startVoiceStream,
    stopVoiceStream,
    cancelVoiceStream
  } = useLogStore();
  
  // Refs to hold media objects
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const webSocket = useRef<WebSocket | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const chunkInterval = useRef<number | null>(null);
  
  // Clean up function
  const cleanupMediaRecording = useCallback(() => {
    // Clear interval
    if (chunkInterval.current) {
      clearInterval(chunkInterval.current);
      chunkInterval.current = null;
    }
    
    // Clear audio chunks
    audioChunks.current = [];
    
    // Stop MediaRecorder if running
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
    }
    
    // Close WebSocket if open
    if (webSocket.current && webSocket.current.readyState === WebSocket.OPEN) {
      webSocket.current.close();
      webSocket.current = null;
    }
    
    // Close AudioContext if open
    if (audioContext.current && audioContext.current.state !== 'closed') {
      audioContext.current.close();
      audioContext.current = null;
    }
  }, []);
  
  // Clean up when component unmounts
  useEffect(() => {
    return () => {
      cleanupMediaRecording();
    };
  }, [cleanupMediaRecording]);
  
  // Start recording
  const startRecording = useCallback(async () => {
    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Initialize AudioContext
      audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: audioConfig.sampleRate
      });
      
      // Reset audio chunks
      audioChunks.current = [];
      
      if (useWebSocket) {
        // Initialize WebSocket
        webSocket.current = logService.createVoiceStreamWebSocket(userId, audioConfig);
        
        // Set up WebSocket event handlers
        webSocket.current.onmessage = (event) => {
          const response = JSON.parse(event.data);
          console.log('WebSocket response:', response);
          
          // Handle errors
          if (response.error) {
            console.error('WebSocket error:', response.error);
          }
        };
        
        webSocket.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          cleanupMediaRecording();
        };
        
        webSocket.current.onclose = () => {
          console.log('WebSocket closed');
        };
      } else {
        // Start voice stream via HTTP API
        const streamId = await startVoiceStream(userId);
        if (!streamId) {
          throw new Error('Failed to start voice stream');
        }
      }
      
      // Create MediaRecorder
      mediaRecorder.current = new MediaRecorder(stream);
      
      // Set up MediaRecorder event handlers
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };
      
      // Start recording
      mediaRecorder.current.start(chunkDuration);
      
      // Set up chunk sending interval for HTTP API
      if (!useWebSocket && voiceStreamId) {
        chunkInterval.current = window.setInterval(async () => {
          if (audioChunks.current.length > 0) {
            const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
            audioChunks.current = [];
            
            // Convert blob to base64
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = async () => {
              const base64data = reader.result as string;
              // Remove data URL prefix
              const base64Audio = base64data.split(',')[1];
              
              // Send chunk to server
              if (voiceStreamId) {
                try {
                  await logService.sendAudioChunk(voiceStreamId, base64Audio);
                } catch (error) {
                  console.error('Error sending audio chunk:', error);
                }
              }
            };
          }
        }, chunkDuration);
      }
    } catch (error) {
      console.error('Error starting recording:', error);
      cleanupMediaRecording();
      throw error;
    }
  }, [userId, useWebSocket, audioConfig, chunkDuration, voiceStreamId, startVoiceStream, cleanupMediaRecording]);
  
  // Stop recording
  const stopRecording = useCallback(async (): Promise<LogEntry | null> => {
    try {
      if (useWebSocket) {
        // Tell server we're done via WebSocket
        if (webSocket.current && webSocket.current.readyState === WebSocket.OPEN) {
          // Send stop command
          webSocket.current.send(JSON.stringify({ command: 'stop' }));
          
          // Wait for final response
          const entry = await new Promise<LogEntry | null>((resolve) => {
            if (!webSocket.current) {
              resolve(null);
              return;
            }
            
            // Set up one-time message handler for the final result
            const messageHandler = (event: MessageEvent) => {
              const response = JSON.parse(event.data);
              
              // If we got an entry ID, fetch the entry
              if (response.entryId) {
                logService.getLogEntry(response.entryId)
                  .then(entry => resolve(entry))
                  .catch(() => resolve(null));
              } else {
                resolve(null);
              }
              
              // Remove the handler
              if (webSocket.current) {
                webSocket.current.removeEventListener('message', messageHandler);
              }
            };
            
            // Add the handler
            webSocket.current.addEventListener('message', messageHandler);
            
            // Set a timeout in case we don't get a response
            setTimeout(() => {
              if (webSocket.current) {
                webSocket.current.removeEventListener('message', messageHandler);
              }
              resolve(null);
            }, 10000); // 10 second timeout
          });
          
          // Clean up
          cleanupMediaRecording();
          
          return entry;
        } else {
          cleanupMediaRecording();
          return null;
        }
      } else {
        // Stop MediaRecorder
        if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
          mediaRecorder.current.stop();
          
          // Wait for the final chunks
          await new Promise<void>((resolve) => {
            if (!mediaRecorder.current) {
              resolve();
              return;
            }
            
            mediaRecorder.current.onstop = () => {
              resolve();
            };
            
            // Set a timeout in case onstop doesn't fire
            setTimeout(resolve, 1000);
          });
        }
        
        // Clean up interval
        if (chunkInterval.current) {
          clearInterval(chunkInterval.current);
          chunkInterval.current = null;
        }
        
        // Use stored stream ID to stop the stream and get the final result
        const entry = await stopVoiceStream(userId);
        
        // Clean up
        cleanupMediaRecording();
        
        return entry;
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      cleanupMediaRecording();
      return null;
    }
  }, [useWebSocket, userId, stopVoiceStream, cleanupMediaRecording]);
  
  // Cancel recording
  const cancelRecording = useCallback(() => {
    try {
      if (useWebSocket) {
        // Tell server to cancel via WebSocket
        if (webSocket.current && webSocket.current.readyState === WebSocket.OPEN) {
          webSocket.current.send(JSON.stringify({ command: 'cancel' }));
        }
      } else {
        // Cancel voice stream via HTTP API
        cancelVoiceStream();
      }
      
      // Clean up
      cleanupMediaRecording();
    } catch (error) {
      console.error('Error canceling recording:', error);
    }
  }, [useWebSocket, cancelVoiceStream, cleanupMediaRecording]);
  
  return {
    isRecording,
    isTranscribing,
    recordingError,
    startRecording,
    stopRecording,
    cancelRecording
  };
};

export default useVoiceInput;