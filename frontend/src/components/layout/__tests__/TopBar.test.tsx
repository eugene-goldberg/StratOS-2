import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import TopBar from '../TopBar';
import { useAlertStore } from '../../../store/alertStore';
import { AlertType, AlertSeverity, AlertStatus } from '../../../types/alerts';

// Mock the store
jest.mock('../../../store/alertStore');

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('TopBar Alert Notifications', () => {
  const mockAlerts = [
    {
      id: '1',
      user_id: 'user1',
      alert_type: AlertType.RISK,
      severity: AlertSeverity.HIGH,
      status: AlertStatus.NEW,
      title: 'High Risk Alert',
      description: 'This is a high risk alert that needs attention',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_type: 'analysis',
      detection_method: 'ai'
    },
    {
      id: '2',
      user_id: 'user1',
      alert_type: AlertType.OPPORTUNITY,
      severity: AlertSeverity.MEDIUM,
      status: AlertStatus.NEW,
      title: 'Market Opportunity',
      description: 'New market opportunity detected',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_type: 'analysis',
      detection_method: 'ai'
    }
  ];

  const mockStats = {
    total_alerts: 5,
    by_type: { risk: 3, opportunity: 2 },
    by_severity: { high: 1, medium: 3, low: 1 },
    by_status: { new: 2, viewed: 1, acknowledged: 2 },
    unread_count: 2,
    critical_count: 0
  };

  beforeEach(() => {
    const mockStore = {
      alerts: mockAlerts,
      stats: mockStats,
      loadAlerts: jest.fn(),
      loadStats: jest.fn(),
      markAsViewed: jest.fn(),
      isLoading: false,
      error: null
    };

    (useAlertStore as jest.Mock).mockReturnValue(mockStore);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('displays correct unread count in notification badge', () => {
    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    const badge = screen.getByText('2');
    expect(badge).toBeInTheDocument();
  });

  it('opens notification popover when clicking notification icon', () => {
    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Find and click the notifications button
    const notificationButton = screen.getByLabelText(/notifications/i).closest('button');
    fireEvent.click(notificationButton!);

    // Check that popover content is displayed
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('2 new alerts')).toBeInTheDocument();
    expect(screen.getByText('High Risk Alert')).toBeInTheDocument();
    expect(screen.getByText('Market Opportunity')).toBeInTheDocument();
  });

  it('calls markAsViewed when clicking on an alert', async () => {
    const mockMarkAsViewed = jest.fn();
    (useAlertStore as jest.Mock).mockReturnValue({
      ...useAlertStore(),
      markAsViewed: mockMarkAsViewed
    });

    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Open notifications
    const notificationButton = screen.getByLabelText(/notifications/i).closest('button');
    fireEvent.click(notificationButton!);

    // Click on first alert
    const firstAlert = screen.getByText('High Risk Alert');
    fireEvent.click(firstAlert);

    await waitFor(() => {
      expect(mockMarkAsViewed).toHaveBeenCalledWith('1');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('displays correct icons for different alert types', () => {
    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Open notifications
    const notificationButton = screen.getByLabelText(/notifications/i).closest('button');
    fireEvent.click(notificationButton!);

    // Check for presence of different icons (by testing the alert containers)
    const alertItems = screen.getAllByRole('button', { name: /risk|opportunity/i });
    expect(alertItems).toHaveLength(2);
  });

  it('shows no alerts message when there are no unread alerts', () => {
    (useAlertStore as jest.Mock).mockReturnValue({
      alerts: [],
      stats: { ...mockStats, unread_count: 0 },
      loadAlerts: jest.fn(),
      loadStats: jest.fn(),
      markAsViewed: jest.fn(),
      isLoading: false,
      error: null
    });

    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Open notifications
    const notificationButton = screen.getByLabelText(/notifications/i).closest('button');
    fireEvent.click(notificationButton!);

    expect(screen.getByText('No new alerts')).toBeInTheDocument();
  });

  it('navigates to dashboard when clicking View All Alerts', () => {
    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Open notifications
    const notificationButton = screen.getByLabelText(/notifications/i).closest('button');
    fireEvent.click(notificationButton!);

    // Click View All
    const viewAllButton = screen.getByText('View All Alerts');
    fireEvent.click(viewAllButton);

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('refreshes alerts periodically', () => {
    jest.useFakeTimers();
    const mockLoadAlerts = jest.fn();
    const mockLoadStats = jest.fn();

    (useAlertStore as jest.Mock).mockReturnValue({
      ...useAlertStore(),
      loadAlerts: mockLoadAlerts,
      loadStats: mockLoadStats
    });

    render(
      <BrowserRouter>
        <TopBar sidebarOpen={true} toggleSidebar={() => {}} />
      </BrowserRouter>
    );

    // Initial load
    expect(mockLoadAlerts).toHaveBeenCalledTimes(1);
    expect(mockLoadStats).toHaveBeenCalledTimes(1);

    // Fast forward 1 minute
    jest.advanceTimersByTime(60000);

    expect(mockLoadAlerts).toHaveBeenCalledTimes(2);
    expect(mockLoadStats).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });
});