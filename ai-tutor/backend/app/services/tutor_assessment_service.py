"""
Service for AI tutor performance assessment.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from app import db
from app.models.session import Session
from app.models.student import Student
from app.services.mcp_interaction_service import MCPInteractionService
from ai.session_processor import SessionProcessor

logger = logging.getLogger(__name__)

class TutorAssessmentService:
    """Service for assessing AI tutor performance using post-session analysis."""
    
    def __init__(self):
        """Initialize the tutor assessment service."""
        self.processor = SessionProcessor()
        self.mcp_service = MCPInteractionService()
        
    def assess_tutor_performance(self, session_id: int) -> Dict:
        """
        Assess AI tutor performance for a completed tutoring session.
        
        Args:
            session_id (int): The ID of the session to assess
            
        Returns:
            Dict: Assessment results containing success status and any errors
        """
        try:
            # Log the start of assessment
            self.mcp_service.log_interaction(
                interaction_type="tutor_assessment_start",
                data={"session_id": session_id},
                session_id=session_id
            )
            
            # Get session data
            session = Session.query.get(session_id)
            if not session:
                error_msg = f"Session {session_id} not found"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Skip assessment for welcome/introductory sessions (no student_id)
            if not session.student_id:
                logger.info(f"Skipping assessment for welcome session {session_id}")
                return {"success": True, "skipped": True, "reason": "Welcome session"}
            
            # Check if session has transcript
            if not session.transcript or len(session.transcript.strip()) < 50:
                error_msg = f"Session {session_id} has insufficient transcript data"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}
            
            # Gather assessment data
            assessment_data = self._gather_assessment_data(session)
            if not assessment_data["success"]:
                return assessment_data
            
            # Generate assessment prompt
            assessment_prompt = self._create_assessment_prompt(assessment_data["data"])
            
            # Call AI model for assessment
            assessment_result = self._call_ai_for_assessment(assessment_prompt, session_id)
            if not assessment_result["success"]:
                return assessment_result
            
            # Parse and validate JSON response
            parsed_assessment = self._parse_assessment_response(assessment_result["response"])
            if not parsed_assessment["success"]:
                return parsed_assessment
            
            # Save assessment to database
            session.tutor_assessment = parsed_assessment["data"]["assessment-of-ai-tutor"]
            session.prompt_suggestions = parsed_assessment["data"]["suggested-changes"]
            
            try:
                db.session.commit()
                
                # Log successful assessment
                self.mcp_service.log_interaction(
                    interaction_type="tutor_assessment_completed",
                    data={
                        "session_id": session_id,
                        "assessment_length": len(session.tutor_assessment),
                        "suggestions_length": len(session.prompt_suggestions)
                    },
                    session_id=session_id
                )
                
                logger.info(f"Successfully completed tutor assessment for session {session_id}")
                return {
                    "success": True,
                    "session_id": session_id,
                    "assessment_saved": True
                }
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"Failed to save assessment for session {session_id}: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Error assessing tutor performance for session {session_id}: {str(e)}"
            logger.error(error_msg)
            
            # Log the error
            self.mcp_service.log_interaction(
                interaction_type="tutor_assessment_error",
                data={"session_id": session_id, "error": str(e)},
                session_id=session_id
            )
            
            return {"success": False, "error": error_msg}
    
    def _gather_assessment_data(self, session: Session) -> Dict:
        """
        Gather all data needed for tutor assessment.
        
        Args:
            session (Session): The session to assess
            
        Returns:
            Dict: Gathered data or error information
        """
        try:
            # Get student profile
            student = Student.query.get(session.student_id)
            if not student:
                return {"success": False, "error": f"Student {session.student_id} not found"}
            
            # Read guidelines file
            guidelines_content = self._read_guidelines_file()
            if not guidelines_content:
                return {"success": False, "error": "Could not read guidelines file"}
            
            # Read current AI tutor prompt
            prompt_content = self._read_ai_tutor_prompt()
            if not prompt_content:
                return {"success": False, "error": "Could not read AI tutor prompt"}
            
            # Compile student profile data
            student_profile = {
                "name": f"{student.first_name} {student.last_name}",
                "age": student.age,
                "grade": student.grade,
                "phone_number": student.phone_number,
                "interests": student.interests or [],
                "learning_preferences": student.learning_preferences,
                "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
                "created_at": str(student.created_at),
                "updated_at": str(student.updated_at)
            }
            
            return {
                "success": True,
                "data": {
                    "transcript": session.transcript,
                    "guidelines": guidelines_content,
                    "student_profile": student_profile,
                    "ai_tutor_prompt": prompt_content,
                    "session_info": {
                        "session_id": session.id,
                        "duration": session.duration,
                        "session_type": session.session_type,
                        "start_datetime": str(session.start_datetime)
                    }
                }
            }
            
        except Exception as e:
            error_msg = f"Error gathering assessment data: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _read_guidelines_file(self) -> Optional[str]:
        """Read the AI tutor guidelines file."""
        try:
            # Path to guidelines file
            guidelines_path = Path(__file__).parent.parent / "ai" / "resources" / "guidelines-for-ai-tutor.md"
            
            if not guidelines_path.exists():
                logger.error(f"Guidelines file not found at {guidelines_path}")
                return None
            
            with open(guidelines_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading guidelines file: {str(e)}")
            return None
    
    def _read_ai_tutor_prompt(self) -> Optional[str]:
        """Read the current AI tutor prompt system."""
        try:
            # Path to AI assistant prompt file
            prompt_path = Path(__file__).parent.parent.parent.parent / "docs" / "AI_ASSISTANT_PROMPT_SYSTEM.md"
            
            if not prompt_path.exists():
                logger.error(f"AI prompt file not found at {prompt_path}")
                return None
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading AI prompt file: {str(e)}")
            return None
    
    def _create_assessment_prompt(self, assessment_data: Dict) -> str:
        """
        Create the prompt for AI tutor performance assessment.
        
        Args:
            assessment_data (Dict): All gathered data for assessment
            
        Returns:
            str: The assessment prompt
        """
        prompt = f"""You are an expert educational consultant specializing in AI tutoring effectiveness. Your task is to assess the performance of an AI tutor during a tutoring session and provide constructive feedback.

