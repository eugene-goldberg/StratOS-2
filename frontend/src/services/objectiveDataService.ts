import api from './apiService';


export interface KPI {
  id: string;
  name: string;
  description?: string;
  category: string;
  current_value: number;
  target_value?: number;
  unit?: string;
  trend?: string;
  created_at?: string;
}

export interface KPICreate {
  name: string;
  description?: string;
  category: string;
  current_value: number;
  target_value?: number;
  unit?: string;
}

export interface DataSetMetadata {
  processing_status?: string;
  size_bytes?: number;
  [key: string]: any;
}

export interface DataSet {
  id: string;
  name: string;
  description?: string;
  category: string;
  source_type?: string;
  data_format?: string;
  import_date?: string;
  metadata?: DataSetMetadata;
  created_at?: string;
}

export interface DataSetCreate {
  name: string;
  description?: string;
  category: string;
  source_type?: string;
  data_format?: string;
}

export interface DataPoint {
  id: string;
  dataset_id: string;
  timestamp: string;
  dimension: Record<string, string>;
  metrics: Record<string, number | string>;
}

export interface DataPointCreate {
  dataset_id: string;
  timestamp: string;
  dimension: Record<string, string>;
  metrics: Record<string, number | string>;
}

export const objectiveDataService = {
  // KPI endpoints
  createKPI: async (kpi: KPICreate): Promise<KPI> => {
    const res = await api.post('/api/objective/kpis', kpi);
    return res.data;
  },

  getKPI: async (id: string): Promise<KPI> => {
    const res = await api.get(`/api/objective/kpis/${id}`);
    return res.data;
  },

  listKPIs: async (
    limit = 20,
    offset = 0,
    category?: string,
    goalId?: string
  ): Promise<KPI[]> => {
    const res = await api.get('/api/objective/kpis', {
      params: { limit, offset, category, goal_id: goalId }
    });
    return res.data;
  },

  updateKPI: async (id: string, data: Partial<KPICreate>): Promise<KPI> => {
    const res = await api.put(`/api/objective/kpis/${id}`, data);
    return res.data;
  },

  deleteKPI: async (id: string): Promise<void> => {
    await api.delete(`/api/objective/kpis/${id}`);
  },

  // Dataset endpoints
  listDatasets: async (
    limit = 20,
    offset = 0,
    category?: string,
    sourceType?: string
  ): Promise<DataSet[]> => {
    const res = await api.get('/api/objective/datasets', {
      params: { limit, offset, category, source_type: sourceType }
    });
    return res.data;
  },

  createDataset: async (data: DataSetCreate): Promise<DataSet> => {
    const res = await api.post('/api/objective/datasets', data);
    return res.data;
  },

  uploadDataset: async (
    file: File,
    name: string,
    category: string,
    description?: string,
    onUploadProgress?: (progressEvent: ProgressEvent) => void
  ): Promise<DataSet> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await api.post('/api/objective/datasets/upload', formData, {
      params: { name, description, category },
      onUploadProgress
    });
    return res.data;
  },

  getDataset: async (id: string): Promise<DataSet> => {
    const res = await api.get(`/api/objective/datasets/${id}`);
    return res.data;
  },

  updateDataset: async (id: string, data: Partial<DataSet>): Promise<DataSet> => {
    const res = await api.put(`/api/objective/datasets/${id}`, data);
    return res.data;
  },

  deleteDataset: async (id: string): Promise<void> => {
    await api.delete(`/api/objective/datasets/${id}`);
  },

  // Data point endpoints
  listDataPoints: async (
    datasetId: string,
    limit = 100,
    offset = 0
  ): Promise<DataPoint[]> => {
    const res = await api.get('/api/objective/datapoints', {
      params: { dataset_id: datasetId, limit, offset }
    });
    return res.data;
  },

  createDataPoint: async (data: DataPointCreate): Promise<DataPoint> => {
    const res = await api.post('/api/objective/datapoints', data);
    return res.data;
  },

  createBatchDataPoints: async (
    datasetId: string,
    datapoints: DataPointCreate[]
  ): Promise<void> => {
    await api.post(`/api/objective/datasets/${datasetId}/batch-datapoints`, datapoints);
  }
};

export default objectiveDataService;
