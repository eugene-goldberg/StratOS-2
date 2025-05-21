StratOS MVP: Comprehensive Feature Descriptions

Date: May 19, 2025
Product: StratOS (Strategy Operating System)
Version: Minimum Viable Product (MVP)

I. Introduction

This document provides a comprehensive and detailed description of every feature planned for the StratOS Minimum Viable Product (MVP). It consolidates information from the product roadmap, UX vision, technology stack, and various feature deep dives. The MVP is designed to deliver core value to CEOs by enabling them to define their strategic foundation, capture subjective insights, integrate objective data, receive initial AI-driven analysis, and formulate basic strategic plans, all within a secure and intuitive platform.
The StratOS MVP is built upon the SOAP (Subjective, Objective, Analysis, Plan) methodology and the WHAT/WHY/HOW strategic tenets.

II. Core MVP Features

The MVP includes the following core features and foundational components:
1. F0.0: Authentication & Authorization (Foundational)
2. F1.1: "Our North Star" Module (The WHY & WHAT)
3. F1.2: "CEO's Log" (Subjective Input - S)
4. F2.1: "Foundational Objective Data Input" (Objective Input - O)
5. F3.1: "Initial S+O Linkage & Prompting" (Analysis - A)
6. F3.2: "Guided SWOT/TOWS AI Assistant" (Analysis - A)
7. F4.1: "Basic Initiative Planner" (Plan - P)
---

1. F0.0: Authentication & Authorization (Foundational)

- Core Purpose: To ensure secure access to the StratOS platform and enforce user-level data isolation, protecting sensitive strategic information.
- SOAP/Tenets Link: Underpins the entire platform, ensuring the privacy and integrity of all S, O, A, and P data associated with a user's WHY, WHAT, and HOW.
- Key Functionalities (MVP):
  User Management (Backend & Frontend):
  
  User registration with email, password (securely hashed using bcrypt), and optional profile information (e.g., full name, company name, job title).
  Secure user login mechanism.
  Pydantic models for user data (UserBase, UserCreate, UserInDB, UserResponse, TokenData).
  User records stored in Azure Cosmos DB ("Users" container, partitioned by email or user ID).
  
  
  JWT-Based Authentication (Backend & Frontend):
  
  OAuth2-compatible login endpoint (/api/auth/token) issues short-lived JWT access tokens and potentially longer-lived refresh tokens (refresh mechanism optional for strict MVP but planned).
  Tokens contain user ID and email claims.
  FastAPI dependency (get_current_active_user in dependencies.py) validates JWTs from Authorization: Bearer <token> headers on all protected API endpoints.
  Frontend apiService.ts (axios interceptor) automatically includes the access token in requests.
  Frontend authStore.ts (Zustand) manages authentication state, user profile, and secure token storage (e.g., localStorage).
  Login and Registration pages (Login.tsx, Register.tsx) for user interaction.
  
  
  User-Level Data Isolation (Authorization - Backend):
  
  All backend services (StrategicFoundationService, SubjectiveInputService, ObjectiveDataService, AnalysisService, PlanningService) are refactored to accept and use the authenticated user_id for all data operations.
  Database queries in all services are strictly filtered by user_id to ensure a user can only access and modify their own data.
  HTTP 401 (Unauthorized) for invalid/missing tokens and HTTP 403 (Forbidden) for attempts to access data not owned by the user.
  
  
  Protected Routes (Frontend):
  
  React component (ProtectedRoute.tsx) wraps routes for authenticated sections, redirecting to login if the user is not authenticated.
  
  
  Security Best Practices:
  
  Secure password hashing.
  Environment variables for sensitive settings (SECRET_KEY, token expiration).
  HTTPS enforced for all communication.
  
  
  
---

2. F1.1: "Our North Star" Module (The WHY & WHAT)

