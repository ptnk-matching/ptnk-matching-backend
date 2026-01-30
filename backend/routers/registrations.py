"""Registration routes for student professor preferences."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database.registration_repository import RegistrationRepository
from database.user_repository import UserRepository
from database.document_repository import DocumentRepository
from database.notification_repository import NotificationRepository
from services.s3_service import S3Service

router = APIRouter(prefix="/api/registrations", tags=["registrations"])
registration_repo = RegistrationRepository()
user_repo = UserRepository()
doc_repo = DocumentRepository()
notification_repo = NotificationRepository()
s3_service = S3Service() if S3Service else None


class CreateRegistrationRequest(BaseModel):
    """Request model for creating registration."""
    professor_id: str
    document_id: str
    priority: int = 1
    notes: Optional[str] = None


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized. Please provide X-User-Id header.")
    return user_id


@router.post("/")
async def create_registration(
    request: CreateRegistrationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new registration (student registers for professor)."""
    # Check if user is a student
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can register for professors")
    
    # Check if student already has a registration for this document
    # Students can only register for ONE professor per document
    existing_regs = await registration_repo.get_registrations_by_student(user_id)
    for reg in existing_regs:
        # Check if already registered for this document (regardless of professor)
        if reg.get("document_id") == request.document_id:
            raise HTTPException(
                status_code=400,
                detail="Bạn đã đăng ký một giảng viên cho tài liệu này. Mỗi học sinh chỉ được đăng ký 1 giảng viên."
            )
        # Also check if already registered for this specific professor
        if reg.get("professor_id") == request.professor_id and reg.get("document_id") == request.document_id:
            raise HTTPException(
                status_code=400,
                detail="Bạn đã đăng ký giảng viên này rồi."
            )
    
    # Create registration
    registration_data = {
        "student_id": user_id,
        "professor_id": request.professor_id,
        "document_id": request.document_id,
        "priority": request.priority,
        "status": "pending",
        "notes": request.notes
    }
    
    registration_id = await registration_repo.create_registration(registration_data)
    
    # Add to user's registrations
    await user_repo.add_registration_to_student(user_id, registration_id)
    
    # Create notification for professor
    try:
        from database.professor_profile_repository import ProfessorProfileRepository
        profile_repo = ProfessorProfileRepository()
        professor_profile = await profile_repo.get_profile_by_id(request.professor_id)
        if professor_profile:
            professor_user_id = professor_profile.get("user_id")
            student_name = user.get("name", "Một học sinh")
            document = await doc_repo.get_document_by_id(request.document_id)
            document_name = document.get("filename", "tài liệu") if document else "tài liệu"
            
            await notification_repo.create_notification({
                "user_id": professor_user_id,
                "type": "registration_request",
                "title": "Có học sinh đăng ký hướng dẫn",
                "message": f"{student_name} đã đăng ký hướng dẫn với tài liệu '{document_name}'",
                "related_user_id": user_id,
                "related_registration_id": str(registration_id),
                "related_document_id": request.document_id
            })
    except Exception as e:
        print(f"Warning: Could not create notification for professor: {e}")
    
    # Convert all values to JSON-serializable format
    response_data = {
        "success": True,
        "registration_id": str(registration_id),
        "student_id": str(registration_data["student_id"]),
        "professor_id": str(registration_data["professor_id"]),
        "document_id": str(registration_data["document_id"]),
        "priority": registration_data.get("priority", 1),
        "status": registration_data.get("status", "pending"),
        "notes": registration_data.get("notes")
    }
    
    return response_data


