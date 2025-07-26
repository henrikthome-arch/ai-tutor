"""
Student Memory repository for database operations
Manages scoped key-value memory storage for AI tutor personalization
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from app import db
from app.models.student_memory import StudentMemory, MemoryScope

def get_many(student_id: int, scope: Optional[MemoryScope] = None, include_expired: bool = False) -> List[Dict[str, Any]]:
    """
    Get memories for a student, optionally filtered by scope
    
    Args:
        student_id: The student ID
        scope: Optional memory scope filter
        include_expired: Whether to include expired memories
        
    Returns:
        List of memory dictionaries
    """
    try:
        query = StudentMemory.query.filter_by(student_id=student_id)
        
        # Filter by scope if provided
        if scope:
            query = query.filter_by(scope=scope)
        
        # Filter out expired memories unless explicitly requested
        if not include_expired:
            now = datetime.utcnow()
            query = query.filter(
                (StudentMemory.expires_at.is_(None)) | 
                (StudentMemory.expires_at > now)
            )
        
        # Order by creation date (newest first)
        query = query.order_by(StudentMemory.created_at.desc())
        
        memories = query.all()
        return [memory.to_dict() for memory in memories]
        
    except Exception as e:
        print(f"Error getting memories for student {student_id}: {e}")
        return []

def get_by_scope_grouped(student_id: int, include_expired: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get memories grouped by scope for easy categorization
    
    Args:
        student_id: The student ID
        include_expired: Whether to include expired memories
        
    Returns:
        Dictionary with scope names as keys and memory lists as values
    """
    try:
        memories = get_many(student_id, include_expired=include_expired)
        
        grouped = {}
        for memory in memories:
            scope = memory['scope']
            if scope not in grouped:
                grouped[scope] = []
            grouped[scope].append(memory)
        
        return grouped
        
    except Exception as e:
        print(f"Error getting grouped memories for student {student_id}: {e}")
        return {}

