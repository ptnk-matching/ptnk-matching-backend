"""Routes for professor profile management."""
import os
from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile
from typing import Optional
from pydantic import BaseModel
from database.professor_profile_repository import ProfessorProfileRepository
from database.user_repository import UserRepository
from services.document_processor import DocumentProcessor
from services.cv_extractor import CVExtractor
from services.s3_service import S3Service

router = APIRouter(prefix="/api/professor-profile", tags=["professor-profile"])
profile_repo = ProfessorProfileRepository()
user_repo = UserRepository()


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized. Please provide X-User-Id header.")
    return user_id


class ProfileCreateRequest(BaseModel):
    """Request model for creating/updating profile."""
    name: str
    title: str
    department: str
    research_interests: list[str] = []
    bio: str = ""
    expertise_areas: list[str] = []
    education: Optional[str] = None
    publications: Optional[str] = None
    contact_email: Optional[str] = None


@router.get("/")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """Get current user's professor profile."""
    # Check if user is professor
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only professors can access this endpoint")
    
    profile = await profile_repo.get_profile_by_user_id(user_id)
    if not profile:
        return {"profile": None, "exists": False}
    
    return {"profile": profile, "exists": True}


@router.post("/")
async def create_profile(
    request: ProfileCreateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create or update professor profile."""
    # Check if user is professor
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only professors can create profiles")
    
    profile_data = {
        "user_id": user_id,
        "name": request.name,
        "title": request.title,
        "department": request.department,
        "research_interests": request.research_interests,
        "bio": request.bio,
        "expertise_areas": request.expertise_areas,
        "education": request.education,
        "publications": request.publications,
        "contact_email": request.contact_email or user.get("email"),
    }
    
    # Check if profile exists
    existing = await profile_repo.get_profile_by_user_id(user_id)
    if existing:
        # Update existing profile
        success = await profile_repo.update_profile(user_id, profile_data)
        if success:
            updated_profile = await profile_repo.get_profile_by_user_id(user_id)
            return {
                "success": True,
                "message": "Profile updated successfully",
                "profile": updated_profile
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
    else:
        # Create new profile
        profile_id = await profile_repo.create_profile(profile_data)
        new_profile = await profile_repo.get_profile_by_id(profile_id)
        return {
            "success": True,
            "message": "Profile created successfully",
            "profile": new_profile
        }


@router.put("/")
async def update_profile(
    request: ProfileCreateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Update professor profile."""
    # Check if user is professor
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only professors can update profiles")
    
    profile_data = {
        "name": request.name,
        "title": request.title,
        "department": request.department,
        "research_interests": request.research_interests,
        "bio": request.bio,
        "expertise_areas": request.expertise_areas,
        "education": request.education,
        "publications": request.publications,
        "contact_email": request.contact_email or user.get("email"),
    }
    
    success = await profile_repo.update_profile(user_id, profile_data)
    if success:
        updated_profile = await profile_repo.get_profile_by_user_id(user_id)
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": updated_profile
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.delete("/")
async def delete_profile(user_id: str = Depends(get_current_user_id)):
    """Delete professor profile."""
    # Check if user is professor
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only professors can delete profiles")
    
    success = await profile_repo.delete_profile(user_id)
    if success:
        return {"success": True, "message": "Profile deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Profile not found")


@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Upload CV and extract profile information using AI."""
    # Check if user is professor
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "professor":
        raise HTTPException(status_code=403, detail="Only professors can upload CVs")
    
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.docx', '.doc', '.txt']:
        raise HTTPException(
            status_code=400,
            detail="File type not supported. Please upload PDF, DOCX, DOC, or TXT file."
        )
    
    try:
        # Read file content
        contents = await file.read()
        
        # Process document to extract text
        document_processor = DocumentProcessor()
        text = await document_processor.process_file(contents, file_ext)
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from CV. Please ensure the file is readable."
            )
        
        # Extract profile information using AI
        cv_extractor = CVExtractor()
        extracted_data = await cv_extractor.extract_from_cv(text)
        
        # Upload CV to S3
        s3_url = None
        s3_key = None
        try:
            s3_service = S3Service()
            s3_url, s3_key = s3_service.upload_file(
                file_content=contents,
                filename=file.filename,
                user_id=user_id,
                file_type=file_ext[1:] if file_ext.startswith('.') else file_ext
            )
        except Exception as e:
            print(f"Warning: S3 upload failed (continuing without S3): {e}")
        
        # Get or create profile
        profile = await profile_repo.get_profile_by_user_id(user_id)
        
        # Prepare profile data from extracted information
        profile_data = {
            "user_id": user_id,
            "name": extracted_data.get("name") or user.get("name", ""),
            "title": extracted_data.get("title") or "",
            "department": extracted_data.get("department") or "",
            "research_interests": extracted_data.get("research_interests", []),
            "bio": extracted_data.get("bio") or extracted_data.get("summary") or "",
            "expertise_areas": extracted_data.get("expertise_areas", []),
            "education": extracted_data.get("education") or "",
            "publications": extracted_data.get("publications") or "",
            "contact_email": extracted_data.get("email") or user.get("email"),
            "cv_url": s3_url or "",
            "cv_text": text[:10000],  # Store first 10000 chars
        }
        
        if profile:
            # Update existing profile
            await profile_repo.update_profile(user_id, profile_data)
            updated_profile = await profile_repo.get_profile_by_user_id(user_id)
            return {
                "success": True,
                "message": "CV uploaded and profile updated successfully",
                "profile": updated_profile,
                "extracted_data": extracted_data
            }
        else:
            # Create new profile
            profile_id = await profile_repo.create_profile(profile_data)
            new_profile = await profile_repo.get_profile_by_id(profile_id)
            return {
                "success": True,
                "message": "CV uploaded and profile created successfully",
                "profile": new_profile,
                "extracted_data": extracted_data
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing CV: {str(e)}"
        )

