"""
Curriculum-related models
"""

from app import db
from sqlalchemy.sql import func

class Curriculum(db.Model):
    """Curriculum model for educational frameworks"""
    __tablename__ = 'curriculums'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    curriculum_type = db.Column(db.String(50), nullable=True)  # e.g., 'Cambridge', 'IB', 'National'
    grade_levels = db.Column(db.JSON, nullable=True)  # Array of grade levels [1, 2, 3, 4, 5, 6]
    is_template = db.Column(db.Boolean, default=False, nullable=False)  # Template curriculum vs school-specific
    is_default = db.Column(db.Boolean, default=False, nullable=False)  # System-wide default curriculum
    created_by = db.Column(db.String(50), nullable=True)  # User who created it
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    curriculum_details = db.relationship('CurriculumDetail', back_populates='curriculum', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Curriculum {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'curriculum_type': self.curriculum_type,
            'grade_levels': self.grade_levels,
            'is_template': self.is_template,
            'is_default': self.is_default,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Subject(db.Model):
    """Subject model for academic subjects"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'Mathematics', 'History'
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # e.g., 'STEM', 'Language Arts', 'Arts'
    is_core = db.Column(db.Boolean, default=False, nullable=False)  # Core vs elective subject
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    curriculum_details = db.relationship('CurriculumDetail', back_populates='subject', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_core': self.is_core,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CurriculumDetail(db.Model):
    """CurriculumDetail model mapping subjects to curriculums by grade level"""
    __tablename__ = 'curriculum_details'
    
    id = db.Column(db.Integer, primary_key=True)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculums.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    learning_objectives = db.Column(db.JSON, nullable=True)  # Array of learning objectives
    assessment_criteria = db.Column(db.JSON, nullable=True)  # Array of assessment criteria
    recommended_hours_per_week = db.Column(db.Integer, nullable=True)  # Recommended weekly hours
    prerequisites = db.Column(db.JSON, nullable=True)  # Array of prerequisites
    resources = db.Column(db.JSON, nullable=True)  # Array of recommended resources
    goals_description = db.Column(db.Text, nullable=True)  # Natural language description of learning goals
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    curriculum = db.relationship('Curriculum', back_populates='curriculum_details')
    subject = db.relationship('Subject', back_populates='curriculum_details')
    student_subjects = db.relationship('StudentSubject', back_populates='curriculum_detail', lazy='dynamic')
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('curriculum_id', 'subject_id', 'grade_level', name='uix_curriculum_subject_grade'),
    )
    
    def __repr__(self):
        return f'<CurriculumDetail {self.curriculum.name if self.curriculum else "Unknown"} - {self.subject.name if self.subject else "Unknown"} Grade {self.grade_level}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'curriculum_id': self.curriculum_id,
            'curriculum_name': self.curriculum.name if self.curriculum else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'grade_level': self.grade_level,
            'is_mandatory': self.is_mandatory,
            'learning_objectives': self.learning_objectives,
            'assessment_criteria': self.assessment_criteria,
            'recommended_hours_per_week': self.recommended_hours_per_week,
            'prerequisites': self.prerequisites,
            'resources': self.resources,
            'goals_description': self.goals_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }