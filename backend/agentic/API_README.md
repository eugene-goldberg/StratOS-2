# StratOS FastAPI Backend

This is the FastAPI backend for the StratOS Multi-Agent System, serving as the primary interface between the React web application and the Azure AI Foundry Agent Service.

## Architecture

```
React Web App
     ↓ REST/WebSocket
FastAPI Backend (This)
     ↓ 
Azure AI Foundry Agent Service
     ↓
3 Multi-Agent Systems
```

## Features

- **RESTful API**: Agent invocation endpoints
- **WebSocket Support**: Real-time streaming of agent responses
- **MSAL Authentication**: Microsoft Entra ID integration
- **Health Checks**: Kubernetes/Container Apps ready
- **Error Handling**: Consistent error responses
- **Development Mode**: Works without Azure services for local development

## Quick Start

### 1. Set up Python environment

```bash
cd backend/agentic
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Azure service configurations
```

### 3. Run the application

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the application

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
- WebSocket Test: ws://localhost:8000/ws/agent-stream

## API Endpoints

### Health Checks
- `GET /api/health` - Basic health check
- `GET /api/health/ready` - Readiness probe (checks service connections)
- `GET /api/health/live` - Liveness probe

### Agent Operations
- `POST /api/agents/invoke` - Invoke an agent system
- `GET /api/agents/systems` - List available agent systems
- `GET /api/agents/threads/{thread_id}` - Get conversation history

### WebSocket
- `WS /ws/agent-stream` - Real-time agent response streaming

## Project Structure

```
backend/agentic/
├── main.py                 # FastAPI application entry point
├── api/
│   ├── routes/            # API route handlers
│   │   ├── agents.py      # Agent invocation endpoints
│   │   ├── health.py      # Health check endpoints
│   │   └── websocket.py   # WebSocket endpoints
│   └── middleware/        # Middleware components
│       ├── auth.py        # MSAL authentication
│       └── error.py       # Error handling
├── config/
│   └── settings.py        # Configuration management
├── services/
│   └── agent_client.py    # Azure AI Foundry client
├── common/                # Shared agent components
├── agents/                # Agent implementations
└── requirements.txt       # Python dependencies
```

## Authentication

The API uses Microsoft Entra ID (formerly Azure AD) for authentication:

1. React app obtains token from MSAL
2. Token included in Authorization header: `Bearer <token>`
3. Backend validates token with Microsoft Entra ID
4. User context passed to agent invocations

In development mode, authentication is bypassed with mock user data.

## WebSocket Protocol

The WebSocket endpoint supports real-time streaming of agent responses:

### Message Types

**Client → Server:**
```json
{
  "type": "agent_request",
  "data": {
    "system": "strategic-foundation",
    "type": "ceo_log",
    "action": "create_entry",
    "data": {...}
  }
}
```

**Server → Client:**
```json
{
  "type": "partial_response",
  "request_id": "...",
  "data": {
    "content": "partial text...",
    "position": 0
  }
}
```

### Connection Flow
1. Connect to WebSocket with token
2. Receive connection confirmation
3. Send agent requests
4. Receive streamed responses
5. Handle status updates and errors

## Environment Variables

See `.env.example` for all available configurations. Key variables:

- `ENVIRONMENT`: development/staging/production
- `AI_FOUNDRY_ENDPOINT`: Azure AI Foundry endpoint
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `COSMOS_ENDPOINT`: Cosmos DB endpoint
- `SEARCH_ENDPOINT`: Azure AI Search endpoint

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

### Docker
```bash
# Build image
docker build -t stratos-backend .

# Run container
docker run -p 8000:8000 --env-file .env stratos-backend
```

## Deployment

The backend is designed to run on Azure Container Apps:

1. Build and push Docker image
2. Deploy to Azure Container Apps
3. Configure environment variables
4. Set up health check probes
5. Enable auto-scaling

## Troubleshooting

### Common Issues

1. **"Agent service not initialized"**
   - Check AI_FOUNDRY_ENDPOINT is configured
   - Verify network connectivity to Azure

2. **Authentication errors**
   - Ensure AZURE_CLIENT_ID and AZURE_TENANT_ID are set
   - Verify token is valid and not expired

3. **WebSocket disconnections**
   - Check firewall/proxy settings
   - Verify WebSocket support in deployment environment

## Next Steps

- Complete Azure AI Foundry SDK integration when available
- Implement actual agent streaming
- Add comprehensive test coverage
- Set up CI/CD pipeline
- Configure monitoring and alerts