- Core Purpose: To allow the CEO to define, document, and persist the organization's fundamental strategic direction—its Purpose, Vision, Core Values (the WHY), and overarching Strategic Goals (the WHATs). This module provides the foundational context for all other strategic activities within StratOS.
- SOAP/Tenets Link: Directly captures and makes explicit the CEO-driven WHY and WHAT. This data serves as a reference for alignment in (A)nalysis and (P)lanning.
- Key Functionalities (MVP):
  Data Management (Backend - StrategicFoundationService):
  
  Stores a single, comprehensive "NorthStar" document per user_id in Azure Cosmos DB ("NorthStarConfigurations" container). The user_id serves as the document ID and partition key.
  The NorthStar document embeds:
  
  Purpose: Statement, description.
  Vision: Statement, description, time horizon.
  Values: List of Value objects (name, description, examples).
  Strategic Goals (WHATs): List of StrategicGoal objects (title, description, time frame, basic metrics).
  
  
  Service methods for get_north_star(user_id) and create_or_update_north_star(user_id, data).
  Granular CRUD methods for adding, updating, and deleting individual Value and StrategicGoal objects within the user's NorthStar document (involves reading, modifying the list, and replacing the parent document).
  
  
  API Endpoints (Backend - Strategic Foundation Router):
  
  Endpoints for retrieving the entire North Star for the authenticated user.
  Endpoints for creating/updating the North Star (Purpose, Vision, and full lists of Values/Goals).
  Endpoints for granular CRUD operations on Values and Strategic Goals.
  
  
  User Interface (Frontend - NorthStar.tsx, northStarStore.ts, strategicFoundationService.ts):
  
  Dedicated UI section for displaying and editing the Purpose and Vision statements.
  Separate UI sections for managing lists of Company Values (add, view, edit, delete).
  Separate UI sections for managing lists of Strategic Goals (WHATs) (add, view, edit, delete).
  All interactions are authenticated and operate on the current user's North Star data.
  Zustand store (northStarStore.ts) manages state for North Star components, loading, and errors.
  API service (strategicFoundationService.ts) handles communication with the backend.
  
  
  
---

3. F1.2: "CEO's Log" (Subjective Input - S)

- Core Purpose: To provide a secure, private, and intelligent digital journal for the CEO to capture their "strategic mindstream"—Subjective (S) insights, intuitions, observations, concerns, and nascent ideas. This is the primary input for the (S) component of SOAP.
- SOAP/Tenets Link: Directly facilitates the capture of (S)ubjective data. Entries can be linked to the CEO's WHY and WHAT.
- Key Functionalities (MVP):
  Conversational & Manual Note Capture (Frontend & Backend):
  
  Primary (Mobile-First Conversational): CEO activates the global "StratOS Assistant" (voice or text) and dictates/types a note (e.g., "StratOS, take a strategic note: [thought]").
  Secondary (Manual Text): A "+ New Text Note" option in the CEO's Log interface.
  
  
  Voice-to-Text (Backend - SubjectiveInputService, VoiceInputSkill):
  
  Integration with Azure Cognitive Services Speech (or Azure OpenAI real-time audio STT) for transcribing dictated notes.
  Handles audio streaming from client to backend for transcription.
  
  
  Log Entry Structure & Storage (Backend - SubjectiveInputService, LogManagementSkill):
  
  Log entries stored in Azure Cosmos DB ("LogEntries" container), associated with user_id.
  Each entry includes: id (UUID), user_id, content (text), entry_type (Enum: IDEA, OBSERVATION, etc.), tags (List[LogEntryTag]), ai_generated_tags (List[str]), ai_summary (Optional[str]), ai_insights (Optional[List[str]]), created_at, updated_at.
  Pydantic models (LogEntry, LogEntryCreate, LogEntryUpdate) for data validation.
  
  
  Tagging & Linking (Frontend UI & Backend Service):
  
  Manual Tagging: CEO can add free-form text tags to log entries.
  Manual Linking to Strategic Elements: CEO can explicitly link log entries to defined WHYs (Purpose, Vision, Values) and WHATs (Strategic Goals) from the "Our North Star" module (F1.1).
  Basic AI-Suggested Tags (Backend - BasicAITaggingSkill): After a note is saved, AI suggests 2-3 relevant tags based on keyword extraction from the note's content and matching against WHY/WHAT titles. CEO can accept these suggestions in the UI.
  
  
  Viewing & Management (Frontend - CEOLog.tsx, logStore.ts, logService.ts):
  
  Reverse chronological list display of log entries (title/snippet, date, tags).
  Ability to view, edit (text, tags, links), and delete log entries.
  Basic search by keywords and filtering by date/tags.
  
  
  Synchronization: All log entries and modifications are synced across the CEO's devices.
  
