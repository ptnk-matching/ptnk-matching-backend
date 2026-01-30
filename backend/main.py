"""Main FastAPI application for professor matching system."""
import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from services.matching import MatchingService
from services.document_processor import DocumentProcessor
from database.professors import ProfessorDatabase
from database.mongodb import MongoDB
from routers import users, documents, registrations, notifications
try:
    from routers import professor_profile
except ImportError:
    professor_profile = None

app = FastAPI(
    title="Hạnh Matching API",
    description="Hệ thống đề xuất giảng viên phù hợp cho bài báo cáo",
    version="1.0.0"
)

# CORS middleware
# Get allowed origins from environment variable or default to all
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, set CORS_ORIGINS env var with comma-separated domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
# MatchingService requires OPENAI_API_KEY environment variable
try:
    matching_service = MatchingService()
except ValueError as e:
    print(f"Warning: {e}")
    print("Matching service will not be available until OPENAI_API_KEY is set.")
    matching_service = None

document_processor = DocumentProcessor()
professor_db = ProfessorDatabase()

# Initialize MongoDB (optional)
try:
    db = MongoDB.get_database()  # Test connection
    # Test connection asynchronously
    import asyncio
    async def test_connection():
        try:
            await db.command('ping')
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection test failed: {e}")
            raise
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, connection will be tested on first use
            print("MongoDB client initialized (connection will be tested on first use)")
        else:
            loop.run_until_complete(test_connection())
    except Exception as e:
        print(f"Warning: MongoDB connection issue: {e}")
        print("MongoDB will be attempted on first use")
    
    # Collections will be created automatically on first insert
    # No need to pre-create them
except Exception as e:
    print(f"Warning: MongoDB not available: {e}")
    print("Some features will not work without MongoDB")
    print("Make sure MONGODB_URI is set correctly in .env file")

# Register routers
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(registrations.router)
app.include_router(notifications.router)
if professor_profile:
    app.include_router(professor_profile.router)


class MatchRequest(BaseModel):
    """Request model for matching."""
    text: str
    top_k: Optional[int] = 5
    include_analysis: Optional[bool] = True


class MatchResponse(BaseModel):
    """Response model for matching results."""
    matches: List[dict]
    processed_text: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "hanh-matching"}


@app.get("/api/professors")
async def get_professors():
    """Get all professors."""
    professors = professor_db.get_all_professors()
    return {"professors": professors, "count": len(professors)}


@app.post("/api/upload")
async def upload_report(file: UploadFile = File(...)):
    """Upload and process student report."""
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
        
        # Process document
        text = await document_processor.process_file(contents, file_ext)
        
        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "length": len(text)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match", response_model=MatchResponse)
