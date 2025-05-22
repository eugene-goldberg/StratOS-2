import { create } from 'zustand';
import alertService from '../services/alertService';
import { Alert, AlertStats, AlertStatus, AlertType, AlertSeverity } from '../types/alerts';

interface AlertState {
  alerts: Alert[];
  stats: AlertStats | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    alert_type?: AlertType;
    severity?: AlertSeverity[];
    status?: AlertStatus[];
  };
  
  // Actions
  loadAlerts: () => Promise<void>;
  loadStats: () => Promise<void>;
  setFilters: (filters: Partial<AlertState['filters']>) => void;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string, notes?: string) => Promise<void>;
  dismissAlert: (alertId: string, reason?: string) => Promise<void>;
  deleteAlert: (alertId: string) => Promise<void>;
  triggerScan: () => Promise<{ message: string; user_id: string; status: string } | undefined>;
  markAsViewed: (alertId: string) => Promise<void>;
}

export const useAlertStore = create<AlertState>((set, get) => ({
  alerts: [],
  stats: null,
  isLoading: false,
  error: null,
  filters: {},

  loadAlerts: async () => {
    set({ isLoading: true, error: null });
    try {
      const filters = get().filters;
      const alerts = await alertService.listAlerts({
        alert_type: filters.alert_type,
        severity: filters.severity,
        status: filters.status,
        limit: 100
      });
      set({ alerts, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to load alerts',
        isLoading: false 
      });
    }
  },

  loadStats: async () => {
    try {
      const stats = await alertService.getAlertStats();
      set({ stats });
    } catch (error) {
      console.error('Failed to load alert stats:', error);
    }
  },

  setFilters: (filters) => {
    set(state => ({ filters: { ...state.filters, ...filters } }));
    // Reload alerts with new filters
    get().loadAlerts();
  },

  acknowledgeAlert: async (alertId) => {
    try {
      const updatedAlert = await alertService.acknowledgeAlert(alertId);
      set(state => ({
        alerts: state.alerts.map(alert => 
          alert.id === alertId ? updatedAlert : alert
        )
      }));
      // Reload stats
      get().loadStats();
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to acknowledge alert'
      });
    }
  },

  resolveAlert: async (alertId, notes) => {
    try {
      const updatedAlert = await alertService.resolveAlert(alertId, notes);
      set(state => ({
        alerts: state.alerts.map(alert => 
          alert.id === alertId ? updatedAlert : alert
        )
      }));
      // Reload stats
      get().loadStats();
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to resolve alert'
      });
    }
  },

  dismissAlert: async (alertId, reason) => {
    try {
      const updatedAlert = await alertService.dismissAlert(alertId, reason);
      set(state => ({
        alerts: state.alerts.map(alert => 
          alert.id === alertId ? updatedAlert : alert
        )
      }));
      // Reload stats
      get().loadStats();
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to dismiss alert'
      });
    }
  },

  deleteAlert: async (alertId) => {
    try {
      await alertService.deleteAlert(alertId);
      set(state => ({
        alerts: state.alerts.filter(alert => alert.id !== alertId)
      }));
      // Reload stats
      get().loadStats();
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to delete alert'
      });
    }
  },

  triggerScan: async () => {
    try {
      const result = await alertService.triggerScan();
      // Reload alerts after a delay to allow scan to complete
      setTimeout(() => {
        get().loadAlerts();
        get().loadStats();
      }, 5000);
      return result;
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to trigger scan'
      });
    }
  },

  markAsViewed: async (alertId) => {
    try {
      const alert = get().alerts.find(a => a.id === alertId);
      if (alert && alert.status === AlertStatus.NEW) {
        const updatedAlert = await alertService.updateAlertStatus(alertId, AlertStatus.VIEWED);
        set(state => ({
          alerts: state.alerts.map(a => 
            a.id === alertId ? updatedAlert : a
          )
        }));
        // Reload stats
        get().loadStats();
      }
    } catch (error) {
      console.error('Failed to mark alert as viewed:', error);
    }
  }
}));

export default useAlertStore;