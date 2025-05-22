import { create } from 'zustand';
import northStarService, { 
  NorthStar, 
  StrategicGoal, 
  Value, 
  NorthStarCreate, 
  NorthStarUpdate 
} from '../services/northStarService';

interface NorthStarState {
  northStar: NorthStar | null;
  isLoading: boolean;
  error: string | null;
  
  // North Star operations
  loadNorthStar: () => Promise<void>;
  createNorthStar: (data: NorthStarCreate) => Promise<void>;
  updateNorthStar: (data: NorthStarUpdate) => Promise<void>;
  
  // Strategic Goals operations
  loadStrategicGoals: (hierarchical?: boolean) => Promise<void>;
  createStrategicGoal: (data: Partial<StrategicGoal>) => Promise<void>;
  updateStrategicGoal: (goalId: string, data: Partial<StrategicGoal>) => Promise<void>;
  deleteStrategicGoal: (goalId: string) => Promise<void>;
  
  // Values operations
  createValue: (data: Partial<Value>) => Promise<void>;
  updateValue: (valueId: string, data: Partial<Value>) => Promise<void>;
  deleteValue: (valueId: string) => Promise<void>;
}

export const useNorthStarStore = create<NorthStarState>((set, get) => ({
  northStar: null,
  isLoading: false,
  error: null,
  
  loadNorthStar: async () => {
    set({ isLoading: true, error: null });
    try {
      const northStar = await northStarService.getNorthStar();
      set({ northStar, isLoading: false });
    } catch (err: any) {
      // If North Star doesn't exist, that's ok - user needs to create one
      if (err.response?.status === 404) {
        set({ northStar: null, isLoading: false, error: null });
      } else {
        set({
          isLoading: false,
          error: err.response?.data?.detail || err.message || 'Failed to load North Star'
        });
      }
    }
  },
  
  createNorthStar: async (data: NorthStarCreate) => {
    set({ isLoading: true, error: null });
    try {
      const northStar = await northStarService.createNorthStar(data);
      set({ northStar, isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to create North Star'
      });
      throw err;
    }
  },
  
  updateNorthStar: async (data: NorthStarUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const northStar = await northStarService.updateNorthStar(data);
      set({ northStar, isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to update North Star'
      });
      throw err;
    }
  },
  
  loadStrategicGoals: async (hierarchical: boolean = false) => {
    set({ isLoading: true, error: null });
    try {
      const goals = await northStarService.listStrategicGoals(hierarchical);
      const currentNorthStar = get().northStar;
      if (currentNorthStar) {
        set({
          northStar: { ...currentNorthStar, strategic_goals: goals },
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to load goals'
      });
    }
  },
  
  createStrategicGoal: async (data: Partial<StrategicGoal>) => {
    set({ isLoading: true, error: null });
    try {
      await northStarService.createStrategicGoal(data);
      
      // Reload to get updated hierarchy
      await get().loadNorthStar();
      set({ isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to create goal'
      });
      throw err;
    }
  },
  
  updateStrategicGoal: async (goalId: string, data: Partial<StrategicGoal>) => {
    set({ isLoading: true, error: null });
    try {
      await northStarService.updateStrategicGoal(goalId, data);
      
      // Reload to get updated hierarchy
      await get().loadNorthStar();
      set({ isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to update goal'
      });
      throw err;
    }
  },
  
  deleteStrategicGoal: async (goalId: string) => {
    set({ isLoading: true, error: null });
    try {
      await northStarService.deleteStrategicGoal(goalId);
      
      // Reload to get updated hierarchy
      await get().loadNorthStar();
      set({ isLoading: false });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to delete goal'
      });
      throw err;
    }
  },
  
  createValue: async (data: Partial<Value>) => {
    set({ isLoading: true, error: null });
    try {
      const newValue = await northStarService.createValue(data);
      
      // Update local state
      const currentNorthStar = get().northStar;
      if (currentNorthStar) {
        set({
          northStar: {
            ...currentNorthStar,
            values: [...currentNorthStar.values, newValue]
          },
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to create value'
      });
      throw err;
    }
  },
  
  updateValue: async (valueId: string, data: Partial<Value>) => {
    set({ isLoading: true, error: null });
    try {
      const updatedValue = await northStarService.updateValue(valueId, data);
      
      // Update local state
      const currentNorthStar = get().northStar;
      if (currentNorthStar) {
        set({
          northStar: {
            ...currentNorthStar,
            values: currentNorthStar.values.map(v => 
              v.id === valueId ? updatedValue : v
            )
          },
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to update value'
      });
      throw err;
    }
  },
  
  deleteValue: async (valueId: string) => {
    set({ isLoading: true, error: null });
    try {
      await northStarService.deleteValue(valueId);
      
      // Update local state
      const currentNorthStar = get().northStar;
      if (currentNorthStar) {
        set({
          northStar: {
            ...currentNorthStar,
            values: currentNorthStar.values.filter(v => v.id !== valueId)
          },
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || err.message || 'Failed to delete value'
      });
      throw err;
    }
  }
}));

export default useNorthStarStore;