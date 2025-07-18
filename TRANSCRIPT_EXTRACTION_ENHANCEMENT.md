# Transcript Information Extraction Enhancement

## Current Issue

The system correctly identifies returning callers and saves conversation transcripts, but it doesn't extract and update student profile information from these conversations. For example, when a student mentions their age, grade, or interests during a conversation, this information isn't automatically added to their profile.

## Proposed Solution

Implement a transcript analysis feature that extracts key student information from conversations and updates their profile accordingly.

### Implementation Steps

1. **Create a Transcript Analyzer Module**

```python
# ai-tutor/backend/transcript_analyzer.py

import re
import json
import os
import logging

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """Extracts student information from conversation transcripts"""
    
    def __init__(self):
        self.age_patterns = [
            r"I'?m\s+(\d+)(?:\s+years\s+old)?",
            r"I\s+am\s+(\d+)(?:\s+years\s+old)?",
            r"(\d+)\s+years\s+old"
        ]
        
        self.grade_patterns = [
            r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+grade",
            r"(?:I'?m in|I am in|in)\s+(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+grade",
            r"grade\s+(\d+)"
        ]
        
        self.grade_words = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
            "eleventh": 11, "twelfth": 12
        }
        
        self.interest_patterns = [
            r"(?:I\s+like|I\s+love|I\s+enjoy|my\s+hobby\s+is|my\s+favorite\s+is)\s+([^.,!?]+)",
            r"(?:favorite|like to)\s+([^.,!?]+)"
        ]
    
    def extract_age(self, text):
        """Extract age from text"""
        for pattern in self.age_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    age = int(matches.group(1))
                    if 3 <= age <= 18:  # Reasonable age range for students
                        return age
                except ValueError:
                    pass
        return None
    
    def extract_grade(self, text):
        """Extract grade from text"""
        for pattern in self.grade_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                grade_value = matches.group(1).lower()
                
                # Convert word to number if needed
                if grade_value in self.grade_words:
                    return self.grade_words[grade_value]
                
                # Try to convert to integer
                try:
                    grade = int(grade_value)
                    if 1 <= grade <= 12:  # Valid grade range
                        return grade
                except ValueError:
                    pass
        return None
    
    def extract_interests(self, text):
        """Extract potential interests from text"""
        interests = []
        for pattern in self.interest_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                interest = match.group(1).strip()
                if 3 <= len(interest) <= 50:  # Reasonable length for an interest
                    interests.append(interest)
        return interests
    
    def analyze_transcript(self, transcript):
        """Analyze transcript and extract student information"""
        if not transcript:
            return {}
        
        # Extract user parts from transcript
        user_parts = []
        lines = transcript.split('\n')
        is_user = False
        
        for line in lines:
            if line.startswith('User:'):
                is_user = True
                user_parts.append(line[5:].strip())
            elif line.startswith('AI:'):
                is_user = False
            elif is_user and line.strip():
                user_parts.append(line.strip())
        
        user_text = ' '.join(user_parts)
        
        # Extract information
        extracted_info = {}
        
        age = self.extract_age(user_text)
        if age:
            extracted_info['age'] = age
        
        grade = self.extract_grade(user_text)
        if grade:
            extracted_info['grade'] = grade
        
        interests = self.extract_interests(user_text)
        if interests:
            extracted_info['interests'] = interests
        
        return extracted_info
    
    def update_student_profile(self, student_id, extracted_info):
        """Update student profile with extracted information"""
        if not extracted_info:
            return False
        
        profile_path = f'../data/students/{student_id}/profile.json'
        if not os.path.exists(profile_path):
            logger.warning(f"Profile not found for student {student_id}")
            return False
        
        try:
            # Read existing profile
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Update profile with extracted info
            updated = False
            
            if 'age' in extracted_info and (not profile.get('age') or profile.get('age') == 'Unknown'):
                profile['age'] = extracted_info['age']
                updated = True
            
            if 'grade' in extracted_info and (not profile.get('grade') or profile.get('grade') == 'Unknown'):
                profile['grade'] = extracted_info['grade']
                updated = True
            
            if 'interests' in extracted_info:
                current_interests = profile.get('interests', [])
                for interest in extracted_info['interests']:
                    if interest not in current_interests:
                        current_interests.append(interest)
                        updated = True
                profile['interests'] = current_interests
            
            if updated:
                # Save updated profile
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, indent=2, ensure_ascii=False)
                logger.info(f"Updated profile for student {student_id} with {extracted_info}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating profile for student {student_id}: {e}")
            return False
```

2. **Integrate with Session Processing**

