"""
Service for generating and validating access tokens for debugging and testing.
"""

from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
from flask_jwt_extended import create_access_token, decode_token, get_jwt

logger = logging.getLogger(__name__)

class TokenService:
    """Service for managing access tokens for debugging and testing."""
    
    # Define available scopes and their descriptions
    AVAILABLE_SCOPES = {
        'api:read': 'Read access to API endpoints',
        'api:write': 'Write access to API endpoints',
        'logs:read': 'Read access to system logs',
        'mcp:access': 'Access to MCP server functionality',
        'admin:read': 'Read access to admin dashboard',
    }
    
    def __init__(self):
        """Initialize the token service."""
        pass
    
    def generate_token(self, 
                      scopes: List[str], 
                      expires_in_minutes: int = 30, 
                      user_id: Optional[str] = None,
                      additional_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a JWT access token with specific scopes and expiration time.
        
        Args:
            scopes: List of permission scopes to include in the token
            expires_in_minutes: Token expiration time in minutes (default: 30)
            user_id: Optional user ID to associate with the token
            additional_claims: Optional additional claims to include in the token
            
        Returns:
            Dictionary containing the token and metadata
        """
        # Validate scopes
        valid_scopes = [scope for scope in scopes if scope in self.AVAILABLE_SCOPES]
        if not valid_scopes:
            raise ValueError("At least one valid scope must be provided")
        
        # Prepare claims
        claims = {
            'scopes': valid_scopes,
            'type': 'debug_access',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Add user ID if provided
        if user_id:
            claims['user_id'] = user_id
            
        # Add additional claims if provided
        if additional_claims:
            claims.update(additional_claims)
        
        # Generate token with expiration
        expires = timedelta(minutes=expires_in_minutes)
        token = create_access_token(
            identity=user_id or 'debug_user',
            additional_claims=claims,
            expires_delta=expires
        )
        
        # Log token generation (without the actual token)
        logger.info(
            f"Generated debug access token with scopes {valid_scopes}, "
            f"expires in {expires_in_minutes} minutes"
        )
        
        # Return token with metadata
        expiration_time = datetime.utcnow() + expires
        return {
            'token': token,
            'expires_at': expiration_time.isoformat(),
            'expires_in_minutes': expires_in_minutes,
            'scopes': valid_scopes,
            'type': 'debug_access'
        }
    
    def validate_token_has_scope(self, required_scope: str) -> bool:
        """
        Check if the current JWT token has the required scope.
        
        Args:
            required_scope: The scope to check for
            
        Returns:
            True if the token has the required scope, False otherwise
        """
        try:
            # Get the JWT claims
            claims = get_jwt()
            
            # Check if the token has the required scope
            scopes = claims.get('scopes', [])
            return required_scope in scopes
        except Exception as e:
            logger.error(f"Error validating token scope: {str(e)}")
            return False
    
    def decode_token_data(self, token: str) -> Dict[str, Any]:
        """
        Decode a JWT token and return its data (without validation).
        
        Args:
            token: The JWT token to decode
            
        Returns:
            Dictionary containing the decoded token data
        """
        try:
            # Decode the token without verification (for display purposes only)
            decoded = decode_token(token, allow_expired=True)
            return decoded
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}")
            return {'error': str(e)}
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token.
        
        Args:
            token: The JWT token
            
        Returns:
            Expiration datetime or None if error
        """
        try:
            decoded = decode_token(token, allow_expired=True)
            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            return None
        except Exception as e:
            logger.error(f"Error getting token expiration: {str(e)}")
            return None
    
    def get_available_scopes(self) -> Dict[str, str]:
        """
        Get all available scopes with descriptions.
        
        Returns:
            Dictionary of scope names and descriptions
        """
        return self.AVAILABLE_SCOPES.copy()