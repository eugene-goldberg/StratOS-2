import apiService from './apiService';

export interface Purpose {
  id: string;
  statement: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Vision {
  id: string;
  statement: string;
  description?: string;
  time_horizon?: string;
  created_at: string;
  updated_at: string;
}

export interface Value {
  id: string;
  name: string;
  description: string;
  examples?: string[];
  created_at: string;
  updated_at: string;
}

export interface StrategicGoal {
  id: string;
  title: string;
  description: string;
  time_frame?: string;
  metrics?: string[];
  target_value?: number;
  current_value?: number;
  parent_goal_id?: string;
  sub_goals?: StrategicGoal[];
  created_at: string;
  updated_at: string;
}

export interface NorthStar {
  id: string;
  purpose: Purpose;
  vision: Vision;
  values: Value[];
  strategic_goals: StrategicGoal[];
  created_at: string;
  updated_at: string;
}

export interface NorthStarCreate {
  purpose: string;
  purpose_description?: string;
  vision: string;
  vision_description?: string;
  vision_time_horizon?: string;
  values: Array<{
    name: string;
    description: string;
    examples?: string[];
  }>;
  strategic_goals: Array<{
    title: string;
    description: string;
    time_frame?: string;
    metrics?: string[];
    target_value?: number;
    current_value?: number;
    parent_goal_id?: string;
  }>;
}

export interface NorthStarUpdate {
  purpose?: string;
  purpose_description?: string;
  vision?: string;
  vision_description?: string;
  vision_time_horizon?: string;
}

const northStarService = {
  // North Star operations
  getNorthStar: async (): Promise<NorthStar> => {
    const res = await apiService.get('/foundation/north-star');
    return res.data;
  },

  createNorthStar: async (data: NorthStarCreate): Promise<NorthStar> => {
    const res = await apiService.post('/foundation/north-star', data);
    return res.data;
  },

  updateNorthStar: async (data: NorthStarUpdate): Promise<NorthStar> => {
    const res = await apiService.put('/foundation/north-star', data);
    return res.data;
  },

  // Strategic Goals operations
  listStrategicGoals: async (hierarchical: boolean = false): Promise<StrategicGoal[]> => {
    const res = await apiService.get(`/foundation/north-star/strategic-goals?hierarchical=${hierarchical}`);
    return res.data;
  },

  getStrategicGoal: async (goalId: string): Promise<StrategicGoal> => {
    const res = await apiService.get(`/foundation/north-star/strategic-goals/${goalId}`);
    return res.data;
  },

  createStrategicGoal: async (data: Partial<StrategicGoal>): Promise<StrategicGoal> => {
    const res = await apiService.post('/foundation/north-star/strategic-goals', data);
    return res.data;
  },

  updateStrategicGoal: async (goalId: string, data: Partial<StrategicGoal>): Promise<StrategicGoal> => {
    const res = await apiService.put(`/foundation/north-star/strategic-goals/${goalId}`, data);
    return res.data;
  },

  deleteStrategicGoal: async (goalId: string): Promise<void> => {
    await apiService.delete(`/foundation/north-star/strategic-goals/${goalId}`);
  },

  getSubGoals: async (parentGoalId: string): Promise<StrategicGoal[]> => {
    const res = await apiService.get(`/foundation/north-star/strategic-goals/${parentGoalId}/sub-goals`);
    return res.data;
  },

  // Values operations
  listValues: async (): Promise<Value[]> => {
    const res = await apiService.get('/foundation/north-star/values');
    return res.data;
  },

  createValue: async (data: Partial<Value>): Promise<Value> => {
    const res = await apiService.post('/foundation/north-star/values', data);
    return res.data;
  },

  updateValue: async (valueId: string, data: Partial<Value>): Promise<Value> => {
    const res = await apiService.put(`/foundation/north-star/values/${valueId}`, data);
    return res.data;
  },

  deleteValue: async (valueId: string): Promise<void> => {
    await apiService.delete(`/foundation/north-star/values/${valueId}`);
  }
};

export default northStarService;