Update the `save_api_driven_session` function in `admin-server.py` to analyze the transcript and update the student profile:

```python
def save_api_driven_session(call_id: str, student_id: str, phone: str, 
                           duration: int, transcript: str, call_data: Dict[Any, Any]):
    """Save VAPI session data using API-fetched data"""
    try:
        # Create student directory if it doesn't exist
        student_dir = f'../data/students/{student_id}'
        sessions_dir = f'{student_dir}/sessions'
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Generate session filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        session_file = f'{sessions_dir}/{timestamp}_vapi_session.json'
        transcript_file = f'{sessions_dir}/{timestamp}_vapi_transcript.txt'
        
        # Create session data using API metadata
        metadata = vapi_client.extract_call_metadata(call_data)
        session_data = {
            'call_id': call_id,
            'student_id': student_id,
            'phone_number': phone,
            'start_time': metadata.get('created_at', datetime.now().isoformat()),
            'duration_seconds': duration,
            'session_type': 'vapi_call_api',
            'transcript_file': f'{timestamp}_vapi_transcript.txt',
            'transcript_length': len(transcript) if transcript else 0,
            'data_source': 'vapi_api',
            'call_status': metadata.get('status'),
            'call_cost': metadata.get('cost', 0),
            'has_recording': metadata.get('has_recording', False),
            'recording_url': metadata.get('recording_url'),
            'vapi_metadata': metadata,
            'analysis_summary': metadata.get('analysis_summary', ''),
            'analysis_data': metadata.get('analysis_structured_data', {})
        }
        
        # Save session metadata
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Save transcript
        if transcript:
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            # NEW: Analyze transcript and update student profile
            try:
                from transcript_analyzer import TranscriptAnalyzer
                analyzer = TranscriptAnalyzer()
                extracted_info = analyzer.analyze_transcript(transcript)
                if extracted_info:
                    analyzer.update_student_profile(student_id, extracted_info)
                    log_webhook('profile-updated', f"Updated student profile from transcript",
                               call_id=call_id, student_id=student_id, 
                               extracted_info=extracted_info)
            except Exception as e:
                log_error('TRANSCRIPT_ANALYSIS', f"Error analyzing transcript", e,
                         call_id=call_id, student_id=student_id)
        
        print(f"💾 Saved API-driven session: {session_file}")
        log_webhook('session-saved', f"Saved session for call {call_id}",
                   call_id=call_id,
                   student_id=student_id,
                   session_file=session_file,
                   transcript_length=len(transcript) if transcript else 0)
        
    except Exception as e:
        log_error('WEBHOOK', f"Error saving API-driven session for call {call_id}", e,
                 call_id=call_id, student_id=student_id)
        print(f"❌ Error saving API-driven session: {e}")
```

3. **Add Similar Integration to the Webhook Fallback Handler**

Update the `save_vapi_session` function in a similar way to analyze transcripts from the webhook fallback handler.

## Benefits

1. **Automatic Profile Enrichment**: Student profiles will be automatically updated with information gathered during conversations.
2. **Improved Personalization**: With more complete profiles, the AI tutor can provide more personalized interactions.
3. **Reduced Manual Data Entry**: Administrators won't need to manually update student profiles with information that was already shared in conversations.

## Implementation Notes

1. The transcript analyzer uses regular expressions to extract information, which may not catch all variations of how students express their age, grade, or interests.
2. The analyzer only updates fields that are empty or "Unknown" to avoid overwriting manually entered information.
3. For interests, new interests are added to the existing list rather than replacing it.
4. The analyzer could be extended to extract other information like favorite subjects, learning preferences, etc.

## Implemented Enhancements

1. **AI-Powered Extraction**: Replaced regex-based extraction with a more sophisticated AI model that can better understand context and extract information more accurately.
   - The system now uses AI to analyze transcripts and extract student information
   - A clear, structured prompt ensures the AI returns information in a consistent JSON format
   - The AI is instructed to only extract information that is explicitly stated by the student

2. **Improved Prompt Design**: The AI prompt has been optimized to:
   - Focus on extracting only explicitly stated information
   - Return results in a standardized JSON format
   - Include examples to guide the AI's extraction process
   - Extract age, grade, interests, learning preferences, and favorite/challenging subjects

## Future Enhancements

1. **Confidence Scoring**: Add confidence scores to extracted information to avoid updating profiles with low-confidence extractions.
2. **Admin Review**: Add a feature for administrators to review and approve extracted information before it's added to profiles.
3. **Enhanced Extraction Categories**: Expand the types of information extracted to include more detailed educational preferences and needs.