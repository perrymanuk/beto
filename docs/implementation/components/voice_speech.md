# Voice and Speech Subsystem

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document details the implementation of voice and speech capabilities in the RadBot framework, covering both the core speech subsystem and voice integration with the ADK streaming functionality.

## 1. Core Speech Subsystem

The speech subsystem consists of three primary elements:

1. **Speech-to-Text (STT)**: Converts spoken audio to text using Whisper
2. **Text-to-Speech (TTS)**: Converts text to speech using TTS engines
3. **Voice Activity Detection (VAD)**: Detects when speech is present in audio

### Speech Subsystem Implementation

```python
# radbot/speech/speech_system.py

import logging
import os
import tempfile
from typing import Optional, Tuple

import numpy as np
import soundfile as sf
import torch
import whisper
from TTS.api import TTS

class SpeechSystem:
    def __init__(self, whisper_model="base", language="en"):
        """
        Initialize the speech subsystem.
        
        Args:
            whisper_model: Whisper model size ("tiny", "base", "small", "medium", "large")
            language: Default language code
        """
        self.language = language
        
        # Initialize Whisper model
        logging.info(f"Loading Whisper {whisper_model} model...")
        self.whisper_model = whisper.load_model(whisper_model)
        
        # Initialize TTS model
        logging.info("Loading TTS model...")
        self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC")
        
        logging.info("Speech subsystem initialized")
    
    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe speech from an audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            logging.info(f"Transcribing audio from {audio_path}")
            
            # Transcribe using Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                language=self.language,
                initial_prompt="This is a conversation with a personal assistant."
            )
            
            # Return transcribed text
            return result["text"].strip()
        except Exception as e:
            logging.error(f"Error transcribing audio: {str(e)}")
            raise SpeechProcessingError(f"Failed to transcribe audio: {str(e)}")
    
    async def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file
            
        Returns:
            Path to audio file
        """
        try:
            # Create temp file if output_path not provided
            if output_path is None:
                fd, output_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
            
            logging.info(f"Synthesizing speech to {output_path}")
            
            # Generate speech with TTS
            self.tts_model.tts_to_file(
                text=text,
                file_path=output_path
            )
            
            return output_path
        except Exception as e:
            logging.error(f"Error synthesizing speech: {str(e)}")
            raise SpeechProcessingError(f"Failed to synthesize speech: {str(e)}")
    
    def detect_speech(self, audio_data: np.ndarray, sample_rate: int = 16000, threshold: float = 0.5) -> bool:
        """
        Detect if speech is present in audio data.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            threshold: Energy threshold for speech detection
            
        Returns:
            True if speech is detected, False otherwise
        """
        try:
            # Calculate audio energy
            energy = np.mean(np.abs(audio_data))
            
            # Compare to threshold
            return energy > threshold
        except Exception as e:
            logging.error(f"Error detecting speech: {str(e)}")
            return False
    
    async def transcribe_stream(self, audio_chunks: list, sample_rate: int = 16000) -> str:
        """
        Transcribe speech from a stream of audio chunks.
        
        Args:
            audio_chunks: List of audio chunks as numpy arrays
            sample_rate: Audio sample rate
            
        Returns:
            Transcribed text
        """
        try:
            # Combine audio chunks
            audio_data = np.concatenate(audio_chunks)
            
            # Save to temporary file
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            
            sf.write(temp_path, audio_data, sample_rate)
            
            # Transcribe
            result = await self.transcribe(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            
            return result
        except Exception as e:
            logging.error(f"Error transcribing audio stream: {str(e)}")
            raise SpeechProcessingError(f"Failed to transcribe audio stream: {str(e)}")


class SpeechProcessingError(Exception):
    """Exception raised for errors in speech processing."""
    pass
```

### Integration with Agent Framework

