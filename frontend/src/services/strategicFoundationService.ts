import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface Purpose {
  id: string;
  statement: string;
  description?: string;
}

export interface Vision {
  id: string;
  statement: string;
  description?: string;
  time_horizon?: string;
}

export interface Value {
  id: string;
  name: string;
  description: string;
}

export interface StrategicGoal {
  id: string;
  title: string;
  description: string;
  time_frame?: string;
  metrics?: string[];
}

export interface NorthStar {
  id: string;
  purpose: Purpose;
  vision: Vision;
  values: Value[];
  strategic_goals: StrategicGoal[];
}

export interface NorthStarUpdate {
  purpose?: string;
  purpose_description?: string;
  vision?: string;
  vision_description?: string;
  vision_time_horizon?: string;
  values?: Value[];
  strategic_goals?: StrategicGoal[];
}

export const strategicFoundationService = {
  async getNorthStar(): Promise<NorthStar> {
    const response = await axios.get(`${API_BASE_URL}/api/strategic-foundation/north-star`);
    return response.data;
  },

  async updateNorthStar(updateData: NorthStarUpdate): Promise<NorthStar> {
    const response = await axios.put(`${API_BASE_URL}/api/strategic-foundation/north-star`, updateData);
    return response.data;
  }
};

export default strategicFoundationService;
