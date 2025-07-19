"""
VAPI API Client
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class VAPIClient:
    """Client for interacting with the VAPI API"""
    
    def __init__(self):
        self.api_key = os.getenv('VAPI_API_KEY')
        self.base_url = 'https://api.vapi.ai/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def is_configured(self) -> bool:
        """Check if the client is configured with an API key"""
        return bool(self.api_key)
    
    def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific call
        
        Args:
            call_id: The call ID
            
        Returns:
            Call details or None if not found
        """
        if not self.is_configured():
            logger.error("VAPI API client not configured - missing API key")
            return None
        
        try:
            response = requests.get(
                f'{self.base_url}/call/{call_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Call {call_id} not found")
                return None
            else:
                logger.error(f"Error fetching call {call_id}: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception fetching call {call_id}: {e}")
            return None
    
    def get_call_transcript(self, call_id: str) -> str:
        """
        Get transcript for a specific call
        
        Args:
            call_id: The call ID
            
        Returns:
            Call transcript or empty string if not found
        """
        call_data = self.get_call_details(call_id)
        if not call_data:
            return ""
        
        # Extract transcript from call data
        transcript = ""
        
        # Check if there's a transcript field
        if 'transcript' in call_data:
            if isinstance(call_data['transcript'], str):
                transcript = call_data['transcript']
            elif isinstance(call_data['transcript'], dict):
                # Handle structured transcript
                user_transcript = call_data['transcript'].get('user', '')
                assistant_transcript = call_data['transcript'].get('assistant', '')
                transcript = f"User: {user_transcript}\n\nAssistant: {assistant_transcript}"
        
        # If no transcript field, try to extract from messages
        elif 'messages' in call_data and isinstance(call_data['messages'], list):
            messages = call_data['messages']
            for message in messages:
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                transcript += f"{role.capitalize()}: {content}\n\n"
        
        return transcript.strip()
    
    def extract_call_metadata(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from call data
        
        Args:
            call_data: The call data
            
        Returns:
            Extracted metadata
        """
        if not call_data:
            return {}
        
        # Extract basic metadata
        metadata = {
            'call_id': call_data.get('id'),
            'status': call_data.get('status'),
            'created_at': call_data.get('createdAt'),
            'updated_at': call_data.get('updatedAt'),
            'duration_seconds': call_data.get('durationSeconds', 0),
            'cost': call_data.get('cost', 0),
            'has_recording': False,
            'recording_url': None
        }
        
        # Extract customer phone
        customer = call_data.get('customer', {})
        if isinstance(customer, dict):
            metadata['customer_phone'] = customer.get('number')
        
        # Extract recording info
        recording = call_data.get('recording', {})
        if isinstance(recording, dict) and recording.get('url'):
            metadata['has_recording'] = True
            metadata['recording_url'] = recording.get('url')
        
        return metadata

# Global client instance
vapi_client = VAPIClient()