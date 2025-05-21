import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
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
    _instance = None

    def __new__(cls, *args, **kwargs): # Keep *args, **kwargs here if __init__ uses them
        if not cls._instance:
            cls._instance = super(KernelService, cls).__new__(cls) # Removed *args, **kwargs
        return cls._instance

    def __init__(self, auto_initialize: bool = True): # auto_initialize is a kwarg
        # Ensure __init__ is idempotent for the singleton pattern
        if hasattr(self, '_initialized_singleton') and self._initialized_singleton:
            return
            
        self.kernel: Optional[sk.Kernel] = None
        self.memory: Optional[SemanticTextMemory] = None
        self.logger = logging.getLogger("kernel_service")
        self._initialized_components = False # Flag to track full initialization
        
        if auto_initialize: # Default behavior for app
            self.setup_logging() # Basic logging setup
            # Full initialization is deferred to ensure_initialized or explicit call
            # self.initialize_kernel_components() # Renamed and deferred

        self._initialized_singleton = True


    def setup_logging(self):
        # Check if logger already has handlers to avoid duplicate logs in some scenarios (like tests)
        if not self.logger.hasHandlers():
            logging.basicConfig(level=logging.INFO) # Ensure basicConfig is called if no handlers
            # If you want to ensure it's always INFO even if basicConfig was called with different level:
            # self.logger.setLevel(logging.INFO)
            # handler = logging.StreamHandler() # Example handler
            # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            # handler.setFormatter(formatter)
            # self.logger.addHandler(handler)
        
    def initialize_kernel_components(self):
        if self._initialized_components:
            return
        
        self.setup_logging() # Ensure logger is set up
        self.logger.info("Attempting to initialize KernelService components...")

        try:
            self.kernel = sk.Kernel()
            
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
            search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

            if not all([deployment_name, endpoint, api_key, embedding_deployment, search_endpoint, search_api_key, search_index_name]):
                self.logger.error("One or more Azure environment variables are not set. Kernel components cannot be fully initialized.")
                # raise ValueError("Missing one or more Azure environment variables for KernelService.")
                # For tests, we might want this to not raise an error if env vars are mocked later.
                # However, for actual app, this should be an error.
                # Let's allow it to proceed but log heavily, services using it will fail if not mocked.
                self._initialized_components = False # Mark as not fully initialized
                return


            chat_service_instance = AzureChatCompletion(
                chat_deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key
            )
            self.kernel.add_service(chat_service_instance, service_id="chat_completion")
            
            embedding_service_instance = AzureTextEmbedding(
                deployment_name=embedding_deployment,
                endpoint=endpoint,
                api_key=api_key
            )
            self.kernel.add_service(embedding_service_instance, service_id="embedding")
            
            self._setup_memory_internal() # Renamed to avoid conflict with potential property
            self._register_skills_internal() # Renamed
            
            self.logger.info("Semantic Kernel components initialized successfully.")
            self._initialized_components = True
        except Exception as e:
            self.logger.error(f"Error initializing Semantic Kernel components: {str(e)}")
            self._initialized_components = False
            # raise # Re-raise if this should halt application startup

    def _ensure_initialized(self):
        """Ensures kernel components are initialized before use."""
        if not self._initialized_components:
            self.logger.warning("KernelService components not initialized. Attempting to initialize now.")
            self.initialize_kernel_components()
            if not self._initialized_components:
                 raise RuntimeError("KernelService components failed to initialize.")
        if not self.kernel: # Should be caught by _initialized_components check
            raise RuntimeError("Kernel is not initialized in KernelService.")


    def _register_skills_internal(self):
        self.logger.info("Registering skills...")
        # Skills might need the kernel or services, ensure they are initialized or passed
        log_management_skill = LogManagementSkill() # Pass dependencies if needed
        voice_input_skill = VoiceInputSkill()
        swot_skill = SWOTAnalysisSkill(kernel=self.kernel) # Example if skill needs kernel
        context_prompt_skill = ContextualPromptGenerationSkill()
        strategic_context_skill = StrategicContextRetrieverSkill()
        linkage_skill = SubjectiveObjectiveLinkageSkill()

        self.kernel.import_skill(log_management_skill, "LogManagement")
        self.kernel.import_skill(voice_input_skill, "VoiceInput")
        self.kernel.import_skill(swot_skill, "SWOTAnalysis")
        self.kernel.import_skill(context_prompt_skill, "ContextualPrompt")
        self.kernel.import_skill(strategic_context_skill, "StrategicContext")
        self.kernel.import_skill(linkage_skill, "SubjectiveObjectiveLinkage")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        subjective_log_dir = os.path.join(current_dir, "skills", "subjective_log")
        self.kernel.import_semantic_skill_from_directory(subjective_log_dir, "SubjectiveLog")
        analysis_skills_dir = os.path.join(current_dir, "skills", "analysis_skills") # Semantic functions
        self.kernel.import_semantic_skill_from_directory(analysis_skills_dir, "Analysis")
        self.logger.info("Skills registered.")
            
    def _setup_memory_internal(self):
        self.logger.info("Setting up memory system...")
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

        # These should have been checked in initialize_kernel_components
        if not all([search_endpoint, search_api_key, search_index_name]):
             self.logger.error("Azure Search environment variables not set. Memory setup failed.")
             return # Cannot proceed

        memory_store = AzureCognitiveSearchMemoryStore(
            vector_size=1536,
            search_endpoint=search_endpoint,
            admin_key=search_api_key,
            index_name=search_index_name
        )
        
        embedding_service = self.kernel.get_service("embedding")
        if not embedding_service:
            self.logger.error("Embedding service not found in kernel. Memory setup failed.")
            # raise ValueError("Embedding service 'embedding' not found in kernel for memory setup.")
            return # Cannot proceed

        self.memory = SemanticTextMemory(
            storage=memory_store,
            embeddings_generator=embedding_service
        )
        self.logger.info("Memory system configured.")
            
    async def invoke_semantic_function(self, skill_name, function_name, input_text, variables=None):
        self._ensure_initialized()
        # ... (rest of the method)
        try:
            if variables is None:
                variables = {}
            sk_function = self.kernel.skills.get_function(skill_name, function_name)
            context = self.kernel.create_new_context()
            for key, value in variables.items():
                context[key] = value
            result = await self.kernel.run_async(sk_function, input_text, context)
            return str(result)
        except Exception as e:
            self.logger.error(f"Error invoking semantic function {skill_name}.{function_name}: {str(e)}")
            raise
            
    async def generate_completion(self, prompt, max_tokens=1000):
        self._ensure_initialized()
        # ... (rest of the method)
        try:
            completion_service = self.kernel.get_service("chat_completion")
            if not completion_service:
                 raise RuntimeError("Chat completion service not available.")
            result = await completion_service.complete_async(prompt, max_tokens=max_tokens)
            return result # This is usually an SK ChatMessageContent or similar, not str
        except Exception as e:
            self.logger.error(f"Error generating completion: {str(e)}")
            raise
            
    async def remember(self, collection, key, text, description=None):
        self._ensure_initialized()
        if not self.memory:
            self.logger.error("Memory not initialized, cannot remember.")
            return False
        # ... (rest of the method)
        try:
            await self.memory.save_information_async(collection=collection, id=key, text=text, description=description)
            return True
        except Exception as e:
            self.logger.error(f"Error saving to memory (collection: {collection}, key: {key}): {str(e)}")
            return False
            
    async def recall(self, collection, query, limit=5):
        self._ensure_initialized()
        if not self.memory:
            self.logger.error("Memory not initialized, cannot recall.")
            return []
        # ... (rest of the method)
        try:
            results = await self.memory.search_async(collection=collection, query=query, limit=limit)
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving from memory (collection: {collection}, query: {query[:50]}...): {str(e)}")
            return []

# Singleton access function
_kernel_service_singleton_instance = None

def get_kernel_service(auto_initialize_components=True):
    global _kernel_service_singleton_instance
    if _kernel_service_singleton_instance is None:
        # Pass auto_initialize=False if we want to control component init externally (e.g. app startup)
        _kernel_service_singleton_instance = KernelService(auto_initialize=False) 
    
    # If components need to be initialized (e.g. for actual app run, not necessarily for all tests)
    if auto_initialize_components and not _kernel_service_singleton_instance._initialized_components:
        _kernel_service_singleton_instance.initialize_kernel_components()
        
    return _kernel_service_singleton_instance

# Make kernel_service available for import, but its full initialization is now deferred/controlled.
# For services importing this, they will get an instance.
# If they call methods that need full init, _ensure_initialized() will trigger it.
# Tests can mock _ensure_initialized or initialize_kernel_components on the instance.
kernel_service = get_kernel_service(auto_initialize_components=False) # Do not auto-init components on module load
