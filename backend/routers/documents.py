"""Document routes."""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime
from services.document_processor import DocumentProcessor
from services.s3_service import S3Service
from database.document_repository import DocumentRepository
from database.user_repository import UserRepository
import os

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_repo = DocumentRepository()
user_repo = UserRepository()
document_processor = DocumentProcessor()

# Initialize S3 service (optional, will fail gracefully if not configured)
try:
    s3_service = S3Service()
except Exception as e:
    print(f"Warning: S3 service not available: {e}")
    s3_service = None


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    # Try to get from header
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        # Try from query param (for testing)
        user_id = request.query_params.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized. Please provide X-User-Id header.")
    return user_id


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Upload a document and save to S3 + MongoDB."""
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        
        # Extract text
        text = await document_processor.process_file(contents, file_ext)
        
        # Upload to S3 if available
        s3_url = None
        s3_key = None
        if s3_service:
            try:
                s3_url, s3_key = s3_service.upload_file(
                    file_content=contents,
                    filename=file.filename,
                    user_id=user_id,
                    file_type=file_ext[1:]  # Remove the dot
                )
            except Exception as e:
                print(f"Warning: Failed to upload to S3: {e}")
                # Continue without S3, store text only
        
        # Save to MongoDB
        document_data = {
            "user_id": user_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_type": file_ext[1:],
            "file_size": file_size,
            "s3_url": s3_url or "",
            "s3_key": s3_key or "",
            "extracted_text": text
        }
        
        document_id = await document_repo.create_document(document_data)
        
        # Add to user's uploads
        await user_repo.add_upload_to_student(user_id, document_id)
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "s3_url": s3_url,
            "text_length": len(text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_my_documents(user_id: str = Depends(get_current_user_id)):
    """Get all documents for current user."""
    documents = await document_repo.get_documents_by_user(user_id)
    return {"documents": documents, "count": len(documents)}


@router.get("/me")
async def get_my_documents_me(user_id: str = Depends(get_current_user_id)):
    """Get all documents for current user (alias for /)."""
    documents = await document_repo.get_documents_by_user(user_id)
    return {"documents": documents, "count": len(documents)}


@router.get("/{document_id}")
async def get_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific document."""
    # Prevent "me" from being treated as document_id
    if document_id == "me":
        raise HTTPException(status_code=400, detail="Use /api/documents/me to get your documents")
    
    document = await document_repo.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access: student can only see their own documents
    # Professor can see documents if they have a registration for it
    user = await user_repo.get_user_by_id(user_id)
    user_role = user.get("role") if user else None
    
    if user_role == "student":
        # Students can only see their own documents
        if document.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif user_role == "professor":
        # Professors can see documents if they have a registration for it
        try:
            from database.registration_repository import RegistrationRepository
            from database.professor_profile_repository import ProfessorProfileRepository
            
            registration_repo = RegistrationRepository()
            profile_repo = ProfessorProfileRepository()
            
            # Get professor's profile ID
            profile = await profile_repo.get_profile_by_user_id(user_id)
            if profile:
                profile_id = profile.get("id")
                # Check if there's a registration for this document and professor
                registrations = await registration_repo.get_registrations_by_professor(profile_id)
                has_access = any(reg.get("document_id") == document_id for reg in registrations)
                
                if not has_access:
                    raise HTTPException(status_code=403, detail="Access denied. You don't have a registration for this document.")
            else:
                raise HTTPException(status_code=403, detail="Professor profile not found")
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error checking professor access: {e}")
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Convert ObjectId to string for JSON serialization
    result = {}
    for key, value in document.items():
        if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
        else:
            result[key] = value
    
    return result


@router.get("/{document_id}/download")
async def get_document_download_url(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Get presigned URL for document download."""
    document = await document_repo.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access: student can only see their own documents
    # Professor can see documents if they have a registration for it
    user = await user_repo.get_user_by_id(user_id)
    user_role = user.get("role") if user else None
    
    if user_role == "student":
        # Students can only see their own documents
        if document.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif user_role == "professor":
        # Professors can see documents if they have a registration for it
        try:
            from database.registration_repository import RegistrationRepository
            from database.professor_profile_repository import ProfessorProfileRepository
            
            registration_repo = RegistrationRepository()
            profile_repo = ProfessorProfileRepository()
            
            # Get professor's profile ID
            profile = await profile_repo.get_profile_by_user_id(user_id)
            if profile:
                profile_id = profile.get("id")
                # Check if there's a registration for this document and professor
                registrations = await registration_repo.get_registrations_by_professor(profile_id)
                has_access = any(reg.get("document_id") == document_id for reg in registrations)
                
                if not has_access:
                    raise HTTPException(status_code=403, detail="Access denied. You don't have a registration for this document.")
            else:
                raise HTTPException(status_code=403, detail="Professor profile not found")
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error checking professor access: {e}")
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate presigned URL if S3 key exists
    s3_key = document.get("s3_key")
    if not s3_key:
        raise HTTPException(status_code=404, detail="File not found in S3")
    
    if not s3_service:
        raise HTTPException(status_code=503, detail="S3 service not available")
    
    try:
        # Generate presigned URL (valid for 1 hour)
        presigned_url = s3_service.get_presigned_url(s3_key, expiration=3600)
        return {
            "download_url": presigned_url,
            "filename": document.get("filename", "document"),
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating download URL: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a document."""
    document = await document_repo.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete from S3 if exists
    if s3_service and document.get("s3_key"):
        s3_service.delete_file(document["s3_key"])
    
    # Delete from MongoDB
    success = await document_repo.delete_document(document_id)
    return {"success": success}

