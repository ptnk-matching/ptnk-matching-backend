"""Registration repository for MongoDB operations."""
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB


class RegistrationRepository:
    """Repository for registration operations."""
    
    def __init__(self):
        self.db = MongoDB.get_database()
        self.collection = self.db.registrations
    
    async def create_registration(self, registration_data: dict) -> str:
        """Create a new registration."""
        registration_data['created_at'] = datetime.utcnow()
        registration_data['updated_at'] = datetime.utcnow()
        result = await self.collection.insert_one(registration_data)
        return str(result.inserted_id)
    
    async def get_registration_by_id(self, registration_id: str) -> Optional[dict]:
        """Get registration by ID."""
        reg = await self.collection.find_one({"_id": ObjectId(registration_id)})
        if reg:
            reg['id'] = str(reg['_id'])
            del reg['_id']
        return reg
    
    async def get_registrations_by_student(self, student_id: str) -> List[dict]:
        """Get all registrations for a student."""
        cursor = self.collection.find({"student_id": student_id}).sort("priority", 1)
        registrations = []
        async for reg in cursor:
            reg['id'] = str(reg['_id'])
            del reg['_id']
            registrations.append(reg)
        return registrations
    
    async def get_registrations_by_professor(self, professor_id: str) -> List[dict]:
        """Get all registrations for a professor."""
        cursor = self.collection.find({"professor_id": professor_id}).sort("created_at", -1)
        registrations = []
        async for reg in cursor:
            reg['id'] = str(reg['_id'])
            del reg['_id']
            registrations.append(reg)
        return registrations
    
    async def update_registration_status(
        self,
        registration_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update registration status."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            update_data["notes"] = notes
        
        result = await self.collection.update_one(
            {"_id": ObjectId(registration_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_registration(self, registration_id: str) -> bool:
        """Delete a registration."""
        result = await self.collection.delete_one({"_id": ObjectId(registration_id)})
        return result.deleted_count > 0

