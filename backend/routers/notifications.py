"""Notification routes."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from database.notification_repository import NotificationRepository

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
notification_repo = NotificationRepository()


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized. Please provide X-User-Id header.")
    return user_id


@router.get("/")
async def get_my_notifications(user_id: str = Depends(get_current_user_id)):
    """Get all notifications for current user."""
    notifications = await notification_repo.get_notifications_by_user(user_id)
    unread_count = await notification_repo.get_unread_count(user_id)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "total": len(notifications)
    }


@router.get("/unread-count")
async def get_unread_count(user_id: str = Depends(get_current_user_id)):
    """Get unread notification count."""
    count = await notification_repo.get_unread_count(user_id)
    return {"unread_count": count}


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Mark a notification as read."""
    # Verify notification belongs to user
    notifications = await notification_repo.get_notifications_by_user(user_id)
    notification = next((n for n in notifications if n.get("id") == notification_id), None)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    success = await notification_repo.mark_as_read(notification_id)
    return {"success": success}


@router.put("/read-all")
async def mark_all_as_read(user_id: str = Depends(get_current_user_id)):
    """Mark all notifications as read."""
    success = await notification_repo.mark_all_as_read(user_id)
    return {"success": success, "message": "Đã đánh dấu tất cả thông báo là đã đọc"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a notification."""
    # Verify notification belongs to user
    notifications = await notification_repo.get_notifications_by_user(user_id)
    notification = next((n for n in notifications if n.get("id") == notification_id), None)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    success = await notification_repo.delete_notification(notification_id)
    return {"success": success}

