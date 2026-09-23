import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException
from app.core.config import settings

# Initialize Cloudinary if credentials are provided
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

def validate_upload(file: UploadFile):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    
    # Ideally, we should check file size before uploading to memory, 
    # but FastAPI SpooledTemporaryFile handles it. 
    # For now we rely on the route reading the file size.
    return True

async def upload_file(file: UploadFile, folder: str = "mediconnect_reports") -> dict:
    if not settings.CLOUDINARY_CLOUD_NAME:
        # Mock behavior for local testing if no keys are provided
        return {
            "public_id": f"mock_{file.filename}",
            "secure_url": f"https://mock-cloudinary.com/{file.filename}",
            "bytes": 1024
        }
        
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        resource_type = "image" if file.content_type.startswith("image") else "raw"
        
        response = cloudinary.uploader.upload(
            contents,
            folder=folder,
            resource_type=resource_type,
            original_filename=file.filename
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading to Cloudinary: {str(e)}")

def delete_file(public_id: str, resource_type: str = "image"):
    if not settings.CLOUDINARY_CLOUD_NAME or public_id.startswith("mock_"):
        return True
        
    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return True
    except Exception:
        return False
