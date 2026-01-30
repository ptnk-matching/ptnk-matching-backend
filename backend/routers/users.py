"""User routes."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from database.user_repository import UserRepository
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])
user_repo = UserRepository()


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized. Please provide X-User-Id header.")
    return user_id


@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get current user profile."""
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/")
async def create_user(user_data: dict):
    """Create a new user or get existing user."""
    try:
        # Check if user already exists
        existing_user = await user_repo.get_user_by_google_id(user_data.get("google_id"))
        if existing_user:
            # User already exists - check role mismatch
            existing_role = existing_user.get("role")
            requested_role = user_data.get("role")
            
            # If roles don't match and user already has a role, reject role change
            if existing_role and requested_role and existing_role != requested_role:
                print(f"⚠️ Role mismatch: User {user_data.get('google_id')} tried to login as '{requested_role}' but database has '{existing_role}'. Keeping original role.")
                # Update other info but keep original role
                update_data = {}
                if user_data.get("email") and existing_user.get("email") != user_data.get("email"):
                    update_data["email"] = user_data.get("email")
                if user_data.get("name") and existing_user.get("name") != user_data.get("name"):
                    update_data["name"] = user_data.get("name")
                if user_data.get("avatar_url") and existing_user.get("avatar_url") != user_data.get("avatar_url"):
                    update_data["avatar_url"] = user_data.get("avatar_url")
                
                if update_data:
                    from datetime import datetime
                    update_data["updated_at"] = datetime.utcnow()
                    await user_repo.update_user(existing_user["id"], update_data)
                    updated_user = await user_repo.get_user_by_id(existing_user["id"])
                    return {"id": updated_user.get("id"), **updated_user, "role_mismatch": True, "original_role": existing_role}
                
                # Return existing user with role mismatch flag
                return {"id": existing_user.get("id"), **existing_user, "role_mismatch": True, "original_role": existing_role}
            
            # Update user info if needed (but keep original role)
            update_data = {}
            if user_data.get("email") and existing_user.get("email") != user_data.get("email"):
                update_data["email"] = user_data.get("email")
            if user_data.get("name") and existing_user.get("name") != user_data.get("name"):
                update_data["name"] = user_data.get("name")
            if user_data.get("avatar_url") and existing_user.get("avatar_url") != user_data.get("avatar_url"):
                update_data["avatar_url"] = user_data.get("avatar_url")
            
            # Only update role if user doesn't have one yet (first time setup)
            if not existing_role and requested_role:
                update_data["role"] = requested_role
            
            if update_data:
                from datetime import datetime
                update_data["updated_at"] = datetime.utcnow()
                await user_repo.update_user(existing_user["id"], update_data)
                updated_user = await user_repo.get_user_by_id(existing_user["id"])
                return {"id": updated_user.get("id"), **updated_user}
            
            # Return existing user with id
            return {"id": existing_user.get("id"), **existing_user}
        
        # Create new user (first time)
        user_id = await user_repo.create_user(user_data)
        # Get the created user to return full data
        created_user = await user_repo.get_user_by_id(user_id)
        return {"id": user_id, **created_user} if created_user else {"id": user_id, **user_data}
    except Exception as e:
        # If MongoDB connection fails, still return user data but log error
        import traceback
        print(f"ERROR creating user in MongoDB: {e}")
        traceback.print_exc()
        # Return user data anyway so frontend can continue
        # Frontend will use Google ID as fallback
        return {
            "id": user_data.get("google_id"),  # Use Google ID as fallback
            **user_data,
            "warning": "User not saved to database due to MongoDB connection error"
        }


@router.put("/me")
async def update_current_user(
    update_data: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Update current user profile."""
    success = await user_repo.update_user(user_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}

