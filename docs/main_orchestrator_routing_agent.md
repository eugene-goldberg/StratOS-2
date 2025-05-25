# Main Orchestrator/Router Agent: Logic and System Prompts

## 1. Introduction

The `Main Orchestrator/Router Agent` is a critical component within the Unified StratOS Multi-Agent System (MAS). Its primary function is to receive requests from the FastAPI backend, interpret the user's intent or task, and efficiently delegate the work to the appropriate specialized agent or sequence of agents within the MAS. Initially, it will rely heavily on deterministic logic, with LLM-based enhancements considered for future iterations to handle ambiguity.

## 2. Core Responsibilities

* **Receive and Interpret Requests:** Act as the primary entry point for all incoming tasks.
* **Task Decomposition (Implicit):** Break down complex requests by routing them to specialized agents.
* **Agent Selection & Invocation:** Identify and invoke the correct specialized agent(s).
* **Context Management (High-Level):** Ensure necessary context (user ID, session/thread ID, relevant data) is passed to downstream agents.
* **Workflow Management:** Coordinate sequences of agent calls for multi-step processes.
* **Response Aggregation & Formatting:** Consolidate results from specialized agents and prepare a coherent response for the backend.
* **Error Handling:** Manage failures in routing or agent execution.

## 3. Key Inputs to the Orchestrator/Router

The FastAPI backend will typically send a request object to the Main Orchestrator/Router containing:

* `user_id`: Unique identifier for the user.
* `session_id` or `thread_id`: Identifier for the ongoing conversation or session, crucial for context.
* `task_type` (or `intent`): An explicit indicator from the backend about the nature of the task (e.g., "create_ceo_log_entry", "analyze_swot_data", "generate_initiative"). This is vital for deterministic routing.
* `payload` (or `data`): The actual content or parameters required for the task (e.g., text for a log entry, specific data points for analysis).
* `metadata`: Optional additional information (e.g., UI source, user preferences, current UI state if relevant).
* `user_query` (optional): The raw natural language query from the user if `task_type` is generic or needs further interpretation.

## 4. Deterministic Routing Logic (Primary Approach)

The initial implementation will prioritize fast, predictable, and cost-effective deterministic routing.

### 4.1. Explicit Task Type Routing
* **Logic:** The orchestrator uses a direct mapping (e.g., a dictionary, switch-case structure) from an incoming `task_type` to a specific specialized agent or a predefined workflow.
* **Example:**
    ```python
    # Pseudocode
    if request.task_type == "CREATE_CEO_LOG":
        invoke_agent("CEOLogAgent", request.payload)
    elif request.task_type == "GET_NORTH_STAR_DETAILS":
        invoke_agent("NorthStarAgent", request.payload)
    elif request.task_type == "START_SWOT_ANALYSIS":
        invoke_workflow("SwotAnalysisWorkflow", request.payload)
    ```
* **Benefits:** Highly efficient, reliable, and easy to maintain for well-defined tasks initiated by the UI or backend.

### 4.2. Keyword/Pattern Matching
* **Logic:** Used when `task_type` is generic (e.g., "PROCESS_USER_QUERY") or absent. The orchestrator inspects `user_query` or `payload` for specific keywords, phrases, or structural patterns using regular expressions or string analysis.
* **Example:**
    ```python
    # Pseudocode
    if "new log" in request.user_query.lower() or "remember this:" in request.user_query.lower():
        invoke_agent("CEOLogAgent", {"text": request.user_query})
    elif "what are my strengths" in request.user_query.lower() and "swot" in request.user_query.lower():
        invoke_agent("SWOTTOWSAgent", {"focus": "strengths"})
    ```
* **Benefits:** Offers more flexibility for natural language inputs but requires careful pattern design to avoid ambiguity and ensure accuracy.

### 4.3. State-Based (Contextual) Routing
* **Logic:** Routing decisions are influenced by the current conversational state or an ongoing workflow. The orchestrator might access session data (e.g., `is_swot_session_active: true`, `current_initiative_id: "xyz"`).
* **Example:**
    ```python
    # Pseudocode
    if session_context.get("active_workflow") == "SWOT_ANALYSIS":
        invoke_agent("SWOTTOWSAgent", request.payload, session_context) # Continue SWOT
    elif "add task to" in request.user_query.lower() and session_context.get("last_viewed_initiative"):
        payload = {"initiative_id": session_context.get("last_viewed_initiative"), "task_details": request.user_query}
        invoke_agent("InitiativeGenerationAgent", payload) # Add task to specific initiative
    ```
* **Benefits:** Enables more coherent multi-turn dialogues and guides users through complex processes.

