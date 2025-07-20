#!/usr/bin/env python3
"""
Transcript Analyzer Module
Extracts student information from conversation transcripts using AI
"""

import json
import os
import logging
import asyncio
from typing import Dict, Any, Optional

# Import database models and repositories
from app import db

# Import AI POC components
from ai_poc.session_processor import session_processor
from ai_poc.prompts import prompt_manager
from ai_poc.providers import provider_manager

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """Extracts student information from conversation transcripts using AI"""
    
    def __init__(self):
        self.session_processor = session_processor
        self.prompt_manager = prompt_manager
        self.provider_manager = provider_manager
        
        # Create a profile extraction prompt if it doesn't exist
        if 'profile_extraction' not in self.prompt_manager.get_available_prompts():
            self._create_profile_extraction_prompt()
        
        # Log initialization
        logger.info("TranscriptAnalyzer initialized with AI-powered extraction")
    
    def _create_profile_extraction_prompt(self):
        """Create a custom prompt for profile information extraction"""
        from ai_poc.prompts import PromptTemplate
        from datetime import datetime
        
        profile_prompt = PromptTemplate(
            name="Profile Information Extraction",
            version="1.0",
            description="Extract student profile information from conversation transcripts",
            system_prompt="""You are an expert educational data analyst specializing in extracting student profile information from conversation transcripts. Your task is to carefully analyze the conversation and extract key information about the student.

EXTRACTION GUIDELINES:
- Focus only on factual information explicitly stated by the student
- Do not make assumptions or inferences beyond what is clearly stated
- Extract information only when you have high confidence it is accurate
- Format all extracted information in a consistent, structured way
- If information is not present or unclear, indicate it as unknown

RESPONSE FORMAT:
You must provide extracted information in JSON format with these fields:
{
  "age": <integer or null>,
  "grade": <integer or null>,
  "interests": [<list of strings>],
  "learning_preferences": [<list of strings>],
  "subjects": {
    "favorite": [<list of strings>],
    "challenging": [<list of strings>]
  },
  "confidence_score": <float between 0.0 and 1.0>
}

For each field, provide the exact information mentioned by the student. If the information is not present, use null for numeric fields and empty arrays for lists.""",
            user_prompt_template="""Please extract student profile information from this conversation transcript.

CONVERSATION TRANSCRIPT:
{transcript}

Extract only information that is explicitly stated by the student. Format your response as a valid JSON object with the following fields:
- age: The student's age (integer or null if not mentioned)
- grade: The student's grade level (integer or null if not mentioned)
- interests: List of the student's interests or hobbies
- learning_preferences: List of how the student prefers to learn
- subjects: Object containing favorite and challenging subjects
- confidence_score: Your confidence in the extracted information (0.0-1.0)

If information for a field is not present in the transcript, use null for numeric fields and empty arrays for lists.

IMPORTANT: Look for statements like "I'm 10" or "I'm in 4th grade" or "I like playing games" and extract them accurately.
Do not include any explanatory text in your response, ONLY the JSON object.
""",
            
            
            parameters={
                "transcript": "Full conversation transcript"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.prompt_manager.add_custom_prompt(profile_prompt)
        logger.info("Created profile extraction prompt template")
    
    async def analyze_transcript_with_ai(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript and extract student information using AI"""
        if not transcript:
            return {}
        
        try:
            # Log the transcript length for debugging
            logger.info(f"Analyzing transcript with {len(transcript)} characters")
            
            # Create a direct prompt for the AI model following the user's suggestion
            direct_prompt = f"""Below follows a transcript of a conversation between an AI tutor and a Student:

{transcript}

END OF TRANSCRIPT

Provide the response in the format of JSON as per the example below. Extract only information that is explicitly stated by the student.

{{
  "age": 10,
  "grade": 4,
  "interests": ["playing games", "building things", "playing in the forest"],
  "learning_preferences": [],
  "subjects": {{
    "favorite": ["math"],
    "challenging": []
  }},
  "confidence_score": 0.9
}}

IMPORTANT:
1. Return ONLY the JSON object, no other text
2. If information is not present, use null for numbers and empty arrays for lists
3. Make sure to extract ALL information mentioned by the student
4. Pay attention to direct answers to questions like "How old are you?" or "What grade are you in?"
"""
            
            # Log the prompt for debugging
            logger.info(f"Using AI extraction prompt: {direct_prompt[:100]}...")
            
            # Use the provider manager directly for a custom analysis
            provider = self.provider_manager.providers[self.provider_manager.current_provider]
            logger.info(f"Using AI provider: {self.provider_manager.current_provider}")
            
            # Create a minimal context for the AI
            context = {
                "name": "Student",
                "task": "profile_extraction"
            }
            
            # Get AI analysis
            logger.info("Sending transcript to AI model for analysis")
            
            # Use the direct prompt we created
            context["prompt"] = direct_prompt
            logger.info("Added direct prompt to context")
            
            # Log that we're about to call the AI provider
            from system_logger import log_ai_analysis
            log_ai_analysis("Sending transcript to AI provider for analysis",
                           provider=self.provider_manager.current_provider,
                           transcript_length=len(transcript),
                           context_type="profile_extraction")
            
            analysis = await provider.analyze_session(transcript, context)
            logger.info(f"Received analysis response from provider")
            
            # Extract the JSON from the raw response
            try:
                # Log the raw response for debugging
                raw_text = analysis.raw_response
                logger.info(f"Received AI response with {len(raw_text) if raw_text else 0} characters")
                logger.info(f"Raw response preview: {raw_text[:200] if raw_text else 'None'}")
                
                # Try to parse the entire response as JSON first
                try:
                    extracted_info = json.loads(raw_text)
                    logger.info(f"Successfully parsed JSON response: {json.dumps(extracted_info)}")
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the text
                    import re
                    json_match = re.search(r'({[\s\S]*})', raw_text)
                    if json_match:
                        extracted_info = json.loads(json_match.group(1))
                        logger.info(f"Extracted JSON from text: {json.dumps(extracted_info)}")
                    else:
                        # Try a more aggressive approach to find JSON
                        json_match = re.search(r'({.*})', raw_text.replace('\n', ' '))
                        if json_match:
                            extracted_info = json.loads(json_match.group(1))
                            logger.info(f"Extracted JSON with aggressive approach: {json.dumps(extracted_info)}")
                        else:
                            logger.error("Could not extract JSON from AI response")
                            logger.error(f"Raw response: {raw_text}")
                            return {}
                
                # Validate and clean the extracted information
                cleaned_info = self._clean_extracted_info(extracted_info)
                logger.info(f"Cleaned extracted info: {json.dumps(cleaned_info)}")
                return cleaned_info
                
            except Exception as e:
                logger.error(f"Error parsing AI response: {e}")
                logger.error(f"Raw response: {analysis.raw_response if hasattr(analysis, 'raw_response') else 'No raw response'}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in AI transcript analysis: {e}")
            return {}
    
    def _clean_extracted_info(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate the extracted information"""
        clean_info = {}
        
        # Process age
        if 'age' in extracted_info and extracted_info['age'] is not None:
            try:
                age = int(extracted_info['age'])
                if 3 <= age <= 18:  # Reasonable age range for students
                    clean_info['age'] = age
            except (ValueError, TypeError):
                pass
        
        # Process grade
        if 'grade' in extracted_info and extracted_info['grade'] is not None:
            try:
                grade = int(extracted_info['grade'])
                if 1 <= grade <= 12:  # Valid grade range
                    clean_info['grade'] = grade
            except (ValueError, TypeError):
                pass
        
        # Process interests
        if 'interests' in extracted_info and isinstance(extracted_info['interests'], list):
            clean_info['interests'] = [
                interest.strip() for interest in extracted_info['interests']
                if isinstance(interest, str) and 3 <= len(interest.strip()) <= 50
            ]
        
        # Process learning preferences
        if 'learning_preferences' in extracted_info and isinstance(extracted_info['learning_preferences'], list):
            clean_info['learning_preferences'] = [
                pref.strip() for pref in extracted_info['learning_preferences']
                if isinstance(pref, str) and len(pref.strip()) > 0
            ]
        
        # Process subjects
        if 'subjects' in extracted_info and isinstance(extracted_info['subjects'], dict):
            subjects = {}
            
            if 'favorite' in extracted_info['subjects'] and isinstance(extracted_info['subjects']['favorite'], list):
                subjects['favorite'] = [
                    subj.strip() for subj in extracted_info['subjects']['favorite']
                    if isinstance(subj, str) and len(subj.strip()) > 0
                ]
            
            if 'challenging' in extracted_info['subjects'] and isinstance(extracted_info['subjects']['challenging'], list):
                subjects['challenging'] = [
                    subj.strip() for subj in extracted_info['subjects']['challenging']
                    if isinstance(subj, str) and len(subj.strip()) > 0
                ]
            
            if subjects:
                clean_info['subjects'] = subjects
        
        return clean_info
    
    def analyze_transcript(self, transcript, student_id=None):
        """Analyze transcript and extract student information (synchronous wrapper)"""
        if not transcript:
            return {}
        
        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async analysis
        try:
            extracted_info = loop.run_until_complete(self.analyze_transcript_with_ai(transcript))
            
            # Log the result
            if extracted_info:
                logger.info(f"Successfully extracted information: {json.dumps(extracted_info)}")
                # Log each extracted field for better debugging
                for key, value in extracted_info.items():
                    logger.info(f"Extracted {key}: {value}")
                
                # Log successful extraction to system logger
                from system_logger import log_ai_analysis
                log_ai_analysis("Successfully extracted profile information",
                               extracted_fields=list(extracted_info.keys()),
                               student_id=student_id,
                               provider=self.provider_manager.current_provider)
            else:
                logger.warning("No information extracted from transcript")
                # Log a sample of the transcript to help debug
                logger.warning(f"Transcript sample: {transcript[:200]}...")
                
                # Log failed extraction to system logger
                from system_logger import log_ai_analysis
                log_ai_analysis("Failed to extract profile information",
                               level="WARNING",
                               transcript_length=len(transcript),
                               student_id=student_id,
                               provider=self.provider_manager.current_provider)
                
            return extracted_info
        except Exception as e:
            logger.error(f"Error in transcript analysis: {e}")
            return {}
    
    def update_student_profile(self, student_id, extracted_info):
        """Update student profile with extracted information using SQL database"""
        if not extracted_info:
            return False
        
        try:
            # Import student repository
            from app.repositories import student_repository
            from app.models.profile import Profile
            
            # Get student from database
            student_data = student_repository.get_by_id(student_id)
            if not student_data:
                logger.warning(f"Student {student_id} not found in database")
                return False
            
            # Prepare update data
            update_data = {}
            
            # Add basic profile fields
            if 'age' in extracted_info and (not student_data.get('age') or student_data.get('age') == 'Unknown'):
                update_data['age'] = extracted_info['age']
            
            if 'grade' in extracted_info and (not student_data.get('grade') or student_data.get('grade') == 'Unknown'):
                update_data['grade'] = extracted_info['grade']
            
            # Handle profile-specific fields
            profile_data = {}
            
            # Handle interests
            if 'interests' in extracted_info:
                # Get current interests from profile
                current_interests = student_data.get('interests', [])
                # Add new interests
                for interest in extracted_info['interests']:
                    if interest not in current_interests:
                        current_interests.append(interest)
                profile_data['interests'] = current_interests
            
            # Handle learning preferences
            if 'learning_preferences' in extracted_info:
                current_prefs = student_data.get('learning_preferences', [])
                for pref in extracted_info['learning_preferences']:
                    if pref not in current_prefs:
                        current_prefs.append(pref)
                profile_data['learning_preferences'] = current_prefs
            
            # Handle subjects
            if 'subjects' in extracted_info:
                if 'favorite' in extracted_info['subjects']:
                    current_favorites = student_data.get('favorite_subjects', [])
                    for subj in extracted_info['subjects']['favorite']:
                        if subj not in current_favorites:
                            current_favorites.append(subj)
                    profile_data['favorite_subjects'] = current_favorites
                
                if 'challenging' in extracted_info['subjects']:
                    current_challenging = student_data.get('challenging_subjects', [])
                    for subj in extracted_info['subjects']['challenging']:
                        if subj not in current_challenging:
                            current_challenging.append(subj)
                    profile_data['challenging_subjects'] = current_challenging
            
            # Add profile data to update data if it exists
            if profile_data:
                update_data['interests'] = profile_data.get('interests', [])
                update_data['learning_preferences'] = profile_data.get('learning_preferences', [])
            
            # Update student in database if there are changes
            if update_data:
                updated_student = student_repository.update(student_id, update_data)
                if updated_student:
                    logger.info(f"Updated profile for student {student_id} with {extracted_info}")
                    
                    # Log successful update to system logger
                    from system_logger import log_ai_analysis
                    log_ai_analysis("Successfully updated student profile in database",
                                   updated_fields=list(update_data.keys()),
                                   student_id=student_id)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating profile for student {student_id}: {e}")
            
            # Log error to system logger
            from system_logger import log_error
            log_error('TRANSCRIPT_ANALYSIS', f"Error updating student profile in database", e,
                     student_id=student_id)
            return False