# multi_agent_orchestrator_config.py

AGENT_NAME_PREFIX = "MultiAgentOrchestrator"

# Template for orchestrator instructions that can handle multiple specialized agents
AGENT_INSTRUCTIONS_TEMPLATE = """You are an advanced orchestrator assistant that coordinates multiple specialized agents to provide the best possible assistance.

YOUR ROLE:
- Analyze user requests and determine which specialized tool/agent to use
- Always delegate to the appropriate specialized agent when one is available
- Only answer directly for general questions that don't match any specialized agent's domain

AVAILABLE SPECIALIZED AGENTS:
{agent_descriptions}

TOOL USAGE RULES:
{tool_rules}

CRITICAL INSTRUCTIONS:
1. You MUST use the appropriate specialized tool for any request that matches their domain
2. NEVER provide your own response for domains covered by specialized agents
3. Always pass the user's request to the specialized agent without modification
4. If multiple agents could handle a request, choose the most specific one
5. Clearly indicate when you're using a specialized tool

EXAMPLES:
{examples}

Remember: Your strength lies in knowing when to delegate. Always use specialized agents when available!"""


def generate_orchestrator_instructions(agents_config):
    """
    Generate orchestrator instructions based on available agents.
    
    Args:
        agents_config: List of tuples (tool_name, description, trigger_keywords, example)
        
    Returns:
        Formatted orchestrator instructions
    """
    agent_descriptions = []
    tool_rules = []
    examples = []
    
    for i, (tool_name, description, keywords, example) in enumerate(agents_config):
        # Add agent description
        agent_descriptions.append(f"- {tool_name}: {description}")
        
        # Add tool rule
        keywords_str = ", ".join(keywords)
        tool_rules.append(
            f"{i+1}. For requests about {keywords_str}, use '{tool_name}'"
        )
        
        # Add example if provided
        if example:
            examples.append(f"User: '{example['user']}' → Use {tool_name}")
    
    return AGENT_INSTRUCTIONS_TEMPLATE.format(
        agent_descriptions="\n".join(agent_descriptions),
        tool_rules="\n".join(tool_rules),
        examples="\n".join(examples) if examples else "No specific examples provided"
    )


# Example configuration for multiple agents
EXAMPLE_AGENTS_CONFIG = [
    (
        "enthusiastic_greeter_tool",
        "Provides extremely enthusiastic greetings with emojis and excitement",
        ["greeting", "hello", "hi", "hey", "greet"],
        {"user": "Hello there!"}
    ),
    (
        "weather_information_tool", 
        "Provides real-time weather data from National Weather Service for US cities",
        ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny"],
        {"user": "What's the weather in New York?"}
    ),
    (
        "calculator_tool",
        "Performs mathematical calculations and solves equations",
        ["calculate", "math", "equation", "solve", "compute"],
        {"user": "Calculate 15% of 240"}
    ),
    (
        "translation_tool",
        "Translates text between different languages",
        ["translate", "translation", "language", "convert to"],
        {"user": "Translate 'hello world' to Spanish"}
    )
]