```python
# radbot/agent.py (extension)

class RadbotAgent:
    # Existing code...
    
    async def process_voice_input(self, audio_path: str) -> str:
        """
        Process voice input and return a response.
        
        Args:
            audio_path: Path to audio file with speech input
            
        Returns:
            Agent response as text
        """
        try:
            # Create speech system if not already initialized
            if not hasattr(self, 'speech_system'):
                from radbot.speech.speech_system import SpeechSystem
                self.speech_system = SpeechSystem()
                
            # Transcribe speech to text
            text_input = await self.speech_system.transcribe(audio_path)
            
            # Process text input
            response = self.process_message(user_id="voice_user", message=text_input)
            
            return response
        except Exception as e:
            logging.error(f"Voice processing error: {str(e)}")
            return "I'm sorry, but I had trouble understanding that. Could you try again?"
    
    async def generate_voice_response(self, response_text: str) -> str:
        """
        Generate speech for a response.
        
        Args:
            response_text: Text to convert to speech
            
        Returns:
            Path to audio file with synthesized speech
        """
        try:
            # Create speech system if not already initialized
            if not hasattr(self, 'speech_system'):
                from radbot.speech.speech_system import SpeechSystem
                self.speech_system = SpeechSystem()
                
            # Synthesize speech
            audio_path = await self.speech_system.synthesize(response_text)
            
            return audio_path
        except Exception as e:
            logging.error(f"Speech synthesis error: {str(e)}")
            return None
```

### Web API Integration

For web application integration, FastAPI endpoints were implemented:

```python
# radbot/api/speech_endpoints.py

from fastapi import APIRouter, File, UploadFile, HTTPException
import base64
import os
import tempfile
import logging
from typing import Dict, Any, Optional

from radbot.agent import create_agent

router = APIRouter()

@router.post("/api/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Transcribe audio to text.
    
    Args:
        file: Audio file upload
        
    Returns:
        Transcribed text
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            # Write uploaded file to temporary file
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Get agent instance
        agent = create_agent()
        
        # Process voice input
        text = await agent.process_voice_input(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return {"text": text}
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/voice/synthesize")
async def synthesize_speech(text: str) -> Dict[str, str]:
    """
    Convert text to speech.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Base64-encoded audio
    """
    try:
        # Get agent instance
        agent = create_agent()
        
        # Generate speech
        audio_path = await agent.generate_voice_response(text)
        
        if not audio_path:
            raise HTTPException(status_code=500, detail="Speech synthesis failed")
        
        # Read audio file and encode as base64
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        # Clean up
        os.unlink(audio_path)
        
        return {"audio": audio_base64}
    except Exception as e:
        logging.error(f"Speech synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/voice/process")
async def process_voice(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Process voice input and return response with speech.
    
    Args:
        file: Audio file upload
        
    Returns:
        Response with text and audio
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            # Write uploaded file to temporary file
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Get agent instance
        agent = create_agent()
        
        # Process voice input
        text_response = await agent.process_voice_input(tmp_path)
        
        # Generate speech response
        audio_path = await agent.generate_voice_response(text_response)
        
        # Clean up input file
        os.unlink(tmp_path)
        
        # Process audio response
        if audio_path:
            # Read audio file and encode as base64
            with open(audio_path, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # Clean up
            os.unlink(audio_path)
            
            return {
                "text": text_response,
                "audio": audio_base64
            }
        else:
            return {
                "text": text_response,
                "audio": None
            }
    except Exception as e:
        logging.error(f"Voice processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Model Optimization

For optimal performance on different hardware, model selection was implemented:

```python
# radbot/speech/model_optimizer.py

import torch
import logging
from typing import Dict, Any, Optional

