#!/usr/bin/env python3
"""
VAPI API Client
Handles communication with VAPI REST API for fetching complete call data
"""

import os
import requests
import json
import time
from typing import Optional, Dict, Any, List
from functools import wraps
from system_logger import log_webhook, log_error

class VAPIClient:
    """Client for interacting with VAPI REST API"""
    
    def __init__(self):
        self.api_key = os.getenv('VAPI_API_KEY')
        self.base_url = 'https://api.vapi.ai'
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        else:
            log_error('VAPI_CLIENT', 'VAPI_API_KEY not configured', 
                     ValueError('Missing API key'))
    
    def is_configured(self) -> bool:
        """Check if VAPI API client is properly configured"""
        return bool(self.api_key)
    
    @staticmethod
    def retry_on_failure(max_attempts=3, delay=1.0):
        """Decorator for retrying failed API calls with exponential backoff"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return func(self, *args, **kwargs)
                    except requests.exceptions.RequestException as e:
                        if attempt == max_attempts - 1:
                            log_error('VAPI_CLIENT', 
                                    f"Final attempt failed for {func.__name__}", e,
                                    attempt=attempt + 1,
                                    max_attempts=max_attempts)
                            raise e
                        
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        log_webhook('api-retry', 
                                  f"Retrying {func.__name__} after {wait_time}s",
                                  attempt=attempt + 1,
                                  max_attempts=max_attempts,
                                  error=str(e))
                        time.sleep(wait_time)
                        
                return None
            return wrapper
        return decorator
    
    @retry_on_failure(max_attempts=3)
    def get_call_details(self, call_id: str) -> Optional[Dict[Any, Any]]:
        """Fetch complete call details from VAPI API"""
        if not self.is_configured():
            log_error('VAPI_CLIENT', 'Cannot fetch call details - API key not configured',
                     ValueError('VAPI_API_KEY missing'))
            return None
            
        try:
            log_webhook('api-request', f'Fetching call details for {call_id}',
                       call_id=call_id, endpoint='get_call')
            
            response = self.session.get(f'{self.base_url}/call/{call_id}')
            response.raise_for_status()
            
            call_data = response.json()
            log_webhook('api-success', f'Successfully fetched call {call_id}',
                       call_id=call_id,
                       response_size=len(response.text),
                       has_transcript=bool(call_data.get('transcript')))
            
            return call_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                log_error('VAPI_CLIENT', f'Call {call_id} not found', e, 
                         call_id=call_id, status_code=404)
            else:
                log_error('VAPI_CLIENT', f'HTTP error fetching call {call_id}', e,
                         call_id=call_id, status_code=e.response.status_code)
            return None
            
        except Exception as e:
            log_error('VAPI_CLIENT', f'Failed to fetch call {call_id}', e, 
                     call_id=call_id)
            return None
    
    def get_call_transcript(self, call_id: str) -> Optional[str]:
        """Get formatted transcript from call details"""
        call_data = self.get_call_details(call_id)
        if not call_data:
            return None
            
        try:
            # Extract transcript data based on VAPI's format
            transcript_data = call_data.get('transcript', {})
            
            if isinstance(transcript_data, dict):
                # Format: {"user": "...", "assistant": "..."}
                user_transcript = transcript_data.get('user', '')
                assistant_transcript = transcript_data.get('assistant', '')
                
                if user_transcript or assistant_transcript:
                    return self._format_transcript_dict(user_transcript, assistant_transcript, call_data)
            
            elif isinstance(transcript_data, list):
                # Format: [{"role": "user", "message": "..."}, ...]
                return self._format_transcript_list(transcript_data, call_data)
            
            elif isinstance(transcript_data, str):
                # Format: Raw transcript string
                return self._format_transcript_string(transcript_data, call_data)
            
            log_error('VAPI_CLIENT', f'Unknown transcript format for call {call_id}',
                     ValueError(f'Unexpected transcript type: {type(transcript_data)}'),
                     call_id=call_id, transcript_type=type(transcript_data).__name__)
            return None
            
        except Exception as e:
            log_error('VAPI_CLIENT', f'Error formatting transcript for call {call_id}', e,
                     call_id=call_id)
            return None
    
    def _format_transcript_dict(self, user_transcript: str, assistant_transcript: str, 
                               call_data: Dict) -> str:
        """Format transcript from dict format"""
        call_id = call_data.get('id', 'unknown')
        duration = call_data.get('durationSeconds', 0)
        phone = call_data.get('customer', {}).get('number', 'unknown')
        
        formatted = f"=== VAPI Call Transcript ===\n"
        formatted += f"Call ID: {call_id}\n"
        formatted += f"Duration: {duration} seconds\n"
        formatted += f"Phone: {phone}\n"
        formatted += f"Timestamp: {call_data.get('createdAt', 'unknown')}\n\n"
        
        if user_transcript:
            formatted += f"=== User Transcript ===\n{user_transcript.strip()}\n\n"
        
        if assistant_transcript:
            formatted += f"=== Assistant Transcript ===\n{assistant_transcript.strip()}\n"
        
        return formatted
    
    def _format_transcript_list(self, transcript_list: List[Dict], call_data: Dict) -> str:
        """Format transcript from list format"""
        call_id = call_data.get('id', 'unknown')
        duration = call_data.get('durationSeconds', 0)
        phone = call_data.get('customer', {}).get('number', 'unknown')
        
        formatted = f"=== VAPI Call Transcript ===\n"
        formatted += f"Call ID: {call_id}\n"
        formatted += f"Duration: {duration} seconds\n"
        formatted += f"Phone: {phone}\n"
        formatted += f"Timestamp: {call_data.get('createdAt', 'unknown')}\n\n"
        
        for entry in transcript_list:
            role = entry.get('role', 'unknown')
            message = entry.get('message', '')
            timestamp = entry.get('timestamp', '')
            
            if message:
                formatted += f"[{timestamp}] {role.upper()}: {message.strip()}\n"
        
        return formatted
    
    def _format_transcript_string(self, transcript: str, call_data: Dict) -> str:
        """Format transcript from string format"""
        call_id = call_data.get('id', 'unknown')
        duration = call_data.get('durationSeconds', 0)
        phone = call_data.get('customer', {}).get('number', 'unknown')
        
        formatted = f"=== VAPI Call Transcript ===\n"
        formatted += f"Call ID: {call_id}\n"
        formatted += f"Duration: {duration} seconds\n"
        formatted += f"Phone: {phone}\n"
        formatted += f"Timestamp: {call_data.get('createdAt', 'unknown')}\n\n"
        formatted += f"=== Transcript ===\n{transcript.strip()}\n"
        
        return formatted
    
    def extract_call_metadata(self, call_data: Dict) -> Dict[str, Any]:
        """Extract essential metadata from call data"""
        if not call_data:
            return {}
        
        try:
            metadata = {
                'call_id': call_data.get('id'),
                'duration_seconds': call_data.get('durationSeconds', 0),
                'customer_phone': call_data.get('customer', {}).get('number'),
                'assistant_id': call_data.get('assistantId'),
                'created_at': call_data.get('createdAt'),
                'status': call_data.get('status'),
                'cost': call_data.get('cost', 0),
                'has_transcript': bool(call_data.get('transcript')),
                'has_recording': bool(call_data.get('recordingUrl')),
                'recording_url': call_data.get('recordingUrl')
            }
            
            # Extract analysis/summary if available
            analysis = call_data.get('analysis', {})
            if analysis:
                metadata['analysis_summary'] = analysis.get('summary', '')
                metadata['analysis_structured_data'] = analysis.get('structuredData', {})
            
            return metadata
            
        except Exception as e:
            log_error('VAPI_CLIENT', 'Error extracting call metadata', e,
                     call_id=call_data.get('id', 'unknown'))
            return {'call_id': call_data.get('id')}
    
    def get_calls_list(self, limit: int = 10) -> Optional[List[Dict]]:
        """Get list of recent calls (for testing/debugging)"""
        if not self.is_configured():
            return None
            
        try:
            response = self.session.get(f'{self.base_url}/call', 
                                      params={'limit': limit})
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            log_error('VAPI_CLIENT', 'Error fetching calls list', e)
            return None


# Global instance for use throughout the application
vapi_client = VAPIClient()