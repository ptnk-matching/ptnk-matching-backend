"""Repository for professor profile operations."""
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB


class ProfessorProfileRepository:
    """Repository for managing professor profiles."""
    
    def __init__(self):
        self.collection_name = "professor_profiles"
        self.db = MongoDB.get_database()
        self.collection = self.db[self.collection_name]
    
    async def get_collection(self):
        """Get MongoDB collection."""
        return self.collection
    
    async def create_profile(self, profile_data: Dict) -> str:
        """Create a new professor profile."""
        collection = await self.get_collection()
        
        # Generate profile text
        profile_text = self._generate_profile_text(profile_data)
        profile_data["profile_text"] = profile_text
        
        # Check completeness
        profile_data["is_complete"] = self._check_completeness(profile_data)
        
        # Set timestamps
        profile_data["created_at"] = datetime.utcnow()
        profile_data["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(profile_data)
        return str(result.inserted_id)
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[Dict]:
        """Get profile by user ID."""
        collection = await self.get_collection()
        profile = await collection.find_one({"user_id": user_id})
        if profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
        return profile
    
    async def get_profile_by_id(self, profile_id: str) -> Optional[Dict]:
        """Get profile by ID."""
        collection = await self.get_collection()
        try:
            profile = await collection.find_one({"_id": ObjectId(profile_id)})
            if profile:
                profile["id"] = str(profile["_id"])
                del profile["_id"]
            return profile
        except Exception:
            return None
    
    async def update_profile(self, user_id: str, update_data: Dict) -> bool:
        """Update professor profile."""
        collection = await self.get_collection()
        
        # Generate updated profile text
        existing = await self.get_profile_by_user_id(user_id)
        if existing:
            merged_data = {**existing, **update_data}
        else:
            merged_data = update_data
        
        profile_text = self._generate_profile_text(merged_data)
        update_data["profile_text"] = profile_text
        
        # Check completeness
        update_data["is_complete"] = self._check_completeness(merged_data)
        
        # Update timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def get_all_complete_profiles(self) -> List[Dict]:
        """Get all profiles that are complete enough for matching."""
        collection = await self.get_collection()
        profiles = await collection.find({"is_complete": True}).to_list(length=1000)
        for profile in profiles:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
        return profiles
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete professor profile."""
        collection = await self.get_collection()
        result = await collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
    
    def _generate_profile_text(self, profile_data: Dict) -> str:
        """Generate combined text for embedding."""
        parts = []
        
        if profile_data.get("name"):
            parts.append(f"Tên: {profile_data['name']}")
        if profile_data.get("title"):
            parts.append(f"Chức danh: {profile_data['title']}")
        if profile_data.get("department"):
            parts.append(f"Khoa/Bộ môn: {profile_data['department']}")
        if profile_data.get("bio"):
            parts.append(f"Tiểu sử: {profile_data['bio']}")
        if profile_data.get("research_interests"):
            interests = profile_data["research_interests"]
            if isinstance(interests, list):
                parts.append(f"Lĩnh vực nghiên cứu: {', '.join(interests)}")
        if profile_data.get("expertise_areas"):
            expertise = profile_data["expertise_areas"]
            if isinstance(expertise, list):
                parts.append(f"Chuyên môn: {', '.join(expertise)}")
        if profile_data.get("education"):
            parts.append(f"Học vấn: {profile_data['education']}")
        if profile_data.get("publications"):
            parts.append(f"Công trình nghiên cứu: {profile_data['publications']}")
        
        return "\n".join(parts)
    
    def _check_completeness(self, profile_data: Dict) -> bool:
        """Check if profile is complete enough for matching."""
        has_basic_info = bool(
            profile_data.get("name") and 
            profile_data.get("title") and 
            profile_data.get("department")
        )
        has_content = bool(
            profile_data.get("research_interests") or 
            profile_data.get("expertise_areas") or 
            profile_data.get("bio")
        )
        return has_basic_info and has_content

