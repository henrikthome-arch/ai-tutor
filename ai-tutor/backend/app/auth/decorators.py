"""
Authentication and authorization decorators for the AI Tutor application.
"""

import functools
import logging
from typing import Callable, List, Optional, Union

from flask import request, jsonify, session, current_app, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from werkzeug.exceptions import Unauthorized, Forbidden

from app.services.token_service import TokenService

logger = logging.getLogger(__name__)
token_service = TokenService()

def require_token_scope(required_scope: str):
    """
    Decorator to require a specific scope in the JWT token.
    
    Args:
        required_scope: The scope required to access the endpoint
        
    Returns:
        Decorated function that checks for the required scope
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Verify JWT is present and valid
                verify_jwt_in_request()
                
                # Get JWT claims
                claims = get_jwt()
                
                # Check if token has the required scope
                scopes = claims.get('scopes', [])
                if required_scope not in scopes:
                    logger.warning(
                        f"Token missing required scope: {required_scope}. "
                        f"Available scopes: {scopes}"
                    )
                    return jsonify({
                        'error': 'insufficient_scope',
                        'message': f'Token is missing required scope: {required_scope}',
                        'required_scope': required_scope
                    }), 403
                
                # Store token info in Flask g object for potential use in the view
                g.token_scopes = scopes
                g.token_type = claims.get('type')
                
                # Call the original function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Token authentication error: {str(e)}")
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Invalid or expired token'
                }), 401
                
        return wrapper
    return decorator


def token_or_session_auth(required_scope: Optional[str] = None):
    """
    Decorator that allows either token-based or session-based authentication.
    
    This decorator first checks for a valid JWT token. If not present, it falls back
    to checking for a valid session. This allows both API clients with tokens and
    browser users with sessions to access the same endpoints.
    
    Args:
        required_scope: Optional scope required if using token authentication
        
    Returns:
        Decorated function that checks for either valid token or session
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if Authorization header is present (token auth)
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    # Verify JWT is present and valid
                    verify_jwt_in_request()
                    
                    # If a scope is required, check it
                    if required_scope:
                        claims = get_jwt()
                        scopes = claims.get('scopes', [])
                        
                        if required_scope not in scopes:
                            logger.warning(
                                f"Token missing required scope: {required_scope}. "
                                f"Available scopes: {scopes}"
                            )
                            return jsonify({
                                'error': 'insufficient_scope',
                                'message': f'Token is missing required scope: {required_scope}',
                                'required_scope': required_scope
                            }), 403
                        
                        # Store token info in Flask g object
                        g.token_scopes = scopes
                        g.token_type = claims.get('type')
                        g.auth_method = 'token'
                    
                    # Call the original function
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    logger.error(f"Token authentication error: {str(e)}")
                    return jsonify({
                        'error': 'invalid_token',
                        'message': 'Invalid or expired token'
                    }), 401
            
            # No valid token, check for session auth
            if session.get('admin_logged_in'):
                # User is authenticated via session
                g.auth_method = 'session'
                return func(*args, **kwargs)
            
            # Neither token nor session auth succeeded
            return jsonify({
                'error': 'unauthorized',
                'message': 'Authentication required'
            }), 401
                
        return wrapper
    return decorator


def require_multiple_scopes(required_scopes: List[str], require_all: bool = False):
    """
    Decorator to require multiple scopes in the JWT token.
    
    Args:
        required_scopes: List of scopes required to access the endpoint
        require_all: If True, all scopes are required; if False, any one is sufficient
        
    Returns:
        Decorated function that checks for the required scopes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Verify JWT is present and valid
                verify_jwt_in_request()
                
                # Get JWT claims
                claims = get_jwt()
                
                # Check if token has the required scopes
                token_scopes = claims.get('scopes', [])
                
                if require_all:
                    # All scopes must be present
                    missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
                    if missing_scopes:
                        logger.warning(
                            f"Token missing required scopes: {missing_scopes}. "
                            f"Available scopes: {token_scopes}"
                        )
                        return jsonify({
                            'error': 'insufficient_scope',
                            'message': f'Token is missing required scopes: {missing_scopes}',
                            'required_scopes': required_scopes,
                            'missing_scopes': missing_scopes
                        }), 403
                else:
                    # At least one scope must be present
                    if not any(scope in token_scopes for scope in required_scopes):
                        logger.warning(
                            f"Token missing any of required scopes: {required_scopes}. "
                            f"Available scopes: {token_scopes}"
                        )
                        return jsonify({
                            'error': 'insufficient_scope',
                            'message': f'Token must have at least one of these scopes: {required_scopes}',
                            'required_scopes': required_scopes
                        }), 403
                
                # Store token info in Flask g object
                g.token_scopes = token_scopes
                g.token_type = claims.get('type')
                
                # Call the original function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Token authentication error: {str(e)}")
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Invalid or expired token'
                }), 401
                
        return wrapper
    return decorator