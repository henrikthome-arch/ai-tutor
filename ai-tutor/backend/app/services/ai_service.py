"""
Service for AI processing with support for asynchronous tasks.
"""

import logging
from app.ai.session_processor import SessionProcessor
from app.tasks.ai_tasks import process_ai_response, analyze_session_transcript

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI processing with support for asynchronous tasks."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.processor = SessionProcessor()
    
    def generate_response(self, prompt, model_params=None, async_mode=False, session_id=None):
        """
        Generate a response from the AI model.
        
        Args:
            prompt (str): The prompt to send to the AI provider
            model_params (dict, optional): Parameters for the AI model
            async_mode (bool): Whether to process asynchronously
            session_id (str, optional): Session ID for tracking
            
        Returns:
            If async_mode is True, returns a task ID
            If async_mode is False, returns the AI response
        """
        if model_params is None:
            model_params = {}
        
        logger.info(f"Generating AI response for session {session_id} (async={async_mode})")
        
        if async_mode:
            # Process asynchronously using Celery
            task = process_ai_response.delay(prompt, model_params, session_id)
            return {"task_id": task.id, "status": "processing"}
        else:
            # Process synchronously
            return self.processor.process(prompt, model_params)
    
    def analyze_transcript(self, transcript, session_id, async_mode=True):
        """
        Analyze a session transcript to extract insights.
        
        Args:
            transcript (str): The session transcript
            session_id (str): Session ID for tracking
            async_mode (bool): Whether to process asynchronously
            
        Returns:
            If async_mode is True, returns a task ID
            If async_mode is False, returns the analysis results
        """
        logger.info(f"Analyzing transcript for session {session_id} (async={async_mode})")
        
        if async_mode:
            # Process asynchronously using Celery
            task = analyze_session_transcript.delay(transcript, session_id)
            return {"task_id": task.id, "status": "processing"}
        else:
            # This would use the AI to analyze the transcript synchronously
            # For now, we'll return a placeholder
            return {
                "session_id": session_id,
                "topics_covered": ["placeholder"],
                "student_understanding": "placeholder",
                "areas_for_improvement": ["placeholder"],
                "recommended_next_steps": ["placeholder"]
            }
    
    def get_task_status(self, task_id):
        """
        Get the status of an asynchronous task.
        
        Args:
            task_id (str): The ID of the task to check
            
        Returns:
            dict: The task status and result if available
        """
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                return {
                    "status": "completed",
                    "result": task_result.result
                }
            else:
                return {
                    "status": "failed",
                    "error": str(task_result.result)
                }
        else:
            return {
                "status": "processing"
            }