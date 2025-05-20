# Pending Enhancements

The following areas require further implementation work to reach the intended MVP functionality.

1. **Authentication Consistency**
   - Remove explicit `user_id` parameters from API endpoints and derive the user from JWT authentication instead.
   - Apply this update to the subjective input and analysis routers (e.g., `create_log_entry` and `discover_so_linkages`).
2. **AI Logic Improvements**
   - Replace placeholder responses in the analysis service (`generate_insight_explanation`, `generate_insights_from_data`) with actual AI-driven reasoning.
   - Enhance the TOWS strategy generation and guided SWOT item creation to utilize the Semantic Kernel more fully.
   - Expand planning service methods such as `generate_actions` and `analyze_plan_alignment` with real scoring and action generation logic.
3. **Test Coverage**
   - Add unit and integration tests across all routers and services, not only the planning endpoints.
4. **Documentation Updates**
   - Keep project_status.md and other docs current as features are completed.
