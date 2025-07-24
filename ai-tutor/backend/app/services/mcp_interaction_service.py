"""
MCP Interaction Service
Business logic for MCP interaction logging and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.repositories.mcp_interaction_repository import MCPInteractionRepository
from app.models.mcp_interaction import MCPInteraction

class MCPInteractionService:
    """Service layer for MCP interaction operations"""
    
    def __init__(self):
        self.repository = MCPInteractionRepository()
    
    def log_request(self, endpoint: str, request_data: Dict[Any, Any], 
                   session_id: Optional[str] = None, 
                   token_id: Optional[int] = None) -> str:
        """
        Log an incoming MCP request
        
        Args:
            endpoint: The MCP endpoint being called
            request_data: The request payload
            session_id: Optional session identifier
            token_id: Optional token ID for authentication
            
        Returns:
            request_id: Unique identifier for this request
        """
        # Prepare the request payload with metadata
        request_payload = {
            'endpoint': endpoint,
            'data': request_data,
            'timestamp': datetime.utcnow().isoformat(),
            'user_agent': None,  # Could be extracted from headers
            'ip_address': None   # Could be extracted from request context
        }
        
        # Create the interaction record
        interaction = self.repository.create_interaction(
            request_payload=request_payload,
            session_id=session_id,
            token_id=token_id
        )
        
        return interaction.request_id
    
    def log_response(self, request_id: str, response_data: Dict[Any, Any], 
                    http_status_code: int = 200) -> bool:
        """
        Log the response for an MCP request
        
        Args:
            request_id: The request ID returned from log_request
            response_data: The response payload
            http_status_code: HTTP status code
            
        Returns:
            bool: True if response was logged successfully
        """
        # Prepare the response payload with metadata
        response_payload = {
            'data': response_data,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success' if 200 <= http_status_code < 300 else 'error'
        }
        
        # Complete the interaction
        interaction = self.repository.complete_interaction(
            request_id=request_id,
            response_payload=response_payload,
            http_status_code=http_status_code
        )
        
        return interaction is not None
    
    def get_interactions(self, page: int = 1, per_page: int = 50,
                        session_id: Optional[str] = None,
                        token_id: Optional[int] = None) -> Dict[str, Any]:
        """Get interactions with pagination and filtering"""
        return self.repository.get_interactions_with_pagination(
            page=page,
            per_page=per_page,
            session_id=session_id,
            token_id=token_id
        )
    
    def get_interaction_by_id(self, interaction_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific interaction by ID"""
        interaction = self.repository.get_by_id(interaction_id)
        return interaction.to_dict() if interaction else None
    
    def get_recent_interactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent interactions"""
        interactions = self.repository.get_recent_interactions(limit)
        return [interaction.to_dict() for interaction in interactions]
    
    def get_interactions_by_session(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a specific session"""
        interactions = self.repository.get_interactions_by_session(session_id, limit)
        return [interaction.to_dict() for interaction in interactions]
    
    def get_interactions_by_token(self, token_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a specific token"""
        interactions = self.repository.get_interactions_by_token(token_id, limit)
        return [interaction.to_dict() for interaction in interactions]
    
    def get_summary_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for MCP interactions"""
        return self.repository.get_interactions_summary(hours)
    
    def get_endpoint_statistics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get statistics grouped by endpoint"""
        return self.repository.get_endpoint_statistics(hours)
    
    def get_incomplete_interactions(self, older_than_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get interactions that haven't received responses"""
        interactions = self.repository.get_incomplete_interactions(older_than_minutes)
        return [interaction.to_dict(include_payloads=False) for interaction in interactions]
    
    def cleanup_old_interactions(self, days: int = 30) -> int:
        """Clean up old interaction records"""
        return self.repository.cleanup_old_interactions(days)
    
    def get_interaction_details(self, interaction_id: int, include_payloads: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed interaction information including payloads"""
        interaction = self.repository.get_by_id(interaction_id)
        if interaction:
            return interaction.to_dict(include_payloads=include_payloads)
        return None
    
    def search_interactions(self, endpoint: Optional[str] = None,
                          status_code: Optional[int] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Search interactions with various filters"""
        if start_date and end_date:
            interactions = self.repository.get_interactions_by_date_range(
                start_date, end_date, limit
            )
        else:
            interactions = self.repository.get_recent_interactions(limit)
        
        # Apply additional filters
        filtered_interactions = []
        for interaction in interactions:
            # Filter by endpoint
            if endpoint and interaction.request_payload.get('endpoint') != endpoint:
                continue
            
            # Filter by status code
            if status_code and interaction.http_status_code != status_code:
                continue
            
            filtered_interactions.append(interaction.to_dict(include_payloads=False))
        
        return filtered_interactions
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for the MCP interaction system"""
        total_interactions = self.repository.get_interaction_count()
        recent_summary = self.get_summary_statistics(hours=1)  # Last hour
        daily_summary = self.get_summary_statistics(hours=24)  # Last 24 hours
        incomplete = self.repository.get_incomplete_interactions(older_than_minutes=5)
        
        return {
            'total_interactions': total_interactions,
            'last_hour': recent_summary,
            'last_24_hours': daily_summary,
            'stuck_interactions': len(incomplete),
            'health_status': 'healthy' if len(incomplete) < 10 else 'warning'
        }