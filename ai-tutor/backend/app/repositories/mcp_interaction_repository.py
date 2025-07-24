"""
MCP Interaction Repository
Handles database operations for MCP interaction logging
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.mcp_interaction import MCPInteraction
from app import db

class MCPInteractionRepository:
    """Repository for MCP interaction database operations"""
    
    def create_interaction(self, request_payload: Dict[Any, Any], 
                          session_id: Optional[str] = None, 
                          token_id: Optional[int] = None) -> MCPInteraction:
        """Create a new MCP interaction record for incoming request"""
        return MCPInteraction.create_interaction(
            request_payload=request_payload,
            session_id=session_id,
            token_id=token_id
        )
    
    def complete_interaction(self, request_id: str, response_payload: Dict[Any, Any], 
                           http_status_code: Optional[int] = None) -> Optional[MCPInteraction]:
        """Complete an interaction with response data"""
        interaction = MCPInteraction.find_by_request_id(request_id)
        if interaction:
            interaction.complete_interaction(response_payload, http_status_code)
            return interaction
        return None
    
    def get_by_id(self, interaction_id: int) -> Optional[MCPInteraction]:
        """Get interaction by ID"""
        return MCPInteraction.query.get(interaction_id)
    
    def get_by_request_id(self, request_id: str) -> Optional[MCPInteraction]:
        """Get interaction by request ID"""
        return MCPInteraction.find_by_request_id(request_id)
    
    def get_recent_interactions(self, limit: int = 100) -> List[MCPInteraction]:
        """Get recent interactions ordered by request timestamp"""
        return MCPInteraction.get_recent_interactions(limit)
    
    def get_interactions_by_session(self, session_id: str, limit: int = 50) -> List[MCPInteraction]:
        """Get interactions for a specific session"""
        return MCPInteraction.get_interactions_by_session(session_id, limit)
    
    def get_interactions_by_token(self, token_id: int, limit: int = 50) -> List[MCPInteraction]:
        """Get interactions for a specific token"""
        return MCPInteraction.get_interactions_by_token(token_id, limit)
    
    def get_incomplete_interactions(self, older_than_minutes: int = 30) -> List[MCPInteraction]:
        """Get interactions that haven't received responses within time limit"""
        return MCPInteraction.get_incomplete_interactions(older_than_minutes)
    
    def get_interactions_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for interactions in the last N hours"""
        return MCPInteraction.get_interactions_summary(hours)
    
    def get_interactions_by_date_range(self, start_date: datetime, end_date: datetime, 
                                     limit: int = 1000) -> List[MCPInteraction]:
        """Get interactions within a date range"""
        return MCPInteraction.query.filter(
            MCPInteraction.request_timestamp >= start_date,
            MCPInteraction.request_timestamp <= end_date
        ).order_by(MCPInteraction.request_timestamp.desc()).limit(limit).all()
    
    def cleanup_old_interactions(self, days: int = 30) -> int:
        """Remove interactions older than specified days"""
        return MCPInteraction.cleanup_old_interactions(days)
    
    def get_interaction_count(self) -> int:
        """Get total count of interactions"""
        return MCPInteraction.query.count()
    
    def get_interactions_with_pagination(self, page: int = 1, per_page: int = 50, 
                                       session_id: Optional[str] = None,
                                       token_id: Optional[int] = None) -> Dict[str, Any]:
        """Get interactions with pagination support"""
        query = MCPInteraction.query
        
        # Apply filters
        if session_id:
            query = query.filter(MCPInteraction.session_id == session_id)
        if token_id:
            query = query.filter(MCPInteraction.token_id == token_id)
        
        # Order by request timestamp (newest first)
        query = query.order_by(MCPInteraction.request_timestamp.desc())
        
        # Paginate
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            'interactions': [interaction.to_dict() for interaction in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    
    def get_endpoint_statistics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get statistics grouped by endpoint for the last N hours"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # This would require raw SQL or more complex SQLAlchemy query
        # For now, return basic stats
        interactions = MCPInteraction.query.filter(
            MCPInteraction.request_timestamp >= since_time
        ).all()
        
        endpoint_stats = {}
        for interaction in interactions:
            # Extract endpoint from request payload
            endpoint = interaction.request_payload.get('endpoint', 'unknown')
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'endpoint': endpoint,
                    'total_calls': 0,
                    'completed_calls': 0,
                    'avg_duration_ms': 0,
                    'total_duration_ms': 0
                }
            
            stats = endpoint_stats[endpoint]
            stats['total_calls'] += 1
            
            if interaction.is_completed():
                stats['completed_calls'] += 1
                if interaction.duration_ms:
                    stats['total_duration_ms'] += interaction.duration_ms
        
        # Calculate averages
        for stats in endpoint_stats.values():
            if stats['completed_calls'] > 0:
                stats['avg_duration_ms'] = stats['total_duration_ms'] // stats['completed_calls']
            stats['completion_rate'] = (stats['completed_calls'] / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 0
        
        return list(endpoint_stats.values())