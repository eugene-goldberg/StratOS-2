"""
Configuration settings for StratOS Multi-Agent System.

Uses Pydantic Settings for environment variable management and validation.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application Settings
    app_name: str = "StratOS Multi-Agent System"
    environment: str = "development"  # development, staging, production
    port: int = 8000
    debug: bool = False
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Azure AI Foundry Settings
    ai_foundry_endpoint: Optional[str] = None
    ai_foundry_project_id: Optional[str] = None
    ai_foundry_api_key: Optional[str] = None
    
    # Azure OpenAI Settings
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Model Deployments (based on research recommendations)
    gpt4_deployment_name: Optional[str] = None  # For routers and complex reasoning
    gpt4o_deployment_name: Optional[str] = None  # For multimodal (CEO Log)
    gpt35_deployment_name: Optional[str] = None  # For simple tasks
    o_series_deployment_name: Optional[str] = None  # For constraint reasoning
    embedding_deployment_name: Optional[str] = None  # For vector search
    
    # Cosmos DB Settings (Standard Agent Setup)
    cosmos_endpoint: Optional[str] = None
    cosmos_key: Optional[str] = None
    cosmos_database_name: str = "stratos_agents"
    
    # Container names as per Standard Agent Setup
    thread_message_container: str = "thread-message-store"
    system_message_container: str = "system-thread-message-store"
    agent_entity_container: str = "agent-entity-store"
    
    # Azure AI Search Settings (Hybrid Search)
    search_endpoint: Optional[str] = None
    search_api_key: Optional[str] = None
    search_index_prefix: str = "stratos"
    
    # Search index names
    ceo_log_index: str = "stratos-ceo-log"
    strategic_docs_index: str = "stratos-strategic-docs"
    insights_index: str = "stratos-insights"
    canvas_index: str = "stratos-canvas"
    
    # Authentication Settings (MSAL)
    azure_client_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    
    # Microsoft Entra settings for agents
    enable_entra_agent_id: bool = True
    
    # Service Bus Settings (for event-driven architecture)
    service_bus_connection_string: Optional[str] = None
    service_bus_namespace: Optional[str] = None
    
    # Application Insights
    appinsights_connection_string: Optional[str] = None
    appinsights_instrumentation_key: Optional[str] = None
    
    # WebSocket Settings
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100
    
    # API Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Agent Configuration
    agent_timeout: int = 120  # seconds
    max_retries: int = 3
    retry_delay: int = 2  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def validate_required_settings(self) -> None:
        """Validate that all required settings are configured."""
        required_settings = []
        
        if self.is_production:
            required_settings = [
                ("ai_foundry_endpoint", self.ai_foundry_endpoint),
                ("ai_foundry_project_id", self.ai_foundry_project_id),
                ("azure_openai_endpoint", self.azure_openai_endpoint),
                ("cosmos_endpoint", self.cosmos_endpoint),
                ("search_endpoint", self.search_endpoint),
                ("azure_client_id", self.azure_client_id),
                ("azure_tenant_id", self.azure_tenant_id),
            ]
        
        missing = [name for name, value in required_settings if not value]
        
        if missing:
            raise ValueError(
                f"Missing required settings for {self.environment} environment: "
                f"{', '.join(missing)}"
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_required_settings()
    return settings