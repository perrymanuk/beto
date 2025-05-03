#!/usr/bin/env python3
"""
Script to fix the Google Cloud TTS adapter.

This script compares the original and simplified TTS adapter implementations
and creates a fixed version of the adapter that addresses the streaming issue.
"""

import os
import sys
import re
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fix_tts_adapter")

def read_file(path):
    """
    Read a file and return its contents.
    
    Args:
        path: Path to the file
        
    Returns:
        str: File contents
    """
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    """
    Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to {path}: {e}")
        return False

def fix_tts_adapter():
    """
    Fix the Google Cloud TTS adapter.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get paths
    project_root = Path(__file__).resolve().parent.parent
    original_adapter_path = project_root / "radbot" / "voice" / "google_cloud_tts_adapter.py"
    simplified_adapter_path = project_root / "radbot" / "voice" / "simplified_tts_adapter.py"
    fixed_adapter_path = project_root / "radbot" / "voice" / "google_cloud_tts_adapter.fixed.py"
    
    # Check if files exist
    if not original_adapter_path.exists():
        logger.error(f"Original adapter not found: {original_adapter_path}")
        return False
    
    if not simplified_adapter_path.exists():
        logger.error(f"Simplified adapter not found: {simplified_adapter_path}")
        return False
    
    # Read the files
    logger.info(f"Reading original adapter: {original_adapter_path}")
    original_content = read_file(original_adapter_path)
    
    logger.info(f"Reading simplified adapter: {simplified_adapter_path}")
    simplified_content = read_file(simplified_adapter_path)
    
    # Create the fixed adapter content
    fixed_content = original_content
    
    # Step 1: Update the imports
    import_pattern = r"from google\.cloud import texttospeech_v1.*"
    import_replacement = "from google.cloud import texttospeech  # Main API\nfrom google.cloud import texttospeech_v1  # For streaming support"
    fixed_content = re.sub(import_pattern, import_replacement, fixed_content)
    
    # Step 2: Update client creation
    client_creation_pattern = r"def create_google_cloud_tts_client.*?return None\n"
    client_creation_replacement = """def create_google_cloud_tts_client() -> Optional[texttospeech.TextToSpeechClient]:
    \"\"\"
    Create a Google Cloud TTS client.
    
    Returns:
        Optional[texttospeech.TextToSpeechClient]: TTS client or None if configuration is missing
    \"\"\"
    try:
        # Check for Google Cloud credentials
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            # Try to use default credentials
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, attempting to use default credentials")
        
        # Create the client using the standard module
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        logger.error(f"Failed to create Google Cloud TTS client: {e}")
        return None
"""
    fixed_content = re.sub(client_creation_pattern, client_creation_replacement, fixed_content, flags=re.DOTALL)
    
    # Step 3: Update stream_speech method
    stream_speech_pattern = r"async def stream_speech.*?# Don't re-raise to avoid unhandled exceptions in async generators\n"
    
    # Extract the stream_speech method from the simplified adapter
    simplified_synthesize_text = """    async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
        \"\"\"
        Stream text to speech using Google Cloud TTS.
        
        Args:
            text: Text to convert to speech
            
        Yields:
            bytes: Audio chunks as they are received
        \"\"\"
        if not text.strip():
            return
        
        logger.info(f"Streaming speech synthesis for: {text[:30]}...")
        
        # Check if we have a client
        if not self.client:
            logger.error("No Google Cloud TTS client available")
            return
        
        # Try streaming synthesis first
        try:
            # Check if streaming is supported
            if not hasattr(self.client, 'streaming_synthesize'):
                raise AttributeError("Client does not support streaming_synthesize")
            
            # Get voice and audio config
            voice_params = get_voice_selection_params()
            audio_config = get_audio_config()
            
            # Try to access the streaming API types
            try:
                # Set up streaming configuration
                streaming_config = texttospeech_v1.StreamingSynthesizeRequest(
                    streaming_config=texttospeech_v1.StreamingSynthesizeConfig(
                        voice=voice_params,
                        audio_config=audio_config
                    )
                )
                
                # Create text iterator for streaming
                # Use a single chunk to avoid generator issues
                text_chunks = [text]
                
                # Create request generator
                def request_generator():
                    # First yield the config
                    yield streaming_config
                    
                    # Then yield each text chunk
                    for chunk in text_chunks:
                        if chunk.strip():
                            yield texttospeech_v1.StreamingSynthesizeRequest(
                                input=texttospeech_v1.StreamingSynthesisInput(text=chunk)
                            )
                
                # Stream responses
                logger.info("Using streaming synthesis API")
                streaming_responses = self.client.streaming_synthesize(request_generator())
                
                # Process streaming responses
                for response in streaming_responses:
                    # Check if we should stop
                    if not self.running:
                        break
                        
                    # Yield audio content
                    if response.audio_content:
                        yield response.audio_content
                
                # If we get here without yielding anything, fall back to standard synthesis
                return
                
            except (ImportError, AttributeError) as e:
                # Failed to use streaming API, fall back to standard synthesis
                logger.warning(f"Streaming synthesis not available: {e}")
                raise
        
        except Exception as e:
            # If streaming fails for any reason, fall back to standard synthesis
            logger.warning(f"Error in streaming synthesis, falling back to standard synthesis: {e}")
            
            try:
                # Create synthesis input
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # Create voice selection
                voice = texttospeech.VoiceSelectionParams(
                    language_code=os.environ.get("GOOGLE_TTS_LANGUAGE_CODE", "en-US"),
                    name=os.environ.get("GOOGLE_TTS_VOICE_NAME", "en-US-Journey-F"),
                )
                
                # Create audio config
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    speaking_rate=float(os.environ.get("GOOGLE_TTS_SPEAKING_RATE", "1.0")),
                    pitch=float(os.environ.get("GOOGLE_TTS_PITCH", "0.0")),
                    volume_gain_db=float(os.environ.get("GOOGLE_TTS_VOLUME_GAIN_DB", "0.0")),
                )
                
                # Make the request
                logger.info("Performing standard synthesis...")
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                )
                
                # Yield the audio content
                if response.audio_content:
                    logger.info(f"Standard synthesis successful: {len(response.audio_content)} bytes")
                    yield response.audio_content
                else:
                    logger.warning("Standard synthesis returned no audio content")
            
            except Exception as inner_e:
                logger.error(f"Error in standard synthesis: {inner_e}")
        """
    
    fixed_content = re.sub(stream_speech_pattern, simplified_synthesize_text, fixed_content, flags=re.DOTALL)
    
    # Step 4: Update voice selection params
    voice_params_pattern = r"def get_voice_selection_params.*?    \)\n"
    voice_params_replacement = """def get_voice_selection_params() -> texttospeech_v1.VoiceSelectionParams:
    \"\"\"
    Get voice selection parameters from environment variables.
    
    Returns:
        texttospeech_v1.VoiceSelectionParams: Voice selection parameters
    \"\"\"
    language_code = os.environ.get("GOOGLE_TTS_LANGUAGE_CODE", "en-US")
    voice_name = os.environ.get("GOOGLE_TTS_VOICE_NAME", "en-US-Journey-F")
    
    # Create voice selection parameters using v1 module for streaming
    return texttospeech_v1.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )
"""
    fixed_content = re.sub(voice_params_pattern, voice_params_replacement, fixed_content, flags=re.DOTALL)
    
    # Step 5: Update audio config
    audio_config_pattern = r"def get_audio_config.*?    \)\n"
    audio_config_replacement = """def get_audio_config() -> texttospeech_v1.AudioConfig:
    \"\"\"
    Get audio configuration from environment variables.
    
    Returns:
        texttospeech_v1.AudioConfig: Audio configuration
    \"\"\"
    # Get audio parameters from environment variables
    audio_encoding_str = os.environ.get("GOOGLE_TTS_AUDIO_ENCODING", "LINEAR16")
    speaking_rate = float(os.environ.get("GOOGLE_TTS_SPEAKING_RATE", "1.0"))
    pitch = float(os.environ.get("GOOGLE_TTS_PITCH", "0.0"))
    volume_gain_db = float(os.environ.get("GOOGLE_TTS_VOLUME_GAIN_DB", "0.0"))
    
    # Map audio encoding string to enum
    audio_encoding_map = {
        "LINEAR16": texttospeech_v1.AudioEncoding.LINEAR16,
        "MP3": texttospeech_v1.AudioEncoding.MP3,
        "OGG_OPUS": texttospeech_v1.AudioEncoding.OGG_OPUS
    }
    
    audio_encoding = audio_encoding_map.get(
        audio_encoding_str, texttospeech_v1.AudioEncoding.LINEAR16
    )
    
    # Create audio configuration for streaming implementation
    return texttospeech_v1.AudioConfig(
        audio_encoding=audio_encoding,
        speaking_rate=speaking_rate,
        pitch=pitch,
        volume_gain_db=volume_gain_db
    )
"""
    fixed_content = re.sub(audio_config_pattern, audio_config_replacement, fixed_content, flags=re.DOTALL)
    
    # Step 6: Update class init method to include streaming check
    init_pattern = r"def __init__.*?            logger\.warning\(\"Google Cloud TTS client not available - check GOOGLE_APPLICATION_CREDENTIALS\"\)\n"
    init_replacement = """    def __init__(self, send_audio_callback: Optional[Callable[[bytes], Awaitable[None]]] = None):
        \"\"\"
        Initialize the Google Cloud TTS adapter.
        
        Args:
            send_audio_callback: Callback for sending audio to the client
        \"\"\"
        # Create the client
        self.client = create_google_cloud_tts_client()
        self.send_audio_callback = send_audio_callback
        self.text_queue = asyncio.Queue()
        self.current_text = ""
        self.running = False
        self.tts_task = None
        
        # Check if TTS is available
        if self.client:
            client_type = type(self.client).__name__
            logger.info(f"Google Cloud TTS client initialized ({client_type})")
            
            # Check if streaming is available
            try:
                if hasattr(self.client, 'streaming_synthesize'):
                    logger.info("Streaming synthesis API is available")
                else:
                    logger.warning("Streaming synthesis API not available - will fall back to standard synthesis")
            except Exception as e:
                logger.warning(f"Error checking streaming API: {e}")
        else:
            logger.warning("Google Cloud TTS client not available - check GOOGLE_APPLICATION_CREDENTIALS")
"""
    fixed_content = re.sub(init_pattern, init_replacement, fixed_content, flags=re.DOTALL)
    
    # Step 7: Update process_speech_text method to include better logging
    process_speech_pattern = r"async def _process_speech_text.*?            logger\.error\(f\"Error processing speech text: \{e\}\"\)\n"
    process_speech_replacement = """    async def _process_speech_text(self, text: str):
        \"\"\"Process a single text chunk for speech synthesis.\"\"\"
        try:
            logger.info(f"Processing speech text: {text[:30]}...")
            # Stream audio from Google Cloud TTS
            async for audio_chunk in self.stream_speech(text):
                if not self.running:
                    # Stop if we're no longer running
                    break
                    
                logger.debug(f"Received audio chunk of {len(audio_chunk)} bytes")
                if self.send_audio_callback:
                    # Send audio chunk to client
                    await self.send_audio_callback(audio_chunk)
                else:
                    # No callback, just log
                    logger.debug(f"Generated {len(audio_chunk)} bytes of audio")
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info("Speech processing cancelled")
            # Don't re-raise
        except Exception as e:
            logger.error(f"Error processing speech text: {e}")
"""
    fixed_content = re.sub(process_speech_pattern, process_speech_replacement, fixed_content, flags=re.DOTALL)
    
    # Write the fixed adapter
    logger.info(f"Writing fixed adapter to {fixed_adapter_path}")
    if write_file(fixed_adapter_path, fixed_content):
        logger.info("Successfully created fixed adapter")
        
        # Also create a backup of the original
        backup_path = original_adapter_path.with_suffix(".py.bak")
        logger.info(f"Creating backup of original adapter at {backup_path}")
        if write_file(backup_path, original_content):
            logger.info("Successfully created backup of original adapter")
            
            # Replace the original with the fixed version
            logger.info(f"Replacing original adapter with fixed version")
            if write_file(original_adapter_path, fixed_content):
                logger.info("Successfully replaced original adapter with fixed version")
                return True
            else:
                logger.error("Failed to replace original adapter with fixed version")
                return False
        else:
            logger.error("Failed to create backup of original adapter")
            return False
    else:
        logger.error("Failed to write fixed adapter")
        return False

if __name__ == "__main__":
    logger.info("Starting to fix TTS adapter...")
    if fix_tts_adapter():
        logger.info("Successfully fixed TTS adapter")
        exit(0)
    else:
        logger.error("Failed to fix TTS adapter")
        exit(1)
