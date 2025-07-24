"""
Call Type Detection and Prompt Selection Logic
Determines whether a call is from a new student (introductory) or returning student (tutoring)
based on phone number presence in the database.
"""

import logging
import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallType(Enum):
    """Enumeration for call types"""
    INTRODUCTORY = "introductory"
    TUTORING = "tutoring"
    UNKNOWN = "unknown"

@dataclass
class CallTypeResult:
    """Result of call type detection"""
    call_type: CallType
    confidence: float
    reason: str
    student_id: Optional[str] = None
    existing_sessions: int = 0
    phone_normalized: Optional[str] = None

class CallTypeDetector:
    """
    Detects call type based on phone number and student database lookup
    """
    
    def __init__(self, database_connection=None):
        """
        Initialize the call type detector
        
        Args:
            database_connection: Optional database connection object
        """
        self.db_connection = database_connection
        self.phone_patterns = [
            r'^\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$',  # US/Canada
            r'^\+?(\d{1,3})[-.\s]?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,4})$',  # International
        ]
        
        # Always try to use database connection from Flask app context
        self._ensure_database_connection()
    
    def _ensure_database_connection(self):
        """Ensure we have access to database through Flask app context"""
        try:
            import flask
            if flask.has_app_context():
                # We have app context, database should be available
                self.db_connection = True  # Flag that database is available
                logger.info("Database connection available through Flask app context")
            else:
                logger.warning("No Flask app context - database operations will be limited")
                self.db_connection = None
        except ImportError:
            logger.warning("Flask not available - database operations will be limited")
            self.db_connection = None
    
    def normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number to a consistent format for database lookup
        
        Args:
            phone_number: Raw phone number string
            
        Returns:
            Normalized phone number string
        """
        if not phone_number:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        
        # Handle common US/Canada formats
        if cleaned.startswith('1') and len(cleaned) == 11:
            return f"+{cleaned}"
        elif len(cleaned) == 10:
            return f"+1{cleaned}"
        elif cleaned.startswith('+'):
            return cleaned
        else:
            return f"+{cleaned}"
    
    def detect_call_type(
        self, 
        phone_number: str, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> CallTypeResult:
        """
        Detect call type based on phone number and optional additional context
        
        Args:
            phone_number: Caller's phone number
            additional_context: Optional additional context for detection
            
        Returns:
            CallTypeResult with detection outcome
        """
        logger.info(f"Detecting call type for phone number: {phone_number}")
        
        # Normalize phone number
        normalized_phone = self.normalize_phone_number(phone_number)
        if not normalized_phone:
            return CallTypeResult(
                call_type=CallType.UNKNOWN,
                confidence=0.0,
                reason="Invalid or missing phone number",
                phone_normalized=normalized_phone
            )
        
        # Check if we have a database connection
        if not self.db_connection:
            logger.warning("No database connection available. Using fallback detection.")
            return self._fallback_detection(normalized_phone, additional_context)
        
        # Perform database lookup
        try:
            student_info = self._lookup_student_by_phone(normalized_phone)
            
            if student_info:
                logger.info(f"Found existing student: {student_info.get('id')} with {student_info.get('session_count', 0)} sessions")
                return CallTypeResult(
                    call_type=CallType.TUTORING,
                    confidence=0.95,
                    reason=f"Phone number found in database for student {student_info.get('name', 'Unknown')}",
                    student_id=student_info.get('id'),
                    existing_sessions=student_info.get('session_count', 0),
                    phone_normalized=normalized_phone
                )
            else:
                logger.info("Phone number not found in database - new student")
                return CallTypeResult(
                    call_type=CallType.INTRODUCTORY,
                    confidence=0.90,
                    reason="Phone number not found in database - new student",
                    phone_normalized=normalized_phone
                )
                
        except Exception as e:
            logger.error(f"Database lookup failed: {e}")
            return self._fallback_detection(normalized_phone, additional_context)
    
    def _lookup_student_by_phone(self, normalized_phone: str) -> Optional[Dict[str, Any]]:
        """
        Look up student information by phone number in the database
        
        Args:
            normalized_phone: Normalized phone number
            
        Returns:
            Student information dictionary or None if not found
        """
        try:
            # Import Flask app context and repositories
            from app.repositories import student_repository, session_repository
            from app import db
            import flask
            
            logger.info(f"Database lookup for phone: {normalized_phone}")
            
            # Create app context if we don't have one
            app_context_created = False
            if not flask.has_app_context():
                logger.info("No Flask app context - creating one for database lookup")
                try:
                    # Import the app instance
                    from admin_server import app
                    app_context = app.app_context()
                    app_context.push()
                    app_context_created = True
                    logger.info("Successfully created Flask app context for database lookup")
                except Exception as context_error:
                    logger.error(f"Failed to create Flask app context: {context_error}")
                    return None
            
            # Query students by phone number
            try:
                # Get all students and check phone numbers
                all_students = student_repository.get_all()
                if not all_students:
                    logger.info("No students found in database")
                    return None
                
                # Find student with matching phone number
                matching_student = None
                for student in all_students:
                    student_phone = student.get('phone_number', '')
                    # Normalize the student's phone for comparison
                    normalized_student_phone = self.normalize_phone_number(student_phone)
                    
                    if normalized_student_phone == normalized_phone:
                        matching_student = student
                        break
                
                if not matching_student:
                    logger.info(f"No student found with phone: {normalized_phone}")
                    return None
                
                # Get session count for this student
                student_id = matching_student.get('id')
                sessions = session_repository.get_by_student_id(str(student_id))
                session_count = len(sessions) if sessions else 0
                
                # Create student info with session count
                student_info = {
                    'id': str(student_id),
                    'name': f"{matching_student.get('first_name', '')} {matching_student.get('last_name', '')}".strip(),
                    'phone_number': matching_student.get('phone_number', ''),
                    'session_count': session_count
                }
                
                logger.info(f"Found student: {student_info['name']} (ID: {student_info['id']}) with {session_count} sessions")
                return student_info
                
            except Exception as db_error:
                logger.error(f"Database query error: {db_error}")
                return None
            
            finally:
                # Clean up app context if we created it
                if app_context_created:
                    try:
                        app_context.pop()
                        logger.info("Cleaned up Flask app context after database lookup")
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up app context: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Database lookup failed: {e}")
            return None
    
    def _fallback_detection(
        self, 
        normalized_phone: str, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> CallTypeResult:
        """
        Fallback detection when database is not available
        
        Args:
            normalized_phone: Normalized phone number
            additional_context: Additional context for detection
            
        Returns:
            CallTypeResult with fallback detection
        """
        logger.info("Using fallback call type detection")
        
        # Check if additional context provides hints
        if additional_context:
            # Look for hints in the context
            if additional_context.get('is_new_student'):
                return CallTypeResult(
                    call_type=CallType.INTRODUCTORY,
                    confidence=0.7,
                    reason="Marked as new student in context",
                    phone_normalized=normalized_phone
                )
            
            if additional_context.get('student_id'):
                return CallTypeResult(
                    call_type=CallType.TUTORING,
                    confidence=0.7,
                    reason="Student ID provided in context",
                    student_id=additional_context.get('student_id'),
                    phone_normalized=normalized_phone
                )
        
        # Default to introductory call when uncertain
        return CallTypeResult(
            call_type=CallType.INTRODUCTORY,
            confidence=0.5,
            reason="No database connection - defaulting to introductory call",
            phone_normalized=normalized_phone
        )

class ConditionalPromptSelector:
    """
    Selects appropriate prompt based on call type and other factors
    """
    
    def __init__(self, call_type_detector: CallTypeDetector = None):
        """
        Initialize the prompt selector
        
        Args:
            call_type_detector: Optional call type detector instance
        """
        self.call_type_detector = call_type_detector or CallTypeDetector()
        
        # Mapping of call types to appropriate prompts
        self.prompt_mappings = {
            CallType.INTRODUCTORY: {
                'primary': 'introductory_analysis',
                'alternatives': ['session_analysis']  # Fallback if introductory not available
            },
            CallType.TUTORING: {
                'primary': 'session_analysis',
                'alternatives': ['math_analysis', 'reading_analysis', 'quick_assessment']
            },
            CallType.UNKNOWN: {
                'primary': 'session_analysis',
                'alternatives': ['introductory_analysis']
            }
        }
    
    def select_prompt(
        self, 
        phone_number: str, 
        subject_hint: Optional[str] = None,
        session_length_hint: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, CallTypeResult]:
        """
        Select the most appropriate prompt based on call analysis
        
        Args:
            phone_number: Caller's phone number
            subject_hint: Optional subject hint (math, reading, etc.)
            session_length_hint: Optional session length hint (short, long)
            additional_context: Additional context for selection
            
        Returns:
            Tuple of (selected_prompt_name, call_type_result)
        """
        logger.info(f"Selecting prompt for phone: {phone_number}")
        
        # Detect call type
        call_type_result = self.call_type_detector.detect_call_type(
            phone_number, additional_context
        )
        
        logger.info(f"Detected call type: {call_type_result.call_type.value} (confidence: {call_type_result.confidence})")
        
        # Get base prompt mapping
        prompt_mapping = self.prompt_mappings.get(call_type_result.call_type)
        if not prompt_mapping:
            logger.warning(f"No prompt mapping for call type: {call_type_result.call_type}")
            prompt_mapping = self.prompt_mappings[CallType.UNKNOWN]
        
        # Select primary prompt
        selected_prompt = prompt_mapping['primary']
        
        # For tutoring sessions, consider subject-specific prompts
        if call_type_result.call_type == CallType.TUTORING and subject_hint:
            subject_lower = subject_hint.lower()
            if 'math' in subject_lower:
                selected_prompt = 'math_analysis'
            elif 'read' in subject_lower or 'language' in subject_lower or 'english' in subject_lower:
                selected_prompt = 'reading_analysis'
            elif session_length_hint and 'short' in session_length_hint.lower():
                selected_prompt = 'quick_assessment'
        
        logger.info(f"Selected prompt: {selected_prompt}")
        
        return selected_prompt, call_type_result
    
    def get_prompt_context_for_call_type(
        self, 
        call_type_result: CallTypeResult,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance context with call-type specific information
        
        Args:
            call_type_result: Result from call type detection
            base_context: Base context dictionary
            
        Returns:
            Enhanced context dictionary
        """
        enhanced_context = base_context.copy()
        
        # Add call type information
        enhanced_context['call_type'] = call_type_result.call_type.value
        enhanced_context['call_type_confidence'] = call_type_result.confidence
        enhanced_context['call_type_reason'] = call_type_result.reason
        
        if call_type_result.student_id:
            enhanced_context['student_id'] = call_type_result.student_id
        
        if call_type_result.existing_sessions > 0:
            enhanced_context['previous_sessions'] = call_type_result.existing_sessions
        
        if call_type_result.phone_normalized:
            enhanced_context['phone_number'] = call_type_result.phone_normalized
        
        # Add call-type specific context
        if call_type_result.call_type == CallType.INTRODUCTORY:
            enhanced_context['is_introductory_call'] = True
            enhanced_context['focus_areas'] = ['student_discovery', 'initial_assessment', 'profile_creation']
        elif call_type_result.call_type == CallType.TUTORING:
            enhanced_context['is_tutoring_session'] = True
            enhanced_context['focus_areas'] = ['progress_tracking', 'skill_development', 'learning_optimization']
        
        logger.info(f"Enhanced context with call type: {call_type_result.call_type.value}")
        
        return enhanced_context

# Global instances for easy access
default_call_type_detector = CallTypeDetector()
default_prompt_selector = ConditionalPromptSelector(default_call_type_detector)

def detect_call_type_simple(phone_number: str, context: Optional[Dict[str, Any]] = None) -> CallTypeResult:
    """
    Simple function to detect call type
    
    Args:
        phone_number: Caller's phone number
        context: Optional additional context
        
    Returns:
        CallTypeResult
    """
    return default_call_type_detector.detect_call_type(phone_number, context)

def select_prompt_for_call(
    phone_number: str, 
    subject: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, CallTypeResult]:
    """
    Simple function to select prompt for a call
    
    Args:
        phone_number: Caller's phone number
        subject: Optional subject hint
        context: Optional additional context
        
    Returns:
        Tuple of (prompt_name, call_type_result)
    """
    return default_prompt_selector.select_prompt(
        phone_number, 
        subject_hint=subject,
        additional_context=context
    )