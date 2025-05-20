# Current MVP Feature Status

The following table summarizes the implementation state of each major feature as observed in the codebase and documentation.

| Feature ID | Status | Evidence |
|-----------|--------|---------|
| **F0.0 Authentication & Authorization** | *Implemented*. JWT auth is enforced and routers now derive the user from the token instead of requiring `user_id` parameters. | Updated `subjective_input.py` and `analysis.py` remove explicit `user_id` arguments. |
| **F1.1 "Our North Star" Module** | *Fully implemented*. CRUD endpoints secured with JWT; frontend store loads strategic goals. | Implemented per `strategic_foundation.py` router and docs. |
| **F1.2 "CEO's Log"** | *Fully implemented*. Voice input, AI tagging, and Azure integration completed. | See detailed implementation description in `mvp_status.md`. |
| **F2.1 Foundational Objective Data Input** | *Mostly implemented*. Upload, parsing, and indexing exist, but some routers still rely on manual IDs. | `objective_data.py` router secured with auth, but docs mention data isolation. |
| **F3.1 Initial S+O Linkage & Prompting** | *Implemented*. Service and endpoints exist. | `analysis_service.discover_so_linkages` and router endpoints. |
| **F3.2 Guided SWOT/TOWS AI Assistant** | *Improved*. AI prompt templates are used and service methods leverage the Semantic Kernel for explanations and insight generation. |
| **F4.1 Basic Initiative Planner** | *Improved*. CRUD works and plan alignment now combines coverage scoring with LLM feedback; action generation uses Semantic Kernel suggestions. |

Additional notes:
- Automated tests now include analysis and subjective input routers in addition to planning.
- Documentation reflects improved AI logic for analysis and planning services.
