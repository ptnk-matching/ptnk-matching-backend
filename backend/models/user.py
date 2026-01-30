"""User model for MongoDB."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId string")
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class User(BaseModel):
    """User model."""
    id: Optional[str] = None  # Store as string (MongoDB ObjectId converted to string)
    google_id: str  # Google OAuth ID
    email: EmailStr
    name: str
    role: str  # 'student' or 'professor'
    avatar_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class StudentProfile(User):
    """Student profile with additional fields."""
    uploads: List[str] = []  # List of upload document IDs
    registrations: List[str] = []  # List of registration IDs


class ProfessorProfile(User):
    """Professor profile with additional fields."""
    expertise: Optional[str] = None
    research_interests: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []
    publications: int = 0

