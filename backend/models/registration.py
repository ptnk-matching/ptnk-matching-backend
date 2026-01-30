"""Registration model for student professor preferences."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from models.user import PyObjectId


class Registration(BaseModel):
    """Student registration/preference for professor."""
    id: Optional[str] = None  # Store as string for Pydantic v2 compatibility
    student_id: str  # User ID of student
    professor_id: str  # Professor ID
    document_id: str  # Related document ID
    priority: int  # 1 = first choice, 2 = second choice, etc.
    status: str = "pending"  # pending, accepted, rejected
    notes: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

