# StratOS: UI Enhancement Plan (Phases 1 & 2)

## 1. Introduction

This document outlines frontend UI development tasks derived from the "StratOS UI Review - May 20, 2025" document. These tasks are intended to bring the current MVP frontend implementation to a functional state, aligning with backend capabilities developed in Phase 1 and Phase 2 of the "Next Steps" development plan. This plan should be used to augment `docs/next_steps_phase_1.md` and `docs/next_steps_phase_2.md` or serve as a detailed companion for UI/UX development.

## 2. Guiding Principle

Frontend development will prioritize implementing UI for features where backend services are stable and functional, ensuring a cohesive user experience. Tasks are grouped by their corresponding development phase (Phase 1 or Phase 2) based on the backend readiness and overall project priorities.

## 3. UI Enhancements for Phase 1

These tasks align with the goals of "Phase 1: Solidifying MVP, Improving Data Integrity, Initial AI Deepening."

### A. Core Application & Foundational UI

*   **Task A1: Authentication Integration**
    *   **File:** `CEOLog.tsx`
    *   **Details:** Replace "Mock user ID" with actual user data obtained from the authentication context (`authStore.ts`). Ensure all relevant service calls from `CEOLog.tsx` use the authenticated user's ID.
    *   **Impact:** Connects CEO Log to the live authentication system.
*   **Task A2: Settings - Basic Account & Security**
    *   **File:** `Settings.tsx`
    *   **Details:**
        *   **Profile Information:** Connect input fields to `authStore.ts` and `authService.ts` to allow users to view and update their profile (Full Name, Job Title, Company). Email should be read-only. Implement "Save Changes" functionality.
        *   **Password Management:** Wire up "Current Password," "New Password," "Confirm New Password" fields and the "Update Password" button to the relevant `authService.ts` method.
    *   **Impact:** Provides basic, functional account management. Other settings tabs remain placeholders or low-fidelity in Phase 1.
*   **Task A3: Dashboard - Initial Data Connectivity**
    *   **File:** `Dashboard.tsx`
    *   **Details:** Replace static/random data with live data by fetching:
        *   A few key KPIs (e.g., from `ObjectiveDataService`).
        *   A small number of recent CEO Log entries (from `SubjectiveInputService`).
        *   A few recent Strategic Canvas sessions (titles/dates, from `SubjectiveInputService`).
        *   AI Alerts & Insights (if a basic version is available from `AnalysisService`).
        *   Focus on read-only display; full interactivity can come later.
    *   **Impact:** Makes the dashboard a relevant overview for the user.

### B. CEO's Log UI (F1.2)

*   **Task B1: Implement Tab Functionality**
    *   **File:** `CEOLog.tsx`
    *   **Details:**
        *   **"Recent" Tab:** Implement correct sorting (most recent first).
        *   **"Favorites" Tab:** Requires a `is_favorite: bool` field in the `LogEntry` model and backend service support to set/unset favorites. Implement frontend filtering based on this.
        *   **"By Tag" Tab:** Implement a layout that groups entries by tags or allows filtering/selection by tags.
    *   **Impact:** Makes CEO Log navigation and organization functional.
*   **Task B2: Implement "Add to Canvas" Placeholder**
    *   **File:** `CEOLog.tsx`
    *   **Details:** The `handleAddToCanvas` function should, at a minimum, store a reference to the selected log entry (e.g., in a global state or `canvasStore`) that can be picked up when the user navigates to the Strategic Canvas. Full integration depends on Canvas implementation (Phase 2).
    *   **Impact:** Prepares for cross-module integration.

### C. Objective Data UI (F2.1)

*   **Task C1: Functional KPI and Datasets Tabs**
    *   **File:** `ObjectiveData.tsx`
    *   **Details:**
        *   Replace mock data in "Key Performance Indicators" and "Datasets" tabs with live data from `ObjectiveDataService`.
        *   Implement basic list display, view details, add, edit, and delete functionalities for KPIs and Datasets.
        *   Search and filter can be basic initially (e.g., client-side filtering on loaded data, or simple backend parameters).
    *   **Impact:** Enables management of objective data sources.
*   **Task C2: Functional "Add New KPI" / "Upload Dataset" Dialog**
    *   **File:** `ObjectiveData.tsx`
    *   **Details:**
        *   Connect the "Add New KPI" form to `objectiveDataService.createKpi`.
        *   Connect the "Upload Dataset" form to `objectiveDataService.uploadDataset`. Ensure file selection, metadata input (including new `tags` and `linked_strategic_elements` fields), and upload initiation are functional.
        *   Provide feedback on upload progress and completion/failure.
    *   **Impact:** Allows users to input their objective data.

### D. Planning UI (F4.1)

*   **Task D1: Implement "Action Tracker" and "Resources" Tabs**
    *   **File:** `Planning.tsx`
    *   **Details:** Replace placeholder text with functional UI for managing Actions and Resources within an Initiative. This involves:
        *   Listing actions/resources associated with a selected initiative.
        *   Forms to add/edit actions/resources (connecting to `PlanningService`).
        *   Ability to delete actions/resources.
    *   **Impact:** Makes the core initiative planning functional.
*   **Task D2: NorthStar.tsx Refactoring Review**
    *   **File:** `NorthStar.tsx`
    *   **Details:** Assess the "legacy" code for edit modes and dialogs. If it's causing significant issues or blocking other North Star UI work, prioritize refactoring. Otherwise, schedule for Phase 2.
    *   **Impact:** Improves maintainability and stability of North Star UI.