def get_by_key(student_id: int, memory_key: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific memory by key
    
    Args:
        student_id: The student ID
        memory_key: The memory key
        
    Returns:
        Memory dictionary or None if not found/expired
    """
    try:
        now = datetime.utcnow()
        memory = StudentMemory.query.filter_by(
            student_id=student_id,
            memory_key=memory_key
        ).filter(
            (StudentMemory.expires_at.is_(None)) | 
            (StudentMemory.expires_at > now)
        ).first()
        
        return memory.to_dict() if memory else None
        
    except Exception as e:
        print(f"Error getting memory '{memory_key}' for student {student_id}: {e}")
        return None

def set(student_id: int, memory_key: str, memory_value: str, scope: MemoryScope, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Set or update a memory entry using UPSERT logic
    
    Args:
        student_id: The student ID
        memory_key: The memory key
        memory_value: The memory value
        scope: The memory scope
        expires_at: Optional expiration datetime
        
    Returns:
        The created/updated memory dictionary
    """
    try:
        # Check for existing memory with the same key
        existing = StudentMemory.query.filter_by(
            student_id=student_id,
            memory_key=memory_key
        ).first()
        
        if existing:
            # Update existing memory
            existing.memory_value = memory_value
            existing.scope = scope
            existing.expires_at = expires_at
            existing.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✅ Updated memory '{memory_key}' for student {student_id}")
            return existing.to_dict()
        else:
            # Create new memory
            new_memory = StudentMemory(
                student_id=student_id,
                memory_key=memory_key,
                memory_value=memory_value,
                scope=scope,
                expires_at=expires_at
            )
            
            db.session.add(new_memory)
            db.session.commit()
            
            print(f"✅ Created memory '{memory_key}' for student {student_id}")
            return new_memory.to_dict()
            
    except Exception as e:
        db.session.rollback()
        print(f"Error setting memory '{memory_key}' for student {student_id}: {e}")
        raise e

def set_multiple(student_id: int, memories: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Set multiple memories in a single transaction
    
    Args:
        student_id: The student ID
        memories: Dictionary with memory_key as key and memory data as value
                 Each memory data should have: value, scope, expires_at (optional)
        
    Returns:
        List of created/updated memory dictionaries
    """
    try:
        results = []
        
        for memory_key, memory_data in memories.items():
            memory_value = memory_data['value']
            scope = MemoryScope(memory_data['scope']) if isinstance(memory_data['scope'], str) else memory_data['scope']
            expires_at = memory_data.get('expires_at')
            
            # Use individual set method for consistency
            result = set(student_id, memory_key, memory_value, scope, expires_at)
            results.append(result)
        
        print(f"✅ Set {len(memories)} memories for student {student_id}")
        return results
        
    except Exception as e:
        print(f"Error setting multiple memories for student {student_id}: {e}")
        raise e

def delete_key(student_id: int, memory_key: str) -> bool:
    """
    Delete a specific memory by key
    
    Args:
        student_id: The student ID
        memory_key: The memory key to delete
        
    Returns:
        True if deleted, False if not found
    """
    try:
        deleted_count = StudentMemory.query.filter_by(
            student_id=student_id,
            memory_key=memory_key
        ).delete()
        
        db.session.commit()
        
        if deleted_count > 0:
            print(f"✅ Deleted memory '{memory_key}' for student {student_id}")
            return True
        else:
            print(f"ℹ️ Memory '{memory_key}' not found for student {student_id}")
            return False
            
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting memory '{memory_key}' for student {student_id}: {e}")
        raise e

def delete_by_scope(student_id: int, scope: MemoryScope) -> int:
    """
    Delete all memories for a student by scope
    
    Args:
        student_id: The student ID
        scope: The memory scope to delete
        
    Returns:
        Number of memories deleted
    """
    try:
        deleted_count = StudentMemory.query.filter_by(
            student_id=student_id,
            scope=scope
        ).delete()
        
        db.session.commit()
        
        print(f"✅ Deleted {deleted_count} memories with scope '{scope.value}' for student {student_id}")
        return deleted_count
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting memories by scope '{scope.value}' for student {student_id}: {e}")
        raise e

def delete_expired() -> int:
    """
    Delete all expired memories system-wide
    
    Returns:
        Number of expired memories deleted
    """
    try:
        now = datetime.utcnow()
        deleted_count = StudentMemory.query.filter(
            StudentMemory.expires_at.isnot(None),
            StudentMemory.expires_at <= now
        ).delete()
        
        db.session.commit()
        
        print(f"✅ Deleted {deleted_count} expired memories system-wide")
        return deleted_count
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting expired memories: {e}")
        raise e

def delete_all_for_student(student_id: int) -> int:
    """
    Delete all memories for a student (GDPR compliance)
    
    Args:
        student_id: The student ID
        
    Returns:
        Number of memories deleted
    """
    try:
        deleted_count = StudentMemory.query.filter_by(student_id=student_id).delete()
        db.session.commit()
        
        print(f"✅ Deleted {deleted_count} memories for student {student_id}")
        return deleted_count
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting all memories for student {student_id}: {e}")
        raise e

def update_from_ai_delta(student_id: int, memory_delta: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Update student memories based on AI-generated delta changes
    
    Args:
        student_id: The student ID
        memory_delta: Dictionary with scope as key and memory updates as value
                     Example: {
                         "personal_fact": {"pet_name": "Buddy"},
                         "strategy_log": {"effective_method": "visual aids"}
                     }
        
    Returns:
        List of updated memory dictionaries
    """
    try:
        results = []
        
        for scope_str, memory_updates in memory_delta.items():
            # Convert string scope to enum
            try:
                scope = MemoryScope(scope_str)
            except ValueError:
                print(f"⚠️ Invalid memory scope '{scope_str}', skipping")
                continue
            
            # Set expiration based on scope policy
            expires_at = None
            if scope == MemoryScope.game_state:
                # Game states expire after 30 days
                from datetime import timedelta
                expires_at = datetime.utcnow() + timedelta(days=30)
            elif scope == MemoryScope.strategy_log:
                # Strategy logs expire after 365 days
                from datetime import timedelta
                expires_at = datetime.utcnow() + timedelta(days=365)
            # personal_fact has no expiration
            
            # Update each memory in this scope
            for memory_key, memory_value in memory_updates.items():
                # Convert non-string values to JSON strings
                if not isinstance(memory_value, str):
                    import json
                    memory_value = json.dumps(memory_value)
                
                result = set(student_id, memory_key, memory_value, scope, expires_at)
                results.append(result)
        
        print(f"✅ Updated {len(results)} memories from AI delta for student {student_id}")
        return results
        
    except Exception as e:
        print(f"Error updating memories from AI delta for student {student_id}: {e}")
        raise e

def get_memory_statistics() -> Dict[str, Any]:
    """
    Get system-wide memory statistics
    
    Returns:
        Dictionary with memory statistics
    """
    try:
        from sqlalchemy import func, distinct
        
        # Total memories
        total_memories = db.session.query(func.count(StudentMemory.id)).scalar()
        
        # Unique students with memories
        students_with_memories = db.session.query(func.count(distinct(StudentMemory.student_id))).scalar()
        
        # Memories by scope
        scope_counts = {}
        for scope in MemoryScope:
            count = db.session.query(func.count(StudentMemory.id))\
                             .filter_by(scope=scope).scalar()
            scope_counts[scope.value] = count
        
        # Expired memories count
        now = datetime.utcnow()
        expired_count = db.session.query(func.count(StudentMemory.id))\
                                 .filter(StudentMemory.expires_at.isnot(None),
                                        StudentMemory.expires_at <= now).scalar()
        
        # Average memories per student
        avg_memories = total_memories / students_with_memories if students_with_memories > 0 else 0
        
        return {
            'total_memories': total_memories,
            'students_with_memories': students_with_memories,
            'memories_by_scope': scope_counts,
            'expired_memories': expired_count,
            'average_memories_per_student': round(avg_memories, 2)
        }
        
    except Exception as e:
        print(f"Error getting memory statistics: {e}")
        return {
            'total_memories': 0,
            'students_with_memories': 0,
            'memories_by_scope': {},
            'expired_memories': 0,
            'average_memories_per_student': 0.0
        }