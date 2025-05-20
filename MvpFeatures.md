StratOS MVP: Master Feature Implementation Guide
Date: May 20, 2025
Product: StratOS (Strategy Operating System)
Version: Minimum Viable Product (MVP)
I. Introduction
This document provides a comprehensive and detailed description of every feature planned for the StratOS Minimum Viable Product (MVP), outlining the expected implementation for both backend and frontend components. It consolidates the project vision, roadmap, UX principles, technology choices, and specific feature deep dives, reflecting the intended functional state of the MVP upon completion.
The StratOS MVP is designed to deliver core value to CEOs by enabling them to:
Define their strategic foundation (WHY and WHAT).
Capture subjective insights (S).
Integrate foundational objective data (O).
Receive initial AI-driven analysis (A).
Formulate basic strategic plans (P).
All features are built upon the SOAP (Subjective, Objective, Analysis, Plan) methodology and the WHAT/WHY/HOW strategic tenets, within a secure, authenticated, and user-centric platform.
II. Foundational Components (Implemented or In Progress)
F0.0: Authentication & Authorization System
Core Purpose: To secure the StratOS platform, authenticate users, and ensure strict user-level data isolation for all strategic information.
SOAP/Tenets Link: Underpins the integrity and confidentiality of all user-specific WHY, WHAT, HOW, S, O, A, and P data.
Expected Implementation (MVP):
Backend (AuthService, models/user.py, routers/auth.py, dependencies.py):
User registration with email, full name, and securely hashed password (bcrypt via passlib).
User login via OAuth2 password flow (/api/auth/token) issuing JWT access tokens (short-lived, e.g., 30-60 mins) and potentially refresh tokens (longer-lived, for seamless re-authentication - if fully implemented for MVP).
JWTs contain user_id and email claims, signed with a SECRET_KEY (from environment variables).
User data (including hashed_password) stored in Azure Cosmos DB ("Users" container, partitioned by email or user ID).
FastAPI dependency (get_current_active_user) in dependencies.py to:
Extract JWT from Authorization: Bearer <token> header.
Decode and validate the token (signature, expiration).
Retrieve the active user from the database based on token claims.
Make the authenticated user object (or user_id) available to protected API endpoints.
All other API routers (Strategic Foundation, Subjective Input, Objective Data, Analysis, Planning) are protected and use this dependency.
All service methods are refactored to accept user_id and enforce data isolation by filtering all database queries by this user_id.
Frontend (authService.ts, authStore.ts, Login.tsx, Register.tsx, ProtectedRoute.tsx, apiService.ts):
Login and Registration pages with forms, input validation, and interaction with authService.ts.
authStore.ts (Zustand) manages authentication state (user info, token, loading/error states) and persists token(s) securely (e.g., localStorage).
apiService.ts (axios instance) includes an interceptor to automatically attach the JWT access token to outgoing requests to protected backend endpoints.
Logic to handle token expiration (e.g., attempt refresh if refresh tokens are used, or redirect to login on 401 errors).
ProtectedRoute.tsx to guard application routes, redirecting unauthenticated users to the login page.
III. Core MVP Features: Detailed Implementation Descriptions
F1.1: "Our North Star" Module (The WHY & WHAT)
Core Purpose: Enables the CEO to define, document, and persist the organization's fundamental strategic direction: Purpose, Vision, Core Values (the WHY), and overarching Strategic Goals (the WHATs).
SOAP/Tenets Link: Directly captures and makes explicit the CEO-driven WHY and WHAT. This data serves as a reference for alignment in (A)nalysis and (P)lanning.
Expected Implementation (MVP):
Backend (StrategicFoundationService, models/strategic_foundation.py, routers/strategic_foundation.py):
A single "NorthStar" document is stored per user_id in Azure Cosmos DB ("NorthStarConfigurations" container), with user_id as the document ID and partition key.
The NorthStar document embeds Purpose, Vision objects, and lists of Value and StrategicGoal objects.
StrategicFoundationService provides methods:
get_north_star(user_id): Retrieves the user's North Star document.
create_or_update_north_star(user_id, data): Creates a new North Star document if one doesn't exist for the user, or updates the existing one. Handles updates to embedded objects and lists (for MVP, list updates may involve replacing the entire list).
Granular CRUD methods for Value and StrategicGoal objects within a user's North Star document (e.g., add_value_to_north_star, update_strategic_goal_in_north_star). These methods read the parent North Star, modify the relevant list, and replace the entire document.
Methods like get_strategic_goal(user_id, goal_id) and list_strategic_goals(user_id) for other services to consume.
API endpoints in Strategic Foundation Router map to these service methods, secured by JWT authentication and operating on the authenticated user's data.
Frontend (NorthStar.tsx, northStarStore.ts, strategicFoundationService.ts):
A dedicated UI section ("Our North Star") allows the authenticated CEO to view and edit their Purpose and Vision statements.
Separate UI sections within "Our North Star" for managing lists of Company Values (add, view, edit, delete forms/dialogs).
Separate UI sections for managing lists of Strategic Goals (WHATs) (add, view, edit, delete forms/dialogs).
northStarStore.ts (Zustand) manages the state of the North Star components, handles API interactions via strategicFoundationService.ts, and manages loading/error states.
All displayed data and operations are for the currently authenticated user.
F1.2: "CEO's Log" (Subjective Input - S)
Core Purpose: Provides a secure, private, and intelligent digital journal for the CEO to capture their Subjective (S) "strategic mindstream."
SOAP/Tenets Link: Primary input for the (S)ubjective component. Entries can be linked to WHYs/WHATs.
Expected Implementation (MVP):
Backend (SubjectiveInputService, VoiceInputSkill, LogManagementSkill, BasicAITaggingSkill, models/subjective_input.py, routers/subjective_input.py):
Conversational & Manual Note Capture:
Primary: CEO uses the global StratOS Assistant (voice input via API endpoint like POST /api/subjective/log-entries/voice-note/stream).
VoiceInputSkill (Semantic Kernel native function) uses Azure Cognitive Services Speech (or Azure OpenAI real-time audio STT) for streaming transcription of audio chunks sent from the client.
SubjectiveInputService orchestrates voice note creation: receives transcribed text, calls LogManagementSkill to save, then calls BasicAITaggingSkill.
Secondary: Manual text note creation via POST /api/subjective/log-entries/.
Log Entry Storage: LogEntry objects (Pydantic model: content, type, tags, AI fields, timestamps, user_id) stored in Azure Cosmos DB ("LogEntries" container), partitioned by user_id or id.
Tagging & Linking:
LogManagementSkill handles CRUD for LogEntry tags (which can be free-form or link to WHY/WHAT IDs).
BasicAITaggingSkill (Semantic Kernel function using LLM) takes log entry text and a list of current WHY/WHAT titles, and returns a JSON list of suggested string tags based on keyword extraction and matching. The SubjectiveInputService appends these to the LogEntry as ai_suggested_tags.
CRUD API endpoints for log entries, secured and user-specific.
Frontend (CEOLog.tsx, logStore.ts, logService.ts, VoiceInputButton.tsx):
Conversational Capture: Global "StratOS Assistant" microphone icon. VoiceInputButton.tsx uses Web Audio API to capture audio, streams it to the backend. Assistant UI shows "Listening," "Transcribing," then transcribed text for confirmation before saving.
Log Management UI: CEOLog.tsx displays entries in a reverse chronological list (title/snippet, date, tags). Allows viewing, editing (text, manual tags, manual links to WHY/WHATs), and deleting.
AI Tag Display: Displays ai_suggested_tags from the backend, allowing the CEO to one-click accept them into the manual tags list.
logStore.ts (Zustand) manages log entries, current entry, voice recording state, loading/error states.
logService.ts handles API calls. All data synced across devices.
F2.1: "Foundational Objective Data Input" (Objective Input - O)
Core Purpose: Enables users to upload, manage, and make accessible Objective (O) data (PDFs, CSVs, XLSX files) for AI-driven analysis.
SOAP/Tenets Link: Provides the (O)bjective data component.
Expected Implementation (MVP):
Backend (ObjectiveDataService, models/objective_data.py, routers/objective_data.py):
File Upload & Storage: API endpoint (POST /api/objective-data/datasets/upload) accepts multipart form data (file, title, description, tags, links to WHYs/WHATs). Original files stored in Azure Blob Storage.
Metadata Storage: DataSet metadata (Pydantic model: title, description, blob URI, file type, tags, parsed content summary, processing status, user_id) stored in Azure Cosmos DB ("datasets" container).
File Parsing:
PDFs: PyPDF2 or pdfplumber extracts text.
CSVs/XLSX: pandas extracts sheet names, column headers, textual summary/first N rows.
AI Indexing Pipeline (Asynchronous Task via _trigger_ai_indexing):
Parsed textual content is chunked (using _create_semantic_chunks).
Each chunk is embedded using Azure OpenAI embedding service (via kernel_service).
Chunks, embeddings, and metadata (dataset ID, user ID, title) stored in Azure AI Search (vector store, collection dataset-{dataset_id} via kernel_service.remember).
Dataset status in Cosmos DB updated ("uploaded," "parsing," "indexing," "indexed," "error").
CRUD for Datasets, KPIs, DataPoints: Service methods and API endpoints for managing metadata of DataSet objects, and for basic CRUD of KPI and DataPoint objects (stored in separate Cosmos DB containers).
Deletion: delete_dataset method ensures deletion from Cosmos DB, Blob Storage, and Azure AI Search.
Frontend (ObjectiveData.tsx, objectiveDataStore.ts, objectiveDataService.ts):
UI to list uploaded datasets with their processing status.
File upload form (file input, title, description, tags, linking to WHYs/WHATs).
objectiveDataService.ts handles FormData submission.
objectiveDataStore.ts (Zustand) manages dataset list, upload state, loading/error states.
UI to view dataset details and delete datasets.
Basic UI for managing KPIs and DataPoints if directly user-managed in MVP.
F3.1: "Initial S+O Linkage & Prompting" (Analysis - A)
Core Purpose: AI-driven feature to help the CEO discover potential connections (correlations, contradictions, emerging themes) between their Subjective (S) insights and available Objective (O) data.
SOAP/Tenets Link: Core (A)nalysis feature, directly using (S) and (O) to generate insights.
Expected Implementation (MVP):
Backend (AnalysisService, SubjectiveObjectiveLinkageSkill, StrategicContextRetrieverSkill, models/analysis.py (SOLinkage models), routers/analysis.py):
User-Initiated Discovery: API endpoint (POST /api/analysis/so-linkage/discover) accepts user_id, topic_context, optional S-entry IDs, optional O-dataset IDs, date ranges.
Data Retrieval: AnalysisService calls StrategicContextRetrieverSkill (via kernel_service) to fetch relevant (S) snippets (from CEO's Log indexed in Azure AI Search) and (O) snippets (from indexed datasets in Azure AI Search).
AI Linkage Discovery: Retrieved S and O snippets (as JSON strings) and topic_context are passed to SubjectiveObjectiveLinkageSkill.FindPotentialLinkages. This SK semantic function uses a detailed LLM prompt (Azure OpenAI) to analyze S+O pairs/groups and identify linkages.
LLM Output: LLM returns a JSON array of linkage objects, each with subjective_ref_id, objective_ref_id, linkage_type ("correlation," "contradiction," "emerging_theme"), ai_summary_of_linkage, and ai_prompt_for_ceo.
Storage: AnalysisService parses the LLM response and stores each valid linkage as an SOLinkage object (Pydantic model) in a new "SOLinkages" container in Azure Cosmos DB.
API endpoints for listing (GET /api/analysis/so-linkage) and deleting S+O linkages.
Frontend (Analysis.tsx or new Insights.tsx, analysisStore.ts or soLinkageStore.ts, analysisService.ts):
UI to trigger S+O linkage discovery (e.g., button with context input fields).
analysisStore.ts action calls the discoverSOLinkages API.
UI displays the returned list of linkages (e.g., as cards showing S snippet, O snippet, linkage type, AI summary, and the AI-generated prompt for the CEO).
UI to list/view previously saved linkages.
F3.2: "Guided SWOT/TOWS AI Assistant" (Analysis - A)
Core Purpose: Interactive, AI-guided module for constructing SWOT and TOWS analyses, with AI providing contextual prompts based on (S) and (O) data.
SOAP/Tenets Link: Structured (A)nalysis tool using (S) and (O) to understand the current situation and formulate potential strategic HOWs (via TOWS).
Expected Implementation (MVP):
Backend (AnalysisService, SWOTAnalysisSkill, ContextualPromptGenerationSkill, StrategicContextRetrieverSkill, models/analysis.py (SWOT/TOWS models), routers/analysis.py):
Session Management: AnalysisService manages an active SWOT/TOWS session (in-memory for MVP, persisted to Cosmos DB on completion via save_analysis).
Guided SWOT Input:
CEO defines SWOT subject.
For each quadrant (S, W, O, T), AnalysisService orchestrates:
Calling StrategicContextRetrieverSkill to get relevant (S) log snippets and (O) data snippets based on swot_subject.
Passing these snippets, quadrant info, and subject to ContextualPromptGenerationSkill.generate_swot_quadrant_prompt.
This SK skill uses an LLM to generate guiding questions and highlight relevant S/O snippets for the CEO.
CEO inputs points for each quadrant; these are added to the session via AnalysisService (which might call a simple SWOTAnalysisSkill data handling function).
Guided TOWS Input:
After SWOT, for each TOWS cell (SO, WO, ST, WT), AnalysisService orchestrates:
Providing the completed SWOT data and active TOWS cell to ContextualPromptGenerationSkill.generate_tows_cell_prompt.
This SK skill uses an LLM to generate guiding questions for formulating strategies.
CEO inputs strategic actions, saved to the session.
Storage: Completed SWOT/TOWS analyses stored as SWOTAnalysis documents in Azure Cosmos DB ("SWOTAnalyses" container).
AI-Generated Insights & TOWS Strategies: AnalysisService.generate_insights and AnalysisService.generate_tows_strategies methods use LLMs with prompts constructed from completed SWOT data to suggest high-level insights and example TOWS strategies, which are then saved with the analysis.
Frontend (Analysis.tsx or dedicated SWOT page, swotTowsStore.ts, analysisService.ts):
UI for initiating a SWOT/TOWS analysis (setting subject).
Four-quadrant SWOT UI. "AI Copilot Pane" displays LLM-generated guiding questions and S/O snippets for the active quadrant. CEO inputs points.
UI for TOWS matrix. "AI Copilot Pane" displays LLM-generated guiding questions for the active cell. CEO inputs strategic actions.
swotTowsStore.ts manages session state, user inputs, and AI prompts.
Interactions call analysisService.ts methods to progress the session and save data.
F4.1: "Basic Initiative Planner" (Plan - P)
Core Purpose: Allows CEO to define and track high-level strategic initiatives (HOWs) and their key actions, linked to Strategic Goals (WHATs).
SOAP/Tenets Link: Foundational (P)lan component, defining actionable HOWs linked to WHATs.
Expected Implementation (MVP):
Backend (PlanningService, models/planning.py, routers/planning.py):
CRUD operations for Initiative objects. Each initiative has title, description, owner (text), target_start_date, target_end_date, status (Enum), and crucially, a linked_strategic_goal_id (UUID referencing a StrategicGoal from F1.1).
PlanningService validates the linked_strategic_goal_id against existing goals for the user.
Action objects (description, owner, target date, status) are stored as a nested list within their parent Initiative document in Azure Cosmos DB ("StrategicInitiatives" or "Initiatives" container).
API endpoints in Planning Router for CRUD on initiatives and their nested actions, secured and user-specific.
Frontend (Planning.tsx, planningStore.ts, planningService.ts, InitiativeDialog.tsx, ActionDialog.tsx):
UI to list initiatives, with filtering (e.g., by linked Strategic Goal, status).
Forms/dialogs (InitiativeDialog.tsx) for creating/editing initiatives. Includes a selector to choose an existing StrategicGoal (from northStarStore data) to link the initiative to.
Within an initiative's detail view, UI to add, view, edit, and delete its Actions (using ActionDialog.tsx).
planningStore.ts (Zustand) manages state for initiatives, actions, loading/errors.
planningService.ts handles API communication.
Visual indicators for initiative/action progress and status.
This master document outlines the expected detailed implementation for each StratOS MVP feature. It should serve as the primary guide for development, ensuring all components align with the overall product vision and technical architecture.