def select_whisper_model(performance_level: str = "medium", available_memory: Optional[int] = None) -> str:
    """
    Select the appropriate Whisper model based on performance requirements and available resources.
    
    Args:
        performance_level: "low", "medium", "high", or "max"
        available_memory: Available memory in MB (if None, will be estimated)
        
    Returns:
        Whisper model name
    """
    # Model size requirements (approximate, in MB)
    model_sizes = {
        "tiny": 150,
        "base": 300,
        "small": 500,
        "medium": 1500,
        "large": 3000
    }
    
    # Performance level to model mapping
    models = {
        "low": "tiny",      # Fastest, least accurate
        "medium": "base",   # Good balance
        "high": "small",    # More accurate but slower
        "max": "medium"     # Most accurate, slowest
    }
    
    # Get initial model choice
    model = models.get(performance_level, "base")
    
    # If available memory is provided, ensure the model fits
    if available_memory is not None:
        # Allow some headroom (70% of available memory)
        usable_memory = available_memory * 0.7
        
        # Find the largest model that fits
        selected_model = model
        for m, size in model_sizes.items():
            if size <= usable_memory and model_sizes.get(selected_model, 0) < size:
                if models.get(performance_level, "") >= m:  # Don't exceed requested performance
                    selected_model = m
        
        model = selected_model
    
    return model

def optimize_whisper_model(model: Any, device: Optional[str] = None) -> Any:
    """
    Optimize the Whisper model for inference.
    
    Args:
        model: Whisper model
        device: Compute device ("cpu", "cuda", etc.)
        
    Returns:
        Optimized model
    """
    # Determine device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logging.info(f"Optimizing Whisper model for {device}")
    
    # Move model to device
    model.to(device)
    
    # Optimize for inference
    if device == "cpu":
        # Quantize model for CPU
        try:
            model = torch.quantization.quantize_dynamic(
                model, {torch.nn.Linear}, dtype=torch.qint8
            )
            logging.info("Applied dynamic quantization to model")
        except Exception as e:
            logging.warning(f"Could not quantize model: {str(e)}")
    elif device == "cuda":
        # Use mixed precision for GPU
        try:
            model = model.half()
            logging.info("Converted model to half precision for GPU")
        except Exception as e:
            logging.warning(f"Could not convert model to half precision: {str(e)}")
    
    return model
```

## 2. ADK Streaming Voice Integration

This section details the integration of native streaming capabilities from the Google Agent Development Kit (ADK) version 0.4.0 into the RadBot framework, enabling real-time voice interactions.

### ADK Streaming Fundamentals

ADK Streaming integrates the capabilities of the Gemini Live API to enable low-latency, bidirectional voice and video interactions with ADK agents. This differs from traditional request-response interactions by maintaining a persistent connection (typically WebSockets) allowing for real-time data exchange. Key benefits include a more natural, human-like conversational experience where users can interrupt the agent, and the agent can respond with synthesized voice in near real-time.

The core technology enabling ADK streaming is the Gemini Live API, designed specifically for stateful, low-latency, bidirectional communication. When an ADK agent is configured with a model compatible with the Live API, ADK manages the underlying connection and data flow. The Gemini model itself handles not only the language understanding and generation but also the real-time speech synthesis for voice output when configured for audio modality.

### Agent Definition Configuration

The primary change to enable streaming involves ensuring that the RadBot agent definition uses a Gemini model compatible with the Live API:

```python
# In the relevant radbot agent definition file
from google.adk.agents import Agent

