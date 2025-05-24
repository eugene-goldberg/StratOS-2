# StratOS: Strategy Operating System

StratOS is an AI-powered strategic copilot for CEOs and leadership teams, transforming how businesses develop, analyze, plan, execute, and refine their strategies for sustained success.

[![Test Suite](https://github.com/eugene-goldberg/StratOS-2/actions/workflows/test.yml/badge.svg)](https://github.com/eugene-goldberg/StratOS-2/actions/workflows/test.yml)

## Project Overview

StratOS empowers leaders by seamlessly integrating their subjective insights with objective data, providing profound analysis, and offering dynamic planning capabilities, all while ensuring clear alignment with the company's core "WHY" (Purpose, Vision, Values) and "WHAT" (Strategic Goals).

### Key Features

- **Strategic Foundation & CEO's Compass**: Define and anchor your company's WHY and WHAT
- **Subjective Input Capture**: CEO's Log and Strategic Canvas for capturing qualitative insights
- **Objective Data Integration**: KPI tracking and data upload capabilities
- **AI-Powered Analysis**: SWOT/TOWS analysis, S+O linkage, insights generation
- **Dynamic Planning**: Initiative creation, plan comparison, action tracking
- **Conversational AI**: Memory-enabled AI assistant for strategic discussions

## Technology Stack

### Backend
- Python 3.11+ with FastAPI
- Semantic Kernel (Python SDK) - Structured with mock AI implementations
- Azure Cosmos DB - Fully integrated with 15 containers
- JWT Authentication with bcrypt - Fully implemented
- WebSocket support for real-time features
- Celery for background tasks

### Frontend
- React 18 with TypeScript
- Material UI components with custom theming
- Recharts/Nivo for data visualizations
- React Flow for Strategic Canvas - Fully implemented
- Zustand for state management
- Axios for API communication

### AI Services (Structured, Mock Implementations)
- Azure OpenAI Service - Ready for GPT-4.1 integration
- Azure AI Search - Interfaces defined
- Azure Speech Services - WebSocket streaming ready
- Azure Blob Storage - Package installed, not implemented

### Current Status
**✅ MVP Complete + Enhanced** (May 2025)
- All Phase 1 features implemented
- 89% of Phase 2 features complete
- 376+ backend tests, 93+ frontend tests passing
- Production-ready architecture
- **🚀 LIVE DEPLOYMENT**: FastAPI backend deployed to Azure Container Apps
  - Production URL: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io
  - API Docs: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/docs

## Project Structure

```
stratos/
├── backend/            # Python FastAPI backend
│   ├── ai/             # Semantic Kernel integration
│   ├── models/         # Pydantic models
│   ├── routers/        # API routes
│   ├── services/       # Service layer
│   └── main.py         # Main application entry point
│
├── frontend/           # React frontend
│   ├── public/         # Static assets
│   └── src/
│       ├── components/ # Reusable UI components
│       ├── pages/      # Page components
│       ├── services/   # API client services
│       ├── store/      # State management
│       └── utils/      # Utility functions
│
├── docs/               # Documentation
└── infrastructure/     # Infrastructure as code
```

## Development Setup

Run the setup script from the project root to prepare both the backend and frontend:

```bash
./setup_dev.sh
```

The script verifies that `python3` and `npm` are available, creates `backend/venv` if needed, installs Python dependencies and frontend packages, and reminds you to create `.env` files based on the provided examples.

After setup you can launch the development servers with:

```bash
./run_dev.sh
```

If you prefer to configure each part separately, run `./setup_backend.sh` and `./setup_frontend.sh` instead of the combined script.

For a lightweight dependency setup without the virtual environment helpers you
can use the convenience scripts:

```bash
./pip_install.sh   # install Python packages
./npm_install.sh   # install frontend packages
```

## Deployment

### 🚀 Current Production Deployment
The FastAPI backend is **LIVE** on Azure Container Apps:
- **Production URL**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io
- **API Documentation**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/docs
- **Health Check**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/api/health/

See [docs/azure_deployment_details.md](docs/azure_deployment_details.md) for complete deployment information.

### Quick Deploy Commands
```bash
# Deploy to Azure Container Apps
cd backend/agentic
./scripts/deploy_to_azure_container_apps.sh

# View logs
az containerapp logs show -n stratos-fastapi -g stratos-container-apps-rg --follow
```

### Azure Services Architecture
- **Azure Container Apps** for the backend (✅ DEPLOYED)
- Azure Static Web Apps for the frontend
- Azure Cosmos DB (✅ Currently integrated)
- Azure OpenAI Service (🟡 Ready for integration)
- Azure AI Search (🟡 Ready for integration)
- Azure Speech Services (🟡 Ready for integration)
- Azure Blob Storage (📋 Planned)
- Redis Cache for performance

For detailed implementation status, see [docs/implementation_status.md](docs/implementation_status.md)

## Product Roadmap

### ✅ Phase 1: MVP - "Core Strategic Clarity Loop" (COMPLETE)
- ✅ Strategic Foundation with hierarchical goals
- ✅ CEO's Log with voice input and AI tagging
- ✅ Objective Data Input with file parsing
- ✅ Interactive SWOT/TOWS with guided sessions
- ✅ AI-enhanced Initiative Planner

### 🚧 Phase 2: Enhanced Strategic Copilot (89% COMPLETE)
- ✅ Strategic Canvas with AI assistance
- ✅ Conversation memory and context
- ✅ Risk/Opportunity detection with alerts
- ✅ Voice commands for canvas operations
- ✅ Resource tracking and allocation
- ⚠️ CEO preference learning (partial)

### 📋 Phase 3: Production Deployment
- Azure AI services integration
- Azure AD authentication
- Advanced analytics dashboard
- Mobile application
- Real-time team collaboration

## Contributing

Please refer to the CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## License

This project is proprietary software.
