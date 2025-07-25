"""
School model
"""

from app import db
from sqlalchemy.sql import func

class School(db.Model):
    """School model"""
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    core_values = db.Column(db.Text, nullable=True)
    default_curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculums.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    students = db.relationship('Student', back_populates='school', lazy='dynamic')
    default_curriculum = db.relationship('Curriculum', foreign_keys=[default_curriculum_id])
    
    def __repr__(self):
        return f'<School {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'school_id': self.id,  # For backward compatibility
            'name': self.name,
            'country': self.country,
            'city': self.city,
            'description': self.description,
            'core_values': self.core_values,
            'default_curriculum_id': self.default_curriculum_id,
            'default_curriculum_name': self.default_curriculum.name if self.default_curriculum else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }