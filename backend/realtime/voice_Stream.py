# backend/realtime/voice_stream.py
import asyncio
import base64
import io
import logging
from typing import Callable, Optional
from collections import deque
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class VoiceStreamHandler:
    """
    Handles real-time voice streaming with buffering and transcription
    """
    
    def __init__(
        self,
        api_key: str,
        buffer_duration: float = 2.0,  # seconds
        language: str = "en"
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.buffer_duration = buffer_duration
        self.language = language
        
        # Audio buffer
        self.audio_buffer = deque(maxlen=10)  # Keep last 10 chunks
        self.buffer_size = 0
        
        # Callbacks
        self.on_transcript: Optional[Callable] = None
        self.on_interim: Optional[Callable] = None
        
        logger.info(f"Voice stream handler initialized (buffer: {buffer_duration}s)")
    
    async def process_audio_chunk(
        self,
        audio_base64: str,
        chunk_timestamp: float
    ) -> Optional[str]:
        """
        Process incoming audio chunk
        
        Args:
            audio_base64: Base64 encoded audio data (WebM/Opus)
            chunk_timestamp: Client timestamp
            
        Returns:
            Transcript if buffer threshold reached, None otherwise
        """
        try:
            # Decode audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Add to buffer
            self.audio_buffer.append({
                'data': audio_bytes,
                'timestamp': chunk_timestamp,
                'size': len(audio_bytes)
            })
            self.buffer_size += len(audio_bytes)
            
            logger.debug(f"Audio chunk received: {len(audio_bytes)} bytes (buffer: {len(self.audio_buffer)} chunks)")
            
            # Check if we should transcribe
            # Transcribe when buffer has enough data (roughly every 2 seconds of audio)
            if len(self.audio_buffer) >= 2:  # Adjust based on chunk size
                return await self._transcribe_buffer()
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _transcribe_buffer(self) -> Optional[str]:
        """Transcribe accumulated audio buffer"""
        
        if not self.audio_buffer:
            return None
        
        try:
            # Combine all chunks
            combined_audio = b''.join(chunk['data'] for chunk in self.audio_buffer)
            
            logger.info(f"Transcribing buffer: {len(combined_audio)} bytes")
            
            # Create file-like object
            audio_file = io.BytesIO(combined_audio)
            audio_file.name = "audio.webm"
            
            # Transcribe
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=self.language,
                response_format="text"
            )
            
            # Clear buffer after successful transcription
            self.audio_buffer.clear()
            self.buffer_size = 0
            
            transcript_text = transcript.strip()
            if transcript_text:
                logger.info(f"Transcribed: '{transcript_text}'")
                return transcript_text
            
            return None
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Don't clear buffer on error - might retry
            return None
    
    async def transcribe_complete_audio(
        self,
        audio_base64: str
    ) -> str:
        """
        Transcribe a complete audio file (not streaming)
        
        Args:
            audio_base64: Complete audio file as base64
            
        Returns:
            Full transcript
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.webm"
            
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=self.language,
                response_format="text"
            )
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Complete audio transcription error: {e}")
            raise
    
    def reset_buffer(self):
        """Clear audio buffer"""
        self.audio_buffer.clear()
        self.buffer_size = 0
        logger.debug("Audio buffer reset")
    
    def get_buffer_stats(self) -> dict:
        """Get buffer statistics"""
        return {
            "chunks": len(self.audio_buffer),
            "total_bytes": self.buffer_size,
            "duration_estimate": len(self.audio_buffer) * self.buffer_duration
        }
    
    