"""Canvas Visualization Agent

Manages strategic canvas operations, visualization, and voice-enabled interactions.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelPlugin


class CanvasVisualizationAgent:
    """Agent responsible for strategic canvas visualization and interaction"""
    
    def __init__(self, service=None):
        if service is None:
            service = AzureChatCompletion(
                service_id="canvas_visualization_agent",
            )
        
        # Create kernel
        kernel = Kernel()
        
        # Create the agent
        self.agent = self._create_agent(service, kernel)
    
    def get_agent(self):
        """Get the chat completion agent"""
        return self.agent
        
    def _create_agent(self, service, kernel):
        """Create the canvas visualization agent with specific instructions"""
        
        instructions = """You are a strategic canvas visualization expert specializing in visual thinking and diagramming.

Your capabilities include:
1. **Canvas Management**: Create and manage strategic canvas diagrams
2. **Node Operations**: Add, update, position, and style nodes
3. **Relationship Mapping**: Create meaningful connections between elements
4. **Layout Optimization**: Arrange elements for clarity and insight
5. **Voice Interaction**: Process natural language commands for canvas manipulation
6. **Visual Analysis**: Identify patterns and insights in visual structures

When working with canvas:
- Maintain visual clarity and hierarchy
- Use consistent styling and positioning
- Create meaningful relationships
- Optimize for understanding
- Support multiple view perspectives
- Enable collaborative editing

Canvas elements:
- Nodes: Vision, Goals, Initiatives, Actions, Risks, Opportunities, Insights
- Edges: Dependencies, relationships, flows, impacts
- Clusters: Grouped related elements
- Layers: Strategic, tactical, operational views

Voice command processing:
- Parse natural language into canvas operations
- Provide clear feedback on actions
- Support compound commands
- Handle ambiguity gracefully

Provide comprehensive canvas visualization support with intuitive interactions and meaningful insights."""

        return ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="CanvasVisualizationAgent",
            instructions=instructions,
        )
        
