"""User repository for MongoDB operations."""
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB
from models.user import User, StudentProfile, ProfessorProfile


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self):
        self.db = MongoDB.get_database()
        self.collection = self.db.users
    
    async def create_user(self, user_data: dict) -> str:
        """Create a new user."""
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[dict]:
        """Get user by Google ID."""
        user = await self.collection.find_one({"google_id": google_id})
        if user:
            user['id'] = str(user['_id'])
            del user['_id']
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['id'] = str(user['_id'])
            del user['_id']
        return user
    
    async def update_user(self, user_id: str, update_data: dict) -> bool:
        """Update user."""
        update_data['updated_at'] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def add_upload_to_student(self, student_id: str, document_id: str) -> bool:
        """Add upload document ID to student profile."""
        result = await self.collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$push": {"uploads": document_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def add_registration_to_student(self, student_id: str, registration_id: str) -> bool:
        """Add registration ID to student profile."""
        result = await self.collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$push": {"registrations": registration_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

