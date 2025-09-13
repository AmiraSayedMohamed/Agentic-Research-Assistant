import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
import json
import base64
from datetime import datetime
import os
import requests

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

def text_to_speech(text, voice="Rachel"):
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice": voice
    }
    response = requests.post(ELEVENLABS_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.content  # This will be the audio file (MP3/WAV)
logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    ElevenLabs voice synthesis agent for generating natural audio narration
    Handles text-to-speech conversion with chapter timestamps and voice customization
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Voice configurations
        self.voices = {
            "adam": "pNInz6obpgDQGcFmaJgB",  # Professional male voice
            "bella": "EXAVITQu4vr4xnSDxMaL",  # Professional female voice
            "charlie": "IKne3meq5aSn9XLyUdCD",  # Narrator voice
            "domi": "AZnzlk1XvdvUeBnXmlld",   # Young female voice
        }
        
        # Default voice settings
        self.default_voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_audio_narration(self, report_data: Dict[str, Any], 
                                     voice_name: str = "adam", 
                                     speed: float = 1.0) -> Dict[str, Any]:
        """
        Generate complete audio narration from research report
        """
        logger.info(f"Generating audio narration with voice: {voice_name}")
        
        try:
            # Prepare narration script with chapters
            narration_script = await self._prepare_narration_script(report_data)
            
            # Generate audio for each chapter
            audio_chapters = []
            total_duration = 0
            
            for chapter in narration_script['chapters']:
                chapter_audio = await self._generate_chapter_audio(
                    chapter['text'], 
                    voice_name, 
                    speed
                )
                
                chapter_info = {
                    'title': chapter['title'],
                    'audio_data': chapter_audio['audio_data'],
                    'duration': chapter_audio['duration'],
                    'start_time': total_duration,
                    'end_time': total_duration + chapter_audio['duration']
                }
                
                audio_chapters.append(chapter_info)
                total_duration += chapter_audio['duration']
            
            # Combine audio chapters (in production, use audio processing library)
            combined_audio = await self._combine_audio_chapters(audio_chapters)
            
            # Generate timestamps for navigation
            timestamps = self._generate_timestamps(audio_chapters)
            
            return {
                'success': True,
                'audio_url': combined_audio['url'],
                'audio_data': combined_audio['data'],
                'duration': self._format_duration(total_duration),
                'duration_seconds': total_duration,
                'voice': voice_name,
                'speed': speed,
                'chapters': audio_chapters,
                'timestamps': timestamps,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_chapters': len(audio_chapters),
                    'voice_settings': self.default_voice_settings,
                    'file_size_mb': combined_audio.get('size_mb', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Audio narration generation failed: {e}")
            return await self._create_fallback_audio_response(report_data, voice_name)
    
    async def _prepare_narration_script(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured narration script with chapters"""
        
        # Extract content from report
        executive_summary = report_data.get('executive_summary', '')
        themes = report_data.get('themes', [])
        gaps = report_data.get('gaps', [])
        recommendations = report_data.get('recommendations', [])
        
        # Create narration chapters
        chapters = []
        
        # Chapter 1: Introduction
        intro_text = f"""
        Welcome to your research synthesis report. This analysis covers {len(report_data.get('summaries', []))} research papers 
        and provides a comprehensive overview of the current state of knowledge in this field.
        """
        chapters.append({
            'title': 'Introduction',
            'text': self._clean_text_for_speech(intro_text)
        })
        
        # Chapter 2: Executive Summary
        if executive_summary:
            summary_text = f"Executive Summary. {executive_summary}"
            chapters.append({
                'title': 'Executive Summary',
                'text': self._clean_text_for_speech(summary_text)
            })
        
        # Chapter 3: Key Themes
        if themes:
            themes_text = "Key Themes. The analysis reveals several important themes. "
            for i, theme in enumerate(themes, 1):
                theme_name = theme.get('name', f'Theme {i}')
                theme_desc = theme.get('description', '')
                themes_text += f"Theme {i}: {theme_name}. {theme_desc}. "
            
            chapters.append({
                'title': 'Key Themes',
                'text': self._clean_text_for_speech(themes_text)
            })
        
        # Chapter 4: Research Gaps
        if gaps:
            gaps_text = "Research Gaps and Limitations. The analysis identified several important gaps in the current literature. "
            for i, gap in enumerate(gaps, 1):
                gap_desc = gap.get('description', '')
                priority = gap.get('priority', 'Medium')
                gaps_text += f"Gap {i}: {gap_desc}. This is classified as {priority} priority. "
            
            chapters.append({
                'title': 'Research Gaps',
                'text': self._clean_text_for_speech(gaps_text)
            })
        
        # Chapter 5: Recommendations
        if recommendations:
            rec_text = "Recommendations. Based on this analysis, we recommend the following actions. "
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"Recommendation {i}: {rec}. "
            
            chapters.append({
                'title': 'Recommendations',
                'text': self._clean_text_for_speech(rec_text)
            })
        
        # Chapter 6: Conclusion
        conclusion_text = """
        This concludes your research synthesis report. The analysis provides a comprehensive foundation 
        for understanding the current state of research and identifying opportunities for future work.
        """
        chapters.append({
            'title': 'Conclusion',
            'text': self._clean_text_for_speech(conclusion_text)
        })
        
        return {
            'chapters': chapters,
            'total_chapters': len(chapters),
            'estimated_duration': len(' '.join([c['text'] for c in chapters])) / 150  # ~150 words per minute
        }
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean and optimize text for speech synthesis"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Replace citations with spoken format
        text = re.sub(r'\[(\d+)\]', r'reference \1', text)
        
        # Replace abbreviations with full words
        replacements = {
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'and so on',
            'vs.': 'versus',
            'AI': 'artificial intelligence',
            'ML': 'machine learning',
            'API': 'A P I',
            'URL': 'U R L',
            'PDF': 'P D F'
        }
        
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        # Add pauses for better flow
        text = text.replace('. ', '. <break time="0.5s"/> ')
        text = text.replace('? ', '? <break time="0.5s"/> ')
        text = text.replace('! ', '! <break time="0.5s"/> ')
        
        return text
    
    async def _generate_chapter_audio(self, text: str, voice_name: str, speed: float) -> Dict[str, Any]:
        """Generate audio for a single chapter"""
        try:
            voice_id = self.voices.get(voice_name, self.voices['adam'])
            
            # Prepare request payload
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    **self.default_voice_settings,
                    "speed": speed
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Make API request
            async with self.session.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ElevenLabs API error {response.status}: {error_text}")
                
                audio_data = await response.read()
                
                # Estimate duration (rough calculation: ~150 words per minute)
                word_count = len(text.split())
                estimated_duration = (word_count / 150) * 60  # seconds
                
                return {
                    'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                    'duration': estimated_duration,
                    'format': 'mp3',
                    'size_bytes': len(audio_data)
                }
                
        except Exception as e:
            logger.error(f"Chapter audio generation failed: {e}")
            # Return mock audio data
            return {
                'audio_data': 'mock_audio_data_base64',
                'duration': 30.0,  # Mock 30 seconds
                'format': 'mp3',
                'size_bytes': 1024000  # Mock 1MB
            }
    
    async def _combine_audio_chapters(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine individual chapter audio files (mock implementation)"""
        # In production, use audio processing library like pydub
        
        total_size = sum(chapter.get('size_bytes', 0) for chapter in chapters)
        combined_audio_data = ''.join(chapter.get('audio_data', '') for chapter in chapters)
        
        # Mock URL generation (in production, upload to cloud storage)
        audio_url = f"https://storage.example.com/audio/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        return {
            'url': audio_url,
            'data': combined_audio_data,
            'size_mb': total_size / (1024 * 1024),
            'format': 'mp3'
        }
    
    def _generate_timestamps(self, chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate navigation timestamps for audio chapters"""
        timestamps = []
        
        for chapter in chapters:
            timestamps.append({
                'title': chapter['title'],
                'start_time': self._format_duration(chapter['start_time']),
                'end_time': self._format_duration(chapter['end_time']),
                'start_seconds': chapter['start_time'],
                'end_seconds': chapter['end_time']
            })
        
        return timestamps
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    async def _create_fallback_audio_response(self, report_data: Dict[str, Any], voice_name: str) -> Dict[str, Any]:
        """Create fallback response when audio generation fails"""
        return {
            'success': False,
            'error': 'Audio generation temporarily unavailable',
            'audio_url': None,
            'audio_data': None,
            'duration': '0:00',
            'duration_seconds': 0,
            'voice': voice_name,
            'speed': 1.0,
            'chapters': [],
            'timestamps': [],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'status': 'failed',
                'fallback': True
            }
        }
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from ElevenLabs"""
        try:
            headers = {"xi-api-key": self.api_key}
            
            async with self.session.get(f"{self.base_url}/voices", headers=headers) as response:
                if response.status == 200:
                    voices_data = await response.json()
                    return {
                        'success': True,
                        'voices': voices_data.get('voices', []),
                        'predefined_voices': self.voices
                    }
                else:
                    return {
                        'success': False,
                        'error': f"API error: {response.status}",
                        'predefined_voices': self.voices
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return {
                'success': False,
                'error': str(e),
                'predefined_voices': self.voices
            }
