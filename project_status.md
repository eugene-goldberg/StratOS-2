# Current MVP Feature Status

The following table summarizes the implementation state of each major feature as observed in the codebase and documentation.

| Feature ID | Status | Evidence |
|-----------|--------|---------|
| **F0.0 Authentication & Authorization** | *Partially implemented*. JWT auth is implemented but several routers still require `user_id` parameters instead of deriving the user from the token. | Example lines in `subjective_input.py` show `user_id` arguments despite router-level dependency on `get_current_active_user`. |
| **F1.1 "Our North Star" Module** | *Fully implemented*. CRUD endpoints secured with JWT; frontend store loads strategic goals. | Implemented per `strategic_foundation.py` router and docs. |
| **F1.2 "CEO's Log"** | *Fully implemented*. Voice input, AI tagging, and Azure integration completed. | See detailed implementation description in `mvp_status.md`. |
| **F2.1 Foundational Objective Data Input** | *Mostly implemented*. Upload, parsing, and indexing exist, but some routers still rely on manual IDs. | `objective_data.py` router secured with auth, but docs mention data isolation. |
| **F3.1 Initial S+O Linkage & Prompting** | *Implemented*. Service and endpoints exist. | `analysis_service.discover_so_linkages` and router endpoints. |
| **F3.2 Guided SWOT/TOWS AI Assistant** | *Partially implemented*. AI prompt templates exist, but service methods generate simple outputs using placeholder logic. | `mvp_status.md` states "AI-generated SWOT items and insights use placeholder logic". |
| **F4.1 Basic Initiative Planner** | *Partially implemented*. CRUD works; plan alignment uses a basic ratio; AI-generated actions are simple placeholders. | `planning_service.py` shows placeholder action generation and alignment scoring. |

Additional notes:
- Automated tests cover only the plan alignment endpoint (`tests/test_planning.py`).
- Documentation acknowledges that advanced analysis and planning logic is still basic.
