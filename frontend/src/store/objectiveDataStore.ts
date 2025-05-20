import { create } from 'zustand';
import objectiveDataService, { KPI, KPICreate, DataSet } from '../services/objectiveDataService';

interface ObjectiveDataState {
  kpis: KPI[];
  datasets: DataSet[];
  isLoading: boolean;
  error: string | null;
  loadKPIs: () => Promise<void>;
  loadDatasets: () => Promise<void>;
  createKPI: (data: KPICreate) => Promise<void>;
  uploadDataset: (file: File, name: string, category: string, description?: string) => Promise<void>;
}

export const useObjectiveDataStore = create<ObjectiveDataState>((set) => ({
  kpis: [],
  datasets: [],
  isLoading: false,
  error: null,

  loadKPIs: async () => {
    try {
      set({ isLoading: true, error: null });
      const data = await objectiveDataService.listKPIs();
      set({ kpis: data, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to load KPIs' });
    }
  },

  loadDatasets: async () => {
    try {
      set({ isLoading: true, error: null });
      const data = await objectiveDataService.listDatasets();
      set({ datasets: data, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to load datasets' });
    }
  },

  createKPI: async (data: KPICreate) => {
    try {
      const kpi = await objectiveDataService.createKPI(data);
      set((state) => ({ kpis: [kpi, ...state.kpis] }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to create KPI' });
    }
  },

  uploadDataset: async (file: File, name: string, category: string, description?: string) => {
    try {
      const dataset = await objectiveDataService.uploadDataset(file, name, category, description);
      set((state) => ({ datasets: [dataset, ...state.datasets] }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to upload dataset' });
    }
  }
}));

export default useObjectiveDataStore;
