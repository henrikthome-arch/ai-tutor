"""
Mastery Tracking models for granular curriculum goal and knowledge component tracking
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint


class CurriculumGoal(db.Model):
    """
    Curriculum Goal model representing specific learning objectives.
    Each goal has a unique code and can contain multiple knowledge components.
    """
    __tablename__ = 'curriculum_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_code = db.Column(db.String(50), nullable=False, unique=True, index=True)  # e.g., "4.NBT.A.1"
    title = db.Column(db.String(200), nullable=False)  # Human-readable goal name
    description = db.Column(db.Text, nullable=True)  # Detailed description of the goal
    subject = db.Column(db.String(50), nullable=False)  # e.g., "Mathematics", "Science"
    grade_level = db.Column(db.Integer, nullable=False)  # Grade level this goal applies to
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    goal_kcs = db.relationship('GoalKC', back_populates='goal', lazy='dynamic', cascade='all, delete-orphan')
    student_goal_progress = db.relationship('StudentGoalProgress', back_populates='goal', lazy='dynamic', cascade='all, delete-orphan')
    student_kc_progress = db.relationship('StudentKCProgress', back_populates='goal', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CurriculumGoal {self.goal_code}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'goal_code': self.goal_code,
            'title': self.title,
            'description': self.description,
            'subject': self.subject,
            'grade_level': self.grade_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class GoalKC(db.Model):
    """
    Goal Knowledge Component model representing prerequisite knowledge for goals.
    This creates a many-to-many relationship between goals and knowledge components.
    """
    __tablename__ = 'goal_kcs'
    
    goal_id = db.Column(db.Integer, db.ForeignKey('curriculum_goals.id', ondelete='CASCADE'), nullable=False)
    kc_code = db.Column(db.String(100), nullable=False)  # e.g., "place-value-thousands"
    kc_name = db.Column(db.String(200), nullable=False)  # Human-readable KC name
    description = db.Column(db.Text, nullable=True)  # Detailed description of the knowledge component
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Composite primary key
    __table_args__ = (
        db.PrimaryKeyConstraint('goal_id', 'kc_code', name='pk_goal_kc'),
    )
    
    # Relationships
    goal = db.relationship('CurriculumGoal', back_populates='goal_kcs')
    
    def __repr__(self):
        return f'<GoalKC {self.goal_id}-{self.kc_code}: {self.kc_name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'goal_id': self.goal_id,
            'goal_code': self.goal.goal_code if self.goal else None,
            'kc_code': self.kc_code,
            'kc_name': self.kc_name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentGoalProgress(db.Model):
    """
    Student Goal Progress model tracking mastery percentage for each goal per student.
    Each student can have progress on multiple goals.
    """
    __tablename__ = 'student_goal_progress'
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('curriculum_goals.id', ondelete='CASCADE'), nullable=False)
    mastery_percentage = db.Column(db.Float, nullable=False, default=0.0)  # 0.0 to 100.0
    last_updated = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Composite primary key and constraints
    __table_args__ = (
        db.PrimaryKeyConstraint('student_id', 'goal_id', name='pk_student_goal_progress'),
        db.CheckConstraint('mastery_percentage >= 0.0 AND mastery_percentage <= 100.0', name='ck_goal_mastery_range'),
    )
    
    # Relationships
    student = db.relationship('Student', backref='goal_progress')
    goal = db.relationship('CurriculumGoal', back_populates='student_goal_progress')
    
    def __repr__(self):
        return f'<StudentGoalProgress student_id={self.student_id} goal_id={self.goal_id} mastery={self.mastery_percentage}%>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'goal_id': self.goal_id,
            'goal_code': self.goal.goal_code if self.goal else None,
            'goal_title': self.goal.title if self.goal else None,
            'mastery_percentage': self.mastery_percentage,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class StudentKCProgress(db.Model):
    """
    Student Knowledge Component Progress model tracking mastery for individual KCs per student.
    This provides granular tracking of prerequisite knowledge components.
    """
    __tablename__ = 'student_kc_progress'
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('curriculum_goals.id', ondelete='CASCADE'), nullable=False)
    kc_code = db.Column(db.String(100), nullable=False)  # Must match kc_code in goal_kcs table
    mastery_percentage = db.Column(db.Float, nullable=False, default=0.0)  # 0.0 to 100.0
    last_updated = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Composite primary key and constraints
    __table_args__ = (
        db.PrimaryKeyConstraint('student_id', 'goal_id', 'kc_code', name='pk_student_kc_progress'),
        db.CheckConstraint('mastery_percentage >= 0.0 AND mastery_percentage <= 100.0', name='ck_kc_mastery_range'),
        # Foreign key constraint to ensure kc_code exists for the goal
        db.ForeignKeyConstraint(
            ['goal_id', 'kc_code'], 
            ['goal_kcs.goal_id', 'goal_kcs.kc_code'],
            name='fk_student_kc_progress_goal_kc',
            ondelete='CASCADE'
        ),
    )
    
    # Relationships
    student = db.relationship('Student', backref='kc_progress')
    goal = db.relationship('CurriculumGoal', back_populates='student_kc_progress')
    
    def __repr__(self):
        return f'<StudentKCProgress student_id={self.student_id} goal_id={self.goal_id} kc_code={self.kc_code} mastery={self.mastery_percentage}%>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'goal_id': self.goal_id,
            'goal_code': self.goal.goal_code if self.goal else None,
            'kc_code': self.kc_code,
            'mastery_percentage': self.mastery_percentage,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class GoalPrerequisite(db.Model):
    """
    Goal Prerequisites model representing prerequisite knowledge components for goals.
    This establishes dependencies between goals and prerequisite knowledge components.
    """
    __tablename__ = 'goal_prerequisites'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('curriculum_goals.id', ondelete='CASCADE'), nullable=False)
    prerequisite_kc_code = db.Column(db.String(100), nullable=False)  # KC code that is prerequisite
    prerequisite_goal_id = db.Column(db.Integer, db.ForeignKey('curriculum_goals.id', ondelete='CASCADE'), nullable=True)  # Goal that contains the prerequisite KC
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Ensure unique combinations of goal and prerequisite KC
    __table_args__ = (
        UniqueConstraint('goal_id', 'prerequisite_kc_code', name='uix_goal_prerequisite_kc'),
    )
    
    # Relationships
    goal = db.relationship('CurriculumGoal', foreign_keys=[goal_id], backref='prerequisites')
    prerequisite_goal = db.relationship('CurriculumGoal', foreign_keys=[prerequisite_goal_id], backref='dependent_goals')
    
    def __repr__(self):
        return f'<GoalPrerequisite goal_id={self.goal_id} prerequisite_kc={self.prerequisite_kc_code}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'goal_code': self.goal.goal_code if self.goal else None,
            'prerequisite_kc_code': self.prerequisite_kc_code,
            'prerequisite_goal_id': self.prerequisite_goal_id,
            'prerequisite_goal_code': self.prerequisite_goal.goal_code if self.prerequisite_goal else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }