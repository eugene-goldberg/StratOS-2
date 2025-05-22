import axios from 'axios';
import { Alert, AlertStats, AlertStatus } from '../types/alerts';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface AlertFilter {
  alert_type?: string;
  severity?: string[];
  status?: string[];
  category?: string;
  min_risk_score?: number;
  max_risk_score?: number;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

const alertService = {
  // Get all alerts
  listAlerts: async (filters?: AlertFilter): Promise<Alert[]> => {
    const params = new URLSearchParams();
    
    if (filters) {
      if (filters.alert_type) params.append('alert_type', filters.alert_type);
      if (filters.severity) filters.severity.forEach(s => params.append('severity', s));
      if (filters.status) filters.status.forEach(s => params.append('status', s));
      if (filters.category) params.append('category', filters.category);
      if (filters.min_risk_score !== undefined) params.append('min_risk_score', filters.min_risk_score.toString());
      if (filters.max_risk_score !== undefined) params.append('max_risk_score', filters.max_risk_score.toString());
      if (filters.created_after) params.append('created_after', filters.created_after);
      if (filters.created_before) params.append('created_before', filters.created_before);
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());
    }
    
    const response = await axios.get(`${API_BASE_URL}/api/alerts?${params.toString()}`);
    return response.data;
  },

  // Get a specific alert
  getAlert: async (alertId: string): Promise<Alert> => {
    const response = await axios.get(`${API_BASE_URL}/api/alerts/${alertId}`);
    return response.data;
  },

  // Update alert status
  updateAlertStatus: async (alertId: string, status: AlertStatus): Promise<Alert> => {
    const response = await axios.put(`${API_BASE_URL}/api/alerts/${alertId}`, { status });
    return response.data;
  },

  // Acknowledge an alert
  acknowledgeAlert: async (alertId: string): Promise<Alert> => {
    const response = await axios.post(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  // Resolve an alert
  resolveAlert: async (alertId: string, notes?: string): Promise<Alert> => {
    const response = await axios.post(`${API_BASE_URL}/api/alerts/${alertId}/resolve`, { notes });
    return response.data;
  },

  // Dismiss an alert
  dismissAlert: async (alertId: string, reason?: string): Promise<Alert> => {
    const response = await axios.post(`${API_BASE_URL}/api/alerts/${alertId}/dismiss`, { reason });
    return response.data;
  },

  // Delete an alert
  deleteAlert: async (alertId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/alerts/${alertId}`);
  },

  // Get alert statistics
  getAlertStats: async (): Promise<AlertStats> => {
    const response = await axios.get(`${API_BASE_URL}/api/alerts/stats/summary`);
    return response.data;
  },

  // Trigger manual scan
  triggerScan: async (): Promise<{ message: string; user_id: string; status: string }> => {
    const response = await axios.post(`${API_BASE_URL}/api/alerts/scan/trigger`);
    return response.data;
  }
};

export default alertService;