"""Notification repository for MongoDB operations."""
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB


class NotificationRepository:
    """Repository for notification operations."""
    
    def __init__(self):
        self.db = MongoDB.get_database()
        self.collection = self.db.notifications
    
    async def create_notification(self, notification_data: dict) -> str:
        """Create a new notification."""
        notification_data['created_at'] = datetime.utcnow()
        notification_data['is_read'] = False
        result = await self.collection.insert_one(notification_data)
        return str(result.inserted_id)
    
    async def get_notifications_by_user(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get all notifications for a user, sorted by newest first."""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        notifications = []
        async for notif in cursor:
            notif['id'] = str(notif['_id'])
            del notif['_id']
            # Convert datetime to ISO format string with timezone info
            if 'created_at' in notif and isinstance(notif['created_at'], datetime):
                notif['created_at'] = notif['created_at'].isoformat() + 'Z'  # Add Z to indicate UTC
            notifications.append(notif)
        return notifications
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        count = await self.collection.count_documents({
            "user_id": user_id,
            "is_read": False
        })
        return count
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0
    
    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        result = await self.collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0
    
    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        result = await self.collection.delete_one({"_id": ObjectId(notification_id)})
        return result.deleted_count > 0

