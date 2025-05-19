import axios from 'axios';

// Define the base URL for the API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Types
export interface LogEntry {
  id: string;
  content: string;
  entry_type: string;
  tags: LogEntryTag[];
  sentiment?: number;
  ai_generated_tags: string[];
  ai_summary?: string;
  ai_insights?: string[];
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface LogEntryTag {
  id: string;
  name: string;
  type: string;
  reference_id?: string;
}

export interface LogEntryCreate {
  content: string;
  entry_type?: string;
  tags?: string[];
}

export interface LogEntryUpdate {
  content?: string;
  entry_type?: string;
  tags?: string[];
}

export interface VoiceStreamResponse {
  streamId?: string;
  status: string;
  text?: string;
  entryId?: string;
  error?: string;
}

// API Functions
export const logService = {
  /**
   * Create a new log entry
   */
  createLogEntry: async (userId: string, entryData: LogEntryCreate): Promise<LogEntry> => {
    const response = await axios.post(`${API_BASE_URL}/api/subjective/log`, entryData, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Get a log entry by ID
   */
  getLogEntry: async (entryId: string): Promise<LogEntry> => {
    const response = await axios.get(`${API_BASE_URL}/api/subjective/log/${entryId}`);
    return response.data;
  },

  /**
   * List log entries with optional filtering
   */
  listLogEntries: async (
    userId: string, 
    limit: number = 20, 
    offset: number = 0, 
    entry_type?: string, 
    tag?: string
  ): Promise<LogEntry[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/subjective/log`, {
      params: {
        user_id: userId,
        limit,
        offset,
        entry_type,
        tag
      }
    });
    return response.data;
  },

  /**
   * Update a log entry
   */
  updateLogEntry: async (entryId: string, entryData: LogEntryUpdate): Promise<LogEntry> => {
    const response = await axios.put(`${API_BASE_URL}/api/subjective/log/${entryId}`, entryData);
    return response.data;
  },

  /**
   * Delete a log entry
   */
  deleteLogEntry: async (entryId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/subjective/log/${entryId}`);
  },

  /**
   * Upload a voice recording file to create a log entry
   */
  createVoiceLogEntry: async (userId: string, audioBlob: Blob): Promise<LogEntry> => {
    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/subjective/log/voice`,
      formData,
      {
        params: { user_id: userId },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  },

  /**
   * Start a voice streaming session for real-time transcription
   */
  startVoiceStream: async (
    userId: string, 
    audioConfig = { sampleRate: 16000, bitsPerSample: 16, channels: 1 }
  ): Promise<VoiceStreamResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/subjective/voice-note/stream/start`,
      audioConfig,
      {
        params: { user_id: userId }
      }
    );
    
    return response.data;
  },

  /**
   * Send an audio chunk to an active streaming session
   */
  sendAudioChunk: async (
    streamId: string, 
    audioChunk: string, 
    isFinal: boolean = false, 
    userId?: string
  ): Promise<VoiceStreamResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/subjective/voice-note/stream/chunk`,
      {
        streamId,
        audioChunk,
        isFinal
      },
      {
        params: { userId }
      }
    );
    
    return response.data;
  },

  /**
   * Cancel an active voice streaming session
   */
  cancelVoiceStream: async (streamId: string): Promise<VoiceStreamResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/subjective/voice-note/stream/cancel`,
      { streamId }
    );
    
    return response.data;
  },

  /**
   * Create a WebSocket connection for voice streaming
   * This is an alternative to the HTTP-based approach and offers lower latency
   */
  createVoiceStreamWebSocket: (
    userId: string, 
    audioConfig = { sampleRate: 16000, bitsPerSample: 16, channels: 1 }
  ): WebSocket => {
    // Create WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = API_BASE_URL.replace('http://', '').replace('https://', '');
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/api/subjective/voice-note/stream/ws`);
    
    // Set up basic event handlers
    ws.onopen = () => {
      // Send initialization data when connection is established
      ws.send(JSON.stringify({
        userId,
        ...audioConfig
      }));
    };
    
    return ws;
  }
};

export default logService;