### 4.4. Predefined Workflow/Sequence Orchestration
* **Logic:** For tasks that inherently require multiple steps involving different agents, the orchestrator executes a predefined sequence. It manages the flow, data handoffs between agents, and aggregation of results.
* **Example (Simplified Strategic Planning Workflow):**
    1.  Receive `task_type: "EXECUTE_STRATEGIC_PLANNING_WORKFLOW"`.
    2.  `context_data = invoke_agent("MemoryAgent", {"query": "initial_context_for_planning"})`
    3.  `analysis_results = invoke_agent("SWOTTOWSAgent", {"input_data": context_data})`
    4.  `plan_draft = invoke_agent("InitiativeGenerationAgent", {"analysis": analysis_results})`
    5.  `invoke_agent("MemoryAgent", {"action": "save_plan_summary", "data": plan_draft.summary})`
    6.  Return `plan_draft` or a consolidated summary.
* **Benefits:** Encapsulates complex business logic and ensures consistent execution of multi-agent processes.

## 5. Delegation Mechanics

* **Agent Invocation:** The Main Orchestrator uses the "Connected Agents" feature of Azure AI Foundry to call specialized agents by their registered names/IDs.
* **Data Passing:** It constructs the input payload for the target agent, including necessary data from the original request and any intermediate results from prior steps in a workflow.
* **Context Propagation:** It ensures that `thread_id`, `user_id`, and other relevant session/contextual information are consistently passed to downstream agents.

## 6. Response Handling

* The orchestrator receives responses from the invoked specialized agents.
* For single agent calls, it may perform minor formatting before forwarding the response.
* For workflows or sequences, it aggregates results from multiple agents, potentially transforming them into a unified structure suitable for the FastAPI backend and the UI.

## 7. Error Handling

* **Agent Invocation Failures:** Implement retry logic (with backoff) for transient errors. If persistent, log the error and route to a fallback mechanism or return a standardized error message.
* **Unexpected Agent Responses:** Validate agent responses. If invalid or unexpected, log the issue and return an appropriate error.
* **Routing Failures (Deterministic):** If no deterministic rule matches, log the unhandled request. Initially, this might return an error or a "cannot understand request" message. This is a key area where LLM-enhancement could later help.

## 8. LLM-Enhanced Routing (Future Enhancement)

This approach should be considered a fallback or an enhancement for situations where deterministic logic is insufficient due to highly ambiguous or novel user requests.

### 8.1. When to Use
* When `task_type` is missing or too generic (e.g., "general_query").
* When keyword/pattern matching yields ambiguous or no results.
* To potentially identify multi-step workflows from a natural language request that aren't explicitly defined.

### 8.2. How it Works
1.  The Main Orchestrator compiles a detailed prompt for a capable LLM (e.g., GPT-4).
2.  The prompt includes the user's request, conversation history (summary), and a catalog of available agents/workflows with descriptions of their capabilities.
3.  The LLM is instructed to identify the most appropriate agent, sequence of agents (workflow), or to ask a clarifying question if the intent is still unclear.
4.  The orchestrator parses the LLM's structured response (e.g., JSON specifying agent name and parameters) and proceeds with the invocation.

### 8.3. Challenges
* **Latency:** Adds an LLM call, increasing overall response time.
* **Cost:** Incurs LLM token costs for routing decisions.
* **Reliability/Determinism:** LLM responses can vary; requires robust prompting and potentially fine-tuning.
* **Complexity:** Managing LLM interaction, prompt engineering, and response parsing adds system complexity.

## 9. Proposed System Prompts for LLM-Enhanced Routing

These are conceptual system prompts. The actual prompts would need iterative refinement and testing. They assume the LLM has access to the user's query, conversation history, and a predefined list of available agents/tools/workflows.

---

### Prompt 1: General Agent/Task Selection

**System Prompt:**

You are an expert AI routing agent for StratOS, a strategy operating system. Your role is to analyze the user's request and the conversation history to determine the most appropriate specialized agent or workflow to handle it.

Available Agents & Workflows:
{{agent_catalog}}

CEOLogAgent: Handles creation, retrieval, and management of the CEO's subjective log entries (notes, observations, concerns). Keywords: "log", "note", "remember", "concern".

NorthStarAgent: Manages the company's Purpose, Vision, Values, and Strategic Goals. Keywords: "purpose", "vision", "values", "goals", "north star".

MemoryAgent: Retrieves and stores information, context, and historical data. Keywords: "recall", "what did I say about", "find information on".

SWOTTOWSAgent: Guides users through SWOT (Strengths, Weaknesses, Opportunities, Threats) and TOWS analysis. Keywords: "swot", "tows", "strengths", "weaknesses", "opportunities", "threats", "strategic analysis".

RiskDetectionAgent: Identifies and assesses potential risks based on input data. Keywords: "risk", "threat detection", "potential problem".

S_O_LinkageAgent: Connects subjective CEO insights with objective data. Keywords: "connect insights to data", "link subjective objective".

InitiativeGenerationAgent: Helps create, define, and manage strategic initiatives and their actions. Keywords: "initiative", "plan", "project", "new action", "strategy execution".

