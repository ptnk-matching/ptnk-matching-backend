"""Professor profile model."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from models.user import PyObjectId


class ProfessorProfile(BaseModel):
    """Professor profile model for matching."""
    id: Optional[str] = None  # Store as string for Pydantic v2 compatibility
    user_id: str  # Link to User collection
    name: str
    title: str  # e.g., "Giáo sư", "Phó Giáo sư", "Tiến sĩ"
    department: str  # Khoa/Bộ môn
    research_interests: List[str] = []  # Lĩnh vực nghiên cứu
    bio: str = ""  # Tiểu sử ngắn
    expertise_areas: List[str] = []  # Chuyên môn
    education: Optional[str] = None  # Học vấn
    publications: Optional[str] = None  # Công trình nghiên cứu
    contact_email: Optional[str] = None
    cv_url: Optional[str] = None  # URL to uploaded CV file (S3)
    cv_s3_key: Optional[str] = None  # S3 key for CV
    cv_extracted_text: Optional[str] = None  # Extracted text from CV
    profile_text: str = ""  # Combined text for embedding (auto-generated)
    is_complete: bool = False  # Whether profile is complete enough for matching
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
    
    def generate_profile_text(self) -> str:
        """Generate combined text for embedding."""
        parts = [
            f"Tên: {self.name}",
            f"Chức danh: {self.title}",
            f"Khoa/Bộ môn: {self.department}",
        ]
        
        if self.bio:
            parts.append(f"Tiểu sử: {self.bio}")
        
        if self.research_interests:
            parts.append(f"Lĩnh vực nghiên cứu: {', '.join(self.research_interests)}")
        
        if self.expertise_areas:
            parts.append(f"Chuyên môn: {', '.join(self.expertise_areas)}")
        
        if self.education:
            parts.append(f"Học vấn: {self.education}")
        
        if self.publications:
            parts.append(f"Công trình nghiên cứu: {self.publications}")
        
        return "\n".join(parts)
    
    def check_completeness(self) -> bool:
        """Check if profile is complete enough for matching."""
        # At minimum: name, title, department, and at least one research interest or expertise
        has_basic_info = bool(self.name and self.title and self.department)
        has_content = bool(
            self.research_interests or 
            self.expertise_areas or 
            self.bio
        )
        return has_basic_info and has_content

