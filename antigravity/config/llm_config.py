import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """
    Configuration management for Antigravity LLMs.
    """
    # LLM Settings
    LLM_BACKEND = os.getenv("ANTIGRAVITY_LLM", "kimi")
    
    # Kimi K2.5 Setup
    KIMI_API_BASE = "https://integrate.api.nvidia.com/v1"
    KIMI_MODEL = "moonshotai/kimi-k2.5"
    
    # Secure API Key retrieval (placeholder for Phase 5)
    @staticmethod
    def get_api_key():
        key = os.getenv("NVIDIA_API_KEY")
        if not key:
            return "MOCK_KEY"
        return key

    # Multi-agent defaults
    MAX_PARALLEL_AGENTS = 5
    DEFAULT_TIMEOUT = 300
