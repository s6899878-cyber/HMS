from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import base64
from app.services.openai_service import analyze_medicine_image
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/analyze")
async def analyze_medicine(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    try:
        contents = await file.read()
        b64_str = base64.b64encode(contents).decode("utf-8")
        content_type = file.content_type
        
        # Fallback for empty content type
        if not content_type:
            content_type = "image/jpeg"
            
        base64_image_data = f"data:{content_type};base64,{b64_str}"
        
        # Analyze using OpenAI
        ai_data = analyze_medicine_image(base64_image_data)
        
        return ai_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze medicine image: {str(e)}")
