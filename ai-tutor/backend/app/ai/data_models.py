#!/usr/bin/env python3
"""
AI-Extracted Data Models
Defines standardized data structures for AI-extracted student profile information
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class AIExtractedProfile:
    """
    Standardized data model for AI-extracted student profile information.
    This ensures consistent parsing and validation of AI responses.
    """
    # Core identification
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Demographics
    age: Optional[int] = None
    grade: Optional[int] = None
    
    # Interests and preferences
    interests: List[str] = None
    learning_preferences: List[str] = None
    
    # Academic information
    favorite_subjects: List[str] = None
    challenging_subjects: List[str] = None
    
    # Metadata
    confidence_score: float = 0.0
    extraction_source: str = "ai_analysis"
    
    def __post_init__(self):
        """Initialize empty lists if None provided"""
        if self.interests is None:
            self.interests = []
        if self.learning_preferences is None:
            self.learning_preferences = []
        if self.favorite_subjects is None:
            self.favorite_subjects = []
        if self.challenging_subjects is None:
            self.challenging_subjects = []
    
    @classmethod
    def from_ai_response(cls, ai_response: str) -> 'AIExtractedProfile':
        """
        Parse AI response JSON into validated AIExtractedProfile object.
        
        Args:
            ai_response: Raw AI response string (should contain JSON)
            
        Returns:
            AIExtractedProfile object with validated data
            
        Raises:
            ValueError: If parsing fails or data is invalid
        """
        if not ai_response or not ai_response.strip():
            logger.warning("Empty AI response provided")
            return cls()
        
        try:
            # Parse JSON from response
            data = cls._parse_json_from_response(ai_response)
            
            # Extract and validate fields
            profile = cls()
            
            # Extract name information with validation
            profile.first_name = cls._extract_name_field(data, 'first_name')
            profile.last_name = cls._extract_name_field(data, 'last_name')
            
            # Handle legacy 'name' field that might contain full name
            if not profile.first_name and 'name' in data:
                full_name = str(data['name']).strip()
                if full_name and full_name.lower() not in ['unknown', 'none', 'null', '']:
                    name_parts = full_name.split(maxsplit=1)
                    profile.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        profile.last_name = name_parts[1]
            
            # Extract numeric fields with validation
            profile.age = cls._extract_numeric_field(data, 'age', min_val=3, max_val=18)
            profile.grade = cls._extract_numeric_field(data, 'grade', min_val=1, max_val=12)
            
            # Extract list fields
            profile.interests = cls._extract_list_field(data, 'interests')
            profile.learning_preferences = cls._extract_list_field(data, 'learning_preferences')
            
            # Handle subjects (both nested and flat structures)
            if 'subjects' in data and isinstance(data['subjects'], dict):
                profile.favorite_subjects = cls._extract_list_field(data['subjects'], 'favorite')
                profile.challenging_subjects = cls._extract_list_field(data['subjects'], 'challenging')
            else:
                profile.favorite_subjects = cls._extract_list_field(data, 'favorite_subjects')
                profile.challenging_subjects = cls._extract_list_field(data, 'challenging_subjects')
            
            # Extract confidence score
            profile.confidence_score = float(data.get('confidence_score', 0.0))
            if not 0.0 <= profile.confidence_score <= 1.0:
                profile.confidence_score = 0.0
            
            logger.info(f"Successfully parsed AI response into profile: {profile}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Raw AI response: {ai_response}")
            raise ValueError(f"Invalid AI response format: {e}")
    
    @staticmethod
    def _parse_json_from_response(response: str) -> Dict[str, Any]:
        """Extract and parse JSON from AI response text"""
        response = response.strip()
        
        # Try parsing as direct JSON first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Extract JSON from text using regex
        import re
        json_pattern = r'```json\s*(\{.*?\})\s*```|```\s*(\{.*?\})\s*```|(\{[\s\S]*\})'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            for group in match:
                if group.strip():
                    try:
                        return json.loads(group.strip())
                    except json.JSONDecodeError:
                        continue
        
        # Try to find JSON-like structure without code blocks
        json_match = re.search(r'(\{[\s\S]*\})', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"No valid JSON found in response: {response[:200]}...")
    
    @staticmethod
    def _extract_name_field(data: Dict, field_name: str) -> Optional[str]:
        """Extract and validate name field"""
        value = data.get(field_name)
        if not value:
            return None
        
        name = str(value).strip()
        if name.lower() in ['unknown', 'none', 'null', '', 'student']:
            return None
        
        # Validate name contains only letters, spaces, hyphens, apostrophes
        import re
        if re.match(r"^[a-zA-Z\s\-']+$", name) and len(name) <= 50:
            return name
        
        logger.warning(f"Invalid name format: {name}")
        return None
    
    @staticmethod
    def _extract_numeric_field(data: Dict, field_name: str, min_val: int = None, max_val: int = None) -> Optional[int]:
        """Extract and validate numeric field"""
        value = data.get(field_name)
        if value is None:
            return None
        
        try:
            num_val = int(value)
            if min_val is not None and num_val < min_val:
                return None
            if max_val is not None and num_val > max_val:
                return None
            return num_val
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _extract_list_field(data: Dict, field_name: str) -> List[str]:
        """Extract and validate list field"""
        value = data.get(field_name, [])
        if not isinstance(value, list):
            return []
        
        # Clean and validate list items
        cleaned_items = []
        for item in value:
            if item and isinstance(item, str):
                clean_item = str(item).strip()
                if clean_item and len(clean_item) <= 100:
                    cleaned_items.append(clean_item)
        
        return cleaned_items
    
    def has_valid_name(self) -> bool:
        """Check if profile contains valid name information"""
        return bool(self.first_name and self.first_name.strip())
    
    def has_any_data(self) -> bool:
        """Check if profile contains any useful data"""
        return (
            self.has_valid_name() or
            self.age is not None or
            self.grade is not None or
            len(self.interests) > 0 or
            len(self.learning_preferences) > 0 or
            len(self.favorite_subjects) > 0 or
            len(self.challenging_subjects) > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'grade': self.grade,
            'interests': self.interests,
            'learning_preferences': self.learning_preferences,
            'favorite_subjects': self.favorite_subjects,
            'challenging_subjects': self.challenging_subjects,
            'confidence_score': self.confidence_score,
            'extraction_source': self.extraction_source
        }
    
    def __str__(self) -> str:
        """String representation for logging"""
        name = f"{self.first_name or ''} {self.last_name or ''}".strip() or "Unknown"
        details = []
        if self.age:
            details.append(f"age {self.age}")
        if self.grade:
            details.append(f"grade {self.grade}")
        if self.interests:
            details.append(f"interests: {', '.join(self.interests[:3])}")
        
        detail_str = f" ({', '.join(details)})" if details else ""
        return f"AIExtractedProfile[{name}{detail_str}]"


class ValidationError(Exception):
    """Custom exception for data validation errors"""
    pass