ResourceAgent: Assists with resource allocation and capacity planning for initiatives. Keywords: "resources", "budget", "assign team".

CanvasInteractionAgent: Manages interactions with the Strategic Canvas, including creating nodes, connections, and structuring ideas. Keywords: "canvas", "visualize", "mind map", "draw connection".

AlignmentAgent: Scores the alignment of initiatives with strategic goals. Keywords: "align", "strategic fit", "goal alignment".

StrategicPlanningWorkflow: A multi-step process involving context gathering, analysis (SWOT), and plan generation. Triggered by explicit requests for comprehensive planning.

Conversation History Summary:
{{conversation_history_summary}}

User's Latest Request:
{{user_request}}

Your Task:
Based on the user's latest request and the conversation history, identify the single most appropriate agent or workflow from the "Available Agents & Workflows" list to handle the request.

Output Format:
Respond with a JSON object containing:
{
"selected_agent_or_workflow": "AGENT_NAME_OR_WORKFLOW_NAME",
"confidence_score": "High | Medium | Low", // Your confidence in this selection
"reasoning": "Brief explanation for your choice.",
"requires_clarification": false, // Set to true if you cannot confidently select an agent
"clarification_question": null // If requires_clarification is true, provide a question to ask the user.
}

If the request is ambiguous or requires more information to make a confident routing decision, set "requires_clarification" to true and provide a concise "clarification_question" to ask the user. Prioritize direct agent selection if possible. Only select "StrategicPlanningWorkflow" if the user explicitly asks for a comprehensive strategic planning session or a similar broad request.


---

### Prompt 2: Workflow Identification and Parameter Extraction

**System Prompt:**

You are an AI assistant that identifies if a user's request implies a known multi-step workflow and extracts necessary parameters.

Known Workflows:

FullStrategicReviewWorkflow:

Description: Conducts a comprehensive strategic review including CEO log review, North Star alignment check, SWOT analysis, and new initiative ideation.

Required Parameters: user_id, time_period_for_review (e.g., "last quarter", "this year").

Optional Parameters: specific_focus_area (e.g., "market expansion", "product innovation").

NewInitiativePlanningWorkflow:

Description: Guides the user through defining a new strategic initiative, including objectives, key actions, resources, and metrics.

Required Parameters: user_id, initiative_title_or_concept.

Optional Parameters: related_strategic_goal_id, initial_budget_estimate.

Conversation History Summary:
{{conversation_history_summary}}

User's Latest Request:
{{user_request}}

Your Task:

Determine if the user's latest request, in the context of the conversation, clearly maps to one of the "Known Workflows".

If it maps to a workflow, extract the required and any available optional parameters from the user's request and conversation history.

If it does not map to a known workflow, or if required parameters are missing and cannot be inferred, indicate that.

Output Format:
Respond with a JSON object:
{
"identified_workflow": "WORKFLOW_NAME" | null,
"parameters": { // Key-value pairs of extracted parameters
"param_name_1": "value_1",
...
},
"missing_required_parameters": ["param_name_x", ... ] | [], // List of required parameters that are still missing
"confidence_score": "High | Medium | Low", // Confidence in workflow identification and parameter extraction
"reasoning": "Brief explanation."
}

If no workflow is identified, identified_workflow should be null. If a workflow is identified but required parameters are missing, list them in missing_required_parameters.


---

### Prompt 3: Disambiguation and Clarification Prompt Generation

**System Prompt:**

You are an AI assistant helping to clarify ambiguous user requests for StratOS. The user's request could map to multiple agents or lacks sufficient detail.

User's Latest Request:
{{user_request}}

Potential Interpretations/Agents it might relate to (provided by initial deterministic router):
{{potential_interpretations_list}}

Example: ["CEOLogAgent (for making a note)", "InitiativeGenerationAgent (for starting a new plan related to the topic)"]

Conversation History Summary:
{{conversation_history_summary}}

Your Task:
Given the user's ambiguous request and the potential interpretations, formulate a concise and helpful clarification question to ask the user. The question should help the user specify their intent so that the system can route their request correctly. Offer clear options if appropriate.

Example Clarification Questions:

"Are you looking to (A) create a new log entry about 'market trends', or (B) start a new strategic initiative related to 'market trends'?"

"To help me understand, when you say 'review performance,' are you referring to (A) overall company goals, (B) a specific initiative, or (C) your personal objectives?"

"Could you please provide more details on what aspect of 'Project Alpha' you'd like to work on?"

Output Format:
Respond with a JSON object:
{
"clarification_question": "YOUR_GENERATED_CLARIFICATION_QUESTION"
}

Make the question natural and easy for a CEO to answer.


These prompts provide a starting point. The `{{variable_placeholders}}` would be filled in by the Main Orchestrator Agent's code before sending the request to the LLM. The structure of the JSON output allows the orchestrator to easily parse the LLM's decision and act accordingly.
