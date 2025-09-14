import asyncio
from shazamio import Shazam
from typing import Dict, Any
import tempfile
import os
from pydub import AudioSegment
import io
import logging

logger = logging.getLogger(__name__)

class ShazamService:
    def __init__(self):
        self.shazam = Shazam()
    
    async def recognize_audio_file(self, file_path: str) -> Dict[str, Any]:
        try:
           
            audio = AudioSegment.from_file(file_path)
            
            audio = audio.set_frame_rate(44100).set_channels(2)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                output_path = tmp.name
            
            audio.export(output_path, format="mp3", bitrate="192k")
            
            result = await self.shazam.recognize(output_path)
            
            try:
                os.unlink(output_path)
            except:
                pass
                
            return self._parse_result(result)
            
        except Exception as e:
            logger.error(f"Shazam recognition failed: {str(e)}")
            return {"status": "error", "message": f"Recognition failed: {str(e)}"}
    
    async def recognize_audio_bytes(self, audio_data: bytes) -> Dict[str, Any]:
        
        try:
      
            with tempfile.NamedTemporaryFile(suffix='.input', delete=False) as tmp:
                tmp.write(audio_data)
                input_path = tmp.name
            
            result = await self.recognize_audio_file(input_path)
            
            try:
                os.unlink(input_path)
            except:
                pass
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    

    
    def _parse_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        
        if not result or 'track' not in result:
            return {"status": "not_found", "message": "No match found"}
        
        track = result['track']

        streaming_links = {}
        if 'hub' in track:
            for action in track['hub'].get('actions', []):
                if action.get('type') == 'uri' and 'uri' in action:
                    service = action.get('name', 'unknown').lower()
                    streaming_links[service] = action['uri']
        
        lyrics = []
        if 'sections' in track:
            for section in track['sections']:
                if section.get('type') == 'LYRICS':
                    lyrics = section.get('text', [])
                    break
    
        metadata = {}

        if 'sections' in track:
            for section in track['sections']:
                if section.get('type') == 'METADATA':
                    for item in section.get('metadata', []):
                        if 'title' in item and 'text' in item:
                            metadata[item['title']] = item['text']
    

        return {
            "status": "success",
            "service": "Shazam",
            "result": {
                "title": track.get('title', 'Unknown'),
                "artist": track.get('subtitle', 'Unknown Artist'),
                "album": track.get('sections', [{}])[0].get('metadata', [{}])[0].get('text', 'Unknown Album'),
                "image_url": track.get('images', {}).get('coverart', ''),
                "streaming_links": streaming_links,
                "lyrics": lyrics,
                "metadata": metadata,
                "genre": track.get('genres', {}).get('primary', ''),
                "release_date": track.get('release_date', ''),
                "isrc": track.get('isrc', ''),
                "music_video_url": track.get('url', ''),
                "artist_images": {
                "coverart": track.get('images', {}).get('coverart', ''),
                'background': track.get('share', {}).get('image', ''),
                }
            }
        }

shazam_service = ShazamService()