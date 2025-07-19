"""
Configuration management for AI module
Simple environment-based configuration
"""

import os
from typing import Dict, Any, Optional

class AIConfig:
    """Simple configuration manager for AI providers"""
    
    def __init__(self):
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai')
        self.cost_limit_daily = float(os.getenv('DAILY_COST_LIMIT_USD', '10.0'))
        self.max_retries = int(os.getenv('AI_MAX_RETRIES', '2'))
        
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration"""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.3')),
            'timeout': int(os.getenv('OPENAI_TIMEOUT', '30'))
        }
    
    def get_anthropic_config(self) -> Dict[str, Any]:
        """Get Anthropic configuration"""
        return {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            'max_tokens': int(os.getenv('ANTHROPIC_MAX_TOKENS', '2000')),
            'temperature': float(os.getenv('ANTHROPIC_TEMPERATURE', '0.3')),
            'timeout': int(os.getenv('ANTHROPIC_TIMEOUT', '30'))
        }
    
    def get_current_provider_config(self) -> Dict[str, Any]:
        """Get configuration for current provider"""
        if self.ai_provider == 'openai':
            return self.get_openai_config()
        elif self.ai_provider == 'anthropic':
            return self.get_anthropic_config()
        else:
            raise ValueError(f"Unsupported provider: {self.ai_provider}")
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if provider is properly configured"""
        if provider == 'openai':
            return bool(os.getenv('OPENAI_API_KEY'))
        elif provider == 'anthropic':
            return bool(os.getenv('ANTHROPIC_API_KEY'))
        return False
    
    def get_available_providers(self) -> list:
        """Get list of available providers"""
        providers = []
        if self.is_provider_configured('openai'):
            providers.append('openai')
        if self.is_provider_configured('anthropic'):
            providers.append('anthropic')
        return providers

# Global config instance
ai_config = AIConfig()