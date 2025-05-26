# StratOS: Next Steps for Development

## 1. Introduction

This document outlines the next phase of development for StratOS, building upon the current Minimum Viable Product (MVP) state. The enhancements detailed here are designed to move StratOS closer to its full product vision as an AI-powered strategic copilot, focusing on deepening AI capabilities, improving data integrity, and refining core user workflows based on the SOAP methodology and WHAT/WHY/HOW tenets.

## 2. Overarching Goals for the Next Phase

*   **Deepen AI Integration:** Transition AI features from foundational/placeholder states to more interactive and contextually aware "copilot" functionalities.
*   **Enhance Data Integrity & Linkage:** Ensure robust connections between strategic elements (North Star, CEO Logs, Objective Data, Plans) and validate these links.
*   **Solidify Backend Foundations:** Complete essential setup tasks (e.g., database initialization) and ensure all services align with user-centric data models.
*   **Iterate on Core UX Workflows:** Prepare backend capabilities to support envisioned UX advancements like the Strategic Canvas.

## 3. Key Development Areas & Specific Enhancements

### A. Enhancing AI-Powered Analysis & Guidance

This area focuses on making the AI a more active and intelligent partner in the analysis and planning processes.

**A1. Guided SWOT/TOWS AI Assistant (F3.2 - AnalysisService)**
    *   **Task:** Develop/Refine `ContextualPromptGenerationSkill`.
        *   **Details:** Modify the existing Semantic Kernel skill (or create a new one) to generate guiding questions and contextual prompts for each SWOT quadrant (Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix cell (SO, ST, WO, WT). This skill should leverage user-specific Subjective (S) and Objective (O) data snippets retrieved by `StrategicContextRetrieverSkill`. The goal is to guide the user's input rather than directly generating SWOT/TOWS content.
        *   **Impact:** Aligns F3.2 closer to the vision of an "AI-guided module."
    *   **Task:** Implement robust session management for interactive SWOT/TOWS.
        *   **Details:** Utilize the `analysis_sessions` Cosmos DB container in `AnalysisService` to store the state of an ongoing, interactive SWOT/TOWS analysis. This allows users to build their analysis step-by-step, with AI guidance at each stage.
        *   **Impact:** Enables the guided, interactive experience described in F3.2.

**A2. Planning AI Features (F4.1 - PlanningService)**
    *   **Task:** Enhance `analyze_plan_alignment`.
        *   **Details:** Improve the LLM prompt to provide more detailed qualitative feedback by comparing `StrategicPlan` initiatives against the user's specific North Star elements (Purpose, Vision, Strategic Goals). The service already fetches North Star context; ensure the prompt leverages this effectively.
        *   **Impact:** Provides more meaningful AI-driven alignment analysis.
    *   **Task:** Enhance `generate_plan_variants`.
        *   **Details:** Refine the LLM prompt to generate more strategically distinct and relevant plan variants. The prompt should encourage the AI to consider different approaches based on the base plan's details and any specified focus areas.
        *   **Impact:** Increases the value of AI-suggested plan alternatives.
    *   **Task:** Enhance `generate_actions` for initiatives.
        *   **Details:** Improve the LLM prompt to guide the AI in generating more SMART (Specific, Measurable, Achievable, Relevant, Time-bound) actions for a given initiative. The prompt should consider the initiative's title, description, status, and desired outcome.
        *   **Impact:** Provides more actionable AI-generated suggestions.

### B. Strengthening Data & Model Integrity

This area focuses on ensuring data is correctly linked, validated, and utilized across different modules.

**B1. CEO's Log - Linking to Strategic Elements (F1.2 - SubjectiveInputService, models/subjective_input.py)**
    *   **Task:** Refine `LogEntryTag` for explicit linking.
        *   **Details:** If not already precise, ensure the `LogEntryTag` model can clearly represent links to North Star elements (e.g., `reference_type: Literal["purpose", "vision", "value", "goal"]`, `reference_id: UUID`).
        *   **Impact:** Standardizes how log entries are linked to core strategic components.
    *   **Task:** Implement backend validation for these links.
        *   **Details:** In `SubjectiveInputService`, when a log entry tag representing a link is created or updated, validate that the `reference_id` corresponds to a valid North Star element owned by the user. This will likely require `SubjectiveInputService` to call methods from `StrategicFoundationService`.
        *   **Impact:** Ensures data integrity for links between subjective insights and the strategic foundation.

**B2. Objective Data - User-Provided Metadata (F2.1 - ObjectiveDataService, routers/objective_data.py)**
    *   **Task:** Update dataset upload endpoint.
        *   **Details:** Modify the `POST /api/objective-data/datasets/upload` endpoint in `objective_data_router.py` to accept `tags: Optional[List[str]]` and `linked_strategic_elements: Optional[List[Dict[str, str]]]` as part of the request (e.g., in form data alongside the file).
        *   **Impact:** Allows users to provide richer context for uploaded datasets, aligning with F2.1 description.
    *   **Note:** `ObjectiveDataService` and `DataSet` models were already updated to handle these fields; this task focuses on the router.

**B3. Planning - Model Consistency (F4.1 - models/planning.py)**
    *   **Task:** Verify `Initiative` and `StrategicPlan` models.
        *   **Details:** (Largely addressed) Ensure `Initiative` includes `user_id: UUID` and `plan_id: UUID`. Ensure `StrategicPlan` includes `user_id: UUID`. These fields are crucial for data ownership, partitioning strategies, and linking initiatives to plans.
        *   **Impact:** Correct data modeling for user-specific planning data.

### C. Foundational Backend & Application Setup

Focuses on essential backend infrastructure and setup procedures.

**C1. Cosmos DB Container Initialization (All Services, backend/main.py)**
    *   **Task:** Implement asynchronous container creation at application startup.
        *   **Details:** Create a dedicated async function in `backend/main.py` (or a new `core/db_setup.py` module) that is executed during FastAPI's startup event. This function will:
            1.  Initialize an `AsyncCosmosClient`.
            2.  Get/create the main database (`stratosdb`).
            3.  For each service/container:
                *   `AnalysisService`: `analyses` (PK: `/user_id`), `insights` (PK: `/user_id`), `so_linkages` (PK: `/user_id`), `analysis_sessions` (PK: `/user_id`).
                *   `AuthService`: `Users` (PK: `/email`).
                *   `ObjectiveDataService`: `datasets` (PK: `/id`), `kpis` (PK: `/id`), `datapoints` (PK: `/dataset_id`).
                *   `PlanningService`: `StrategicPlans` (PK: `/id`), `Initiatives` (PK: `/id`). (Re-evaluate if `/user_id` or `/plan_id` is better for `Initiatives` based on query patterns).
                *   `StrategicFoundationService`: `NorthStarConfigurations` (PK: `/id`, which is user_id).
                *   `SubjectiveInputService`: `log_entries` (PK: `/user_id`), `strategic_canvases` (PK: `/user_id`).
            4.  Use `database.create_container_if_not_exists()` with the specified ID and `PartitionKey`.
        *   **Impact:** Ensures the database schema is correctly initialized before the application starts serving requests, preventing runtime errors related to missing containers.

### D. Advancing User Experience (Backend Support)

Laying groundwork for future UX enhancements described in the product vision.

**D1. Strategic Canvas - Backend (SubjectiveInputService)**
    *   **Task:** Review and ensure robustness of existing `StrategicCanvas` and `CanvasElement` CRUD.
        *   **Details:** Verify that the current backend operations are solid and can support initial frontend development of the Strategic Canvas feature.
        *   **Impact:** Provides a stable base for this key visionary feature.
    *   **Task:** Plan for future AI interaction with canvas elements.
        *   **Details:** Conceptualize how canvas elements (text, drawings, connections) might be processed by AI (e.g., text recognition, shape analysis, relationship inference). This is exploratory for now.
        *   **Impact:** Long-term planning for AI integration with the canvas.

**D2. Voice Interaction Enhancements (SubjectiveInputService, VoiceInputSkill)**
    *   **Task:** Evaluate and plan improvements for voice streaming.
        *   **Details:** Assess the current `kernel_service`-based voice streaming. Identify potential areas for improvement towards the "full-duplex voice dialogues" vision, such as reducing latency, handling interruptions, and enabling more natural conversational flow. This is likely an R&D-heavy task.
        *   **Impact:** Moves towards a more advanced conversational AI partner experience.

## 4. Cross-Cutting Concerns

*   **API Documentation:** Regularly update OpenAPI/Swagger documentation to reflect all model changes, new endpoints, and modifications to request/response schemas.
*   **Testing:** Incrementally expand unit and integration test suites to cover all new functionalities, refactored code, `user_id` isolation logic, and interactions with AI skills.
*   **Logging & Monitoring:** Review and enhance logging across all services for consistency, ensuring sufficient detail for debugging operational issues and monitoring system health.

## 5. Prioritization Approach (Suggested)

1.  **High Priority (Foundational):**
    *   Cosmos DB Container Initialization (C1).
    *   Objective Data - User-Provided Metadata (Router Update) (B2).
    *   CEO's Log - Linking Validation (B1 - if critical for MVP integrity).
2.  **Medium Priority (Core MVP Feature Enhancement):**
    *   Guided SWOT/TOWS - `ContextualPromptGenerationSkill` development (A1).
    *   Planning AI Features - Initial enhancements to prompts (A2).
    *   Strategic Canvas - Backend robustness review (D1).
3.  **Lower Priority / Ongoing / R&D:**
    *   Guided SWOT/TOWS - Session Management (A1 - if current model is workable for MVP).
    *   Advanced Voice Interaction Enhancements (D2).
    *   Deeper AI feature development beyond initial prompt enhancements.

This plan provides a structured approach to the next development phase, balancing foundational improvements with targeted feature enhancements aligned with the StratOS product vision.