@router.get("/")
async def get_my_registrations(user_id: str = Depends(get_current_user_id)):
    """Get all registrations for current user."""
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") == "student":
        registrations = await registration_repo.get_registrations_by_student(user_id)
    elif user.get("role") == "professor":
        # For professors, we need to find their profile first, then get registrations
        # because professor_id in registration is profile ID, not user_id
        try:
            from database.professor_profile_repository import ProfessorProfileRepository
            profile_repo = ProfessorProfileRepository()
            profile = await profile_repo.get_profile_by_user_id(user_id)
            
            if profile:
                # Get registrations by profile ID
                profile_id = profile.get("id")
                registrations = await registration_repo.get_registrations_by_professor(profile_id)
            else:
                # No profile found, return empty list
                registrations = []
        except Exception as e:
            print(f"Error getting professor profile: {e}")
            # Fallback: try to get by user_id directly (for backward compatibility)
            registrations = await registration_repo.get_registrations_by_professor(user_id)
    else:
        raise HTTPException(status_code=403, detail="Invalid user role")
    
    # Enrich registrations with professor and document info
    from database.professors import ProfessorDatabase
    professor_db = ProfessorDatabase()
    
    enriched_registrations = []
    for reg in registrations:
        # Convert all ObjectId fields to string for JSON serialization
        enriched_reg = {}
        for key, value in reg.items():
            # Check if value is ObjectId
            if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                enriched_reg[key] = str(value)
            elif isinstance(value, datetime):
                # Convert datetime to ISO format string
                enriched_reg[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            else:
                enriched_reg[key] = value
        
        # Get professor info
        try:
            professor = professor_db.get_professor_by_id(reg.get("professor_id"))
            if professor:
                enriched_reg["professor_name"] = professor.get("name")
                enriched_reg["professor_title"] = professor.get("title")
                enriched_reg["professor_department"] = professor.get("department")
        except Exception as e:
            print(f"Warning: Could not get professor info: {e}")
        
        # Get professor email from profile or user
        try:
            from database.professor_profile_repository import ProfessorProfileRepository
            profile_repo = ProfessorProfileRepository()
            profile = await profile_repo.get_profile_by_id(reg.get("professor_id"))
            
            if profile:
                # Try to get email from profile first (contact_email)
                professor_email = profile.get("contact_email")
                
                # If no contact_email, get from user
                if not professor_email:
                    professor_user_id = profile.get("user_id")
                    if professor_user_id:
                        professor_user = await user_repo.get_user_by_id(professor_user_id)
                        if professor_user:
                            professor_email = professor_user.get("email")
                
                if professor_email:
                    enriched_reg["professor_email"] = professor_email
        except Exception as e:
            print(f"Warning: Could not get professor email: {e}")
        
        # Get document info (if available)
        try:
            from database.document_repository import DocumentRepository
            doc_repo = DocumentRepository()
            document = await doc_repo.get_document_by_id(reg.get("document_id"))
            if document:
                enriched_reg["document_filename"] = document.get("filename")
                enriched_reg["document_created_at"] = document.get("created_at")
        except Exception as e:
            print(f"Warning: Could not get document info: {e}")
        
        enriched_registrations.append(enriched_reg)
    
    return {"registrations": enriched_registrations, "count": len(enriched_registrations)}


@router.get("/{registration_id}")
async def get_registration(
    registration_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific registration."""
    registration = await registration_repo.get_registration_by_id(registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Check access (student or professor)
    user = await user_repo.get_user_by_id(user_id)
    if user.get("role") == "student" and registration.get("student_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if user.get("role") == "professor":
        # For professors, check by profile ID
        try:
            from database.professor_profile_repository import ProfessorProfileRepository
            profile_repo = ProfessorProfileRepository()
            profile = await profile_repo.get_profile_by_user_id(user_id)
            if profile:
                profile_id = profile.get("id")
                if registration.get("professor_id") != profile_id:
                    raise HTTPException(status_code=403, detail="Access denied")
            else:
                # Fallback: check by user_id directly
                if registration.get("professor_id") != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")
        except HTTPException:
            raise
        except Exception:
            # Fallback: check by user_id directly
            if registration.get("professor_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
    
    # Convert ObjectId to string for JSON serialization
    result = {}
    for key, value in registration.items():
        if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
        else:
            result[key] = value
    
    return result


class UpdateStatusRequest(BaseModel):
    """Request model for updating registration status."""
    status: str
    notes: Optional[str] = None
    reason: Optional[str] = None  # Lý do chấp nhận/từ chối


@router.put("/{registration_id}/status")
async def update_registration_status(
    registration_id: str,
    request: UpdateStatusRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update registration status (only professor can accept/reject)."""
    registration = await registration_repo.get_registration_by_id(registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Check if user is the professor
    user = await user_repo.get_user_by_id(user_id)
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only the professor can update status")
    
    # Get professor's profile ID (professor_id in registration is profile ID, not user_id)
    profile_id = None
    try:
        from database.professor_profile_repository import ProfessorProfileRepository
        profile_repo = ProfessorProfileRepository()
        profile = await profile_repo.get_profile_by_user_id(user_id)
        
        if profile:
            profile_id = profile.get("id")
            if registration.get("professor_id") != profile_id:
                raise HTTPException(status_code=403, detail="Only the professor can update status")
        else:
            # Fallback: check by user_id directly (for backward compatibility)
            if registration.get("professor_id") != user_id:
                raise HTTPException(status_code=403, detail="Only the professor can update status")
            profile_id = user_id
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking professor profile: {e}")
        # Fallback: check by user_id directly
        if registration.get("professor_id") != user_id:
            raise HTTPException(status_code=403, detail="Only the professor can update status")
        profile_id = user_id
    
    if request.status not in ["pending", "accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Check limit: professor can only accept maximum 2 students
    if request.status == "accepted" and profile_id:
        # Count current accepted registrations for this professor
        all_regs = await registration_repo.get_registrations_by_professor(profile_id)
        accepted_count = sum(1 for reg in all_regs if reg.get("status") == "accepted")
        
        # If this registration is already accepted, don't count it again
        if registration.get("status") != "accepted":
            accepted_count += 1
        
        if accepted_count > 2:
            raise HTTPException(
                status_code=400,
                detail="Mỗi giảng viên chỉ được hướng dẫn tối đa 2 học sinh. Vui lòng từ chối một đăng ký khác trước khi chấp nhận đăng ký này."
            )
    
    # Combine notes and reason
    combined_notes = request.notes or ""
    if request.reason:
        if combined_notes:
            combined_notes += f"\n\nLý do: {request.reason}"
        else:
            combined_notes = f"Lý do: {request.reason}"
    
    success = await registration_repo.update_registration_status(
        registration_id,
        request.status,
        combined_notes
    )
    
    return {
        "success": success,
        "status": request.status,
        "message": f"Đã {request.status == 'accepted' and 'chấp nhận' or 'từ chối'} đăng ký thành công"
    }


@router.delete("/{registration_id}")
async def delete_registration(
    registration_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a registration (only student can delete their own)."""
    registration = await registration_repo.get_registration_by_id(registration_id)
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Check ownership
    if registration.get("student_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await registration_repo.delete_registration(registration_id)
    return {"success": success}

