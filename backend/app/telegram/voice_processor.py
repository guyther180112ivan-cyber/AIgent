import logging
import asyncio
import tempfile
import os
from typing import Optional, Dict, Any
from pathlib import Path

import aiofiles
import aiohttp
from pydub import AudioSegment
import speech_recognition as sr

from .exceptions import VoiceProcessingError

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Processes voice messages from Telegram for speech-to-text conversion.
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Configuration
        self.supported_formats = ['.ogg', '.wav', '.mp3', '.m4a']
        self.max_file_size = 20 * 1024 * 1024  # 20MB
        self.temp_dir = tempfile.gettempdir()
        
        # STT providers
        self.stt_providers = {
            'openai': self._transcribe_with_openai,
            'google': self._transcribe_with_google,
            'whisper_local': self._transcribe_with_whisper_local
        }
        
        # Default provider
        self.default_provider = 'openai'
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        provider: Optional[str] = None,
        language: str = 'en-US'
    ) -> Optional[str]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            provider: STT provider to use
            language: Language code
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Validate file
            if not await self._validate_audio_file(audio_file_path):
                raise VoiceProcessingError("Invalid audio file")
            
            # Convert to WAV format for compatibility
            wav_path = await self._convert_to_wav(audio_file_path)
            
            try:
                # Use specified provider or default
                provider = provider or self.default_provider
                
                if provider not in self.stt_providers:
                    logger.warning(f"Unknown provider {provider}, using default")
                    provider = self.default_provider
                
                # Transcribe using chosen provider
                transcribe_func = self.stt_providers[provider]
                text = await transcribe_func(wav_path, language)
                
                if text:
                    logger.info(f"Successfully transcribed audio using {provider}")
                    return text.strip()
                else:
                    logger.warning(f"No transcription result from {provider}")
                    return None
                    
            finally:
                # Clean up converted file
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise VoiceProcessingError(f"Failed to transcribe audio: {str(e)}")
    
    async def _validate_audio_file(self, file_path: str) -> bool:
        """Validate audio file."""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"Audio file too large: {file_size} bytes")
                return False
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Unsupported audio format: {file_ext}")
                return False
            
            # Try to load audio file
            audio = AudioSegment.from_file(file_path)
            if len(audio) == 0:
                logger.error("Audio file is empty")
                return False
            
            # Check duration (max 5 minutes)
            duration_seconds = len(audio) / 1000.0
            if duration_seconds > 300:  # 5 minutes
                logger.error(f"Audio too long: {duration_seconds} seconds")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio file: {str(e)}")
            return False
    
    async def _convert_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format."""
        try:
            # Generate output path
            output_path = os.path.join(
                self.temp_dir,
                f"converted_{os.path.basename(input_path)}.wav"
            )
            
            # Convert using pydub
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono and 16kHz for better STT
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            
            logger.info(f"Converted audio to WAV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            raise VoiceProcessingError(f"Failed to convert audio: {str(e)}")
    
    async def _transcribe_with_openai(self, wav_path: str, language: str) -> Optional[str]:
        """Transcribe using OpenAI Whisper API."""
        try:
            from ..core.config import settings
            
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
                return None
            
            # Read audio file
            async with aiofiles.open(wav_path, 'rb') as f:
                audio_data = await f.read()
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {settings.openai_api_key}'
            }
            
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            data.add_field('language', language.split('-')[0])  # Extract language code
            
            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('text')
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error transcribing with OpenAI: {str(e)}")
            return None
    
    async def _transcribe_with_google(self, wav_path: str, language: str) -> Optional[str]:
        """Transcribe using Google Speech Recognition."""
        try:
            # Use speech_recognition library
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
            
            # Recognize using Google Speech Recognition
            text = self.recognizer.recognize_google(
                audio_data,
                language=language
            )
            
            return text
            
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing with Google: {str(e)}")
            return None
    
    async def _transcribe_with_whisper_local(self, wav_path: str, language: str) -> Optional[str]:
        """Transcribe using local Whisper model."""
        try:
            # Import whisper (lazy loading)
            import whisper
            
            # Load model (use base model for balance of speed/accuracy)
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(
                wav_path,
                language=language.split('-')[0],  # Extract language code
                fp16=False  # Use FP32 for compatibility
            )
            
            return result.get('text')
            
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Error transcribing with Whisper: {str(e)}")
            return None
    
    async def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about audio file."""
        try:
            audio = AudioSegment.from_file(file_path)
            
            return {
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'file_size_bytes': os.path.getsize(file_path),
                'format': Path(file_path).suffix.lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return {}
    
    async def cleanup_temp_files(self):
        """Clean up temporary audio files."""
        try:
            temp_pattern = os.path.join(self.temp_dir, "voice_*.ogg")
            temp_pattern_converted = os.path.join(self.temp_dir, "converted_*.wav")
            
            import glob
            temp_files = glob.glob(temp_pattern) + glob.glob(temp_pattern_converted)
            
            for temp_file in temp_files:
                try:
                    # Remove files older than 1 hour
                    file_age = os.path.getctime(temp_file)
                    current_time = asyncio.get_event_loop().time()
                    
                    if current_time - file_age > 3600:  # 1 hour
                        os.remove(temp_file)
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                        
                except Exception as e:
                    logger.warning(f"Error cleaning up temp file {temp_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
    
    def set_provider(self, provider: str):
        """Set default STT provider."""
        if provider in self.stt_providers:
            self.default_provider = provider
            logger.info(f"Set STT provider to: {provider}")
        else:
            logger.warning(f"Unknown provider: {provider}")
    
    def get_supported_providers(self) -> list:
        """Get list of supported STT providers."""
        return list(self.stt_providers.keys())
    
    async def test_provider(self, provider: str) -> bool:
        """Test if a provider is available."""
        try:
            if provider == 'openai':
                from ..core.config import settings
                return bool(settings.openai_api_key)
            elif provider == 'google':
                # Test with a short audio
                test_audio = AudioSegment.silent(duration=1000)  # 1 second silence
                test_path = os.path.join(self.temp_dir, "test.wav")
                test_audio.export(test_path, format="wav")
                
                try:
                    with sr.AudioFile(test_path) as source:
                        self.recognizer.record(source)
                    return True
                finally:
                    if os.path.exists(test_path):
                        os.remove(test_path)
                        
            elif provider == 'whisper_local':
                try:
                    import whisper
                    whisper.load_model("tiny")  # Test with tiny model
                    return True
                except ImportError:
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing provider {provider}: {str(e)}")
            return False
