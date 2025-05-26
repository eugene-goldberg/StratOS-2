"""
OpenTelemetry tracing initialization for StratOS Multi-Agent System.
This module provides centralized telemetry configuration for all agents.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
import asyncio

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_initialized = False

def initialize_telemetry(
    service_name: str,
    service_version: str = "1.0.0",
    connection_string: Optional[str] = None,
    additional_attributes: Optional[Dict[str, Any]] = None
) -> trace.Tracer:
    """
    Initialize OpenTelemetry with Azure Monitor integration.
    
    Args:
        service_name: Name of the service/agent (e.g., "CEOLogAgent", "MainOrchestrator")
        service_version: Version of the service
        connection_string: Application Insights connection string (defaults to env var)
        additional_attributes: Additional resource attributes
    
    Returns:
        Configured tracer instance
    """
    global _tracer, _initialized
    
    if _initialized:
        return _tracer
    
    # Get connection string from environment if not provided
    if not connection_string:
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string:
        logging.warning("No Application Insights connection string found. Telemetry will be disabled.")
        _tracer = trace.get_tracer(service_name, service_version)
        return _tracer
    
    # Create resource attributes
    resource_attributes = {
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "production"),
        "azure.ai.agent.type": "stratos-agent",
    }
    
    if additional_attributes:
        resource_attributes.update(additional_attributes)
    
    # Configure Azure Monitor
    configure_azure_monitor(
        connection_string=connection_string,
        resource=Resource.create(resource_attributes),
        logging_enable=True,  # Enable logging integration
        logger_name=service_name,
    )
    
    # Instrument HTTP client
    HTTPXClientInstrumentor().instrument()
    
    # Instrument logging
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    # Get tracer
    _tracer = trace.get_tracer(service_name, service_version)
    _initialized = True
    
    logging.info(f"Telemetry initialized for {service_name} v{service_version}")
    return _tracer


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer instance."""
    return _tracer


def trace_method(span_name: Optional[str] = None):
    """
    Decorator to automatically trace methods with custom span names.
    
    Args:
        span_name: Custom span name (defaults to method name)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return await func(*args, **kwargs)
            
            name = span_name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(name) as span:
                try:
                    # Add method arguments as span attributes
                    span.set_attribute("method.name", func.__name__)
                    span.set_attribute("method.module", func.__module__)
                    
                    # Add selected kwargs as attributes (avoid sensitive data)
                    safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items() 
                                   if k in ["agent_id", "request_type", "category"]}
                    for k, v in safe_kwargs.items():
                        span.set_attribute(f"method.arg.{k}", v)
                    
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)
            
            name = span_name or f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(name) as span:
                try:
                    # Add method arguments as span attributes
                    span.set_attribute("method.name", func.__name__)
                    span.set_attribute("method.module", func.__module__)
                    
                    # Add selected kwargs as attributes (avoid sensitive data)
                    safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items() 
                                   if k in ["agent_id", "request_type", "category"]}
                    for k, v in safe_kwargs.items():
                        span.set_attribute(f"method.arg.{k}", v)
                    
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def add_span_attributes(span: Span, attributes: Dict[str, Any]):
    """
    Safely add attributes to a span.
    
    Args:
        span: The span to add attributes to
        attributes: Dictionary of attributes to add
    """
    for key, value in attributes.items():
        try:
            # Convert value to string and limit length
            str_value = str(value)[:1000] if value is not None else "None"
            span.set_attribute(key, str_value)
        except Exception as e:
            logging.warning(f"Failed to set span attribute {key}: {e}")


def create_span_context(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Create a new span with the given operation name and attributes.
    
    Args:
        operation_name: Name of the operation
        attributes: Optional attributes to add to the span
    
    Returns:
        The created span (use as context manager)
    """
    tracer = get_tracer()
    if not tracer:
        # Return a no-op context manager if tracer is not available
        from contextlib import nullcontext
        return nullcontext()
    
    # Create the span context manager
    span_cm = tracer.start_as_current_span(operation_name)
    
    # If we have attributes, we need to handle them in a custom context manager
    if attributes:
        class SpanWithAttributes:
            def __init__(self, span_context_manager, attrs):
                self.span_cm = span_context_manager
                self.attrs = attrs
                self.span = None
            
            def __enter__(self):
                self.span = self.span_cm.__enter__()
                add_span_attributes(self.span, self.attrs)
                return self.span
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                return self.span_cm.__exit__(exc_type, exc_val, exc_tb)
        
        return SpanWithAttributes(span_cm, attributes)
    
    return span_cm


# Agent-specific span names for consistency
class SpanNames:
    """Standard span names for different agent operations."""
    
    # Orchestrator operations
    ORCHESTRATOR_PROCESS_REQUEST = "orchestrator.process_request"
    ORCHESTRATOR_ROUTE_DECISION = "orchestrator.route_decision"
    ORCHESTRATOR_INVOKE_SPECIALIST = "orchestrator.invoke_specialist"
    
    # CEO Log operations
    CEO_LOG_RECORD = "ceo_log.record_entry"
    CEO_LOG_RETRIEVE = "ceo_log.retrieve_entries"
    CEO_LOG_ANALYZE = "ceo_log.analyze_sentiment"
    
    # Strategic Planning operations
    STRATEGIC_PLAN_CREATE = "strategic_planning.create_plan"
    STRATEGIC_PLAN_UPDATE = "strategic_planning.update_plan"
    STRATEGIC_PLAN_EVALUATE = "strategic_planning.evaluate_progress"
    
    # SWOT Analysis operations
    SWOT_ANALYZE = "swot.analyze"
    SWOT_UPDATE = "swot.update_analysis"
    
    # General agent operations
    AGENT_INITIALIZE = "agent.initialize"
    AGENT_PROCESS_MESSAGE = "agent.process_message"
    AGENT_CALL_LLM = "agent.call_llm"
    AGENT_STORE_RESULT = "agent.store_result"