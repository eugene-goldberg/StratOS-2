StratOS: Alternative Azure AI Foundry Integration Plan

Created: May 25, 2025
Based on original plan dated May 23/24, 2025, incorporating expert assessment and revised architectural strategy.

Executive Summary

This document outlines a revised integration plan for migrating StratOS's Semantic Kernel-based AI capabilities to Azure AI Foundry Agent Service. This alternative architecture emphasizes a phased approach, starting with a Unified Multi-Agent System (MAS). This strategy aims to provide enterprise-grade agent hosting, automatic scaling, built-in persistence, and comprehensive observability, while managing initial complexity and allowing for iterative evolution towards more specialized agent systems as StratOS matures.
Key Revisions from Original Plan:
- Initial Architecture: A single, Unified MAS in AI Foundry for Phase 1, with clear paths for future specialization into distinct systems.
- Backend Architecture: FastAPI on Azure Container Apps remains the primary backend.
- Agent Orchestration: Leverage Azure AI Foundry's "Connected Agents" for intra-MAS orchestration.
- Router Logic: Router/Orchestrator agents will initially rely on deterministic logic, with LLM-based intelligent routing as a potential future enhancement.
- Security: Microsoft Entra Agent ID for first-class agent identities.
- Data Architecture: Standard Agent Setup with customer-managed resources (BYOS, BYOSearch, BYO Cosmos DB).
- Search Strategy: Hybrid search (keyword + vector) in Azure AI Search from the start.
- Deployment: "Agents-as-Code" with CI/CD, emphasizing a more gradual rollout.
- Timeline: A more iterative and phased implementation timeline is implied.
- Strategic Canvas: The "Canvas Visualization Agent" is reframed as a "Canvas Interaction Agent" or a foundational component of a "Strategic Canvas Sub-System" to be developed iteratively.
This plan allows StratOS to leverage the power of Azure AI Foundry effectively from an earlier stage, with a more manageable initial scope and a clear roadmap for scaling complexity and capabilities.

1. Architectural Overview


1.1 Current Architecture (Unchanged from Original Plan)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   FastAPI   │────▶│ KernelService│────▶│ SK Skills       │
│   Backend   │     │ (In-Process) │     │ (Local Execution)│
└─────────────┘     └──────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Cosmos DB   │
                    │ (Manual Mgmt)│
                    └──────────────┘

```
Current Limitations (Unchanged from Original Plan):
- Agent orchestration handled within FastAPI process
- Manual conversation state management
- Limited scalability (bound to App Service limits)
- Complex deployment and monitoring
- No built-in agent lifecycle management

1.2 Target Architecture with AI Foundry Agent Service (Unified MAS, Phased Evolution)

```
                    ┌─────────────────────┐
                    │   React Web App     │
                    └──────────┬──────────┘
                               │ WebSockets/REST
                    ┌──────────▼──────────┐
                    │FastAPI Backend (ACA)│ ← Primary Backend
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ AI Foundry Agent    │
                    │ Service Runtime     │
                    │ (Unified MAS)       │
                    │ "Connected Agents"  │
                    └──────────┬──────────┘
                               │
      ┌────────────────────────▼────────────────────────┐
      │           Unified StratOS Agent System          │
      ├─────────────────────────────────────────────────┤
      │ • Main Orchestrator/Router Agent                │
      │ ----------------------------------------------- │
      │   *Foundation Agents Group:* │
      │   │ • CEO Log Agent                             │
      │   │ • North Star Agent                          │
      │   │ • Memory Agent                              │
      │   │ • Preference Agent                          │
      │ ----------------------------------------------- │
      │   *Analysis Agents Group:* │
      │   │ • SWOT/TOWS Agent                           │
      │   │ • Risk Detection Agent                      │
      │   │ • S+O Linkage Agent                         │
      │   │ • Market Intel Agent (Future)               │
      │ ----------------------------------------------- │
      │   *Planning & Canvas Agents Group:* │
      │   │ • Initiative Agent                          │
      │   │ • Resource Agent                            │
      │   │ • Canvas Interaction Agent (Core)           │
      │   │ • Alignment Agent                           │
      └────────────────────┬────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
  ┌───────▼───────┐  ┌──────────────┐  ┌──▼──────────┐
  │  Cosmos DB    │  │ Azure AI     │  │Azure Monitor│
  │ (Agent State) │  │ Search       │  │ (Metrics)   │
  └───────────────┘  │(Hybrid RAG)  │  └─────────────┘
                    └──────────────┘

```
Key Benefits of this Phased Approach:
- Reduced initial deployment complexity.
- Faster time-to-market for core AI-powered features.
- Iterative development and learning within the AI Foundry environment.
- Clear pathway to evolve into more specialized, distinct agent systems as needed.
- Fault isolation and recovery benefits will be realized as the system potentially evolves into more separated components.

1.3 Key Architectural Decisions (Incorporating Validated Parts & Revisions)


Backend Architecture: FastAPI on Azure Container Apps

- Primary Backend: FastAPI deployed on Azure Container Apps (ACA).
- Why Not Azure Functions (for primary backend): Better WebSocket support, stateful connections, superior async handling for the main conversational interface.
- Supplementary Use: Azure Functions for discrete tool implementations and event-driven tasks callable by agents.

Agent Orchestration: Connected Agents

- Leverage Azure AI Foundry's "Connected Agents" feature for intra-MAS orchestration.
- Agents can call each other as tools within the Unified MAS.
- Automatic lifecycle management, retry logic, and state persistence.
- Built-in thread management for conversation history.

Security: Microsoft Entra Agent ID

- Each agent gets a first-class identity in Microsoft Entra.
- Agent-specific Conditional Access policies.
- Comprehensive audit logging for agent actions.
- RBAC at the agent level.

Data Architecture

- Standard Agent Setup: Customer-managed resources (BYOS, BYOSearch, BYO Cosmos DB).
- Cosmos DB Containers:
	- thread-message-store: End-user conversations
	- system-thread-message-store: Internal system messages
	- agent-entity-store: Model inputs/outputs
- Partition Keys:
	- Chat history: thread_id
	- Agent state: agent_id
	- Consider hierarchical partitioning for multi-tenancy.

Search Strategy: Hybrid from Day One

- Azure AI Search with both keyword and vector search enabled.
- Semantic ranking for improved relevance.
- Built-in indexers for Cosmos DB integration.

Deployment: Agents-as-Code

- Agent definitions stored as version-controlled JSON/YAML.
- Prompts and configurations in Git.
- CI/CD pipelines for agent deployment.
- Automated agent evaluation in pipelines.

Router/Orchestrator Logic

- The Main Orchestrator/Router Agent will primarily use deterministic logic (e.g., based on request types, keywords, predefined rules) for initial versions.
- LLM-based "intelligent routing" for ambiguous requests will be considered as a future enhancement, implemented cautiously after validating performance and cost implications.

2. Multi-Agent System Design (Unified MAS for Initial Phases)


2.1 Unified StratOS Agent System

Purpose: To provide a cohesive and intelligent suite of AI capabilities supporting the CEO's strategic workflow, encompassing foundation setting, analysis, and planning. This unified system will house all agents initially, allowing for robust intra-system collaboration.