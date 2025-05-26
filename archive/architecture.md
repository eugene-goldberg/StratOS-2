# StratOS Architecture Overview

## System Architecture

### Frontend
- React with TypeScript
- Key Libraries:
  - Zustand for state management
  - Recharts/Nivo for visualizations
  - React Flow for Strategic Canvas
  - Material UI for components
  - socket.io-client for real-time communication

### Backend
- Python with FastAPI
- Semantic Kernel (Python SDK) for AI agent orchestration
- Integration with Azure OpenAI Service

### Database Architecture (Azure)
- Azure Database for PostgreSQL (user data, structured plans, WHY/WHATs)
- Azure Cosmos DB (CEO's Log, AI insights, canvas data)
- Azure AI Search (vector capabilities for Semantic Kernel memory)

### AI/ML Stack
- Semantic Kernel Skills and Planners
- Azure Cognitive Services for Speech
- Azure OpenAI Service for LLM capabilities

## Phase 1 MVP Components

### Strategic Foundation
- "Our North Star" Module (WHY/WHAT definition)
- "CEO's Log" for Subjective input

### Objective Intelligence
- Data upload capabilities
- Manual KPI entry

### AI Analysis
- S+O linkage
- SWOT/TOWS analysis

### Strategic Planning
- Basic Initiative Planner

## Implementation Roadmap

1. Project setup and infrastructure
2. Core backend API development
3. Semantic Kernel integration
4. Frontend development for MVP modules
5. AI capabilities integration
6. Testing and refinement