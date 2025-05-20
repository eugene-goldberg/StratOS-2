# StratOS: Strategy Operating System

StratOS is an AI-powered strategic copilot for CEOs and leadership teams, transforming how businesses develop, analyze, plan, execute, and refine their strategies for sustained success.

## Project Overview

StratOS empowers leaders by seamlessly integrating their subjective insights with objective data, providing profound analysis, and offering dynamic planning capabilities, all while ensuring clear alignment with the company's core "WHY" (Purpose, Vision, Values) and "WHAT" (Strategic Goals).

### Key Features

- **Strategic Foundation & CEO's Compass**: Define and anchor your company's WHY and WHAT
- **Subjective Input Capture**: CEO's Log and Strategic Canvas for capturing qualitative insights
- **Objective Data Integration**: KPI tracking and data upload capabilities
- **AI-Powered Analysis**: SWOT/TOWS analysis, S+O linkage, insights generation
- **Dynamic Planning**: Initiative creation, plan comparison, action tracking

## Technology Stack

### Backend
- Python with FastAPI
- Semantic Kernel (Python SDK)
- Integration with Azure OpenAI Service

### Frontend
- React with TypeScript
- Material UI components
- Recharts/Nivo for visualizations
- React Flow for Strategic Canvas

### Database
- Azure Database for PostgreSQL
- Azure Cosmos DB
- Azure AI Search

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

## Deployment

StratOS is designed to be deployed on Azure using:
- Azure App Service for the backend
- Azure Static Web Apps for the frontend
- Azure Database for PostgreSQL
- Azure Cosmos DB
- Azure AI Search
- Azure OpenAI Service

## Product Roadmap

### Phase 1: MVP - "Core Strategic Clarity Loop"
- Strategic Foundation & CEO's Compass
- CEO's Log (Subjective Input)
- Foundational Objective Data Input
- Initial S+O Linkage & Analysis
- Basic Initiative Planner

### Phase 2: Enhanced Strategic Copilot Capabilities
- Advanced Subjective Input Analysis
- Core Business System Integrations
- Interactive "What-If" Scenario Builder
- Multi-Plan Variant Generation
- Initiative & KPI Dashboard

### Phase 3 & Beyond: Autonomous Strategic Partnership
- Advanced External Data Integration
- Predictive Foresight Engine
- AI-Recommended Strategic Pivots
- Intelligent Progress Monitoring
- Leadership Team Collaboration Suite

## Contributing

Please refer to the CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## License

This project is proprietary software.
