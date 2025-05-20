import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

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
  data_format?: string;
  import_date?: string;
  metadata?: DataSetMetadata;
}

export const objectiveDataService = {
  // KPI endpoints
  createKPI: async (kpi: KPICreate): Promise<KPI> => {
    const res = await axios.post(`${API_BASE_URL}/api/objective/kpis`, kpi);
    return res.data;
  },

  getKPI: async (id: string): Promise<KPI> => {
    const res = await axios.get(`${API_BASE_URL}/api/objective/kpis/${id}`);
    return res.data;
  },

  listKPIs: async (
    limit = 20,
    offset = 0,
    category?: string,
    goalId?: string
  ): Promise<KPI[]> => {
    const res = await axios.get(`${API_BASE_URL}/api/objective/kpis`, {
      params: { limit, offset, category, goal_id: goalId }
    });
    return res.data;
  },

  updateKPI: async (id: string, data: Partial<KPICreate>): Promise<KPI> => {
    const res = await axios.put(`${API_BASE_URL}/api/objective/kpis/${id}`, data);
    return res.data;
  },

  deleteKPI: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/objective/kpis/${id}`);
  },

  // Dataset endpoints
  listDatasets: async (
    limit = 20,
    offset = 0,
    category?: string,
    sourceType?: string
  ): Promise<DataSet[]> => {
    const res = await axios.get(`${API_BASE_URL}/api/objective/datasets`, {
      params: { limit, offset, category, source_type: sourceType }
    });
    return res.data;
  },

  uploadDataset: async (
    file: File,
    name: string,
    category: string,
    description?: string
  ): Promise<DataSet> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await axios.post(`${API_BASE_URL}/api/objective/datasets/upload`, formData, {
      params: { name, description, category }
    });
    return res.data;
  },

  getDataset: async (id: string): Promise<DataSet> => {
    const res = await axios.get(`${API_BASE_URL}/api/objective/datasets/${id}`);
    return res.data;
  },

  updateDataset: async (id: string, data: Partial<DataSet>): Promise<DataSet> => {
    const res = await axios.put(`${API_BASE_URL}/api/objective/datasets/${id}`, data);
    return res.data;
  },

  deleteDataset: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/objective/datasets/${id}`);
  }
};

export default objectiveDataService;
