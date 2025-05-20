import { create } from 'zustand';
import objectiveDataService, {
  KPI,
  KPICreate,
  DataSet,
  DataSetCreate
} from '../services/objectiveDataService';

interface ObjectiveDataState {
  kpis: KPI[];
  datasets: DataSet[];
  selectedDataset: DataSet | null;
  isLoading: boolean;
  uploading: boolean;
  deleting: boolean;
  uploadProgress: number;
  error: string | null;
  loadKPIs: () => Promise<void>;
  loadDatasets: () => Promise<void>;
  getDataset: (id: string) => Promise<void>;
  createKPI: (data: KPICreate) => Promise<void>;
  uploadDataset: (file: File, name: string, category: string, description?: string) => Promise<void>;
  deleteDataset: (id: string) => Promise<void>;
}

export const useObjectiveDataStore = create<ObjectiveDataState>((set) => ({
  kpis: [],
  datasets: [],
  selectedDataset: null,
  isLoading: false,
  uploading: false,
  deleting: false,
  uploadProgress: 0,
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

  getDataset: async (id: string) => {
    try {
      set({ isLoading: true, error: null });
      const dataset = await objectiveDataService.getDataset(id);
      set({ selectedDataset: dataset, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : 'Failed to load dataset' });
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
      set({ uploading: true, uploadProgress: 0, error: null });
      const dataset = await objectiveDataService.uploadDataset(
        file,
        name,
        category,
        description,
        (e) => {
          const total = e.total ?? 0;
          const loaded = e.loaded ?? 0;
          const progress = total ? Math.round((loaded / total) * 100) : 0;
          set({ uploadProgress: progress });
        }
      );
      set((state) => ({ datasets: [dataset, ...state.datasets], uploading: false, uploadProgress: 100 }));
    } catch (err) {
      set({ uploading: false, error: err instanceof Error ? err.message : 'Failed to upload dataset' });
    }
  },

  deleteDataset: async (id: string) => {
    try {
      set({ deleting: true, error: null });
      await objectiveDataService.deleteDataset(id);
      set((state) => ({ datasets: state.datasets.filter(d => d.id !== id), deleting: false }));
    } catch (err) {
      set({ deleting: false, error: err instanceof Error ? err.message : 'Failed to delete dataset' });
    }
  }
}));

export default useObjectiveDataStore;
