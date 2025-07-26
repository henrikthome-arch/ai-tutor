"""
Session Post-Processor for AI Analysis POC
Orchestrates the complete analysis pipeline with provider-agnostic AI
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from .providers import provider_manager, BasicAnalysis
from .validator import validator, ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionPostProcessor:
    """
    Main service for post-processing tutoring sessions
    Integrates provider-agnostic AI analysis with quality validation
    """
    
    def __init__(self):
        self.provider_manager = provider_manager
        self.validator = validator
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0
        }
    
    async def process_session_transcript(
        self, 
        transcript: str, 
        student_context: Dict[str, Any],
        save_results: bool = True,
        session_file_path: Optional[str] = None
    ) -> Tuple[BasicAnalysis, ValidationResult]:
        """
        Process a session transcript with AI analysis and validation
        
        Args:
            transcript: The session transcript text
            student_context: Student information (name, age, subject, etc.)
            save_results: Whether to save analysis results to file
            session_file_path: Optional path to save results
            
        Returns:
            Tuple of (analysis_result, validation_result)
        """
        
        logger.info(f"Starting session analysis for student: {student_context.get('name', 'Unknown')}")
        
        # Step 1: Validate transcript
        transcript_validation = self.validator.validate_transcript(transcript)
        if not transcript_validation.is_valid:
            logger.error(f"Transcript validation failed: {transcript_validation.issues}")
            raise ValueError(f"Invalid transcript: {', '.join(transcript_validation.issues)}")
        
        if transcript_validation.warnings:
            logger.warning(f"Transcript warnings: {transcript_validation.warnings}")
        
        # Step 2: Perform AI analysis
        try:
            analysis = await self.provider_manager.analyze_session(transcript, student_context)
            self.processing_stats['successful'] += 1
            logger.info(f"AI analysis completed with {analysis.provider_used}")
            
        except Exception as e:
            self.processing_stats['failed'] += 1
            logger.error(f"AI analysis failed: {e}")
            raise
        
        # Step 3: Validate analysis quality
        analysis_validation = self.validator.validate_analysis(analysis, transcript)
        
        if analysis_validation.warnings:
            logger.warning(f"Analysis quality warnings: {analysis_validation.warnings}")
        
        if not analysis_validation.is_valid:
            logger.warning(f"Analysis quality issues: {analysis_validation.issues}")
        
        # Step 4: Update statistics
        self.processing_stats['total_processed'] += 1
        self.processing_stats['total_cost'] += analysis.cost_estimate
        
        # Step 5: Save results if requested
        if save_results and session_file_path:
            await self._save_analysis_results(analysis, analysis_validation, session_file_path, student_context)
        
        logger.info(f"Session processing completed. Quality score: {analysis_validation.score:.2f}")
        
        return analysis, analysis_validation
    
    async def process_student_session_file(
        self, 
        student_id: str, 
        session_filename: str = "2025-01-14_transcript.txt"
    ) -> Tuple[BasicAnalysis, ValidationResult]:
        """
        Process a specific student session file
        
        Args:
            student_id: Student identifier
            session_filename: Name of the transcript file
            
        Returns:
            Tuple of (analysis_result, validation_result)
        """
        
        # Load transcript
        transcript_path = f"data/students/{student_id}/sessions/{session_filename}"
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        # Load student context
        profile_path = f"data/students/{student_id}/profile.json"
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Student profile not found: {profile_path}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            student_context = json.load(f)
        
        # Add student_id to context
        student_context['student_id'] = student_id
        
        # Process the session
        analysis_results_path = f"data/students/{student_id}/sessions/ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return await self.process_session_transcript(
            transcript=transcript,
            student_context=student_context,
            save_results=True,
            session_file_path=analysis_results_path
        )
    
    async def _save_analysis_results(
        self, 
        analysis: BasicAnalysis, 
        validation: ValidationResult,
        file_path: str,
        student_context: Dict[str, Any]
    ):
        """Save analysis results to file"""
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Prepare results data
            results_data = {
                'metadata': {
                    'student_id': student_context.get('student_id'),
                    'student_name': student_context.get('name'),
                    'session_date': datetime.now().isoformat(),
                    'analysis_version': 'POC-1.0',
                    'provider_used': analysis.provider_used
                },
                'analysis': analysis.to_dict(),
                'validation': {
                    'is_valid': validation.is_valid,
                    'score': validation.score,
                    'issues': validation.issues,
                    'warnings': validation.warnings,
                    'confidence_adjusted': validation.confidence_adjusted
                },
                'processing_stats': {
                    'processing_time': analysis.processing_time,
                    'cost_estimate': analysis.cost_estimate,
                    'timestamp': analysis.timestamp.isoformat()
                }
            }
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis results saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
            raise
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        
        cost_summary = self.provider_manager.get_cost_summary()
        
        return {
            'processing_stats': self.processing_stats.copy(),
            'cost_summary': cost_summary,
            'current_provider': self.provider_manager.get_current_provider(),
            'available_providers': self.provider_manager.get_available_providers(),
            'success_rate': (
                self.processing_stats['successful'] / self.processing_stats['total_processed']
                if self.processing_stats['total_processed'] > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset processing statistics (for testing)"""
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0
        }
        self.provider_manager.reset_daily_costs()
        logger.info("Processing statistics reset")

