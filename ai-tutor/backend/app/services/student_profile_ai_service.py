"""
Student Profile AI Service for post-session updates
Handles AI-driven profile and memory updates after tutoring sessions
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ai.providers import provider_manager
from ai.prompts_file_loader import load_prompt_template
from app.services.student_service import StudentService
from app.services.session_service import SessionService
from app.repositories import student_profile_repository, student_memory_repository

logger = logging.getLogger(__name__)


class StudentProfileAIService:
    """Service for AI-driven student profile and memory updates"""
    
    def __init__(self):
        self.student_service = StudentService()
        self.session_service = SessionService()
        self.provider_manager = provider_manager
    
    async def post_session_ai_update(self, session_id: int) -> Dict[str, Any]:
        """
        Perform AI-driven profile and memory updates after a tutoring session
        
        Args:
            session_id: The session ID to process
            
        Returns:
            Dictionary with update results and status
        """
        try:
            # Get session data
            from app.models.session import Session
            from app import db
            
            session = Session.query.get(session_id)
            if not session:
                return {
                    'success': False,
                    'error': 'Session not found',
                    'session_id': session_id
                }
            
            # Skip if no student ID (welcome sessions)
            if not session.student_id:
                logger.info(f"Skipping AI update for session {session_id} - no student ID")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'No student ID',
                    'session_id': session_id
                }
            
            # Skip if no transcript
            if not session.transcript or len(session.transcript.strip()) < 50:
                logger.info(f"Skipping AI update for session {session_id} - insufficient transcript")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Insufficient transcript',
                    'session_id': session_id
                }
            
            logger.info(f"Starting AI-driven post-session update for session {session_id}, student {session.student_id}")
            
            # Get full student context
            student_context = self.student_service.get_full_context(session.student_id)
            if 'error' in student_context:
                return {
                    'success': False,
                    'error': f"Failed to get student context: {student_context['error']}",
                    'session_id': session_id,
                    'student_id': session.student_id
                }
            
            # Build AI prompt with context
            prompt = self._build_update_prompt(session.transcript, student_context)
            
            # Call AI for analysis
            ai_context = {
                'prompt': prompt,
                'task': 'post_session_update',
                'student_id': session.student_id,
                'session_id': session_id
            }
            
            analysis = await self.provider_manager.analyze_session(session.transcript, ai_context)
            
            # Parse JSON response
            try:
                if analysis.raw_response:
                    # Try to extract JSON from the response
                    ai_response = self._extract_json_from_response(analysis.raw_response)
                else:
                    raise ValueError("No raw response from AI provider")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse AI response for session {session_id}: {e}")
                logger.error(f"Raw response: {analysis.raw_response}")
                return {
                    'success': False,
                    'error': f'Failed to parse AI response: {str(e)}',
                    'session_id': session_id,
                    'student_id': session.student_id,
                    'raw_response': analysis.raw_response
                }
            
            # Apply updates
            update_results = await self._apply_ai_updates(session.student_id, ai_response)
            
            # Ensure session has summary
            self.session_service.ensure_session_summary(session_id)
            
            # Log successful completion
            logger.info(f"✅ AI post-session update completed for session {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'student_id': session.student_id,
                'ai_response': ai_response,
                'update_results': update_results,
                'processing_time': analysis.processing_time,
                'cost_estimate': analysis.cost_estimate,
                'provider_used': analysis.provider_used,
                'confidence_score': ai_response.get('confidence_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error in post-session AI update for session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'student_id': getattr(session, 'student_id', None) if 'session' in locals() else None
            }
    
    def _build_update_prompt(self, transcript: str, student_context: Dict[str, Any]) -> str:
        """
        Build the AI prompt for post-session updates
        
        Args:
            transcript: Session transcript
            student_context: Full student context
            
        Returns:
            Formatted prompt string
        """
        try:
            # Load the prompt template
            template = load_prompt_template('post_session_update.md')
            
            # Format with student context
            formatted_prompt = template.format(
                basic_info=json.dumps(student_context.get('basic_info', {}), indent=2),
                current_profile=json.dumps(student_context.get('current_profile', {}), indent=2),
                existing_memories=json.dumps(student_context.get('memories', {}), indent=2),
                recent_sessions=json.dumps(student_context.get('recent_sessions', []), indent=2),
                transcript=transcript
            )
            
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"Error building update prompt: {e}")
            # Fallback to basic prompt
            return f"""
            Analyze this tutoring session transcript and extract student profile and memory updates.

            Student Context: {json.dumps(student_context, indent=2)}
            
            Session Transcript:
            {transcript}
            
            Respond with a JSON object containing profile_updates and memory_updates.
            """
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON object from AI response
        
        Args:
            response: Raw AI response
            
        Returns:
            Parsed JSON object
        """
        # Try to find JSON block in the response
        import re
        
        # Look for JSON code blocks
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Look for standalone JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to parse the whole response
                json_str = response.strip()
        
        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError:
            # If parsing fails, try to clean up the string
            cleaned = json_str.replace('\n', ' ').replace('\t', ' ')
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return json.loads(cleaned)
    
    async def _apply_ai_updates(self, student_id: int, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply AI-generated updates to student profile and memories
        
        Args:
            student_id: The student ID
            ai_response: Parsed AI response with updates
            
        Returns:
            Results of the update operations
        """
        results = {
            'profile_updated': False,
            'memories_updated': False,
            'profile_result': None,
            'memory_results': [],
            'errors': []
        }
        
        try:
            # Apply profile updates
            profile_updates = ai_response.get('profile_updates', {})
            if profile_updates and (profile_updates.get('narrative_changes') or profile_updates.get('trait_updates')):
                try:
                    profile_result = self.student_service.update_profile_from_ai_delta(student_id, profile_updates)
                    if profile_result:
                        results['profile_updated'] = True
                        results['profile_result'] = profile_result
                        logger.info(f"✅ Updated profile for student {student_id}")
                except Exception as e:
                    error_msg = f"Profile update failed: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Apply memory updates
            memory_updates = ai_response.get('memory_updates', {})
            if memory_updates:
                try:
                    memory_results = self.student_service.update_memories_from_ai_delta(student_id, memory_updates)
                    if memory_results:
                        results['memories_updated'] = True
                        results['memory_results'] = memory_results
                        logger.info(f"✅ Updated {len(memory_results)} memories for student {student_id}")
                except Exception as e:
                    error_msg = f"Memory update failed: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            error_msg = f"Error applying AI updates: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            return results
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about AI processing
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get basic stats from provider manager
            cost_summary = self.provider_manager.get_cost_summary()
            
            # Get profile and memory statistics
            profile_stats = student_profile_repository.get_profile_statistics()
            memory_stats = student_memory_repository.get_memory_statistics()
            
            return {
                'ai_provider': {
                    'current_provider': self.provider_manager.get_current_provider(),
                    'available_providers': self.provider_manager.get_available_providers(),
                    'cost_summary': cost_summary
                },
                'profile_stats': profile_stats,
                'memory_stats': memory_stats,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }


# Create a global instance for easy import
student_profile_ai_service = StudentProfileAIService()