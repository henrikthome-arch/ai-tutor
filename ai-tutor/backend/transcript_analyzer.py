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
from ai_poc.call_type_detector import default_prompt_selector, CallType
from ai_poc.prompts_file_loader import file_prompt_manager

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
  "name": <string - student's full name or null if not mentioned>,
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

IMPORTANT:
- For name, extract the student's actual name if they introduce themselves (e.g., "Hi, I'm Sarah" → "Sarah")
- For age and grade, return ONLY numeric values (e.g., 12, not "12 years old")
- For each field, provide the exact information mentioned by the student
- If the information is not present, use null for numeric fields and empty arrays for lists.""",
            user_prompt_template="""Please extract student profile information from this conversation transcript.

CONVERSATION TRANSCRIPT:
{transcript}

Extract only information that is explicitly stated by the student. Format your response as a valid JSON object with the following fields:
- name: The student's full name if they introduce themselves (e.g., "Hi, I'm Sarah" → "Sarah")
- age: The student's age (integer only, e.g., 10, not "10 years old")
- grade: The student's grade level (integer only, e.g., 4, not "4th grade")
- interests: List of the student's interests or hobbies
- learning_preferences: List of how the student prefers to learn
- subjects: Object containing favorite and challenging subjects
- confidence_score: Your confidence in the extracted information (0.0-1.0)

If information for a field is not present in the transcript, use null for numeric fields and empty arrays for lists.

