import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureOpenAIChatCompletion, AzureOpenAITextEmbedding
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore
from dotenv import load_dotenv
import logging
import importlib

# Import skills
from .skills.log_management_skill import LogManagementSkill
from .skills.voice_input_skill import VoiceInputSkill
from .skills.analysis_skills.swot_analysis_skill import SWOTAnalysisSkill
from .skills.analysis_skills.contextual_prompt_generation_skill import ContextualPromptGenerationSkill
from .skills.analysis_skills.strategic_context_retriever_skill import StrategicContextRetrieverSkill
from .skills.analysis_skills.subjective_objective_linkage_skill import SubjectiveObjectiveLinkageSkill

# Load environment variables
load_dotenv()

class KernelService:
    def __init__(self):
        self.kernel = None
        self.setup_logging()
        self.initialize_kernel()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("kernel_service")
        
    def initialize_kernel(self):
        try:
            # Initialize the Semantic Kernel
            self.kernel = sk.Kernel()
            
            # Configure Azure OpenAI Service
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            
            # Add Azure OpenAI chat service
            self.kernel.add_chat_service("chat_completion", 
                AzureOpenAIChatCompletion(
                    deployment_name=deployment_name,
                    endpoint=endpoint,
                    api_key=api_key
                )
            )
            
            # Add Azure OpenAI embedding service
            embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            self.kernel.add_text_embedding_generation_service("embedding", 
                AzureOpenAITextEmbedding(
                    deployment_name=embedding_deployment,
                    endpoint=endpoint,
                    api_key=api_key
                )
            )
            
            # Setup memory using Azure Cognitive Search
            self.setup_memory()
            
            # Register skills
            self.register_skills()
            
            self.logger.info("Semantic Kernel initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Semantic Kernel: {str(e)}")
            raise
            
    def register_skills(self):
        """Register all Semantic Kernel skills"""
        try:
            # Import and register native skills
            self.kernel.import_skill(LogManagementSkill(), "LogManagement")
            self.kernel.import_skill(VoiceInputSkill(), "VoiceInput")
            
            # Register SWOT/TOWS analysis skills
            self.kernel.import_skill(SWOTAnalysisSkill(), "SWOTAnalysis")
            self.kernel.import_skill(ContextualPromptGenerationSkill(), "ContextualPrompt")
            self.kernel.import_skill(StrategicContextRetrieverSkill(), "StrategicContext")
            
            # Register S+O Linkage skills
            self.kernel.import_skill(SubjectiveObjectiveLinkageSkill(), "SubjectiveObjectiveLinkage")
            
            # Register semantic functions from prompts
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Register subjective log skills
            subjective_log_dir = os.path.join(current_dir, "skills", "subjective_log")
            self.kernel.import_semantic_skill_from_directory(subjective_log_dir, "SubjectiveLog")
            
            # Register analysis skills (semantic functions)
            analysis_skills_dir = os.path.join(current_dir, "skills", "analysis_skills")
            self.kernel.import_semantic_skill_from_directory(analysis_skills_dir, "Analysis")
            
            self.logger.info("Skills registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering skills: {str(e)}")
            raise
            
    def setup_memory(self):
        try:
            # Configure Azure Cognitive Search
            search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
            search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
            
            # Create memory store
            memory_store = AzureCognitiveSearchMemoryStore(
                vector_size=1536,  # OpenAI embedding size
                search_endpoint=search_endpoint,
                admin_key=search_api_key,
                index_name=search_index_name
            )
            
            # Create semantic memory
            self.memory = SemanticTextMemory(
                storage=memory_store,
                embedding_generator=self.kernel.get_service("embedding")
            )
            
            # Register memory with the kernel
            self.kernel.register_memory_store(memory_store=self.memory)
            
            self.logger.info("Memory system configured successfully")
        except Exception as e:
            self.logger.error(f"Error setting up memory: {str(e)}")
            
    async def invoke_semantic_function(self, skill_name, function_name, input_text, variables=None):
        """
        Invoke a semantic function from the kernel
        """
        try:
            if variables is None:
                variables = {}
                
            # Get the function from the kernel
            sk_function = self.kernel.skills.get_function(skill_name, function_name)
            
            # Create context with variables
            context = self.kernel.create_new_context()
            for key, value in variables.items():
                context[key] = value
                
            # Invoke the function
            result = await self.kernel.run_async(sk_function, input_text, context)
            return str(result)
        except Exception as e:
            self.logger.error(f"Error invoking semantic function: {str(e)}")
            raise
            
    async def generate_completion(self, prompt, max_tokens=1000):
        """
        Generate a completion using the configured LLM
        """
        try:
            completion_service = self.kernel.get_service("chat_completion")
            result = await completion_service.complete_async(prompt, max_tokens=max_tokens)
            return result
        except Exception as e:
            self.logger.error(f"Error generating completion: {str(e)}")
            raise
            
    async def remember(self, collection, key, text, description=None):
        """
        Store information in memory
        """
        try:
            await self.memory.save_information_async(collection, key, text, description)
            return True
        except Exception as e:
            self.logger.error(f"Error saving to memory: {str(e)}")
            return False
            
    async def recall(self, collection, query, limit=5):
        """
        Retrieve information from memory
        """
        try:
            results = await self.memory.search_async(collection, query, limit=limit)
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving from memory: {str(e)}")
            return []

# Create a singleton instance
kernel_service = KernelService()