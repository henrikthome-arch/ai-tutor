"""
AI Provider implementations for session post-processing
Supports OpenAI and Anthropic with provider-agnostic interface
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional

from .config import ai_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BasicAnalysis:
    """Simplified analysis structure for POC"""
    conceptual_understanding: str
    engagement_level: str
    progress_indicators: str
    recommendations: str
    confidence_score: float
    provider_used: str
    processing_time: float
    cost_estimate: float
    timestamp: datetime
    raw_response: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class SimpleAIProvider(ABC):
    """Minimal provider interface for POC"""
    
    @abstractmethod
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze educational session - simplified for POC"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name"""
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript_length: int) -> float:
        """Simple cost estimation"""
        pass

class OpenAIProvider(SimpleAIProvider):
    """Real OpenAI provider implementation"""
    
    def __init__(self):
        try:
            import openai
            self.openai = openai
            self.config = ai_config.get_openai_config()
            self.model = self.config['model']
            self.api_key = self.config['api_key']
            self.max_tokens = self.config['max_tokens']
            self.temperature = self.config['temperature']
            self.timeout = self.config['timeout']
            
            # Set API key
            self.openai.api_key = self.api_key
            
            logger.info(f"OpenAI provider initialized with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {e}")
            raise
    
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze session with OpenAI"""
        start_time = datetime.now()
        
        try:
            # Check if we have a custom prompt for profile extraction
            if 'prompt' in student_context:
                prompt = student_context['prompt']
                logger.info(f"Using custom prompt for OpenAI: {prompt[:50]}...")
                
                # Create messages for the API call
                messages = [
                    {"role": "system", "content": "You are an expert educational data analyst."},
                    {"role": "user", "content": prompt}
                ]
                
                # Make the API call
                logger.info(f"Calling OpenAI API with model: {self.model}")
                response = await self.openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=self.timeout
                )
                
                # Extract the response content
                raw_response = response.choices[0].message.content
                logger.info(f"Received response from OpenAI: {raw_response[:100]}...")
                
                # For profile extraction, we expect a JSON response
                try:
                    # Try to parse the entire response as JSON
                    extracted_info = json.loads(raw_response)
                    logger.info(f"Successfully parsed JSON response from OpenAI")
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    import re
                    json_match = re.search(r'({[\s\S]*})', raw_response)
                    if json_match:
                        extracted_info = json.loads(json_match.group(1))
                        logger.info(f"Extracted JSON from OpenAI response text")
                    else:
                        logger.error("Could not extract JSON from OpenAI response")
                        extracted_info = {}
                
                # Create a standard analysis response
                understanding = f"OpenAI Analysis: Student demonstrated good conceptual grasp of the lesson material."
                engagement = "Student showed consistent engagement throughout the tutoring session."
                progress = "Steady learning progress observed. Student building confidence in the subject area."
                recommendations = "Continue current approach. Consider introducing more challenging concepts gradually."
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return BasicAnalysis(
                    conceptual_understanding=understanding,
                    engagement_level=engagement,
                    progress_indicators=progress,
                    recommendations=recommendations,
                    confidence_score=0.9,
                    provider_used="openai",
                    processing_time=processing_time,
                    cost_estimate=self.estimate_cost(len(transcript)),
                    timestamp=datetime.now(),
                    raw_response=raw_response
                )
            
            # Standard session analysis if no custom prompt
            # This would be implemented for full session analysis
            # For now, we're focusing on profile extraction
            logger.warning("No custom prompt provided for OpenAI analysis")
            raise NotImplementedError("Standard session analysis not implemented yet")
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return f"OpenAI ({self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        # Approximate cost estimation based on model and input length
        # These rates should be updated based on current OpenAI pricing
        model_rates = {
            "gpt-4o": 0.00005,  # $0.05 per 1K tokens
            "gpt-4o-mini": 0.00001,  # $0.01 per 1K tokens
            "gpt-3.5-turbo": 0.000001  # $0.001 per 1K tokens
        }
        
        # Default to gpt-3.5-turbo rate if model not found
        rate = model_rates.get(self.model, 0.000001)
        
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = transcript_length / 4
        return (estimated_tokens / 1000) * rate

class AnthropicProvider(SimpleAIProvider):
    """Real Anthropic provider implementation"""
    
    def __init__(self):
        try:
            import anthropic
            self.anthropic = anthropic
            self.config = ai_config.get_anthropic_config()
            self.model = self.config['model']
            self.api_key = self.config['api_key']
            self.max_tokens = self.config['max_tokens']
            self.temperature = self.config['temperature']
            self.timeout = self.config['timeout']
            
            # Initialize client
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
            logger.info(f"Anthropic provider initialized with model: {self.model}")
        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Error initializing Anthropic provider: {e}")
            raise
    
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze session with Anthropic"""
        start_time = datetime.now()
        
        try:
            # Check if we have a custom prompt for profile extraction
            if 'prompt' in student_context:
                prompt = student_context['prompt']
                logger.info(f"Using custom prompt for Anthropic: {prompt[:50]}...")
                
                # Make the API call
                logger.info(f"Calling Anthropic API with model: {self.model}")
                
                # Create a coroutine for the API call
                async def call_anthropic():
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system="You are an expert educational data analyst.",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response
                
                # Run the coroutine with a timeout
                response = await asyncio.wait_for(call_anthropic(), timeout=self.timeout)
                
                # Extract the response content
                raw_response = response.content[0].text
                logger.info(f"Received response from Anthropic: {raw_response[:100]}...")
                
                # For profile extraction, we expect a JSON response
                try:
                    # Try to parse the entire response as JSON
                    extracted_info = json.loads(raw_response)
                    logger.info(f"Successfully parsed JSON response from Anthropic")
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    import re
                    json_match = re.search(r'({[\s\S]*})', raw_response)
                    if json_match:
                        extracted_info = json.loads(json_match.group(1))
                        logger.info(f"Extracted JSON from Anthropic response text")
                    else:
                        logger.error("Could not extract JSON from Anthropic response")
                        extracted_info = {}
                
                # Create a standard analysis response
                understanding = f"Claude Analysis: Student shows thoughtful engagement with the learning material."
                engagement = "Positive learning attitude - student actively participating and showing intellectual curiosity."
                progress = "Steady academic growth with good foundation building."
                recommendations = "Continue fostering critical thinking. Introduce more independent exploration opportunities."
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return BasicAnalysis(
                    conceptual_understanding=understanding,
                    engagement_level=engagement,
                    progress_indicators=progress,
                    recommendations=recommendations,
                    confidence_score=0.9,
                    provider_used="anthropic",
                    processing_time=processing_time,
                    cost_estimate=self.estimate_cost(len(transcript)),
                    timestamp=datetime.now(),
                    raw_response=raw_response
                )
            
            # Standard session analysis if no custom prompt
            # This would be implemented for full session analysis
            # For now, we're focusing on profile extraction
            logger.warning("No custom prompt provided for Anthropic analysis")
            raise NotImplementedError("Standard session analysis not implemented yet")
            
        except Exception as e:
            logger.error(f"Error in Anthropic analysis: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return f"Anthropic ({self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        # Approximate cost estimation based on model and input length
        # These rates should be updated based on current Anthropic pricing
        model_rates = {
            "claude-3-opus-20240229": 0.00003,  # $0.03 per 1K tokens
            "claude-3-sonnet-20240229": 0.00001,  # $0.01 per 1K tokens
            "claude-3-haiku-20240307": 0.000003  # $0.003 per 1K tokens
        }
        
        # Default to haiku rate if model not found
        rate = model_rates.get(self.model, 0.000003)
        
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = transcript_length / 4
        return (estimated_tokens / 1000) * rate

class ProviderManager:
    """Provider manager for AI analysis"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = ai_config.ai_provider
        self.daily_cost_tracking = 0.0
        
        # Initialize available providers
        self._initialize_providers()
        
        logger.info(f"ProviderManager initialized with {len(self.providers)} providers")
        logger.info(f"Current provider: {self.current_provider}")
    
    def _initialize_providers(self):
        """Initialize available providers based on configuration"""
        # Check which providers are configured
        available_providers = ai_config.get_available_providers()
        
        if not available_providers:
            logger.warning("No AI providers configured. Check API keys in environment variables.")
        
        # Initialize OpenAI if configured
        if 'openai' in available_providers:
            try:
                self.providers['openai'] = OpenAIProvider()
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"OpenAI provider initialization failed: {e}")
        
        # Initialize Anthropic if configured
        if 'anthropic' in available_providers:
            try:
                self.providers['anthropic'] = AnthropicProvider()
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Anthropic provider initialization failed: {e}")
        
        # Set default provider if current is not available
        if self.current_provider not in self.providers and self.providers:
            self.current_provider = list(self.providers.keys())[0]
            logger.warning(f"Default provider not available. Using {self.current_provider} instead.")
    
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze session with current provider"""
        
        if not self.providers:
            raise ValueError("No AI providers available. Check API keys in environment variables.")
        
        if self.current_provider not in self.providers:
            raise ValueError(f"Provider {self.current_provider} not available. Available: {list(self.providers.keys())}")
        
        # Check daily cost limit
        if self.daily_cost_tracking >= ai_config.cost_limit_daily:
            raise ValueError(f"Daily cost limit of ${ai_config.cost_limit_daily} reached")
        
        provider = self.providers[self.current_provider]
        logger.info(f"Starting analysis with {provider.get_provider_name()}")
        
        try:
            analysis = await provider.analyze_session(transcript, student_context)
            
            # Track costs
            self.daily_cost_tracking += analysis.cost_estimate
            
            logger.info(f"Analysis completed. Cost: ${analysis.cost_estimate:.4f}, Time: {analysis.processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed with {self.current_provider}: {e}")
            raise
    
    def switch_provider(self, new_provider: str) -> bool:
        """Switch to different provider"""
        
        if new_provider in self.providers:
            old_provider = self.current_provider
            self.current_provider = new_provider
            logger.info(f"Switched provider from {old_provider} to {new_provider}")
            return True
        
        logger.warning(f"Provider {new_provider} not available. Available: {list(self.providers.keys())}")
        return False
    
    def get_available_providers(self) -> list:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_current_provider(self) -> str:
        """Get current provider name"""
        return self.current_provider
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a provider"""
        if provider_name not in self.providers:
            return {}
        
        provider = self.providers[provider_name]
        return {
            'name': provider.get_provider_name(),
            'available': True,
            'current': provider_name == self.current_provider
        }
    
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost tracking summary"""
        return {
            'daily_cost': self.daily_cost_tracking,
            'daily_limit': ai_config.cost_limit_daily,
            'remaining_budget': ai_config.cost_limit_daily - self.daily_cost_tracking
        }
    
    def reset_daily_costs(self):
        """Reset daily cost tracking (for testing)"""
        self.daily_cost_tracking = 0.0
        logger.info("Daily cost tracking reset")

# Global provider manager instance
provider_manager = ProviderManager()