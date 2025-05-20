import { create } from 'zustand';
import northStarService, { StrategicGoal } from '../services/northStarService';

interface NorthStarState {
  strategicGoals: StrategicGoal[];
  isLoading: boolean;
  error: string | null;
  loadStrategicGoals: () => Promise<void>;
}

export const useNorthStarStore = create<NorthStarState>((set) => ({
  strategicGoals: [],
  isLoading: false,
  error: null,
  loadStrategicGoals: async () => {
    set({ isLoading: true, error: null });
    try {
      const goals = await northStarService.listStrategicGoals();
      set({ strategicGoals: goals, isLoading: false });
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load goals'
      });
    }
  }
}));

export default useNorthStarStore;
