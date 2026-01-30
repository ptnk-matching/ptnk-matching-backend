"""Document upload model."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from bson import ObjectId
from models.user import PyObjectId


class Document(BaseModel):
    """Document upload model."""
    id: Optional[str] = None  # Store as string for Pydantic v2 compatibility
    user_id: str  # User ID who uploaded
    filename: str
    original_filename: str
    file_type: str  # pdf, docx, doc, txt
    file_size: int  # in bytes
    s3_url: str  # AWS S3 URL
    s3_key: str  # S3 object key
    extracted_text: str
    summary: Optional[str] = None  # AI-generated summary
    summary_created_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class MatchResult(BaseModel):
    """Match result for a document."""
    document_id: str
    professor_id: str
    professor_name: str
    similarity_score: float
    match_percentage: float
    analysis: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

