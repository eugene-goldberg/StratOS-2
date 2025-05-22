import { renderHook, act, waitFor } from '@testing-library/react';
import { useAlertStore } from '../alertStore';
import alertService from '../../services/alertService';
import { AlertType, AlertSeverity, AlertStatus } from '../../types/alerts';

// Mock the alert service
jest.mock('../../services/alertService');

describe('Alert Store', () => {
  const mockAlerts = [
    {
      id: '1',
      user_id: 'user1',
      alert_type: AlertType.RISK,
      severity: AlertSeverity.HIGH,
      status: AlertStatus.NEW,
      title: 'Test Risk',
      description: 'Test risk description',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_type: 'test',
      detection_method: 'test'
    },
    {
      id: '2',
      user_id: 'user1',
      alert_type: AlertType.OPPORTUNITY,
      severity: AlertSeverity.MEDIUM,
      status: AlertStatus.VIEWED,
      title: 'Test Opportunity',
      description: 'Test opportunity description',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_type: 'test',
      detection_method: 'test'
    }
  ];

  const mockStats = {
    total_alerts: 2,
    by_type: { risk: 1, opportunity: 1 },
    by_severity: { high: 1, medium: 1 },
    by_status: { new: 1, viewed: 1 },
    unread_count: 1,
    critical_count: 0
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store state
    useAlertStore.setState({
      alerts: [],
      stats: null,
      isLoading: false,
      error: null,
      filters: {}
    });
  });

  describe('loadAlerts', () => {
    it('loads alerts successfully', async () => {
      (alertService.listAlerts as jest.Mock).mockResolvedValue(mockAlerts);

      const { result } = renderHook(() => useAlertStore());

      await act(async () => {
        await result.current.loadAlerts();
      });

      expect(result.current.alerts).toEqual(mockAlerts);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('handles load alerts error', async () => {
      const error = new Error('Failed to load');
      (alertService.listAlerts as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useAlertStore());

      await act(async () => {
        await result.current.loadAlerts();
      });

      expect(result.current.alerts).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Failed to load');
    });

    it('applies filters when loading alerts', async () => {
      (alertService.listAlerts as jest.Mock).mockResolvedValue(mockAlerts);

      const { result } = renderHook(() => useAlertStore());

      // Set filters
      act(() => {
        result.current.setFilters({
          alert_type: AlertType.RISK,
          severity: [AlertSeverity.HIGH]
        });
      });

      await waitFor(() => {
        expect(alertService.listAlerts).toHaveBeenCalledWith({
          alert_type: AlertType.RISK,
          severity: [AlertSeverity.HIGH],
          limit: 100
        });
      });
    });
  });

  describe('loadStats', () => {
    it('loads stats successfully', async () => {
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      await act(async () => {
        await result.current.loadStats();
      });

      expect(result.current.stats).toEqual(mockStats);
    });
  });

  describe('acknowledgeAlert', () => {
    it('acknowledges alert and updates state', async () => {
      const acknowledgedAlert = { ...mockAlerts[0], status: AlertStatus.ACKNOWLEDGED };
      (alertService.acknowledgeAlert as jest.Mock).mockResolvedValue(acknowledgedAlert);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      // Set initial alerts
      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.acknowledgeAlert('1');
      });

      expect(result.current.alerts[0].status).toBe(AlertStatus.ACKNOWLEDGED);
      expect(alertService.getAlertStats).toHaveBeenCalled();
    });
  });

  describe('resolveAlert', () => {
    it('resolves alert with notes', async () => {
      const resolvedAlert = { ...mockAlerts[0], status: AlertStatus.RESOLVED };
      (alertService.resolveAlert as jest.Mock).mockResolvedValue(resolvedAlert);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.resolveAlert('1', 'Issue fixed');
      });

      expect(alertService.resolveAlert).toHaveBeenCalledWith('1', 'Issue fixed');
      expect(result.current.alerts[0].status).toBe(AlertStatus.RESOLVED);
    });
  });

  describe('dismissAlert', () => {
    it('dismisses alert with reason', async () => {
      const dismissedAlert = { ...mockAlerts[0], status: AlertStatus.DISMISSED };
      (alertService.dismissAlert as jest.Mock).mockResolvedValue(dismissedAlert);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.dismissAlert('1', 'False positive');
      });

      expect(alertService.dismissAlert).toHaveBeenCalledWith('1', 'False positive');
      expect(result.current.alerts[0].status).toBe(AlertStatus.DISMISSED);
    });
  });

  describe('deleteAlert', () => {
    it('deletes alert and removes from state', async () => {
      (alertService.deleteAlert as jest.Mock).mockResolvedValue(undefined);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.deleteAlert('1');
      });

      expect(result.current.alerts).toHaveLength(1);
      expect(result.current.alerts[0].id).toBe('2');
    });
  });

  describe('triggerScan', () => {
    it('triggers scan and reloads alerts after delay', async () => {
      jest.useFakeTimers();
      
      const scanResult = {
        message: 'Scan triggered',
        user_id: 'user1',
        status: 'queued'
      };
      
      (alertService.triggerScan as jest.Mock).mockResolvedValue(scanResult);
      (alertService.listAlerts as jest.Mock).mockResolvedValue(mockAlerts);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      let scanPromise: Promise<any>;
      act(() => {
        scanPromise = result.current.triggerScan();
      });

      await act(async () => {
        await scanPromise;
      });

      expect(alertService.triggerScan).toHaveBeenCalled();

      // Fast forward 5 seconds
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(alertService.listAlerts).toHaveBeenCalled();
        expect(alertService.getAlertStats).toHaveBeenCalled();
      });

      jest.useRealTimers();
    });
  });

  describe('markAsViewed', () => {
    it('marks new alert as viewed', async () => {
      const viewedAlert = { ...mockAlerts[0], status: AlertStatus.VIEWED };
      (alertService.updateAlertStatus as jest.Mock).mockResolvedValue(viewedAlert);
      (alertService.getAlertStats as jest.Mock).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useAlertStore());

      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.markAsViewed('1');
      });

      expect(alertService.updateAlertStatus).toHaveBeenCalledWith('1', AlertStatus.VIEWED);
      expect(result.current.alerts[0].status).toBe(AlertStatus.VIEWED);
    });

    it('does not update already viewed alerts', async () => {
      const { result } = renderHook(() => useAlertStore());

      act(() => {
        useAlertStore.setState({ alerts: mockAlerts });
      });

      await act(async () => {
        await result.current.markAsViewed('2'); // Already viewed
      });

      expect(alertService.updateAlertStatus).not.toHaveBeenCalled();
    });
  });

  describe('setFilters', () => {
    it('updates filters and reloads alerts', async () => {
      (alertService.listAlerts as jest.Mock).mockResolvedValue(mockAlerts);

      const { result } = renderHook(() => useAlertStore());

      await act(async () => {
        result.current.setFilters({
          alert_type: AlertType.RISK,
          severity: [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        });
      });

      expect(result.current.filters).toEqual({
        alert_type: AlertType.RISK,
        severity: [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
      });

      expect(alertService.listAlerts).toHaveBeenCalledWith({
        alert_type: AlertType.RISK,
        severity: [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
        limit: 100
      });
    });
  });
});