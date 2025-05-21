import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface Action {
  id: string;
  title: string;
  description?: string;
  status: string;
  owner?: string;
  start_date?: string;
  due_date?: string;
}

export interface ActionCreate {
  title: string;
  description?: string;
  owner?: string;
  start_date?: string;
  due_date?: string;
}

export interface Initiative {
  id: string;
  title: string;
  description: string;
  initiative_type: string;
  status: string;
  linked_strategic_goal?: string;
  owner?: string;
  start_date?: string;
  end_date?: string;
  alignmentScore?: number;
  progress?: number;
  actions: Action[];
  risks?: number;
}

export interface InitiativeCreate {
  title: string;
  description: string;
  initiative_type: string;
  linked_strategic_goal?: string;
  owner?: string;
  start_date?: string;
  end_date?: string;
}

export interface StrategicPlan {
  id: string;
  title: string;
  description?: string;
  status: string;
  initiatives: Initiative[];
  alignmentScore?: number;
  progress?: number;
}

const planningService = {
  listPlans: async (): Promise<StrategicPlan[]> => {
    const res = await axios.get(`${API_BASE_URL}/api/planning/plans`);
    return res.data;
  },

  createInitiative: async (planId: string, data: InitiativeCreate): Promise<Initiative> => {
    const res = await axios.post(`${API_BASE_URL}/api/planning/plans/${planId}/initiatives`, data);
    return res.data;
  },

  getInitiative: async (id: string): Promise<Initiative> => {
    const res = await axios.get(`${API_BASE_URL}/api/planning/initiatives/${id}`);
    return res.data;
  },

  updateInitiative: async (id: string, data: Partial<InitiativeCreate>): Promise<Initiative> => {
    const res = await axios.put(`${API_BASE_URL}/api/planning/initiatives/${id}`, data);
    return res.data;
  },

  deleteInitiative: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/planning/initiatives/${id}`);
  },

  addAction: async (initiativeId: string, data: ActionCreate): Promise<Action> => {
    const res = await axios.post(`${API_BASE_URL}/api/planning/initiatives/${initiativeId}/actions`, data);
    return res.data;
  },

  updateAction: async (actionId: string, data: ActionCreate): Promise<Action> => {
    const res = await axios.put(`${API_BASE_URL}/api/planning/actions/${actionId}`, data);
    return res.data;
  },

  deleteAction: async (actionId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/planning/actions/${actionId}`);
  }
};

export default planningService;
