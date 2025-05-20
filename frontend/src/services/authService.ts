import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  company_name?: string;
  job_title?: string;
  is_active: boolean;
  created_at: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
  company_name?: string;
  job_title?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  register: async (data: RegisterData): Promise<UserProfile> => {
    const response = await axios.post(`${API_BASE_URL}/api/auth/register`, data);
    return response.data;
  },
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, null, {
      params: { email, password }
    });
    return response.data;
  },
  refreshToken: async (token: string): Promise<LoginResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/auth/refresh-token`,
      null,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    return response.data;
  },
  getProfile: async (token: string): Promise<UserProfile> => {
    const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};

export default authService;
