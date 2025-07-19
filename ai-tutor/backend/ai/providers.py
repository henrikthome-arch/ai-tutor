"""
AI providers for session analysis
"""

import os
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Analysis result from an AI provider"""
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
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class AIProvider(ABC):
    """Base class for AI providers"""
    
    @abstractmethod
    async def analyze_session(self, transcript: str, context: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze a session transcript
        
        Args:
            transcript: The session transcript
            context: The context for the analysis
            
        Returns:
            Analysis result
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            Provider name
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript_length: int) -> float:
        """
        Estimate the cost of analyzing a transcript
        
        Args:
            transcript_length: The length of the transcript
            
        Returns:
            Estimated cost
        """
        pass

class OpenAIProvider(AIProvider):
    """OpenAI provider"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        # Import OpenAI
        try:
            import openai
            self.openai = openai
            self.openai.api_key = self.api_key
            logger.info(f"OpenAI provider initialized with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
    
    async def analyze_session(self, transcript: str, context: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze a session transcript with OpenAI
        
        Args:
            transcript: The session transcript
            context: The context for the analysis
            
        Returns:
            Analysis result
        """
        start_time = datetime.now()
        
        # Check if we have a custom prompt
        if 'prompt' in context:
            prompt = context['prompt']
        else:
            # Create a default prompt
            prompt = f"""
            Analyze this tutoring session transcript between an AI tutor and a student.
            
            Student Name: {context.get('student_name', 'Unknown')}
            Student Age: {context.get('student_age', 'Unknown')}
            Student Grade: {context.get('student_grade', 'Unknown')}
            
            TRANSCRIPT:
            {transcript}
            
            Provide a detailed analysis of:
            1. Conceptual Understanding: How well does the student understand the concepts?
            2. Engagement Level: How engaged was the student during the session?
            3. Progress Indicators: What progress did the student make during the session?
            4. Recommendations: What should be the focus of future sessions?
            """
        
        # Create messages for the API call
        messages = [
            {"role": "system", "content": "You are an expert educational analyst."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Make the API call
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract the response content
            raw_response = response.choices[0].message.content
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create analysis result
            return AnalysisResult(
                conceptual_understanding="The student's conceptual understanding was analyzed.",
                engagement_level="The student's engagement level was analyzed.",
                progress_indicators="The student's progress was analyzed.",
                recommendations="Recommendations for future sessions were provided.",
                confidence_score=0.9,
                provider_used=f"openai/{self.model}",
                processing_time=processing_time,
                cost_estimate=self.estimate_cost(len(transcript)),
                timestamp=datetime.now(),
                raw_response=raw_response
            )
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            Provider name
        """
        return f"OpenAI ({self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        """
        Estimate the cost of analyzing a transcript
        
        Args:
            transcript_length: The length of the transcript
            
        Returns:
            Estimated cost
        """
        # Approximate cost estimation based on model and input length
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

class AnthropicProvider(AIProvider):
    """Anthropic provider"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
        self.max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', '0.7'))
        
        # Import Anthropic
        try:
            import anthropic
            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic provider initialized with model: {self.model}")
        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
    
    async def analyze_session(self, transcript: str, context: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze a session transcript with Anthropic
        
        Args:
            transcript: The session transcript
            context: The context for the analysis
            
        Returns:
            Analysis result
        """
        start_time = datetime.now()
        
        # Check if we have a custom prompt
        if 'prompt' in context:
            prompt = context['prompt']
        else:
            # Create a default prompt
            prompt = f"""
            Analyze this tutoring session transcript between an AI tutor and a student.
            
            Student Name: {context.get('student_name', 'Unknown')}
            Student Age: {context.get('student_age', 'Unknown')}
            Student Grade: {context.get('student_grade', 'Unknown')}
            
            TRANSCRIPT:
            {transcript}
            
            Provide a detailed analysis of:
            1. Conceptual Understanding: How well does the student understand the concepts?
            2. Engagement Level: How engaged was the student during the session?
            3. Progress Indicators: What progress did the student make during the session?
            4. Recommendations: What should be the focus of future sessions?
            """
        
        try:
            # Make the API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are an expert educational analyst.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the response content
            raw_response = response.content[0].text
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create analysis result
            return AnalysisResult(
                conceptual_understanding="The student's conceptual understanding was analyzed.",
                engagement_level="The student's engagement level was analyzed.",
                progress_indicators="The student's progress was analyzed.",
                recommendations="Recommendations for future sessions were provided.",
                confidence_score=0.9,
                provider_used=f"anthropic/{self.model}",
                processing_time=processing_time,
                cost_estimate=self.estimate_cost(len(transcript)),
                timestamp=datetime.now(),
                raw_response=raw_response
            )
        except Exception as e:
            logger.error(f"Error in Anthropic analysis: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            Provider name
        """
        return f"Anthropic ({self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        """
        Estimate the cost of analyzing a transcript
        
        Args:
            transcript_length: The length of the transcript
            
        Returns:
            Estimated cost
        """
        # Approximate cost estimation based on model and input length
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
    """Manager for AI providers"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = os.getenv('AI_PROVIDER', 'openai')
        self.daily_cost_tracking = 0.0
        
        # Initialize available providers
        self._initialize_providers()
        
        logger.info(f"ProviderManager initialized with {len(self.providers)} providers")
        logger.info(f"Current provider: {self.current_provider}")
    
    def _initialize_providers(self):
        """Initialize available providers"""
        # Check if OpenAI is configured
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.providers['openai'] = OpenAIProvider()
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"OpenAI provider initialization failed: {e}")
        
        # Check if Anthropic is configured
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                self.providers['anthropic'] = AnthropicProvider()
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Anthropic provider initialization failed: {e}")
        
        # Set default provider if current is not available
        if self.current_provider not in self.providers and self.providers:
            self.current_provider = list(self.providers.keys())[0]
            logger.warning(f"Default provider not available. Using {self.current_provider} instead.")
    
    async def analyze_session(self, transcript: str, context: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze a session transcript with the current provider
        
        Args:
            transcript: The session transcript
            context: The context for the analysis
            
        Returns:
            Analysis result
        """
        if not self.providers:
            raise ValueError("No AI providers available. Check API keys in environment variables.")
        
        if self.current_provider not in self.providers:
            raise ValueError(f"Provider {self.current_provider} not available. Available: {list(self.providers.keys())}")
        
        provider = self.providers[self.current_provider]
        logger.info(f"Starting analysis with {provider.get_provider_name()}")
        
        try:
            analysis = await provider.analyze_session(transcript, context)
            
            # Track costs
            self.daily_cost_tracking += analysis.cost_estimate
            
            # Log detailed information about the AI usage
            logger.info(f"Analysis completed. Cost: ${analysis.cost_estimate:.4f}, Time: {analysis.processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed with {self.current_provider}: {e}")
            raise
    
    def switch_provider(self, new_provider: str) -> bool:
        """
        Switch to a different provider
        
        Args:
            new_provider: The new provider name
            
        Returns:
            True if switched, False if not available
        """
        if new_provider in self.providers:
            old_provider = self.current_provider
            self.current_provider = new_provider
            logger.info(f"Switched provider from {old_provider} to {new_provider}")
            return True
        
        logger.warning(f"Provider {new_provider} not available. Available: {list(self.providers.keys())}")
        return False
    
    def get_available_providers(self) -> list:
        """
        Get list of available providers
        
        Returns:
            List of provider names
        """
        return list(self.providers.keys())
    
    def get_current_provider(self) -> str:
        """
        Get current provider name
        
        Returns:
            Current provider name
        """
        return self.current_provider
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """
        Get information about a provider
        
        Args:
            provider_name: The provider name
            
        Returns:
            Provider information
        """
        if provider_name not in self.providers:
            return {}
        
        provider = self.providers[provider_name]
        return {
            'name': provider.get_provider_name(),
            'available': True,
            'current': provider_name == self.current_provider
        }
    
    def get_cost_summary(self) -> Dict[str, float]:
        """
        Get cost tracking summary
        
        Returns:
            Cost summary
        """
        return {
            'daily_cost': self.daily_cost_tracking,
            'daily_limit': float(os.getenv('AI_COST_LIMIT_DAILY', '10.0')),
            'remaining_budget': float(os.getenv('AI_COST_LIMIT_DAILY', '10.0')) - self.daily_cost_tracking
        }
    
    def reset_daily_costs(self):
        """Reset daily cost tracking"""
        self.daily_cost_tracking = 0.0
        logger.info("Daily cost tracking reset")

# Global provider manager instance
provider_manager = ProviderManager()