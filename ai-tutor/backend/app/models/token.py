"""
Token model for persistent token storage
"""

import hashlib
import secrets
from datetime import datetime
from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

class Token(db.Model):
    """Token model for persistent access token storage"""
    __tablename__ = 'tokens'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    name = db.Column(db.String(100), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)  # SHA-256 hash of token
    scopes = db.Column(JSONB, nullable=False, default=list)  # List of scopes as JSON
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    created_by = db.Column(db.String(50), nullable=True)  # Admin username who created it
    last_used_at = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f'<Token {self.id} {self.name}>'
    
    @staticmethod
    def hash_token(token):
        """Create SHA-256 hash of token for secure storage"""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def update_last_used(self):
        """Update last used timestamp and increment usage count"""
        self.last_used_at = func.now()
        self.usage_count += 1
        db.session.commit()
    
    def revoke(self):
        """Revoke the token"""
        self.is_active = False
        db.session.commit()
    
    def to_dict(self, include_token=False):
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'name': self.name,
            'scopes': self.scopes,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count,
            'is_expired': self.is_expired()
        }
        
        # Only include actual token value when explicitly requested (for generation response)
        if include_token and hasattr(self, '_raw_token'):
            result['token'] = self._raw_token
            
        return result
    
    @classmethod
    def create_token(cls, name, scopes, expires_at, created_by=None):
        """Create a new token with proper security"""
        import uuid
        
        # Generate secure token and hash it
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        
        # Create token record
        token = cls(
            id=str(uuid.uuid4()),
            name=name,
            token_hash=token_hash,
            scopes=scopes,
            expires_at=expires_at,
            created_by=created_by
        )
        
        # Store raw token temporarily for return (not persisted)
        token._raw_token = raw_token
        
        db.session.add(token)
        db.session.commit()
        
        return token
    
    @classmethod
    def find_by_token(cls, raw_token):
        """Find token by raw token value"""
        token_hash = cls.hash_token(raw_token)
        return cls.query.filter_by(
            token_hash=token_hash,
            is_active=True
        ).first()
    
    @classmethod
    def get_active_tokens(cls):
        """Get all active, non-expired tokens"""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.is_active == True,
            cls.expires_at > now
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens from database"""
        now = datetime.utcnow()
        expired_count = cls.query.filter(
            cls.expires_at <= now
        ).delete()
        db.session.commit()
        return expired_count
    
    @classmethod
    def revoke_token_by_id(cls, token_id):
        """Revoke a token by its ID"""
        token = cls.query.get(token_id)
        if token:
            token.revoke()
            return True
        return False