# Test data for POC validation
SAMPLE_TRANSCRIPT = """
Tutor: Hello Emma! Today we're going to work on solving linear equations. Are you ready?
Student: Yes, I'm ready! But I'm still a bit confused about how to isolate the variable.
Tutor: That's perfectly normal. Let's start with a simple example: 2x + 5 = 13. What do you think our first step should be?
Student: Um, I think we need to get rid of the 5 first?
Tutor: Excellent thinking! And how would we get rid of the 5?
Student: Subtract 5 from both sides?
Tutor: Perfect! So what do we get when we subtract 5 from both sides?
Student: 2x = 8
Tutor: Great! Now what's our next step?
Student: We divide both sides by 2?
Tutor: Exactly! And what does that give us?
Student: x = 4
Tutor: Wonderful! You solved it correctly. Let's try another one to make sure you understand the process.
Student: Okay, I think I'm starting to get it!
Tutor: Let's try 3x - 7 = 14. Remember the steps we just used.
Student: First I add 7 to both sides... so 3x = 21?
Tutor: Perfect! And then?
Student: Divide by 3... so x = 7?
Tutor: Excellent work! You're really understanding the concept of isolating the variable.
"""

SAMPLE_STUDENT_CONTEXT = {
    'name': 'Emma Smith',
    'age': 14,
    'grade': 8,
    'subject': 'Mathematics',
    'student_id': 'emma_smith',
    'learning_goals': ['Solve linear equations', 'Understand algebraic manipulation'],
    'previous_challenges': ['Variable isolation', 'Order of operations']
}

# Global processor instance
session_processor = SessionPostProcessor()

# Async function for testing
async def test_sample_analysis():
    """Test the session processor with sample data"""
    
    logger.info("Testing session processor with sample data...")
    
    try:
        analysis, validation = await session_processor.process_session_transcript(
            transcript=SAMPLE_TRANSCRIPT,
            student_context=SAMPLE_STUDENT_CONTEXT,
            save_results=False
        )
        
        logger.info("=== ANALYSIS RESULTS ===")
        logger.info(f"Provider: {analysis.provider_used}")
        logger.info(f"Confidence: {analysis.confidence_score:.2f}")
        logger.info(f"Processing time: {analysis.processing_time:.2f}s")
        logger.info(f"Cost: ${analysis.cost_estimate:.4f}")
        
        logger.info("=== VALIDATION RESULTS ===")
        logger.info(f"Valid: {validation.is_valid}")
        logger.info(f"Score: {validation.score:.2f}")
        logger.info(f"Adjusted confidence: {validation.confidence_adjusted:.2f}")
        
        if validation.warnings:
            logger.info(f"Warnings: {validation.warnings}")
        
        if validation.issues:
            logger.warning(f"Issues: {validation.issues}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_sample_analysis())