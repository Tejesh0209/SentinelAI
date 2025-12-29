# backend/services/voice.py
from openai import AsyncOpenAI
import logging
import io
from typing import BinaryIO

logger = logging.getLogger(__name__)

class VoiceService:
    """Handle speech-to-text and text-to-speech"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("Voice service initialized")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en"
    ) -> str:
        """
        Convert speech to text
        
        Args:
            audio_data: Audio bytes (webm, mp3, wav, etc.)
            language: ISO language code
            
        Returns:
            Transcribed text
        """
        try:
            # Create file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"
            
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )
            
            logger.info(f"Audio transcribed: {len(transcript)} chars")
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    async def transcribe_with_timestamps(
        self,
        audio_data: bytes
    ) -> dict:
        """Transcribe with word-level timestamps"""
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"
            
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
            
            return transcript.model_dump()
            
        except Exception as e:
            logger.error(f"Transcription with timestamps error: {e}")
            raise
    
    async def synthesize(
        self,
        text: str,
        voice: str = "alloy"
    ) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: Text to synthesize
            voice: Voice ID (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Audio bytes (MP3)
        """
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            audio_bytes = response.content
            logger.info(f"Speech synthesized: {len(text)} chars")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            raise
    
    async def translate(self, audio_data: bytes) -> str:
        """Translate audio to English"""
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"
            
            translation = await self.client.audio.translations.create(
                model="whisper-1",
                file=audio_file
            )
            
            return translation.text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise