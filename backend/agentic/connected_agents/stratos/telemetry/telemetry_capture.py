"""
Unified Telemetry Capture System for StratOS Connected Agents
Provides standardized telemetry tracking for all agent testing
"""

import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace


@dataclass
class TelemetryEvent:
    """Represents a single telemetry event"""
    event_type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return asdict(self)


class TelemetryCapture:
    """Unified telemetry capture for StratOS agents"""
    
    def __init__(self, agent_name: str, session_id: Optional[str] = None):
        """
        Initialize telemetry capture
        
        Args:
            agent_name: Name of the agent being tested
            session_id: Optional session ID (generates new if not provided)
        """
        self.agent_name = agent_name
        self.session_id = session_id or str(uuid.uuid4())
        self.events: List[TelemetryEvent] = []
        self.logger = logging.getLogger(__name__)
        self.tracer = None
        
        # Configure Application Insights if available
        app_insights_conn = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")
        if app_insights_conn:
            configure_azure_monitor(connection_string=app_insights_conn)
            self.tracer = trace.get_tracer(__name__)
            self.capture_event("telemetry_configured", {"app_insights": True})
        else:
            self.capture_event("telemetry_configured", {"app_insights": False})
    
    def capture_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Capture a telemetry event
        
        Args:
            event_type: Type of event (e.g., 'query_sent', 'response_received')
            data: Event data dictionary
        """
        event = TelemetryEvent(
            event_type=event_type,
            data=data,
            session_id=self.session_id
        )
        self.events.append(event)
        
        # Log the event
        self.logger.info(f"📊 Telemetry: {event_type} - {json.dumps(data)[:100]}...")
        
        # Send to Application Insights if configured
        if self.tracer:
            with self.tracer.start_as_current_span(f"event_{event_type}") as span:
                span.set_attribute("session_id", self.session_id)
                span.set_attribute("agent_name", self.agent_name)
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"data.{key}", value)
    
    def capture_query(self, query: str, target: str, function: Optional[str] = None) -> None:
        """
        Capture a query sent to an agent
        
        Args:
            query: The query text
            target: Target agent name
            function: Expected function to be called
        """
        self.capture_event("query_sent", {
            "query": query,
            "target": target,
            "function": function or "general"
        })
    
    def capture_response(self, response: str, scenario: Optional[str] = None) -> bool:
        """
        Capture a response and check for delegation
        
        Args:
            response: The response text
            scenario: Optional scenario name
            
        Returns:
            True if delegation was detected
        """
        # Check for delegation patterns
        delegation_patterns = {
            "ceo_log": "ceo log specialist",
            "north_star": "north star specialist",
            "memory_recall": "memory recall specialist",
            "preference_learning": "preference learning specialist",
            "swot_tows": "swot/tows specialist",
            "risk_opportunity": "risk opportunity specialist",
            "so_linkage": "so linkage specialist",
            "initiative_generation": "initiative generation specialist",
            "action_planning": "action planning specialist",
            "alignment_scoring": "alignment scoring specialist",
            "resource_optimization": "resource optimization specialist",
            "canvas_visualization": "canvas visualization specialist"
        }
        
        response_lower = response.lower()
        delegation_detected = False
        detected_agent = None
        
        for agent, pattern in delegation_patterns.items():
            if pattern in response_lower:
                delegation_detected = True
                detected_agent = agent
                break
        
        # Capture response event
        event_data = {
            "response_length": len(response),
            "delegation_detected": delegation_detected,
            "response_preview": response[:200] + "..." if len(response) > 200 else response
        }
        
        if scenario:
            event_data["scenario"] = scenario
        
        self.capture_event("response_received", event_data)
        
        # Capture delegation confirmation if detected
        if delegation_detected:
            self.capture_event("delegation_confirmed", {
                "type": detected_agent,
                "scenario": scenario or "unknown"
            })
        
        return delegation_detected
    
    def capture_orchestrator_info(self, orchestrator_id: str, tools: List[Dict[str, str]]) -> None:
        """
        Capture orchestrator configuration information
        
        Args:
            orchestrator_id: Orchestrator agent ID
            tools: List of tool configurations
        """
        self.capture_event("orchestrator_fetch_complete", {
            "orchestrator_id": orchestrator_id,
            "tools_count": len(tools),
            "tools": tools
        })
    
    def capture_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Capture an error event
        
        Args:
            error_message: Error message
            context: Optional error context
        """
        event_data = {"message": error_message}
        if context:
            event_data.update(context)
        
        self.capture_event("error", event_data)
    
    def capture_test_complete(self, tests_run: int, **kwargs) -> None:
        """
        Capture test completion
        
        Args:
            tests_run: Number of tests run
            **kwargs: Additional test metadata
        """
        event_data = {"tests_run": tests_run}
        event_data.update(kwargs)
        
        self.capture_event("test_complete", event_data)
    
    def save(self, base_dir: Optional[Path] = None) -> Path:
        """
        Save telemetry to JSON file
        
        Args:
            base_dir: Base directory for telemetry (defaults to stratos/telemetry)
            
        Returns:
            Path to saved telemetry file
        """
        if base_dir is None:
            base_dir = Path(__file__).parent
        
        # Create agent-specific directory
        agent_dir = base_dir / self.agent_name.lower().replace(" ", "_")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_session = self.session_id.split('-')[0]
        filename = f"{self.agent_name.lower().replace(' ', '_')}_telemetry_{timestamp}_{short_session}.json"
        filepath = agent_dir / filename
        
        # Prepare telemetry data
        telemetry_data = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "capture_time": datetime.utcnow().isoformat(),
            "events": [event.to_dict() for event in self.events]
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(telemetry_data, f, indent=2)
        
        self.logger.info(f"💾 Telemetry saved to: {filepath}")
        
        return filepath
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get telemetry summary
        
        Returns:
            Summary dictionary with event counts and key metrics
        """
        summary = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "total_events": len(self.events),
            "event_types": {}
        }
        
        # Count event types
        for event in self.events:
            event_type = event.event_type
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
        
        # Count delegations
        delegations = [e for e in self.events if e.event_type == "delegation_confirmed"]
        summary["delegations_confirmed"] = len(delegations)
        
        # Count errors
        errors = [e for e in self.events if e.event_type == "error"]
        summary["errors"] = len(errors)
        
        return summary
    
    def print_summary(self) -> None:
        """Print a formatted telemetry summary"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("TELEMETRY CAPTURE SUMMARY")
        print("="*60)
        print(f"Session ID: {summary['session_id']}")
        print(f"Agent: {summary['agent_name']}")
        print(f"Total Events: {summary['total_events']}")
        print(f"Delegations Confirmed: {summary['delegations_confirmed']}")
        print(f"Errors: {summary['errors']}")
        print("\nEvent Types:")
        for event_type, count in summary['event_types'].items():
            print(f"  - {event_type}: {count}")
        print("="*60)