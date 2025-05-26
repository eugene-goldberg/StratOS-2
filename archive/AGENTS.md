# AGENTS.md

## Project Overview

This AGENTS.md document provides guidance for OpenAI Codex-powered AI agents to effectively examine, plan, and directly implement the features of the StratOS Minimum Viable Product (MVP). Codex agents should leverage detailed MVP descriptions to autonomously carry out project implementation, ensuring alignment with the defined architecture, technology stack, and coding standards.

## Guidance for Codex Agents

### 1. Examination and Planning

* Agents should thoroughly analyze provided MVP documentation to gain clarity on each feature's purpose, expected backend and frontend implementation specifics, and integration points.
* Focus on understanding dependencies and interactions among MVP components, especially user authentication, data isolation, and API endpoint interactions.

### 2. Autonomous Implementation

* Codex agents are responsible for generating secure, precise, and robust implementation code directly, fully adhering to the outlined architecture and coding standards.
* Agents will autonomously develop, test, and validate each feature as specified in the MVP documentation.

### 3. Feature-Specific Implementation Instructions

Agents must closely adhere to the detailed implementation guidelines for each MVP feature:

### Foundational Components

* **Authentication & Authorization System:**

  * Backend: Implement OAuth2/JWT authentication, securely storing user data in Azure Cosmos DB, with JWT token management and API protection.
  * Frontend: Develop Login/Register pages, manage auth state with Zustand, and secure API calls with Axios.

### Core MVP Features

* **Our North Star Module (The WHY & WHAT):**

  * Backend: Implement document storage in Azure Cosmos DB, structured handling of strategic elements (Purpose, Vision, Values, Goals).
  * Frontend: Develop UI for editing strategic documents, manage state via Zustand, ensure API integration.

* **CEO's Log (Subjective Input - S):**

  * Backend: Develop voice transcription using Azure Cognitive Services, implement AI tagging and log storage.
  * Frontend: Implement voice recording, log entry management, and tagging confirmation UI.

* **Foundational Objective Data Input (Objective Input - O):**

  * Backend: Implement data upload/storage in Azure Blob Storage, parsing (PDF/CSV/XLSX), indexing in Azure AI Search.
  * Frontend: Create dataset upload interface, manage processing status, dataset details, and metadata management.

* **Initial S+O Linkage & Prompting (Analysis - A):**

  * Backend: Develop AI-driven linkage discovery, using Azure OpenAI to correlate subjective insights and objective data.
  * Frontend: Implement discovery trigger, linkage display, and management UI.

* **Guided SWOT/TOWS AI Assistant (Analysis - A):**

  * Backend: Create AI-assisted SWOT/TOWS analysis sessions, prompt generation, and session management/storage.
  * Frontend: Develop interactive SWOT/TOWS analysis UI, guided prompts, and input handling.

* **Basic Initiative Planner (Plan - P):**

  * Backend: Implement CRUD operations for strategic initiatives/actions linked to goals in Azure Cosmos DB.
  * Frontend: Develop initiative/action management UI, integration with strategic goal selection, and status tracking.

## Best Practices

* Ensure all developed code is clearly documented, with examples and concise explanations.
* Adhere strictly to security best practices, including thorough error handling, data validation, and data privacy measures.
* Engage in iterative autonomous development, consistently validating outputs and integrating feedback.

## Documentation and Maintenance

* Codex agents must autonomously maintain accurate, clear, and concise documentation reflecting the project's implementation progress.
* Continuously update implementation guidance and documentation to reflect ongoing development activities and adjustments.

