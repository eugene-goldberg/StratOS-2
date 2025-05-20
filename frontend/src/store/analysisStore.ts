import { create } from 'zustand';
import analysisService, { SWOTAnalysis, SWOTItemCreate, SOLinkage } from '../services/analysisService';

interface AnalysisState {
  activeSwot: SWOTAnalysis | null;
  linkages: SOLinkage[];
  isLoading: boolean;
  error: string | null;

  createGuidedSwot: (title: string, description?: string) => Promise<void>;
  addSwotItem: (analysisId: string, item: SWOTItemCreate) => Promise<void>;
  generateTows: (analysisId: string) => Promise<void>;
  discoverLinkages: (userId: string, topic?: string) => Promise<void>;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  activeSwot: null,
  linkages: [],
  isLoading: false,
  error: null,

  createGuidedSwot: async (title: string, description?: string) => {
    try {
      set({ isLoading: true, error: null });
      const analysis = await analysisService.createAIGuidedSwot(title, description);
      set({ activeSwot: analysis, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to create SWOT' });
    }
  },

  addSwotItem: async (analysisId: string, item: SWOTItemCreate) => {
    try {
      set({ isLoading: true, error: null });
      const newItem = await analysisService.addSwotItem(analysisId, item);
      set((state) => ({
        activeSwot: state.activeSwot && state.activeSwot.id === analysisId ? { ...state.activeSwot, items: [...state.activeSwot.items, newItem] } : state.activeSwot,
        isLoading: false
      }));
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to add SWOT item' });
    }
  },

  generateTows: async (analysisId: string) => {
    try {
      set({ isLoading: true, error: null });
      const strategies = await analysisService.generateTowsStrategies(analysisId);
      set((state) => ({
        activeSwot: state.activeSwot && state.activeSwot.id === analysisId ? { ...state.activeSwot, tows_strategies: strategies } : state.activeSwot,
        isLoading: false
      }));
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to generate TOWS' });
    }
  },

  discoverLinkages: async (userId: string, topic?: string) => {
    try {
      set({ isLoading: true, error: null });
      const data = await analysisService.discoverSOLinkages({ userId, topicContext: topic });
      set({ linkages: data, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to discover linkages' });
    }
  }
}));

export default useAnalysisStore;
