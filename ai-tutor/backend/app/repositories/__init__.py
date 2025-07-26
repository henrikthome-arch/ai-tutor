"""
Repository layer package
"""

# Import repository modules
from . import student_repository
from . import student_profile_repository
from . import student_memory_repository
from . import session_repository
from . import analytics_repository
from . import system_log_repository
from . import token_repository
from . import school_repository
from . import curriculum_repository
from . import assessment_repository

# Create repository instances for easy import
__all__ = [
    'student_repository',
    'student_profile_repository',
    'student_memory_repository',
    'session_repository',
    'analytics_repository',
    'system_log_repository',
    'token_repository',
    'school_repository',
    'curriculum_repository',
    'assessment_repository'
]