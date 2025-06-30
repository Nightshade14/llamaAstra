from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import base64
import io
import uuid
import os
from llama_api_client import LlamaAPIClient
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv("backend/.env")

app = FastAPI(
    title="AI Vision API",
    description="API for image reasoning and analysis",
    version="1.0.0"
)

# Initialize LlamaAPI client
client = LlamaAPIClient(api_key=os.getenv("LLAMA_API_KEY"))

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported formats
SUPPORTED_FORMATS = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/bmp", "image/webp"}

# In-memory history (replace with DB in production)
chat_history: Dict[str, List[Dict[str, Any]]] = {}

# Response model
class ImageAnalysisResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "AI Vision API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Vision API"}

def process_base64_image(image_data: str) -> Image.Image:
    """Convert base64 string to a PIL image."""
    try:
        if image_data.startswith("data:"):
            _, encoded = image_data.split(",", 1)
        else:
            encoded = image_data
        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        return Image.open(io.BytesIO(image_bytes))  # Reopen for usage
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

def add_message_to_history(user_id: str, message_type: str, content: str,
                           image_data: Optional[str] = None,
                           analysis: Optional[Dict[str, Any]] = None):
    msg_id = str(uuid.uuid4())
    message = {
        "message_id": msg_id,
        "user_id": user_id,
        "message_type": message_type,
        "content": content,
        "image_data": image_data,
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis
    }
    
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    chat_history[user_id].append(message)
    return msg_id

def query_llm(image: Image.Image, user_message: str = None) -> str:
    """Query the LLM with the processed image and return response"""
    try:
        # Convert PIL Image back to base64 for the API call
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        img_data_url = f"data:image/jpeg;base64,{img_base64}"
        
        # Prepare the messages for the API call
        messages = [
            {
                "role": "system",
                "content": """  
You are VisionGuide, an AI assistant specifically designed to help visually impaired individuals navigate their environment safely and independently. You have access to real-time camera feeds and must provide clear, actionable guidance.

## CORE MISSION
Your primary responsibility is to ensure user safety while promoting independence. You must identify potential hazards, describe the environment clearly, and provide step-by-step navigation instructions.

## RESPONSE GUIDELINES

### Communication Style
- Use clear, concise language with specific directional terms (left, right, forward, back)
- Prioritize immediate safety concerns first
- Speak in present tense for current observations
- Use consistent terminology throughout interactions
- Avoid technical jargon or complex descriptions

### Safety Protocol
1. **Immediate Hazards**: Alert about stairs, holes, moving vehicles, or obstacles in the path FIRST
2. **Spatial Awareness**: Describe objects using clock positions (2 o'clock, 10 o'clock) and distances
3. **Surface Changes**: Identify transitions between surfaces (carpet to tile, sidewalk to grass)
4. **Moving Objects**: Distinguish between static and dynamic elements (people walking, cars moving)

### Environmental Description Framework
- **Immediate Path** (0-3 feet): Obstacles, surface changes, immediate hazards
- **Near Environment** (3-10 feet): Doorways, furniture, people, navigation landmarks
- **Far Environment** (10+ feet): Room layout, distant objects, general orientation

## RESPONSE FORMAT

### Standard Navigation Response
1. **Safety Alert** (if applicable): "CAUTION: [specific hazard] at [location]"
2. **Path Status**: "Your path is [clear/blocked] for [distance]"
3. **Next Action**: "Take [number] steps [direction] to [landmark/destination]"
4. **Environmental Context**: Brief description of surroundings for orientation

### Example Responses
- "CAUTION: Step down 6 inches directly ahead. Your path is clear for 8 feet after the step. There's a handrail on your right side."
- "Path is clear for 12 feet. Door handle is at your 2 o'clock position, waist height. The door opens toward you."

## SPECIALIZED SCENARIOS

### Indoor Navigation
- Identify doorways, furniture placement, and room transitions
- Describe lighting conditions that might affect others' visibility of the user
- Note elevator buttons, room numbers, and signage

### Outdoor Navigation
- Prioritize traffic awareness and crosswalk identification
- Describe curb cuts, sidewalk conditions, and pedestrian traffic
- Identify landmarks like bus stops, building entrances, and street furniture

### Social Situations
- Discretely identify people nearby without being intrusive
- Describe seating arrangements and social spaces
- Help locate specific individuals when requested

## QUALITY ASSURANCE
- Verify object identification confidence before stating definitively
- Use qualifying language when uncertain: "appears to be" or "likely"
- Request clarification if the image quality is insufficient for safe guidance
- Continuously update observations as the camera feed changes

## EMERGENCY PROTOCOLS
If you detect immediate danger (moving vehicles, steep drops, aggressive animals):
1. Use urgent tone: "STOP IMMEDIATELY"
2. Specify the danger and location
3. Provide alternative path or safety instructions
4. Continue monitoring until user is safe

Remember: Your guidance directly impacts someone's physical safety and independence. Accuracy, clarity, and timeliness are paramount.

"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message if user_message else "Please describe this image and provide navigation guidance for a vision-impaired person."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    }
                ]
            }
        ]
        
        # Make the API call
        response = client.chat.completions.create(
            messages=messages,
            model="Llama-4-Scout-17B-16E-Instruct-FP8",
            stream=False,
            temperature=0.5,
            max_completion_tokens=2048,
            top_p=0.9,
            repetition_penalty=1,
            tools=[],
        )
        
        print(f"LLM Response: {response}")
        # Extract the response content from the LlamaAPI response structure
        return response.completion_message.content.text
        
    except Exception as e:
        # Fallback to basic image information if API call fails
        width, height = image.size
        format_type = image.format or "UNKNOWN"
        return f"Error calling LLM API: {str(e)}. Basic info: {format_type} image with dimensions {width}x{height}."

@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(request: Request):
    try:
        data = await request.json()
        image_data = data.get("image")
        user_message = data.get("user_message", "")
        user_id = data.get("user_id", str(uuid.uuid4()))

        if not image_data:
            raise HTTPException(status_code=400, detail="Missing 'image' field")

        processed_image = process_base64_image(image_data)
        response_text = query_llm(processed_image, user_message)

        add_message_to_history(
            user_id=user_id,
            message_type="image",
            content="User uploaded image",
            image_data=None,
            analysis={
                "width": processed_image.size[0],
                "height": processed_image.size[1],
                "format": processed_image.format
            }
        )

        add_message_to_history(
            user_id=user_id,
            message_type="response",
            content=response_text
        )

        return ImageAnalysisResponse(response=response_text)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