---

4. F2.1: "Foundational Objective Data Input" (Objective Input - O)

- Core Purpose: To enable the CEO/user to upload, manage, and make accessible various forms of Objective (O) data (e.g., reports, spreadsheets, KPIs) that can be used for AI-driven analysis.
- SOAP/Tenets Link: Provides the (O)bjective data component for the SOAP methodology.
- Key Functionalities (MVP):
  File Upload (Frontend - ObjectiveData.tsx; Backend - ObjectiveDataService):
  
  UI for uploading common business document types (PDFs, CSVs, XLSX).
  User provides title, description, source_name, tags, and can link to WHYs/WHATs for each uploaded dataset.
  Backend API (POST /api/objective-data/datasets/upload) handles multipart form data.
  
  
  File Storage (Backend - ObjectiveDataService):
  
  Original uploaded files are securely stored in Azure Blob Storage.
  
  
  Basic File Parsing (Backend - ObjectiveDataService):
  
  PDFs: Extract raw text content using libraries like PyPDF2 or pdfplumber.
  CSVs/XLSX: Parse using pandas. For MVP, extract sheet names, column headers, and a textual summary or first N rows of key tables for indexing.
  
  
  Metadata Storage (Backend - ObjectiveDataService):
  
  Metadata for each uploaded dataset (title, description, blob URI, file type, tags, parsed content summary, processing status) stored in Azure Cosmos DB ("ObjectiveDataSources" or "datasets" container).
  Pydantic models (DataSet, DataSetCreate, etc.) for data structure.
  
  
  AI Indexing Pipeline (Backend - ObjectiveDataService, kernel_service):
  
  Asynchronous Task: Triggered after file upload and initial parsing.
  Content Chunking: Parsed textual content is broken into smaller, semantically relevant chunks (e.g., using _create_semantic_chunks logic).
  Embedding Generation: Each chunk is converted into a vector embedding using Azure OpenAI embedding service (via kernel_service).
  Vector Storage: Chunks, their embeddings, and associated metadata (dataset ID, user ID, title) are stored in Azure AI Search (configured as the Semantic Kernel memory store, collection e.g., dataset-{dataset_id}).
  Dataset status in Cosmos DB is updated (e.g., "uploaded," "parsing," "indexing," "indexed," "error").
  
  
  Data Management (Frontend - ObjectiveData.tsx, objectiveDataStore.ts, objectiveDataService.ts):
  
  List uploaded datasets with their status.
  View details/metadata of a dataset.
  Delete datasets (which also removes the file from Blob Storage and indexed data from Azure AI Search).
  
  
  KPI & DataPoint Management (Basic - Backend & Frontend):
  
  CRUD operations for manually defining KPIs (KPI model) and associating time-series DataPoint entries with datasets or KPIs. Stored in Cosmos DB.
  
  
  
---

5. F3.1: "Initial S+O Linkage & Prompting" (Analysis - A)

