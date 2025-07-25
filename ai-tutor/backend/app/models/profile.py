"""
Profile model - REMOVED

The Profile model has been migrated to direct fields in the Student model.
Profile data (interests, learning_preferences, motivational_triggers) is now 
stored directly in the students table as ARRAY columns.

This file is kept for reference but the model is no longer used.
"""

# Profile model has been removed - data migrated to Student model
# See ai-tutor/backend/app/models/student.py for the migrated profile fields:
# - interests = db.Column(db.ARRAY(db.String), default=[])
# - learning_preferences = db.Column(db.ARRAY(db.String), default=[])  
# - motivational_triggers = db.Column(db.ARRAY(db.String), default=[])