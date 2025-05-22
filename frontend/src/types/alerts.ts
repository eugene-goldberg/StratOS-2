export enum AlertType {
  RISK = 'risk',
  OPPORTUNITY = 'opportunity',
  INSIGHT = 'insight',
  THRESHOLD = 'threshold',
  ANOMALY = 'anomaly'
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum AlertStatus {
  NEW = 'new',
  VIEWED = 'viewed',
  ACKNOWLEDGED = 'acknowledged',
  RESOLVED = 'resolved',
  DISMISSED = 'dismissed'
}

export interface Alert {
  id: string;
  user_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  
  title: string;
  description: string;
  
  category?: string;
  impact_score?: number;
  likelihood_score?: number;
  risk_score?: number;
  
  source_type: string;
  source_id?: string;
  source_details?: any;
  
  detection_method: string;
  detection_details?: any;
  confidence_score?: number;
  
  recommendations?: string[];
  related_alerts?: string[];
  
  created_at: string;
  updated_at: string;
  viewed_at?: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface AlertStats {
  total_alerts: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  unread_count: number;
  critical_count: number;
}