- Core Purpose: To be the initial AI-driven analytical feature that helps the CEO discover and reflect upon potential connections (correlations, contradictions, emerging themes) between their Subjective (S) insights (from CEO's Log) and the available Objective (O) data (from uploaded datasets).
- SOAP/Tenets Link: Represents a core part of the (A)nalysis phase, directly using (S) and (O) to generate initial insights that can inform the HOW.
- Key Functionalities (MVP):
  User-Initiated Analysis (Frontend - Analysis.tsx or Insights.tsx; Backend - AnalysisService):
  
  CEO can trigger an S+O linkage discovery process, potentially providing context like a specific topic, date range, or selecting specific S log entries and/or O datasets.
  API endpoint: POST /api/analysis/so-linkage/discover.
  
  
  Contextual Data Retrieval (Backend - AnalysisService, StrategicContextRetrieverSkill):
  
  The service calls StrategicContextRetrieverSkill (via kernel_service).
  This skill fetches relevant (S) snippets from the CEO's Log (indexed in Azure AI Search).
  It also fetches relevant (O) data snippets from indexed datasets (F2.1 content in Azure AI Search).
  
  
  AI-Powered Linkage Discovery (Backend - SubjectiveObjectiveLinkageSkill):
  
  The AnalysisService passes the retrieved S and O snippets (as JSON strings) and topic context to the FindPotentialLinkages function of this Semantic Kernel skill.
  The skill uses a detailed LLM prompt (Azure OpenAI) to analyze pairs/groups of S and O snippets.
  The LLM identifies and returns (as a JSON array) potential linkages, each with:
  
  subjective_ref_id, objective_ref_id
  linkage_type ("correlation," "contradiction," "emerging_theme")
  ai_summary_of_linkage (LLM's explanation of the connection)
  ai_prompt_for_ceo (LLM-generated question to stimulate CEO's thought)
  
  
  
  
  Storage of Linkages (Backend - AnalysisService):
  
  Discovered linkages are parsed and stored as SOLinkage objects in a dedicated "SOLinkages" container in Azure Cosmos DB, linked to user_id and context.
  Pydantic models (SOLinkage, SOLinkageCreate, SOLinkageResponse) for data structure.
  
  
  Presentation of Linkages (Frontend - Analysis.tsx/Insights.tsx, analysisStore.ts):
  
  The UI displays the list of discovered linkages (e.g., as cards).
  Each card shows the S snippet, O snippet, linkage type, AI summary, and the AI-generated prompt for the CEO.
  
  
  Listing Saved Linkages (Frontend & Backend):
  
  API endpoint GET /api/analysis/so-linkage to retrieve previously saved linkages.
  
  
  
---

6. F3.2: "Guided SWOT/TOWS AI Assistant" (Analysis - A)

- Core Purpose: To provide an interactive, AI-guided module that helps the CEO construct a comprehensive SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis and then a TOWS (Threats, Opportunities, Weaknesses, Strengths) strategic alternatives matrix, leveraging relevant (S) and (O) data.
- SOAP/Tenets Link: A structured (A)nalysis tool that uses (S) and (O) to understand the current situation and then helps formulate potential strategic HOWs (via TOWS).
- Key Functionalities (MVP):
  Session Management (Backend - AnalysisService):
  
  Manages an active SWOT/TOWS analysis session (in-memory for MVP, with persistence to Cosmos DB upon completion).
  API endpoints for creating a session, adding points, getting data, saving.
  
  
  Guided SWOT Input (Frontend - Analysis.tsx or SWOT page; Backend - AnalysisService, ContextualPromptGenerationSkill):
  
  CEO defines the subject of the SWOT analysis.
  UI presents a four-quadrant SWOT matrix.
  AI Copilot Pane: For each active quadrant (S, W, O, T):
  
  AnalysisService calls StrategicContextRetrieverSkill to fetch relevant (S) log snippets and (O) data snippets based on the SWOT subject.
  These snippets, along with the current quadrant and subject, are passed to ContextualPromptGenerationSkill.generate_swot_quadrant_prompt.
  This skill uses an LLM to generate guiding questions and highlight the S/O snippets for the CEO.
  The frontend displays these AI-generated prompts.
  
  
  CEO inputs points for each quadrant. These points are saved to the active session via the AnalysisService.
  
  
  Guided TOWS Matrix Input (Frontend & Backend):
  
  After SWOT completion, UI transitions to TOWS matrix (SO, WO, ST, WT).
  AI Copilot Pane: For each active TOWS cell:
  
  AnalysisService provides the completed SWOT data (S,W,O,T points) and the active TOWS cell type to ContextualPromptGenerationSkill.generate_tows_cell_prompt.
  This skill uses an LLM to generate guiding questions for formulating strategies by combining specific SWOT elements.
  Frontend displays these AI prompts.
  
  
  CEO inputs strategic actions for each TOWS cell, saved to the session.
  
  
  Storage (Backend - AnalysisService):
  
  Completed SWOT/TOWS analyses (including all points and strategic actions) are saved as SWOTAnalysis documents (defined in models/analysis.py) in Azure Cosmos DB ("SWOTAnalyses" container or similar).
  
  
  AI-Generated Insights & TOWS Strategies (Backend - AnalysisService):
  
  Methods generate_insights and generate_tows_strategies in AnalysisService use LLMs (via kernel_service.generate_completion) with prompts constructed from the completed SWOT data to:
  
  Suggest 3-5 high-level strategic insights.
  Suggest 2-3 example strategies for each TOWS cell.
  
  
  These are saved as part of the SWOTAnalysis document.
  
  
  
---

7. F4.1: "Basic Initiative Planner" (Plan - P)

- Core Purpose: To allow the CEO to define and track high-level strategic initiatives (the HOWs) and their key actions, directly linking them to the overarching Strategic Goals (WHATs) defined in the "Our North Star" module. This is the foundational "Plan" (P) component.
- SOAP/Tenets Link: Focuses on defining the (P)lan by creating actionable HOWs that are directly linked to the CEO's WHATs.
- Key Functionalities (MVP):
  Initiative Management (Backend - PlanningService; Frontend - Planning.tsx, planningStore.ts, planningService.ts):
  
  CRUD operations for Strategic Initiatives.
  Each initiative includes: title, description, owner (manual text), target_start_date, target_end_date, status (Enum: Not Started, In Progress, Completed, etc.).
  Crucial Linkage: Each initiative must be linked to a primary StrategicGoal (WHAT) from the "Our North Star" module (F1.1). The backend service validates this link.
  Initiatives stored in Azure Cosmos DB ("StrategicInitiatives" or "Initiatives" container).
  
  
  Action Management (Backend & Frontend):
  
  Within each initiative, users can define a list of key actions/milestones.
  Each action includes: description, owner (manual text), target_completion_date, status (Enum: To Do, In Progress, Done).
  Actions are stored as a nested array within their parent Initiative document in Cosmos DB for MVP.
  
  
  Strategic Plan Concept (MVP):
  
  For MVP, a "Strategic Plan" might not be a separate explicit database entity but rather a conceptual grouping of initiatives, perhaps filtered by user_id or by a set of related Strategic Goals. The Planning Router and PlanningService primarily operate on Initiative resources.
  
  
  User Interface (Frontend - Planning.tsx, InitiativeDialog.tsx, ActionDialog.tsx):
  
  List display of initiatives, with filtering options (e.g., by linked Strategic Goal, status).
  Forms/dialogs for creating and editing initiatives, including a selector to link to a Strategic Goal (fetched from northStarStore).
  Interface within an initiative's view to add, view, edit, and delete its actions.
  Visual indicators for initiative and action progress/status.
  
  
  
---
This comprehensive description covers all planned MVP features, their core purpose, key functionalities from both backend and frontend perspectives, and their alignment with the SOAP and WHAT/WHY/HOW frameworks.