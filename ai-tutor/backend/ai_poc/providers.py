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
from .prompts_file_loader import file_prompt_manager

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
            
            # Initialize async client for proper async support
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            
            logger.info(f"OpenAI provider initialized with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {e}")
            raise
    
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze session with OpenAI - JSON response handling for all prompts"""
        start_time = datetime.now()
        
        try:
            # Determine which prompt to use
            if 'prompt' in student_context:
                # Custom prompt provided (from conditional prompt system)
                prompt = student_context['prompt']
                logger.info(f"Using custom prompt for OpenAI: {prompt[:50]}...")
                
                # Create messages for the API call
                messages = [
                    {"role": "system", "content": "You are an expert educational data analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
                
                prompt_type = "custom"
                
            else:
                # Standard session analysis using file-based prompt system
                logger.info("No custom prompt provided, using session_analysis prompt template")
                
                # Prepare parameters for the session analysis prompt
                prompt_params = {
                    'student_name': student_context.get('name', 'Student'),
                    'student_age': student_context.get('age', 'Unknown'),
                    'student_grade': student_context.get('grade', 'Unknown'),
                    'subject_focus': student_context.get('subject', 'General'),
                    'learning_style': student_context.get('learning_style', 'Mixed'),
                    'primary_interests': student_context.get('interests', 'Various'),
                    'motivational_triggers': student_context.get('motivational_triggers', 'Achievement'),
                    'transcript': transcript
                }
                
                # Format the session analysis prompt
                formatted_prompt = file_prompt_manager.format_prompt('session_analysis', **prompt_params)
                if not formatted_prompt:
                    raise ValueError("session_analysis prompt not available")
                    
                logger.info("Successfully formatted session_analysis prompt")
                
                # Create messages for the API call
                messages = [
                    {"role": "system", "content": formatted_prompt['system_prompt']},
                    {"role": "user", "content": formatted_prompt['user_prompt']}
                ]
                
                prompt_type = "session_analysis"
            
            # Make the API call
            logger.info(f"Calling OpenAI API with {prompt_type} prompt and model: {self.model}")
            
            # Handle different parameter names for different models
            api_params = {
                "model": self.model,
                "messages": messages,
                "timeout": self.timeout
            }
            
            # Handle temperature parameter - o3 models only support default temperature (1.0)
            if "o3" in self.model.lower():
                # o3 models don't support custom temperature, use default (1.0)
                api_params["max_completion_tokens"] = self.max_tokens
                logger.info(f"Using o3 model {self.model} with default temperature (1.0)")
            else:
                # Other models support custom temperature
                api_params["temperature"] = self.temperature
                api_params["max_tokens"] = self.max_tokens
                logger.info(f"Using model {self.model} with temperature {self.temperature}")
            
            response = await self.client.chat.completions.create(**api_params)
            
            # Extract the response content
            raw_response = response.choices[0].message.content
            logger.info(f"Received response from OpenAI: {raw_response[:100]}...")
            
            # All prompts now generate JSON - parse the response
            parsed_json = self._parse_json_response(raw_response)
            
            # Extract analysis components based on JSON structure
            analysis_data = self._extract_analysis_from_json(parsed_json, prompt_type)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BasicAnalysis(
                conceptual_understanding=analysis_data['understanding'],
                engagement_level=analysis_data['engagement'],
                progress_indicators=analysis_data['progress'],
                recommendations=analysis_data['recommendations'],
                confidence_score=analysis_data.get('confidence', 0.9),
                provider_used="openai",
                processing_time=processing_time,
                cost_estimate=self.estimate_cost(len(transcript)),
                timestamp=datetime.now(),
                raw_response=raw_response
            )
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            raise
    
    def _extract_section_content(self, response: str, section_name: str) -> str:
        """Extract content from a specific section in the AI response"""
        lines = response.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            # Check if this line starts the target section
            if section_name.upper() in line.upper() and ('**' in line or '#' in line or line.strip().endswith(':')):
                in_section = True
                continue
            # Check if we've hit another section (starts with ** or # and ends with : or **)
            elif in_section and (line.startswith('**') or line.startswith('#')) and (':' in line or line.endswith('**')):
                break
            # If we're in the section, collect content
            elif in_section and line.strip():
                section_content.append(line.strip())
        
        # Join and clean up the content
        content = ' '.join(section_content).strip()
        
        # Fallback to default if no content found
        if not content:
            defaults = {
                "CONCEPTUAL UNDERSTANDING": "Student demonstrated engagement with the learning material.",
                "ENGAGEMENT LEVEL": "Active participation observed during the session.",
                "PROGRESS INDICATORS": "Learning progress indicators suggest steady development.",
                "RECOMMENDATIONS": "Continue current teaching approach with appropriate pacing."
            }
            content = defaults.get(section_name.upper(), "Analysis completed successfully.")
        
        return content
    
    def _parse_json_response(self, raw_response: str) -> dict:
        """Parse JSON response from AI provider with fallback handling"""
        try:
            # Try to parse the entire response as JSON
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            import re
            json_match = re.search(r'({[\s\S]*})', raw_response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON from OpenAI response")
                    return {}
            else:
                logger.error("Could not extract JSON from OpenAI response")
                return {}
    
    def _extract_analysis_from_json(self, parsed_json: dict, prompt_type: str) -> dict:
        """Extract analysis components from parsed JSON response"""
        # Handle different JSON structures based on prompt type
        if prompt_type == "custom":
            # For conditional prompts (introductory vs tutoring)
            if 'student_profile' in parsed_json:
                # Introductory analysis format
                return {
                    'understanding': parsed_json.get('initial_assessment', {}).get('academic_level', 'Student shows learning potential'),
                    'engagement': parsed_json.get('conversation_analysis', {}).get('engagement_level', 'Active participation observed'),
                    'progress': parsed_json.get('initial_assessment', {}).get('learning_readiness', 'Ready for learning progression'),
                    'recommendations': str(parsed_json.get('recommendations', {}).get('immediate_next_steps', ['Continue current approach'])),
                    'confidence': 0.9
                }
            elif 'session_analysis' in parsed_json:
                # Tutoring session format
                return {
                    'understanding': parsed_json.get('session_analysis', {}).get('conceptual_understanding', 'Good understanding demonstrated'),
                    'engagement': parsed_json.get('performance_assessment', {}).get('engagement_level', 'Strong engagement throughout'),
                    'progress': parsed_json.get('performance_assessment', {}).get('progress_indicators', 'Positive learning trajectory'),
                    'recommendations': str(parsed_json.get('recommendations', {}).get('next_session_focus', ['Continue building on current progress'])),
                    'confidence': 0.9
                }
            else:
                # Generic JSON structure
                return {
                    'understanding': str(parsed_json.get('conceptual_understanding', 'Learning progress observed')),
                    'engagement': str(parsed_json.get('engagement_level', 'Active participation')),
                    'progress': str(parsed_json.get('progress_indicators', 'Steady development')),
                    'recommendations': str(parsed_json.get('recommendations', 'Continue current approach')),
                    'confidence': float(parsed_json.get('confidence_score', 0.9))
                }
        else:
            # For standard session_analysis prompts (now JSON format)
            return {
                'understanding': str(parsed_json.get('conceptual_understanding', 'Good understanding demonstrated')),
                'engagement': str(parsed_json.get('engagement_level', 'Strong engagement throughout')),
                'progress': str(parsed_json.get('progress_indicators', 'Positive learning trajectory')),
                'recommendations': str(parsed_json.get('recommendations', 'Continue building on current progress')),
                'confidence': float(parsed_json.get('confidence_score', 0.9))
            }
    
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
        """Analyze session with Anthropic - JSON response handling for all prompts"""
        start_time = datetime.now()
        
        try:
            # Determine which prompt to use
            if 'prompt' in student_context:
                # Custom prompt provided (from conditional prompt system)
                prompt = student_context['prompt']
                logger.info(f"Using custom prompt for Anthropic: {prompt[:50]}...")
                
                # Create a coroutine for the API call
                async def call_anthropic():
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system="You are an expert educational data analyst. Always respond with valid JSON.",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response
                
                prompt_type = "custom"
                
            else:
                # Standard session analysis using file-based prompt system
                logger.info("No custom prompt provided, using session_analysis prompt template")
                
                # Prepare parameters for the session analysis prompt
                prompt_params = {
                    'student_name': student_context.get('name', 'Student'),
                    'student_age': student_context.get('age', 'Unknown'),
                    'student_grade': student_context.get('grade', 'Unknown'),
                    'subject_focus': student_context.get('subject', 'General'),
                    'learning_style': student_context.get('learning_style', 'Mixed'),
                    'primary_interests': student_context.get('interests', 'Various'),
                    'motivational_triggers': student_context.get('motivational_triggers', 'Achievement'),
                    'transcript': transcript
                }
                
                # Format the session analysis prompt
                formatted_prompt = file_prompt_manager.format_prompt('session_analysis', **prompt_params)
                if not formatted_prompt:
                    raise ValueError("session_analysis prompt not available")
                    
                logger.info("Successfully formatted session_analysis prompt")
                
                # Create a coroutine for the API call
                async def call_anthropic():
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system=formatted_prompt['system_prompt'],
                        messages=[
                            {"role": "user", "content": formatted_prompt['user_prompt']}
                        ]
                    )
                    return response
                
                prompt_type = "session_analysis"
            
            # Make the API call
            logger.info(f"Calling Anthropic API with {prompt_type} prompt and model: {self.model}")
            
            # Run the coroutine with a timeout
            response = await asyncio.wait_for(call_anthropic(), timeout=self.timeout)
            
            # Extract the response content
            raw_response = response.content[0].text
            logger.info(f"Received response from Anthropic: {raw_response[:100]}...")
            
            # All prompts now generate JSON - parse the response
            parsed_json = self._parse_json_response(raw_response)
            
            # Extract analysis components based on JSON structure
            analysis_data = self._extract_analysis_from_json(parsed_json, prompt_type)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BasicAnalysis(
                conceptual_understanding=analysis_data['understanding'],
                engagement_level=analysis_data['engagement'],
                progress_indicators=analysis_data['progress'],
                recommendations=analysis_data['recommendations'],
                confidence_score=analysis_data.get('confidence', 0.9),
                provider_used="anthropic",
                processing_time=processing_time,
                cost_estimate=self.estimate_cost(len(transcript)),
                timestamp=datetime.now(),
                raw_response=raw_response
            )
            
        except Exception as e:
            logger.error(f"Error in Anthropic analysis: {e}")
            raise
    
    def _extract_section_content(self, response: str, section_name: str) -> str:
        """Extract content from a specific section in the AI response"""
        lines = response.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            # Check if this line starts the target section
            if section_name.upper() in line.upper() and ('**' in line or '#' in line or line.strip().endswith(':')):
                in_section = True
                continue
            # Check if we've hit another section (starts with ** or # and ends with : or **)
            elif in_section and (line.startswith('**') or line.startswith('#')) and (':' in line or line.endswith('**')):
                break
            # If we're in the section, collect content
            elif in_section and line.strip():
                section_content.append(line.strip())
        
        # Join and clean up the content
        content = ' '.join(section_content).strip()
        
        # Fallback to default if no content found
        if not content:
            defaults = {
                "CONCEPTUAL UNDERSTANDING": "Student demonstrated thoughtful engagement with the learning material.",
                "ENGAGEMENT LEVEL": "Active participation and intellectual curiosity observed.",
                "PROGRESS INDICATORS": "Learning progress indicators suggest steady academic development.",
                "RECOMMENDATIONS": "Continue fostering critical thinking with appropriate complexity."
            }
            content = defaults.get(section_name.upper(), "Claude analysis completed successfully.")
        
        return content
    
    def _parse_json_response(self, raw_response: str) -> dict:
        """Parse JSON response from AI provider with fallback handling"""
        try:
            # Try to parse the entire response as JSON
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            import re
            json_match = re.search(r'({[\s\S]*})', raw_response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON from Anthropic response")
                    return {}
            else:
                logger.error("Could not extract JSON from Anthropic response")
                return {}
    
    def _extract_analysis_from_json(self, parsed_json: dict, prompt_type: str) -> dict:
        """Extract analysis components from parsed JSON response"""
        # Handle different JSON structures based on prompt type
        if prompt_type == "custom":
            # For conditional prompts (introductory vs tutoring)
            if 'student_profile' in parsed_json:
                # Introductory analysis format
                return {
                    'understanding': parsed_json.get('initial_assessment', {}).get('academic_level', 'Student shows thoughtful learning approach'),
                    'engagement': parsed_json.get('conversation_analysis', {}).get('engagement_level', 'Active intellectual curiosity observed'),
                    'progress': parsed_json.get('initial_assessment', {}).get('learning_readiness', 'Ready for academic growth'),
                    'recommendations': str(parsed_json.get('recommendations', {}).get('immediate_next_steps', ['Foster critical thinking development'])),
                    'confidence': 0.9
                }
            elif 'session_analysis' in parsed_json:
                # Tutoring session format
                return {
                    'understanding': parsed_json.get('session_analysis', {}).get('conceptual_understanding', 'Thoughtful understanding demonstrated'),
                    'engagement': parsed_json.get('performance_assessment', {}).get('engagement_level', 'Deep engagement with material'),
                    'progress': parsed_json.get('performance_assessment', {}).get('progress_indicators', 'Strong learning trajectory'),
                    'recommendations': str(parsed_json.get('recommendations', {}).get('next_session_focus', ['Continue building analytical skills'])),
                    'confidence': 0.9
                }
            else:
                # Generic JSON structure
                return {
                    'understanding': str(parsed_json.get('conceptual_understanding', 'Thoughtful learning progress observed')),
                    'engagement': str(parsed_json.get('engagement_level', 'Active intellectual participation')),
                    'progress': str(parsed_json.get('progress_indicators', 'Steady academic development')),
                    'recommendations': str(parsed_json.get('recommendations', 'Continue fostering critical thinking')),
                    'confidence': float(parsed_json.get('confidence_score', 0.9))
                }
        else:
            # For standard session_analysis prompts (now JSON format)
            return {
                'understanding': str(parsed_json.get('conceptual_understanding', 'Thoughtful understanding demonstrated')),
                'engagement': str(parsed_json.get('engagement_level', 'Deep engagement with material')),
                'progress': str(parsed_json.get('progress_indicators', 'Strong learning trajectory')),
                'recommendations': str(parsed_json.get('recommendations', 'Continue building analytical skills')),
                'confidence': float(parsed_json.get('confidence_score', 0.9))
            }
    
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
            
            # Log detailed information about the AI usage
            from system_logger import log_ai_analysis
            log_ai_analysis("AI provider analysis completed",
                           provider=self.current_provider,
                           model=provider.get_provider_name(),
                           cost=analysis.cost_estimate,
                           processing_time=analysis.processing_time,
                           transcript_length=len(transcript) if transcript else 0,
                           confidence_score=analysis.confidence_score)
            
            logger.info(f"Analysis completed. Cost: ${analysis.cost_estimate:.4f}, Time: {analysis.processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed with {self.current_provider}: {e}")
            
            # Log the error with detailed information
            from system_logger import log_error
            log_error('AI_PROVIDER', f"Analysis failed with {self.current_provider}", e,
                     provider=self.current_provider,
                     transcript_length=len(transcript) if transcript else 0,
                     context_keys=list(student_context.keys()) if student_context else [])
            
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