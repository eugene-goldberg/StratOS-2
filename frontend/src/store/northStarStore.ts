import { create } from 'zustand';
import strategicFoundationService, { NorthStar, NorthStarUpdate } from '../services/strategicFoundationService';

interface NorthStarState {
  data: NorthStar | null;
  isLoading: boolean;
  error: string | null;
  loadNorthStar: () => Promise<void>;
  updateNorthStar: (payload: NorthStarUpdate) => Promise<void>;
}

export const useNorthStarStore = create<NorthStarState>((set) => ({
  data: null,
  isLoading: false,
  error: null,

  loadNorthStar: async () => {
    try {
      set({ isLoading: true, error: null });
      const northStar = await strategicFoundationService.getNorthStar();
      set({ data: northStar, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to load North Star' });
    }
  },

  updateNorthStar: async (payload: NorthStarUpdate) => {
    try {
      set({ isLoading: true, error: null });
      const updated = await strategicFoundationService.updateNorthStar(payload);
      set({ data: updated, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to update North Star' });
    }
  },
}));

export default useNorthStarStore;