IMPORTANT: Look for statements like "Hi, I'm Emma" or "My name is John" or "I'm 10" or "I'm in 4th grade" or "I like playing games" and extract them accurately.
For age and grade, return ONLY the numeric value - no text formatting.
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
    
    async def analyze_transcript_with_conditional_prompts(
        self,
        transcript: str,
        phone_number: Optional[str] = None,
        subject_hint: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze transcript using conditional prompt selection based on call type
        
        Args:
            transcript: The conversation transcript
            phone_number: Caller's phone number for call type detection
            subject_hint: Optional subject hint (math, reading, etc.)
            additional_context: Additional context for analysis
            
        Returns:
            Dictionary containing extracted information and analysis results
        """
        if not transcript:
            return {}
        
        try:
            logger.info(f"Analyzing transcript with conditional prompts. Phone: {phone_number}, Subject: {subject_hint}")
            
            # Use prompt selector to determine call type and appropriate prompt
            if phone_number:
                selected_prompt, call_type_result = default_prompt_selector.select_prompt(
                    phone_number=phone_number,
                    subject_hint=subject_hint,
                    additional_context=additional_context
                )
                
                logger.info(f"Selected prompt: {selected_prompt}, Call type: {call_type_result.call_type.value}")
                
                # Enhance context with call type information
                enhanced_context = default_prompt_selector.get_prompt_context_for_call_type(
                    call_type_result,
                    additional_context or {}
                )
            else:
                # Fallback to session analysis if no phone number provided
                selected_prompt = 'session_analysis'
                call_type_result = None
                enhanced_context = additional_context or {}
                logger.warning("No phone number provided, using default session_analysis prompt")
            
            # Get the formatted prompt from file manager
            prompt_params = {
                'transcript': transcript,
                'phone_number': phone_number or 'Unknown',
                'call_duration': enhanced_context.get('call_duration', 'Unknown'),
                'call_datetime': enhanced_context.get('call_datetime', 'Unknown')
            }
            
            # Add additional context parameters if available
            if enhanced_context:
                prompt_params.update(enhanced_context)
            
            # Format the selected prompt
            formatted_prompt = file_prompt_manager.format_prompt(selected_prompt, **prompt_params)
            
            if not formatted_prompt:
                logger.error(f"Failed to format prompt: {selected_prompt}")
                # Fallback to legacy method
                return await self.analyze_transcript_with_ai(transcript)
            
            logger.info(f"Successfully formatted {selected_prompt} prompt")
            
            # Use the provider manager to analyze with the formatted prompt
            provider = self.provider_manager.providers[self.provider_manager.current_provider]
            logger.info(f"Using AI provider: {self.provider_manager.current_provider}")
            
            # Create analysis context
            analysis_context = {
                "prompt_type": selected_prompt,
                "call_type": call_type_result.call_type.value if call_type_result else "unknown",
                "formatted_prompt": formatted_prompt['user_prompt']
            }
            
            # Add the formatted prompt to context for the provider
            analysis_context["prompt"] = formatted_prompt['user_prompt']
            
            # Log AI analysis attempt
            from system_logger import log_ai_analysis
            log_ai_analysis("Starting conditional prompt analysis",
                           provider=self.provider_manager.current_provider,
                           prompt_type=selected_prompt,
                           call_type=call_type_result.call_type.value if call_type_result else "unknown",
                           transcript_length=len(transcript))
            
            # Get AI analysis
            analysis = await provider.analyze_session(transcript, analysis_context)
            logger.info(f"Received analysis response from provider")
            
            # Store AI processing debug information if session_id provided
            if session_id:
                logger.info(f"🔍 DEBUG: Storing AI processing step for session_id {session_id}")
                print(f"🔍 DEBUG: Storing AI processing step for session_id {session_id}")
                step_stored = self._store_ai_processing_step(
                    session_id=session_id,
                    step_number=1,
                    prompt=formatted_prompt['user_prompt'],
                    response=analysis.raw_response,
                    metadata={
                        'prompt_type': selected_prompt,
                        'call_type': call_type_result.call_type.value if call_type_result else "unknown",
                        'provider': self.provider_manager.current_provider,
                        'timestamp': analysis.timestamp.isoformat()
                    }
                )
                if step_stored:
                    logger.info(f"🔍 DEBUG: Successfully stored AI processing step for session {session_id}")
                    print(f"🔍 DEBUG: Successfully stored AI processing step for session {session_id}")
                else:
                    logger.error(f"🔍 DEBUG: Failed to store AI processing step for session {session_id}")
                    print(f"🔍 DEBUG: Failed to store AI processing step for session {session_id}")
            else:
                logger.warning(f"🔍 DEBUG: No session_id provided - cannot store AI processing step")
                print(f"🔍 DEBUG: No session_id provided - cannot store AI processing step")
            
            # Extract and process the JSON response
            try:
                raw_response = analysis.raw_response
                logger.info(f"Received AI response with {len(raw_response) if raw_response else 0} characters")
                
                # Parse JSON response (all new prompts generate JSON)
                try:
                    extracted_info = json.loads(raw_response)
                    logger.info(f"Successfully parsed JSON response for {selected_prompt}")
                except json.JSONDecodeError:
                    # Try to extract JSON from the text
                    import re
                    json_match = re.search(r'({[\s\S]*})', raw_response)
                    if json_match:
                        extracted_info = json.loads(json_match.group(1))
                        logger.info(f"Extracted JSON from response text")
                    else:
                        logger.error("Could not extract JSON from AI response")
                        logger.error(f"Raw response: {raw_response}")
                        return {}
                
                # Add metadata about the analysis
                extracted_info['_analysis_metadata'] = {
                    'prompt_used': selected_prompt,
                    'call_type': call_type_result.call_type.value if call_type_result else "unknown",
                    'call_type_confidence': call_type_result.confidence if call_type_result else 0.0,
                    'provider_used': self.provider_manager.current_provider,
                    'processing_time': analysis.processing_time,
                    'analysis_timestamp': analysis.timestamp.isoformat()
                }
                
                logger.info(f"Successfully processed conditional prompt analysis")
                return extracted_info
                
            except Exception as e:
                logger.error(f"Error parsing conditional prompt response: {e}")
                logger.error(f"Raw response: {analysis.raw_response if hasattr(analysis, 'raw_response') else 'No raw response'}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in conditional prompt analysis: {e}")
            # Fallback to legacy analysis
            logger.info("Falling back to legacy analysis method")
            return await self.analyze_transcript_with_ai(transcript)

    async def analyze_transcript_with_ai(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript and extract student information using AI"""
        if not transcript:
            return {}
        
        try:
            # Log the transcript length for debugging
            logger.info(f"Analyzing transcript with {len(transcript)} characters")
            
            # Create a more specific and detailed prompt for better extraction
            direct_prompt = f"""You are analyzing a conversation transcript to extract student profile information.

TRANSCRIPT:
{transcript}

TASK: Extract student information from this conversation and return ONLY a JSON object with the following structure:

{{
  "name": <string or null>,
  "age": <number or null>,
  "grade": <number or null>,
  "interests": ["list", "of", "interests"],
  "learning_preferences": ["list", "of", "preferences"],
  "subjects": {{
    "favorite": ["list", "of", "favorite", "subjects"],
    "challenging": ["list", "of", "challenging", "subjects"]
  }},
  "confidence_score": <number between 0.0 and 1.0>
}}

EXTRACTION RULES:
1. Look for explicit statements like "Hi, I'm Emma", "My name is John", "I'm 8 years old", "I'm in 3rd grade", "I like soccer"
2. Extract the student's actual name if they introduce themselves
3. Extract hobbies, interests, sports, activities mentioned by the student
4. Note any subjects or topics the student mentions liking or finding difficult
5. For name: Extract the actual name, not descriptive terms like "student" or "kid"
6. For age: ONLY return the numeric value (e.g., 8, not "8 years old")
7. For grade: ONLY return the numeric value (e.g., 3, not "third grade" or "Grade 3")
8. If the student mentions grade level with words like "third grade", convert to number: 3
9. Be very careful to extract ALL mentioned interests and hobbies
10. Return confidence_score as 0.9 if you found clear information, 0.5 if uncertain, 0.1 if very little found

IMPORTANT: Return ONLY the JSON object, no explanatory text before or after.
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
                logger.info(f"Raw response preview: {raw_text[:500] if raw_text else 'None'}")
                
                # Log the full response for debugging failed extractions
                print(f"🔍 Full AI response for debugging: {raw_text}")
                
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
                if isinstance(interest, str) and 1 <= len(interest.strip()) <= 100
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
    
    def analyze_transcript_with_conditional_prompts_sync(
        self,
        transcript: str,
        phone_number: Optional[str] = None,
        subject_hint: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for conditional prompt analysis
        
        Args:
            transcript: The conversation transcript
            phone_number: Caller's phone number for call type detection
            subject_hint: Optional subject hint (math, reading, etc.)
            additional_context: Additional context for analysis
            student_id: Optional student ID for logging
            
        Returns:
            Dictionary containing extracted information and analysis results
        """
        if not transcript:
            return {}
        
        # Extract session_id from additional_context if provided
        session_id = None
        if additional_context and 'session_id' in additional_context:
            session_id = additional_context['session_id']
            logger.info(f"🔍 DEBUG: Found session_id {session_id} in additional_context for AI processing step storage")
            print(f"🔍 DEBUG: Found session_id {session_id} in additional_context for AI processing step storage")
        else:
            logger.warning(f"🔍 DEBUG: No session_id found in additional_context: {additional_context}")
            print(f"🔍 DEBUG: No session_id found in additional_context: {additional_context}")
        
        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async conditional analysis
        try:
            extracted_info = loop.run_until_complete(
                self.analyze_transcript_with_conditional_prompts(
                    transcript=transcript,
                    phone_number=phone_number,
                    subject_hint=subject_hint,
                    additional_context=additional_context,
                    session_id=session_id
                )
            )
            
            # Log the result
            if extracted_info:
                logger.info(f"Successfully extracted information using conditional prompts")
                
                # Log successful extraction to system logger
                from system_logger import log_ai_analysis
                log_ai_analysis("Successfully extracted information with conditional prompts",
                               prompt_type=extracted_info.get('_analysis_metadata', {}).get('prompt_used', 'unknown'),
                               call_type=extracted_info.get('_analysis_metadata', {}).get('call_type', 'unknown'),
                               extracted_fields=list(k for k in extracted_info.keys() if not k.startswith('_')),
                               student_id=student_id,
                               provider=self.provider_manager.current_provider)
                
                return extracted_info
            else:
                logger.warning("No information extracted from transcript with conditional prompts - trying fallback")
                
                # Try fallback to legacy analysis if conditional prompts failed
                try:
                    logger.info("Attempting fallback to legacy transcript analysis")
                    fallback_info = self.analyze_transcript(transcript, student_id)
                    
                    if fallback_info:
                        logger.info("Fallback analysis succeeded")
                        from system_logger import log_ai_analysis
                        log_ai_analysis("Fallback analysis extracted information after conditional prompts failed",
                                       extracted_fields=list(fallback_info.keys()),
                                       student_id=student_id,
                                       provider=self.provider_manager.current_provider)
                        return fallback_info
                    else:
                        logger.warning("Both conditional and fallback analysis failed")
                        from system_logger import log_ai_analysis
                        log_ai_analysis("Failed to extract information with conditional prompts and fallback",
                                       level="WARNING",
                                       transcript_length=len(transcript),
                                       student_id=student_id,
                                       provider=self.provider_manager.current_provider)
                        return {}
                        
                except Exception as fallback_error:
                    logger.error(f"Fallback analysis also failed: {fallback_error}")
                    from system_logger import log_ai_analysis
                    log_ai_analysis("Failed to extract information with conditional prompts",
                                   level="WARNING",
                                   transcript_length=len(transcript),
                                   student_id=student_id,
                                   provider=self.provider_manager.current_provider)
                    return {}
        except Exception as e:
            logger.error(f"Error in conditional prompt analysis: {e}")
            # Fallback to legacy analysis
            logger.info("Falling back to legacy analysis method")
            return self.analyze_transcript(transcript, student_id)

    def analyze_transcript(self, transcript, student_id=None, phone_number=None, subject_hint=None, additional_context=None):
        """
        Analyze transcript and extract student information (synchronous wrapper)
        
        Args:
            transcript: The conversation transcript
            student_id: Optional student ID for logging
            phone_number: Optional phone number for conditional prompt selection
            subject_hint: Optional subject hint for prompt selection
            additional_context: Optional additional context
            
        Returns:
            Dictionary containing extracted information
        """
        if not transcript:
            return {}
        
        # Use conditional prompts if phone number is provided
        if phone_number:
            logger.info(f"Using conditional prompt analysis for phone: {phone_number}")
            return self.analyze_transcript_with_conditional_prompts_sync(
                transcript=transcript,
                phone_number=phone_number,
                subject_hint=subject_hint,
                additional_context=additional_context,
                student_id=student_id
            )
        
        # Fallback to legacy analysis for backwards compatibility
        logger.info("Using legacy analysis method (no phone number provided)")
        
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
            logger.info(f"No extracted_info provided for student {student_id}")
            return False
        
        logger.info(f"Starting profile update for student {student_id}")
        logger.info(f"Extracted info received: {json.dumps(extracted_info, indent=2)}")
        
        try:
            # Import models and app context
            from app.models.student import Student
            from app.models.profile import Profile
            from app import db
            import flask
            
            # Ensure we have app context
            if not flask.has_app_context():
                logger.error("No Flask app context for profile update")
                return False
            
            # Get student from database
            try:
                student = Student.query.get(student_id)
                if not student:
                    logger.warning(f"Student {student_id} not found in database")
                    return False
                
                current_first = student.first_name or ''
                current_last = student.last_name or ''
                logger.info(f"Current student name: '{current_first}' '{current_last}'")
                
            except Exception as e:
                logger.error(f"Error getting student {student_id}: {e}")
                return False
            
            # Get or create profile for student
            try:
                profile = student.profile
                if not profile:
                    logger.info(f"Creating new profile for student {student_id}")
                    profile = Profile(student_id=student_id)
                    db.session.add(profile)
                    db.session.flush()  # Get the ID
                    
                    # Update student relationship
                    student.profile = profile
            except Exception as e:
                logger.error(f"Error getting/creating profile for student {student_id}: {e}")
                return False
            
            # Track changes
            updated_fields = []
            
            # PART 1: Standardized Data Access
            def extract_name_from_ai_response(extracted_info):
                """Extract first and last name from AI response with standardized logic"""
                # Priority order for extracting name information
                sources = [
                    extracted_info.get('student_profile', {}),  # Nested structure from conditional prompts
                    extracted_info                              # Direct structure from fallback prompts
                ]
                
                for source in sources:
                    if not source:
                        continue
                        
                    first_name = source.get('first_name')
                    last_name = source.get('last_name')
                    
                    # Clean and validate first name
                    if first_name:
                        first_name = str(first_name).strip()
                        if first_name and first_name not in ['Unknown', 'unknown', 'None', 'null', '']:
                            # Also extract last name if available
                            if last_name:
                                last_name = str(last_name).strip()
                                if last_name in ['Unknown', 'unknown', 'None', 'null', '']:
                                    last_name = None
                            
                            return first_name, last_name
                
                return None, None
            
            # Extract name using standardized logic
            new_first_name, new_last_name = extract_name_from_ai_response(extracted_info)
            
            # PART 2: Decisive Update Rule
            if new_first_name:
                current_first = student.first_name or ''
                
                logger.info(f"Current name: '{current_first}' - Extracted name: '{new_first_name}'")
                
                # Simple, decisive rule: If current first name starts with "Student", update it
                if current_first.startswith('Student'):
                    logger.info(f"✅ UPDATING placeholder name '{current_first}' to '{new_first_name}'")
                    
                    student.first_name = new_first_name
                    if new_last_name:
                        student.last_name = new_last_name
                    
                    updated_fields.append('name')
                    logger.info(f"Updated student name to: '{student.first_name}' '{student.last_name or ''}'")
                else:
                    logger.info(f"Keeping existing name '{current_first}' (not a placeholder)")
            else:
                logger.info("No valid first name extracted from AI response")
            
            # Update other profile fields using the same standardized approach
            def extract_field_value(field_name, expected_type=None):
                """Extract field value from AI response using standardized logic"""
                sources = [
                    extracted_info.get('student_profile', {}),
                    extracted_info
                ]
                
                for source in sources:
                    if not source:
                        continue
                    
                    value = source.get(field_name)
                    if value is not None:
                        if expected_type == int:
                            try:
                                return int(value)
                            except (ValueError, TypeError):
                                continue
                        else:
                            return value
                return None
            
            # Update age by calculating date_of_birth if provided
            age_val = extract_field_value('age', int)
            if age_val is not None and 3 <= age_val <= 18:
                from datetime import date
                current_year = date.today().year
                birth_year = current_year - age_val
                calculated_dob = date(birth_year, 1, 1)
                
                student.date_of_birth = calculated_dob
                updated_fields.append('date_of_birth')
                logger.info(f"Updated date_of_birth to {calculated_dob} (age {age_val})")
            
            # Update grade_level in Student model if provided
            grade_val = extract_field_value('grade', int)
            if grade_val is not None and 1 <= grade_val <= 12:
                student.grade_level = grade_val
                updated_fields.append('grade_level')
                logger.info(f"Updated grade_level to {grade_val}")
            
            # Handle interests
            interests_to_add = extract_field_value('interests')
            if interests_to_add and isinstance(interests_to_add, list):
                current_interests = profile.interests or []
                new_interests = []
                for interest in interests_to_add:
                    if interest and interest not in current_interests:
                        new_interests.append(interest)
                        current_interests.append(interest)
                
                if new_interests:
                    profile.interests = current_interests
                    updated_fields.append('interests')
                    logger.info(f"Added new interests: {new_interests}")
            
            # Handle learning preferences
            learning_prefs_to_add = extract_field_value('learning_preferences')
            if learning_prefs_to_add and isinstance(learning_prefs_to_add, list):
                # Initialize learning_preferences if None
                if profile.learning_preferences is None:
                    profile.learning_preferences = []
                    
                current_prefs = profile.learning_preferences or []
                new_prefs = []
                for pref in learning_prefs_to_add:
                    if pref and pref not in current_prefs:
                        new_prefs.append(pref)
                        current_prefs.append(pref)
                
                if new_prefs:
                    profile.learning_preferences = current_prefs
                    updated_fields.append('learning_preferences')
                    logger.info(f"Added new learning preferences: {new_prefs}")
            
            # Save changes if any were made
            if updated_fields:
                logger.info(f"Changes detected, saving updated fields: {updated_fields}")
                
                try:
                    db.session.commit()
                    logger.info(f"Successfully updated profile for student {student_id} with fields: {updated_fields}")
                    
                    # Log successful update to system logger
                    from system_logger import log_ai_analysis
                    log_ai_analysis("Successfully updated student profile in database",
                                   updated_fields=updated_fields,
                                   student_id=student_id)
                    return True
                except Exception as e:
                    logger.error(f"Database commit failed for student {student_id}: {e}")
                    try:
                        db.session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Rollback error: {rollback_error}")
                    
                    logger.error(f"Error saving profile updates for student {student_id}: {e}")
                    return False
            else:
                logger.info(f"No profile updates needed for student {student_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating profile for student {student_id}: {e}")
            
            # Rollback any pending changes
            try:
                db.session.rollback()
            except:
                pass
            
            # Log error to system logger
            from system_logger import log_error
            log_error('TRANSCRIPT_ANALYSIS', f"Error updating student profile in database", e,
                     student_id=student_id)
            return False
    
    def _store_ai_processing_step(self, session_id: int, step_number: int, prompt: str, response: str, metadata: dict = None):
        """Store AI processing step for debugging purposes"""
        try:
            from app.models.session import Session
            from app import db
            import flask
            
            # Ensure we have app context
            if not flask.has_app_context():
                logger.error("No Flask app context for storing AI processing step")
                return False
            
            # Get session from database
            session = Session.query.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for storing AI processing step")
                return False
            
            # Store prompt and response in appropriate fields
            if step_number == 1:
                session.ai_prompt_1 = prompt
                session.ai_response_1 = response
            elif step_number == 2:
                session.ai_prompt_2 = prompt
                session.ai_response_2 = response
            elif step_number == 3:
                session.ai_prompt_3 = prompt
                session.ai_response_3 = response
            else:
                logger.warning(f"Invalid step number {step_number} for AI processing step")
                return False
            
            # Store or update processing metadata
            if metadata:
                current_metadata = session.processing_metadata or {}
                current_metadata[f'step_{step_number}'] = metadata
                session.processing_metadata = current_metadata
            
            # Save changes
            db.session.commit()
            logger.info(f"Stored AI processing step {step_number} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing AI processing step {step_number} for session {session_id}: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False