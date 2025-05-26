# StratOS: Next Steps - Phase 2: Advancing AI Partnership & Interactive Strategy Development

## 1. Introduction

This document outlines "Phase 2" of StratOS development, building upon the foundational enhancements of "Phase 1" (`docs/next_steps.md`). Phase 2 aims to significantly advance StratOS's capabilities as an AI copilot, focusing on more sophisticated AI interactions, realizing key aspects of the Strategic Canvas, and improving the conversational nature of the AI. This phase directly targets substantial progress in Pillars 1, 2, and 3 of the "Beyond MVP" product vision.

## 2. Overarching Goals for Phase 2

*   **Elevate AI from Assistant to Partner:** Transition AI from providing contextual information to actively participating in strategic dialogue and initial predictive analysis.
*   **Realize Core Interactive Strategic Canvas:** Implement the frontend for the Strategic Canvas and enable initial AI interactions directly on it.
*   **Enhance Conversational AI:** Improve the context-awareness and proactivity of the StratOS AI Assistant.
*   **Strengthen Strategic Planning Capabilities:** Introduce more advanced features for initiative and goal management.

## 3. Key Development Areas & Specific Enhancements

### A. Pillar 1: Deep AI Learning, Personalization, & Proactive Foresight (Initial Steps)

**A1. Basic Predictive Elements & Proactive Flagging (Evolution of F3.5)**
    *   **Task:** Implement AI-driven risk/opportunity flagging.
        *   **Details:** Develop a Semantic Kernel skill that periodically analyzes new Subjective (CEO Log) and Objective (uploaded data summaries, KPI trends) inputs. This skill should identify potential emerging risks or opportunities based on predefined patterns or anomalies and flag them to the CEO (e.g., as a special type of Insight or a notification).
        *   **Backend:** `AnalysisService` to orchestrate this; new skill in `ai/skills/analysis_skills`.
        *   **Impact:** Introduces initial proactive AI behavior, moving towards the "Early Warning System."
    *   **Task:** Initial AI learning of CEO preferences.
        *   **Details:** Start capturing implicit feedback (e.g., which AI-suggested insights/tags are accepted/dismissed, which data sources are frequently consulted after certain types of log entries). Store this feedback linked to `user_id`. This data will be foundational for future hyper-personalization.
        *   **Backend:** Requires new models/storage for user feedback/preferences; services to log this data.
        *   **Impact:** Lays groundwork for hyper-personalized AI copilot.

### B. Pillar 2: The Fully Realized "Strategic Canvas" & Immersive Collaboration (Core Implementation)

**B1. Strategic Canvas Frontend Implementation**
    *   **Task:** Develop the core frontend for the Strategic Canvas.
        *   **Details:** Implement the UI for the canvas, allowing users to create nodes (text, basic shapes), draw freehand connections, and arrange elements. Integrate with `SubjectiveInputService` for saving/loading canvas state.
        *   **Frontend:** New React components for canvas, drawing tools, node management.
        *   **Impact:** Delivers the basic visual ideation workspace.

**B2. Initial AI Interaction on Strategic Canvas**
    *   **Task:** AI structuring of freehand notes on canvas.
        *   **Details:** When a user adds a text block or a recognized shape with text, allow them to trigger an AI function (via `kernel_service`) that attempts to parse the text, identify key concepts, and suggest a more structured representation (e.g., breaking a paragraph into distinct idea nodes, suggesting formalizing a node as a Goal or Initiative).
        *   **Backend:** New Semantic Kernel skill; `SubjectiveInputService` to mediate.
        *   **Frontend:** UI to trigger AI structuring and display suggestions.
        *   **Impact:** First step towards AI as an active participant on the canvas.
    *   **Task:** AI suggestion of links between canvas nodes.
        *   **Details:** Implement an AI function that analyzes the content of selected canvas nodes (or all nodes) and suggests potential meaningful connections between them based on semantic similarity or keyword relationships.
        *   **Backend:** New Semantic Kernel skill.
        *   **Frontend:** Visual representation of suggested links.
        *   **Impact:** AI helps uncover relationships in the CEO's visual thoughts.

