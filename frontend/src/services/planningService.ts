import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface ResourceAllocation {
  id: string;
  initiative_id: string;
  action_id?: string;
  allocated_quantity: number;
  allocation_date: string;
  release_date?: string;
  notes?: string;
}

export interface Resource {
  id: string;
  name: string;
  type: 'financial' | 'human' | 'technology' | 'physical' | 'time' | 'other';
  quantity?: number;
  unit?: string;
  cost?: number;
  total_quantity?: number;
  allocated_quantity: number;
  status: 'available' | 'allocated' | 'partially_allocated' | 'over_allocated' | 'unavailable';
  allocations: ResourceAllocation[];
  availability_start?: string;
  availability_end?: string;
  cost_per_unit?: number;
  utilization_rate?: number;
  tags: string[];
  constraints?: string;
  created_at: string;
  updated_at: string;
}

export interface ResourceCreate {
  name: string;
  type: 'financial' | 'human' | 'technology' | 'physical' | 'time' | 'other';
  quantity?: number;
  unit?: string;
  cost?: number;
  total_quantity?: number;
  availability_start?: string;
  availability_end?: string;
  cost_per_unit?: number;
  tags?: string[];
  constraints?: string;
}

export interface ResourceUpdate {
  name?: string;
  type?: 'financial' | 'human' | 'technology' | 'physical' | 'time' | 'other';
  quantity?: number;
  unit?: string;
  cost?: number;
  total_quantity?: number;
  availability_start?: string;
  availability_end?: string;
  cost_per_unit?: number;
  tags?: string[];
  constraints?: string;
}

export interface ResourceAllocationCreate {
  resource_id: string;
  initiative_id: string;
  action_id?: string;
  allocated_quantity: number;
  notes?: string;
}

export interface ResourceAllocationRelease {
  allocation_id: string;
  release_date?: string;
  notes?: string;
}

export interface ResourceUtilization {
  total_resources: number;
  allocated_resources: number;
  over_allocated_resources: number;
  utilization_by_type: Record<string, {
    total: number;
    allocated: number;
    total_quantity: number;
    allocated_quantity: number;
  }>;
  resources: Array<{
    id: string;
    name: string;
    type: string;
    initiative_id: string;
    initiative_title: string;
    total_quantity: number;
    allocated_quantity: number;
    utilization_rate?: number;
    status: string;
  }>;
}

export interface ResourceConflict {
  resource_id: string;
  resource_name: string;
  conflict_type: 'over_allocation' | 'early_allocation' | 'late_allocation';
  total_quantity?: number;
  allocated_quantity?: number;
  over_allocated_by?: number;
  allocation_date?: string;
  availability_start?: string;
  expected_release?: string;
  availability_end?: string;
}

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
  resources: Resource[];
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
  },

  // Resource management methods
  createResource: async (initiativeId: string, data: ResourceCreate): Promise<Resource> => {
    const res = await axios.post(`${API_BASE_URL}/api/planning/initiatives/${initiativeId}/resources`, data);
    return res.data;
  },

  updateResource: async (initiativeId: string, resourceId: string, data: ResourceUpdate): Promise<Resource> => {
    const res = await axios.put(`${API_BASE_URL}/api/planning/initiatives/${initiativeId}/resources/${resourceId}`, data);
    return res.data;
  },

  deleteResource: async (initiativeId: string, resourceId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/planning/initiatives/${initiativeId}/resources/${resourceId}`);
  },

  // Resource allocation methods
  allocateResource: async (data: ResourceAllocationCreate): Promise<ResourceAllocation> => {
    const res = await axios.post(`${API_BASE_URL}/api/planning/resources/allocate`, data);
    return res.data;
  },

  releaseResourceAllocation: async (data: ResourceAllocationRelease): Promise<void> => {
    await axios.post(`${API_BASE_URL}/api/planning/resources/release`, data);
  },

  // Resource analysis methods
  getResourceUtilization: async (resourceType?: string): Promise<ResourceUtilization> => {
    const params = resourceType ? { resource_type: resourceType } : {};
    const res = await axios.get(`${API_BASE_URL}/api/planning/resources/utilization`, { params });
    return res.data;
  },

  checkResourceConflicts: async (initiativeId: string): Promise<ResourceConflict[]> => {
    const res = await axios.get(`${API_BASE_URL}/api/planning/initiatives/${initiativeId}/resource-conflicts`);
    return res.data;
  }
};

export default planningService;