streaming_radbot_agent = Agent(
    name="radbot_streaming_agent",
    # Use a Live API compatible model for your platform
    # Example for Google AI Studio:
    model="gemini-2.0-flash-exp",
    # Example for Vertex AI:
    # model="gemini-2.0-flash-live-001",
    description="Radbot agent with native ADK streaming capabilities.",
    instruction="You are Radbot. Respond to user queries, supporting voice interaction.",
    tools=[]  # Add appropriate tools
)
```

### Environment Configuration

Sensitive configurations like API keys and cloud project details should be managed using a `.env` file:

**Option 1: Using Google AI Studio**

```
# Use Google AI Studio backend
GOOGLE_GENAI_USE_VERTEXAI=FALSE
# Your Google AI Studio API Key
GOOGLE_API_KEY=YOUR_API_KEY_HERE
```

**Option 2: Using Google Cloud Vertex AI**

```
# Use Google Cloud Vertex AI backend
GOOGLE_GENAI_USE_VERTEXAI=TRUE
# Your Google Cloud Project ID
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
# Your Google Cloud Location (Region)
GOOGLE_CLOUD_LOCATION=your-gcp-region
```

### Voice Output Handling

The synthesized voice output heard during ADK streaming is generated directly by the configured Gemini Live API model, not by a separate Text-to-Speech (TTS) service explicitly configured within the ADK Agent definition. The Gemini model itself possesses multimodal output capabilities, including speech synthesis.

### Testing with ADK Web

Use the ADK web tool for local development and testing:

1. Set the SSL_CERT_FILE environment variable:
   ```bash
   export SSL_CERT_FILE=$(python -m certifi)
   ```

2. Launch ADK web:
   ```bash
   adk web
   ```

3. Access the UI at the provided URL (e.g., http://localhost:8000)

4. Select the configured RadBot streaming agent from the dropdown menu

5. Test both text and voice interactions

## 3. TTS Migration to Google Cloud

In a separate enhancement, the project migrated from ElevenLabs Text-to-Speech to Google Cloud Text-to-Speech for the following reasons:

1. Better integration with ADK's streaming capabilities
2. More consistent streaming experience
3. Reduced latency with bidirectional streaming
4. More voice customization options
5. Better compatibility with Google's ecosystem

### Implementation Changes

1. **Dependencies**:
   - Added `google-cloud-texttospeech>=2.26.0` to `pyproject.toml`
   - Removed dedicated ElevenLabs dependency

2. **Implementation**:
   - Created a new `GoogleCloudTTSAdapter` class
   - Updated voice handlers to use the new adapter
   - Updated documentation

3. **Configuration**:
   - Updated environment variable checks to look for `GOOGLE_APPLICATION_CREDENTIALS`
   - Added new environment variables for voice customization

### Streaming Implementation

The key improvement in the Google Cloud TTS implementation is the use of bidirectional streaming:

```python
async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
    # Create a streaming config request
    streaming_config = texttospeech.StreamingSynthesizeRequest(
        streaming_config=texttospeech.StreamingSynthesisConfig(
            voice=voice_params,
            audio_config=audio_config
        )
    )
    
    # Create text chunks for streaming
    text_chunks = split_text_into_chunks(text)
    
    # Create request generator for bidirectional streaming
    def request_generator():
        yield streaming_config
        for chunk in text_chunks:
            if chunk.strip():
                yield texttospeech.StreamingSynthesizeRequest(
                    input=texttospeech.StreamingSynthesisInput(text=chunk)
                )
    
    # Stream responses - this is bidirectional
    streaming_responses = self.client.streaming_synthesize(request_generator())
    
    # Process streaming responses
    for response in streaming_responses:
        if response.audio_content:
            yield response.audio_content
```

### Voice Customization

The Google Cloud TTS implementation offers various customization options:

- Language code (e.g., `en-US`, `fr-FR`)
- Voice name (e.g., `en-US-Journey-F`)
- Audio encoding (e.g., `LINEAR16`, `MP3`, `OGG_OPUS`)
- Speaking rate (0.25 to 4.0)
- Pitch (-20.0 to 20.0)
- Volume gain (-96.0 to 16.0)

## 4. Future Enhancements

Planned improvements for the voice and speech subsystems:

1. Implement more voice options for TTS
2. Add wake word detection for always-on applications
3. Improve noise resistance in Voice Activity Detection
4. Implement true streaming transcription for real-time responses
5. Add support for multiple languages
6. Add client-side caching for common responses
7. Implement offline fallback TTS options
8. Add more voice customization options in the UI
9. Support for advanced SSML features