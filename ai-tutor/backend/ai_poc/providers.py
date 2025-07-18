"""
AI Provider implementations for session post-processing POC
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

class MockOpenAIProvider(SimpleAIProvider):
    """Mock OpenAI provider for POC validation (no actual API calls)"""
    
    def __init__(self):
        self.config = ai_config.get_openai_config()
        self.model = self.config['model']
        
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Mock OpenAI analysis for POC"""
        
        start_time = datetime.now()
        
        # Simulate API delay
        await asyncio.sleep(1.5)
        
        # Generate mock analysis based on transcript content
        analysis_text = self._generate_mock_analysis(transcript, student_context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return BasicAnalysis(
            conceptual_understanding=analysis_text['understanding'],
            engagement_level=analysis_text['engagement'],
            progress_indicators=analysis_text['progress'],
            recommendations=analysis_text['recommendations'],
            confidence_score=0.85,
            provider_used="openai",
            processing_time=processing_time,
            cost_estimate=self.estimate_cost(len(transcript)),
            timestamp=datetime.now(),
            raw_response=analysis_text.get('raw_response', json.dumps(analysis_text, indent=2))
        )
    
    def _generate_mock_analysis(self, transcript: str, student_context: Dict[str, Any]) -> Dict[str, str]:
        """Generate mock educational analysis with profile extraction"""
        
        student_name = student_context.get('name', 'Student')
        subject = student_context.get('subject', 'General')
        age = student_context.get('age', 'Unknown')
        
        # Check if we have a custom prompt for profile extraction
        if 'prompt' in student_context:
            logger.info("Using custom prompt for profile extraction")
            
            # Extract student profile information from transcript
            import re
            import json
            
            # Extract age
            age_match = re.search(r"I'?m\s+(\d+)", transcript)
            extracted_age = int(age_match.group(1)) if age_match else None
            
            # Extract grade
            grade_match = re.search(r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+grade", transcript)
            grade_word_match = re.search(r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+grade", transcript, re.IGNORECASE)
            
            extracted_grade = None
            if grade_match:
                extracted_grade = int(grade_match.group(1))
            elif grade_word_match:
                grade_words = {
                    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
                    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
                    "eleventh": 11, "twelfth": 12
                }
                grade_word = grade_word_match.group(1).lower()
                if grade_word in grade_words:
                    extracted_grade = grade_words[grade_word]
            
            # Extract interests
            interests = []
            interest_matches = re.findall(r"I (?:like|love|enjoy) ([^.,!?]+)", transcript, re.IGNORECASE)
            for match in interest_matches:
                interests.append(match.strip())
            
            # Create profile JSON
            profile_json = {
                "age": extracted_age,
                "grade": extracted_grade,
                "interests": interests,
                "learning_preferences": [],
                "subjects": {
                    "favorite": [],
                    "challenging": []
                },
                "confidence_score": 0.9
            }
            
            # Log the extracted profile
            logger.info(f"Extracted profile: {json.dumps(profile_json)}")
            
            # Return standard analysis with raw JSON response
            understanding = f"OpenAI Analysis: {student_name} demonstrated good conceptual grasp of the lesson material."
            engagement = "Student showed consistent engagement throughout the tutoring session."
            progress = "Steady learning progress observed. Student building confidence in the subject area."
            recommendations = "Continue current approach. Consider introducing more challenging concepts gradually."
            
            # Set the raw response to the profile JSON
            raw_response = json.dumps(profile_json)
            
            return {
                'understanding': understanding,
                'engagement': engagement,
                'progress': progress,
                'recommendations': recommendations,
                'raw_response': raw_response
            }
        
        # Standard analysis if no custom prompt
        transcript_lower = transcript.lower()
        
        if 'math' in subject.lower() or any(word in transcript_lower for word in ['equation', 'solve', 'number', 'calculate']):
            understanding = f"OpenAI Analysis: {student_name} demonstrated solid mathematical reasoning skills, showing understanding of core algebraic concepts."
            engagement = "High engagement - student actively participated in problem-solving and asked clarifying questions."
            progress = "Strong progress in equation solving. Student successfully applied step-by-step methodology."
            recommendations = "Continue with similar difficulty level. Introduce word problems to apply mathematical concepts in real-world contexts."
        
        elif any(word in transcript_lower for word in ['read', 'story', 'book', 'writing']):
            understanding = f"OpenAI Analysis: {student_name} shows good comprehension skills and vocabulary development for age {age}."
            engagement = "Moderate to high engagement - student showed interest in the reading material."
            progress = "Reading fluency improving. Student demonstrates better comprehension of complex sentences."
            recommendations = "Encourage more independent reading. Focus on expanding vocabulary through context clues."
        
        else:
            understanding = f"OpenAI Analysis: {student_name} demonstrated good conceptual grasp of the lesson material."
            engagement = "Student showed consistent engagement throughout the tutoring session."
            progress = "Steady learning progress observed. Student building confidence in the subject area."
            recommendations = "Continue current approach. Consider introducing more challenging concepts gradually."
        
        return {
            'understanding': understanding,
            'engagement': engagement,
            'progress': progress,
            'recommendations': recommendations
        }
    
    def get_provider_name(self) -> str:
        return f"OpenAI (Mock - {self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        # Mock cost estimation: ~$0.001 per 1000 characters
        return (transcript_length / 1000) * 0.001

class MockAnthropicProvider(SimpleAIProvider):
    """Mock Anthropic provider for POC validation"""
    
    def __init__(self):
        self.config = ai_config.get_anthropic_config()
        self.model = self.config['model']
        
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Mock Anthropic analysis for POC"""
        
        start_time = datetime.now()
        
        # Simulate different processing time
        await asyncio.sleep(2.0)
        
        analysis_text = self._generate_mock_analysis(transcript, student_context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return BasicAnalysis(
            conceptual_understanding=analysis_text['understanding'],
            engagement_level=analysis_text['engagement'],
            progress_indicators=analysis_text['progress'],
            recommendations=analysis_text['recommendations'],
            confidence_score=0.82,
            provider_used="anthropic",
            processing_time=processing_time,
            cost_estimate=self.estimate_cost(len(transcript)),
            timestamp=datetime.now(),
            raw_response=analysis_text.get('raw_response', json.dumps(analysis_text, indent=2))
        )
    
    def _generate_mock_analysis(self, transcript: str, student_context: Dict[str, Any]) -> Dict[str, str]:
        """Generate mock Claude analysis with profile extraction"""
        
        student_name = student_context.get('name', 'Student')
        subject = student_context.get('subject', 'General')
        
        # Check if we have a custom prompt for profile extraction
        if 'prompt' in student_context:
            logger.info("Using custom prompt for profile extraction in Anthropic provider")
            
            # Extract student profile information from transcript
            import re
            import json
            
            # Extract age
            age_match = re.search(r"I'?m\s+(\d+)", transcript)
            extracted_age = int(age_match.group(1)) if age_match else None
            
            # Extract grade
            grade_match = re.search(r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+grade", transcript)
            grade_word_match = re.search(r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+grade", transcript, re.IGNORECASE)
            
            extracted_grade = None
            if grade_match:
                extracted_grade = int(grade_match.group(1))
            elif grade_word_match:
                grade_words = {
                    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
                    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
                    "eleventh": 11, "twelfth": 12
                }
                grade_word = grade_word_match.group(1).lower()
                if grade_word in grade_words:
                    extracted_grade = grade_words[grade_word]
            
            # Extract interests
            interests = []
            interest_matches = re.findall(r"I (?:like|love|enjoy) ([^.,!?]+)", transcript, re.IGNORECASE)
            for match in interest_matches:
                interests.append(match.strip())
            
            # Create profile JSON
            profile_json = {
                "age": extracted_age,
                "grade": extracted_grade,
                "interests": interests,
                "learning_preferences": [],
                "subjects": {
                    "favorite": [],
                    "challenging": []
                },
                "confidence_score": 0.9
            }
            
            # Log the extracted profile
            logger.info(f"Anthropic extracted profile: {json.dumps(profile_json)}")
            
            # Return standard analysis with raw JSON response
            understanding = f"Claude Analysis: {student_name} shows thoughtful engagement with the learning material and demonstrates good critical thinking skills."
            engagement = "Positive learning attitude - student actively participating and showing intellectual curiosity."
            progress = "Steady academic growth with good foundation building. Student developing effective learning strategies."
            recommendations = "Continue fostering critical thinking. Introduce more independent exploration opportunities."
            
            # Set the raw response to the profile JSON
            raw_response = json.dumps(profile_json)
            
            return {
                'understanding': understanding,
                'engagement': engagement,
                'progress': progress,
                'recommendations': recommendations,
                'raw_response': raw_response
            }
        
        # Standard analysis if no custom prompt
        transcript_lower = transcript.lower()
        
        if 'math' in subject.lower() or any(word in transcript_lower for word in ['equation', 'solve', 'number']):
            understanding = f"Claude Analysis: {student_name} exhibits strong analytical thinking and mathematical intuition. Shows excellent grasp of underlying mathematical principles."
            engagement = "Highly engaged - student demonstrates curiosity and willingness to explore different solution approaches."
            progress = "Excellent mathematical development. Student showing increased confidence in tackling complex problems."
            recommendations = "Introduce more challenging multi-step problems. Consider exploring mathematical connections to real-world applications."
        
        elif any(word in transcript_lower for word in ['read', 'story', 'book', 'writing']):
            understanding = f"Claude Analysis: {student_name} demonstrates thoughtful reading comprehension and growing literary awareness."
            engagement = "Good engagement with text - student making meaningful connections and asking insightful questions."
            progress = "Strong progress in critical thinking about literature. Developing analytical reading skills."
            recommendations = "Encourage deeper textual analysis. Introduce more complex literary works appropriate for student's level."
        
        else:
            understanding = f"Claude Analysis: {student_name} shows thoughtful engagement with the learning material and demonstrates good critical thinking skills."
            engagement = "Positive learning attitude - student actively participating and showing intellectual curiosity."
            progress = "Steady academic growth with good foundation building. Student developing effective learning strategies."
            recommendations = "Continue fostering critical thinking. Introduce more independent exploration opportunities."
        
        return {
            'understanding': understanding,
            'engagement': engagement,
            'progress': progress,
            'recommendations': recommendations
        }
    
    def get_provider_name(self) -> str:
        return f"Anthropic (Mock - {self.model})"
    
    def estimate_cost(self, transcript_length: int) -> float:
        # Anthropic cost estimation
        return (transcript_length / 1000) * 0.0008

class ProviderManager:
    """Simplified provider manager for POC"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = ai_config.ai_provider
        self.daily_cost_tracking = 0.0
        
        # Initialize available providers
        self._initialize_providers()
        
        logger.info(f"ProviderManager initialized with {len(self.providers)} providers")
        logger.info(f"Current provider: {self.current_provider}")
    
    def _initialize_providers(self):
        """Initialize available providers"""
        try:
            # Always add mock providers for POC
            self.providers['openai'] = MockOpenAIProvider()
            logger.info("OpenAI mock provider initialized")
        except Exception as e:
            logger.warning(f"OpenAI provider initialization failed: {e}")
        
        try:
            self.providers['anthropic'] = MockAnthropicProvider()
            logger.info("Anthropic mock provider initialized")
        except Exception as e:
            logger.warning(f"Anthropic provider initialization failed: {e}")
    
    async def analyze_session(self, transcript: str, student_context: Dict[str, Any]) -> BasicAnalysis:
        """Analyze session with current provider"""
        
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