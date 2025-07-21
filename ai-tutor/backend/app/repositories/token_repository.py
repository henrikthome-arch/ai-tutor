"""
Token repository for database operations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app import db
from app.models.token import Token

def get_all_active() -> List[Dict[str, Any]]:
    """
    Get all active, non-expired tokens
    
    Returns:
        List of token dictionaries
    """
    tokens = Token.get_active_tokens()
    return [token.to_dict() for token in tokens]

def get_by_id(token_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a token by ID
    
    Args:
        token_id: The token ID
        
    Returns:
        Token dictionary or None if not found
    """
    token = Token.query.get(token_id)
    return token.to_dict() if token else None

def find_by_token(raw_token: str) -> Optional[Dict[str, Any]]:
    """
    Find token by raw token value
    
    Args:
        raw_token: The actual token string
        
    Returns:
        Token dictionary or None if not found
    """
    token = Token.find_by_token(raw_token)
    if token and token.is_valid():
        # Update usage tracking
        token.update_last_used()
        return token.to_dict()
    return None

def create(name: str, scopes: List[str], expiration_hours: int = 4, created_by: str = None) -> Dict[str, Any]:
    """
    Create a new token
    
    Args:
        name: Token name/description
        scopes: List of scopes
        expiration_hours: Hours until expiration
        created_by: Username who created the token
        
    Returns:
        The created token with raw token value
    """
    try:
        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        token = Token.create_token(
            name=name,
            scopes=scopes,
            expires_at=expires_at,
            created_by=created_by
        )
        
        return token.to_dict(include_token=True)
    except Exception as e:
        db.session.rollback()
        print(f"Error creating token: {e}")
        raise e

def revoke(token_id: str) -> bool:
    """
    Revoke a token by ID
    
    Args:
        token_id: The token ID
        
    Returns:
        True if revoked, False if not found
    """
    try:
        return Token.revoke_token_by_id(token_id)
    except Exception as e:
        db.session.rollback()
        print(f"Error revoking token: {e}")
        raise e

def cleanup_expired() -> int:
    """
    Remove expired tokens from database
    
    Returns:
        Number of tokens removed
    """
    try:
        return Token.cleanup_expired_tokens()
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up expired tokens: {e}")
        raise e

def validate_token_scopes(raw_token: str, required_scopes: List[str]) -> bool:
    """
    Validate that a token has all required scopes
    
    Args:
        raw_token: The actual token string
        required_scopes: List of required scopes
        
    Returns:
        True if token is valid and has all required scopes
    """
    token = Token.find_by_token(raw_token)
    if not token or not token.is_valid():
        return False
    
    # Check if token has all required scopes
    if required_scopes:
        token_scopes = token.scopes or []
        if not all(scope in token_scopes for scope in required_scopes):
            return False
    
    # Update usage tracking
    token.update_last_used()
    return True

def get_token_stats() -> Dict[str, Any]:
    """
    Get token usage statistics
    
    Returns:
        Dictionary with token statistics
    """
    try:
        total_tokens = Token.query.count()
        active_tokens = len(Token.get_active_tokens())
        expired_tokens = Token.query.filter(
            Token.expires_at <= datetime.utcnow()
        ).count()
        revoked_tokens = Token.query.filter(
            Token.is_active == False
        ).count()
        
        return {
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'expired_tokens': expired_tokens,
            'revoked_tokens': revoked_tokens
        }
    except Exception as e:
        print(f"Error getting token stats: {e}")
        return {
            'total_tokens': 0,
            'active_tokens': 0,
            'expired_tokens': 0,
            'revoked_tokens': 0
        }