## ASSESSMENT CONTEXT

### SESSION INFORMATION
- Session ID: {assessment_data['session_info']['session_id']}
- Duration: {assessment_data['session_info']['duration']} seconds
- Session Type: {assessment_data['session_info']['session_type']}
- Date: {assessment_data['session_info']['start_datetime']}

### STUDENT PROFILE
- Name: {assessment_data['student_profile']['name']}
- Age: {assessment_data['student_profile']['age']} years old
- Grade: {assessment_data['student_profile']['grade']}
- Interests: {', '.join(assessment_data['student_profile']['interests']) if assessment_data['student_profile']['interests'] else 'Not specified'}
- Learning Preferences: {assessment_data['student_profile']['learning_preferences'] or 'Not specified'}

### AI TUTOR GUIDELINES
The AI tutor should follow these evidence-based best practices:

{assessment_data['guidelines']}

### CURRENT AI TUTOR PROMPT SYSTEM
The AI tutor is operating with this prompt configuration:

{assessment_data['ai_tutor_prompt']}

### SESSION TRANSCRIPT
Here is the actual conversation transcript to assess:

{assessment_data['transcript']}

## ASSESSMENT TASK

Please analyze the AI tutor's performance in this session and provide feedback in JSON format only. Evaluate how well the tutor:

1. **Followed the guidelines**: Applied evidence-based teaching strategies
2. **Personalized the experience**: Used student interests and learning preferences
3. **Maintained engagement**: Kept the student actively participating
4. **Provided effective instruction**: Delivered clear, age-appropriate content
5. **Used appropriate tone and approach**: Matched the student's personality and needs
6. **Managed the session structure**: Balanced content, pacing, and interaction

## REQUIRED OUTPUT FORMAT

Respond with ONLY a valid JSON object containing exactly these two fields:

```json
{{
  "assessment-of-ai-tutor": "Your detailed assessment paragraph(s) here. Discuss what the AI tutor did well and what could be improved. Reference specific examples from the transcript and guidelines.",
  "suggested-changes": "Specific, actionable suggestions for improving the VAPI/chat prompt or tutoring approach. Focus on concrete changes that could enhance effectiveness based on your analysis."
}}
```

## IMPORTANT REQUIREMENTS

- Provide ONLY the JSON response, no additional text
- Base your assessment on evidence from the transcript
- Reference specific examples where possible
- Be constructive and specific in your feedback
- Consider the student's age and learning needs
- Focus on actionable improvements for the prompt/approach
- Ensure suggestions are implementable in an AI tutoring context"""

        return prompt
    
    def _call_ai_for_assessment(self, prompt: str, session_id: int) -> Dict:
        """
        Call the AI model to perform the assessment.
        
        Args:
            prompt (str): The assessment prompt
            session_id (int): Session ID for logging
            
        Returns:
            Dict: AI response or error information
        """
        try:
            # Log the AI call
            self.mcp_service.log_interaction(
                interaction_type="tutor_assessment_ai_call",
                data={
                    "session_id": session_id,
                    "prompt_length": len(prompt)
                },
                session_id=session_id
            )
            
            # Use the existing AI processor
            response = self.processor.process(prompt, {
                "max_tokens": 1500,
                "temperature": 0.3,
                "model": "gpt-4"
            })
            
            if not response:
                return {"success": False, "error": "No response from AI model"}
            
            # Log successful AI response
            self.mcp_service.log_interaction(
                interaction_type="tutor_assessment_ai_response",
                data={
                    "session_id": session_id,
                    "response_length": len(str(response))
                },
                session_id=session_id
            )
            
            return {"success": True, "response": response}
            
        except Exception as e:
            error_msg = f"Error calling AI for assessment: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _parse_assessment_response(self, response) -> Dict:
        """
        Parse and validate the AI assessment response.
        
        Args:
            response: The AI model response
            
        Returns:
            Dict: Parsed assessment data or error information
        """
        try:
            # Convert response to string if needed
            response_text = str(response).strip()
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return {"success": False, "error": "No JSON found in AI response"}
            
            json_text = response_text[json_start:json_end]
            
            # Parse JSON
            try:
                parsed_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON in AI response: {str(e)}"}
            
            # Validate required fields
            required_fields = ["assessment-of-ai-tutor", "suggested-changes"]
            for field in required_fields:
                if field not in parsed_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
                if not isinstance(parsed_data[field], str) or not parsed_data[field].strip():
                    return {"success": False, "error": f"Field {field} must be a non-empty string"}
            
            return {
                "success": True,
                "data": {
                    "assessment-of-ai-tutor": parsed_data["assessment-of-ai-tutor"].strip(),
                    "suggested-changes": parsed_data["suggested-changes"].strip()
                }
            }
            
        except Exception as e:
            error_msg = f"Error parsing assessment response: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}