**B3. Basic Multimodal Input on Canvas**
    *   **Task:** Voice commands to add/modify canvas nodes.
        *   **Details:** Allow users to issue simple voice commands like "StratOS, add a node titled 'New Market Entry'" or "Connect this node to that node with a 'depends on' link." This requires integrating voice input with canvas actions.
        *   **Backend:** `VoiceInputSkill` to process commands; `SubjectiveInputService` to apply changes to canvas.
        *   **Frontend:** Microphone access and voice input handling within the canvas UI.
        *   **Impact:** Introduces initial multimodal interaction on the canvas.

### C. Pillar 3: Full-Duplex, Context-Aware Conversational AI Partner (Enhancements)

**C1. Improved Conversational Context Memory**
    *   **Task:** Enhance AI Assistant's short-term memory across interactions within a session.
        *   **Details:** Modify `kernel_service` or the way skills are invoked to maintain a more robust conversational context (e.g., remembering the last few turns of dialogue, the subject of the current discussion) to provide more relevant follow-up responses or actions.
        *   **Backend:** Primarily `kernel_service` and skill design.
        *   **Impact:** Makes AI Assistant interactions feel more natural and less transactional.

**C2. Basic AI-Initiated Dialogue for Critical Alerts**
    *   **Task:** Implement a mechanism for AI to proactively surface critical alerts from A1 (Risk/Opportunity Flagging).
        *   **Details:** If the AI (from task A1) identifies a high-priority risk/opportunity, it should be able to trigger a notification or a simple proactive message via the UI (e.g., "CEO, I've identified a potential market shift based on new data. Would you like to review?").
        *   **Backend:** `AnalysisService` to generate alert; mechanism to push notification to frontend (e.g., WebSockets if available, or a polling mechanism).
        *   **Frontend:** UI to display proactive AI alerts/messages.
        *   **Impact:** First step towards proactive AI dialogue.

### D. Pillar 4: Enterprise-Wide Strategic Alignment & Execution Ecosystem (Initial Steps)

**D1. Cascading Goals (Basic Implementation)**
    *   **Task:** Allow Strategic Goals to have sub-goals or be linked to departmental objectives.
        *   **Details:** Modify the `StrategicGoal` model in `models/strategic_foundation.py` to support a parent-child relationship (e.g., `parent_goal_id: Optional[UUID]`) or a list of sub-goals. Update `StrategicFoundationService` and relevant UI to manage these hierarchical goals.
        *   **Backend:** Model changes, service logic updates.
        *   **Frontend:** UI to create and visualize hierarchical goals.
        *   **Impact:** Begins to address enterprise-wide alignment by allowing strategy to cascade.

**D2. Basic Resource Tracking for Initiatives**
    *   **Task:** Enhance `Resource` model and management within Initiatives.
        *   **Details:** The `Resource` model (in `models/planning.py`) currently exists. Ensure the UI for `PlanningService` allows for clear definition and basic tracking (e.g., allocated vs. consumed, if applicable for MVP+1) of these resources against initiatives. No complex allocation algorithms yet, just better capture and visibility.
        *   **Backend:** Service logic for `Resource` CRUD is in place.
        *   **Frontend:** UI enhancements in the Planning module.
        *   **Impact:** Improves the "P" (Plan) component by adding more detail to initiatives.

## 4. Cross-Cutting Concerns (Continued from Phase 1)

*   **API Documentation:** Continue updates.
*   **Testing:** Expand test coverage for all new and modified functionalities.
*   **Logging & Monitoring:** Enhance as new features are added.

## 5. Prioritization Approach for Phase 2 (Suggested)

1.  **High Priority:**
    *   Strategic Canvas Frontend (Core) (B1).
    *   AI Structuring of Canvas Notes (B2).
    *   Cascading Goals (Basic) (D1).
    *   Improved Conversational Context Memory (C1).
2.  **Medium Priority:**
    *   AI Risk/Opportunity Flagging (A1 - Task 1).
    *   AI Suggestion of Canvas Links (B2).
    *   Basic AI-Initiated Dialogue for Alerts (C2).
    *   Basic Resource Tracking UI (D2).
3.  **Lower Priority / R&D Focus:**
    *   Voice Commands on Canvas (B3 - can be complex).
    *   Initial AI Learning of CEO Preferences (A1 - Task 2, foundational for long term).

This Phase 2 plan builds significantly on the MVP and Phase 1, pushing StratOS towards a more interactive and intelligent strategic partner, with a strong focus on realizing the initial version of the Strategic Canvas.
