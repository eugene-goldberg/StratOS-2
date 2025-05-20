import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface StrategicGoal {
  id: string;
  title: string;
  description: string;
}

const northStarService = {
  listStrategicGoals: async (): Promise<StrategicGoal[]> => {
    const res = await axios.get(`${API_BASE_URL}/api/foundation/north-star/strategic-goals`);
    return res.data;
  }
};

export default northStarService;