## 4. UI Enhancements for Phase 2

These tasks align with "Phase 2: Advancing AI Partnership & Interactive Strategy Development."

### A. Strategic Canvas UI (Pillar 2)

*   **Task A1: Core Canvas Implementation**
    *   **File:** `StrategicCanvas.tsx`
    *   **Details:**
        *   Replace `MockCanvas` with a chosen canvas library (e.g., React Flow, Konva, Fabric.js, or a custom SVG solution).
        *   Implement core functionalities: adding text nodes, basic shapes, drawing connections.
        *   Integrate with `SubjectiveInputService` for saving and loading canvas state (elements, positions, connections).
        *   Implement functional toolbar buttons: Save, Undo, Redo, Zoom In/Out, Delete Selected.
    *   **Impact:** Delivers the interactive Strategic Canvas, a key visionary feature.
*   **Task A2: Frontend for AI Interaction on Canvas**
    *   **File:** `StrategicCanvas.tsx`
    *   **Details:**
        *   UI to trigger AI structuring of freehand notes/text on canvas elements.
        *   Display AI-suggested structured representations or alternative text.
        *   UI to trigger AI suggestion of links between canvas nodes and visually represent these suggestions.
        *   Allow user to accept/reject AI suggestions.
    *   **Impact:** Brings AI partnership directly onto the canvas.
*   **Task A3: Frontend for Voice Commands on Canvas**
    *   **File:** `StrategicCanvas.tsx`
    *   **Details:** Implement microphone access, voice input capture, and sending commands to `VoiceInputSkill` via backend. Display feedback/results of voice commands on the canvas.
    *   **Impact:** Enables multimodal interaction on the canvas.

### B. Analysis UI (F3.1 & F3.2)

*   **Task B1: Implement "Insights" Tab**
    *   **File:** `Analysis.tsx`
    *   **Details:** Display AI-generated insights (from `AnalysisService`, potentially including S+O Linkages or other analytical outputs) in a user-friendly format.
    *   **Impact:** Makes AI analysis accessible.
*   **Task B2: Dynamic SWOT/TOWS Component**
    *   **File:** `Analysis.tsx` (and new SWOT/TOWS components)
    *   **Details:** Replace the mock SWOT component with a fully dynamic one.
        *   Integrate with `AnalysisService` for creating/loading SWOT analyses.
        *   Implement UI for guided input, displaying AI-generated questions/prompts from `ContextualPromptGenerationSkill` for each quadrant/cell.
        *   Support interactive session management if implemented in backend (Phase 1/2 A1).
    *   **Impact:** Delivers the AI-guided SWOT/TOWS experience.
*   **Task B3: Functional "S+O Connections" Tab**
    *   **File:** `Analysis.tsx`
    *   **Details:** Connect to `AnalysisService` to list, view, and manage S+O Linkages.
    *   **Impact:** Allows users to explore AI-discovered connections.
*   **Task B4: Fully Functional "New Analysis" Dialog**
    *   **File:** `Analysis.tsx`
    *   **Details:** Connect data selection (CEO Logs, Objective Datasets) and configuration steps to backend services. Ensure "Generate Analysis" triggers the appropriate `AnalysisService` methods (e.g., S+O Linkage discovery, new SWOT session).
    *   **Impact:** Enables user-initiated analysis workflows.
*   **Task B5: Wire Up Action Buttons**
    *   **File:** `Analysis.tsx`
    *   **Details:** Implement functionality for "Share", "Refresh", "Create Initiative" (linking to Planning module), "Add to Strategic Canvas" buttons.
    *   **Impact:** Improves interactivity and integration of the Analysis page.

### C. Settings UI (Advanced Functionality)

*   **Task C1: Implement Remaining Settings Tabs**
    *   **File:** `Settings.tsx`
    *   **Details:**
        *   **"Notification settings":** Design and implement UI for managing notification preferences (requires backend support for notifications).
        *   **"API & Integration settings":** Placeholder for future external API integrations. Could initially show API key management if applicable.
        *   **"Data management settings":** UI for data export, import (if planned), or viewing storage usage.
        *   **Account Preferences:** Wire up switches (voice interactions, AI insights, auto-tagging, dark mode) to user preference settings stored via `AuthService` or a dedicated `UserPreferenceService`.
        *   **Two-Factor Authentication:** Implement UI flows for setting up and managing 2FA (requires significant backend 2FA logic).
        *   **Session Management:** Display real active sessions and implement "Log Out All Other Devices" (requires backend session management).
    *   **Impact:** Completes the Settings section, offering users more control.

## 5. General Frontend Considerations for Both Phases

*   **State Management (`Zustand` stores):** Ensure stores are updated to manage state for new/modified features.
*   **API Services (`axios` instances):** Add new service methods for new backend endpoints.
*   **Responsiveness & UI Polish:** Continuously ensure the UI is responsive and visually polished.
*   **Error Handling:** Implement user-friendly error display for API call failures or unexpected UI states.
*   **Loading States:** Provide clear loading indicators for data fetching or processing operations.
*   **Accessibility:** Keep accessibility best practices in mind during development.

This UI enhancement plan provides a roadmap for frontend development, ensuring it aligns with backend progress and the overall product vision. Regular review and adjustment based on backend readiness and user feedback will be essential.
