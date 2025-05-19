import { create } from 'zustand';
import { logService, LogEntry, LogEntryCreate, LogEntryUpdate } from '../services/logService';

// Define the store state interface
interface LogState {
  // Data
  entries: LogEntry[];
  currentEntry: LogEntry | null;
  isLoading: boolean;
  error: string | null;
  
  // Filters
  filters: {
    entryType: string | null;
    tag: string | null;
    searchQuery: string;
  };
  pagination: {
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  
  // Voice recording
  isRecording: boolean;
  recordingError: string | null;
  isTranscribing: boolean;
  voiceStreamId: string | null;
  
  // Actions
  loadEntries: (userId: string, refresh?: boolean) => Promise<void>;
  loadMoreEntries: (userId: string) => Promise<void>;
  getEntry: (entryId: string) => Promise<void>;
  createEntry: (userId: string, entryData: LogEntryCreate) => Promise<LogEntry>;
  updateEntry: (entryId: string, entryData: LogEntryUpdate) => Promise<void>;
  deleteEntry: (entryId: string) => Promise<void>;
  
  // Filter actions
  setEntryTypeFilter: (entryType: string | null) => void;
  setTagFilter: (tag: string | null) => void;
  setSearchQuery: (query: string) => void;
  clearFilters: () => void;
  
  // Voice recording actions
  startRecording: () => void;
  stopRecording: (userId: string) => Promise<LogEntry | null>;
  cancelRecording: () => void;
  
  // Voice streaming actions
  startVoiceStream: (userId: string) => Promise<string | null>;
  stopVoiceStream: (userId: string) => Promise<LogEntry | null>;
  cancelVoiceStream: () => Promise<void>;
  
  // Reset state
  reset: () => void;
}

// Create the store
export const useLogStore = create<LogState>((set, get) => ({
  // Initial data state
  entries: [],
  currentEntry: null,
  isLoading: false,
  error: null,
  
  // Initial filter state
  filters: {
    entryType: null,
    tag: null,
    searchQuery: '',
  },
  pagination: {
    limit: 10,
    offset: 0,
    hasMore: true,
  },
  
  // Voice recording state
  isRecording: false,
  recordingError: null,
  isTranscribing: false,
  voiceStreamId: null,
  
  // Load log entries
  loadEntries: async (userId: string, refresh = false) => {
    try {
      set({ isLoading: true, error: null });
      
      const { filters, pagination } = get();
      
      // Reset pagination if refreshing
      const offset = refresh ? 0 : pagination.offset;
      
      const entries = await logService.listLogEntries(
        userId,
        pagination.limit,
        offset,
        filters.entryType || undefined,
        filters.tag || undefined
      );
      
      // Update state
      set((state) => ({
        entries: refresh ? entries : [...state.entries, ...entries],
        isLoading: false,
        pagination: {
          ...state.pagination,
          offset: offset + entries.length,
          hasMore: entries.length === state.pagination.limit,
        },
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to load log entries'
      });
    }
  },
  
  // Load more entries (pagination)
  loadMoreEntries: async (userId: string) => {
    const { pagination, isLoading } = get();
    
    // Don't load if already loading or no more entries
    if (isLoading || !pagination.hasMore) return;
    
    await get().loadEntries(userId, false);
  },
  
  // Get a single entry
  getEntry: async (entryId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const entry = await logService.getLogEntry(entryId);
      
      set({ currentEntry: entry, isLoading: false });
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to load log entry'
      });
    }
  },
  
  // Create a new entry
  createEntry: async (userId: string, entryData: LogEntryCreate) => {
    try {
      set({ isLoading: true, error: null });
      
      const entry = await logService.createLogEntry(userId, entryData);
      
      // Add to entries list
      set((state) => ({
        entries: [entry, ...state.entries],
        currentEntry: entry,
        isLoading: false,
      }));
      
      return entry;
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to create log entry'
      });
      throw error;
    }
  },
  
  // Update an entry
  updateEntry: async (entryId: string, entryData: LogEntryUpdate) => {
    try {
      set({ isLoading: true, error: null });
      
      const updatedEntry = await logService.updateLogEntry(entryId, entryData);
      
      // Update in entries list and currentEntry if needed
      set((state) => ({
        entries: state.entries.map(e => e.id === entryId ? updatedEntry : e),
        currentEntry: state.currentEntry?.id === entryId ? updatedEntry : state.currentEntry,
        isLoading: false,
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to update log entry'
      });
    }
  },
  
  // Delete an entry
  deleteEntry: async (entryId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      await logService.deleteLogEntry(entryId);
      
      // Remove from entries list and reset currentEntry if needed
      set((state) => ({
        entries: state.entries.filter(e => e.id !== entryId),
        currentEntry: state.currentEntry?.id === entryId ? null : state.currentEntry,
        isLoading: false,
      }));
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to delete log entry'
      });
    }
  },
  
  // Filter functions
  setEntryTypeFilter: (entryType: string | null) => {
    set((state) => ({
      filters: { ...state.filters, entryType },
      pagination: { ...state.pagination, offset: 0 }, // Reset pagination
    }));
  },
  
  setTagFilter: (tag: string | null) => {
    set((state) => ({
      filters: { ...state.filters, tag },
      pagination: { ...state.pagination, offset: 0 }, // Reset pagination
    }));
  },
  
  setSearchQuery: (query: string) => {
    set((state) => ({
      filters: { ...state.filters, searchQuery: query },
    }));
  },
  
  clearFilters: () => {
    set((state) => ({
      filters: {
        entryType: null,
        tag: null,
        searchQuery: '',
      },
      pagination: { ...state.pagination, offset: 0 }, // Reset pagination
    }));
  },
  
  // Voice recording functions using MediaRecorder
  startRecording: () => {
    try {
      set({ 
        isRecording: true, 
        recordingError: null 
      });
      
      // Note: Actual recording is handled in a React hook outside the store
      // to manage MediaRecorder lifecycle properly
    } catch (error) {
      set({ 
        isRecording: false, 
        recordingError: error instanceof Error ? error.message : 'Failed to start recording'
      });
    }
  },
  
  stopRecording: async (userId: string) => {
    try {
      set({ 
        isRecording: false, 
        isTranscribing: true 
      });
      
      // Note: The actual audio blob will be provided by the React hook
      // For now, this is a placeholder function
      // The hook would call logService.createVoiceLogEntry(userId, audioBlob)
      
      set({ isTranscribing: false });
      return null;
    } catch (error) {
      set({ 
        isTranscribing: false, 
        recordingError: error instanceof Error ? error.message : 'Failed to transcribe recording'
      });
      return null;
    }
  },
  
  cancelRecording: () => {
    set({ 
      isRecording: false, 
      recordingError: null 
    });
    
    // Note: Actual cancellation is handled in a React hook
  },
  
  // Voice streaming functions
  startVoiceStream: async (userId: string) => {
    try {
      set({ isRecording: true, recordingError: null });
      
      const response = await logService.startVoiceStream(userId);
      
      if (response.streamId) {
        set({ voiceStreamId: response.streamId });
        return response.streamId;
      } else {
        throw new Error('Failed to get stream ID');
      }
    } catch (error) {
      set({ 
        isRecording: false, 
        recordingError: error instanceof Error ? error.message : 'Failed to start voice stream'
      });
      return null;
    }
  },
  
  stopVoiceStream: async (userId: string) => {
    const { voiceStreamId } = get();
    
    if (!voiceStreamId) {
      set({ isRecording: false });
      return null;
    }
    
    try {
      set({ isTranscribing: true });
      
      // Send final chunk
      const response = await logService.sendAudioChunk(voiceStreamId, '', true, userId);
      
      set({ 
        isRecording: false, 
        isTranscribing: false, 
        voiceStreamId: null 
      });
      
      // If an entry was created, get it and add to entries
      if (response.entryId) {
        const entry = await logService.getLogEntry(response.entryId);
        
        set((state) => ({
          entries: [entry, ...state.entries],
          currentEntry: entry,
        }));
        
        return entry;
      }
      
      return null;
    } catch (error) {
      set({ 
        isRecording: false, 
        isTranscribing: false, 
        voiceStreamId: null,
        recordingError: error instanceof Error ? error.message : 'Failed to stop voice stream'
      });
      return null;
    }
  },
  
  cancelVoiceStream: async () => {
    const { voiceStreamId } = get();
    
    if (voiceStreamId) {
      try {
        await logService.cancelVoiceStream(voiceStreamId);
      } catch (error) {
        // Ignore errors when canceling
      }
    }
    
    set({ 
      isRecording: false, 
      isTranscribing: false, 
      voiceStreamId: null,
      recordingError: null
    });
  },
  
  // Reset state
  reset: () => {
    set({
      entries: [],
      currentEntry: null,
      isLoading: false,
      error: null,
      filters: {
        entryType: null,
        tag: null,
        searchQuery: '',
      },
      pagination: {
        limit: 10,
        offset: 0,
        hasMore: true,
      },
      isRecording: false,
      recordingError: null,
      isTranscribing: false,
      voiceStreamId: null,
    });
  },
}));

export default useLogStore;