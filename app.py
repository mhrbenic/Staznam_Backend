import os
import sys

ffmpeg_bin_dir = r"ffmpegd\bin"
if os.path.exists(ffmpeg_bin_dir):
    os.environ['PATH'] = ffmpeg_bin_dir + os.pathsep + os.environ['PATH']
    
from dotenv import load_dotenv
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File, HTTPException
from acrcloud.recognizer import ACRCloudRecognizer
import json
import requests
import tempfile
from services.shazam_service import shazam_service
import asyncio
from typing import Dict, Any

load_dotenv()

app = FastAPI()

@app.post("/recognize/shazam")
async def recognize_shazam(file: UploadFile = File(...)) -> Dict[str, Any]:
   
    try:
        audio_data = await file.read()
        
        if not file.filename or not file.filename.lower().endswith(('.mp3', '.wav', '.m4a')):
            raise HTTPException(status_code=400, detail="Only audio files are supported (MP3, WAV, M4A)")
        
        if len(audio_data) < 1024: 
            raise HTTPException(status_code=400, detail="File too small")
        
        if len(audio_data) > 10 * 1024 * 1024:  
            raise HTTPException(status_code=400, detail="File too large")
        
        result = await shazam_service.recognize_audio_bytes(audio_data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition error: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Music Recognition API",
        "endpoints": {
            "shazam": "/recognize/shazam (POST)",
            "acr": "/recognize/acr (POST)", 
            "audd": "/recognize/audd (POST)",
            "test": "/test-shazam (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)