async def match_professors(request: MatchRequest):
    """Match professors based on report text."""
    try:
        if matching_service is None:
            raise HTTPException(
                status_code=503,
                detail="Matching service is not available. Please set OPENAI_API_KEY environment variable."
            )
        
        if not request.text or len(request.text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Text must be at least 50 characters long"
            )
        
        # Find matches
        matches = await matching_service.find_matches(
            text=request.text,
            top_k=request.top_k,
            include_analysis=request.include_analysis
        )
        
        return MatchResponse(
            matches=matches,
            processed_text=request.text[:200] + "..." if len(request.text) > 200 else request.text
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-and-match")
async def upload_and_match(
    request: Request,
    file: UploadFile = File(...), 
    top_k: int = 5,
    include_analysis: bool = True
):
    """Upload report and match professors in one request."""
    try:
        if matching_service is None:
            raise HTTPException(
                status_code=503,
                detail="Matching service is not available. Please set OPENAI_API_KEY environment variable."
            )
        
        # Get user ID from header (set by frontend)
        user_id = request.headers.get("X-User-Id")
        google_id = request.headers.get("X-Google-Id")
        # Debug: Log user_id
        print(f"DEBUG: Received X-User-Id header: {user_id}")
        print(f"DEBUG: Received X-Google-Id header: {google_id}")
        
        # If no MongoDB user_id, use Google ID as fallback
        # This allows the system to work even if MongoDB is not available
        if not user_id and google_id:
            user_id = google_id  # Use Google ID as temporary user_id
            print(f"DEBUG: Using Google ID as user_id: {user_id}")
        
        # Try to get MongoDB user_id from Google ID if we have it
        if google_id and user_id == google_id:
            try:
                from database.user_repository import UserRepository
                user_repo = UserRepository()
                user = await user_repo.get_user_by_google_id(google_id)
                if user:
                    user_id = user.get("id")
                    print(f"DEBUG: Found MongoDB user_id from Google ID: {user_id}")
            except Exception as e:
                print(f"DEBUG: Could not get MongoDB user from Google ID (will use Google ID): {e}")
                # Continue with Google ID as fallback
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name is required")
        
        # Read file content first (before processing)
        # We need to read it once and reuse it
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        contents = await file.read()
        file_size = len(contents)
        
        # Process document to extract text
        text = await document_processor.process_file(contents, file_ext)
        
        # Match professors
        match_request = MatchRequest(
            text=text, 
            top_k=top_k,
            include_analysis=include_analysis
        )
        match_result = await match_professors(match_request)
        
        # Validate match_result
        if not match_result or not hasattr(match_result, 'matches'):
            raise HTTPException(status_code=500, detail="Failed to get match results")
        
        # If user_id is provided and MongoDB is available, save document
        document_id = None
        if user_id:
            try:
                from database.document_repository import DocumentRepository
                from database.user_repository import UserRepository
                
                doc_repo = DocumentRepository()
                user_repo = UserRepository()
                
                # Upload to S3 if available
                s3_url = None
                s3_key = None
                try:
                    from services.s3_service import S3Service
                    s3_service = S3Service()
                    s3_url, s3_key = s3_service.upload_file(
                        file_content=contents,
                        filename=file.filename,
                        user_id=user_id,
                        file_type=file_ext[1:]
                    )
                    print(f"DEBUG: Uploaded to S3: {s3_url}")
                except Exception as e:
                    print(f"Warning: S3 upload failed (continuing without S3): {e}")
                    # Continue without S3 - not critical
                
                # Generate AI summary
                summary = None
                try:
                    from services.summarizer import DocumentSummarizer
                    summarizer = DocumentSummarizer()
                    summary = await summarizer.summarize_document(text)
                    print(f"DEBUG: ✅ Generated document summary")
                except Exception as e:
                    print(f"Warning: Could not generate summary: {e}")
                    # Continue without summary
                
                # Save to MongoDB (even without S3)
                document_data = {
                    "user_id": user_id,
                    "filename": file.filename or "unknown",
                    "original_filename": file.filename or "unknown",
                    "file_type": file_ext[1:] if file_ext else "",
                    "file_size": file_size,
                    "s3_url": s3_url or "",
                    "s3_key": s3_key or "",
                    "extracted_text": text[:10000] if text else "",  # Limit text size to avoid issues
                    "summary": summary,
                    "summary_created_at": datetime.utcnow().isoformat() if summary else None
                }
                document_id = await doc_repo.create_document(document_data)
                print(f"DEBUG: ✅ Created document in MongoDB: {document_id}")
                
                # Try to add to user's uploads (may fail if user doesn't exist yet)
                try:
                    await user_repo.add_upload_to_student(user_id, document_id)
                    print(f"DEBUG: ✅ Added document to user's uploads list")
                except Exception as e:
                    print(f"Warning: Could not add to user uploads (user may not exist yet): {e}")
                    # Continue anyway - document is saved
                    
            except Exception as e:
                print(f"ERROR: Failed to save document to database: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole request - return matches anyway
                print("Continuing without saving document to database")
        else:
            print(f"DEBUG: ⚠️ No user_id provided, skipping document save")
            print(f"DEBUG: Headers received: {dict(request.headers)}")
        
        # Ensure matches is a list
        matches_list = match_result.matches if match_result and hasattr(match_result, 'matches') else []
        if not isinstance(matches_list, list):
            matches_list = []
        
        return {
            "success": True,
            "filename": file.filename or "unknown",
            "matches": matches_list,
            "text_preview": match_result.processed_text if match_result and hasattr(match_result, 'processed_text') else text[:200] if text else "",
            "document_id": document_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ ERROR in upload_and_match: {str(e)}")
        print(f"Traceback:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

