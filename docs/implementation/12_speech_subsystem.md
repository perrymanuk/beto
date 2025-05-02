# Speech Subsystem Implementation

This document details the implementation of a speech subsystem for the radbot framework, enabling voice-based interaction through Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.

## Component Overview

The speech subsystem consists of three primary elements:

1. **Speech-to-Text (STT)**: Converts spoken audio to text using Whisper
2. **Text-to-Speech (TTS)**: Converts text to speech using Mozilla TTS
3. **Voice Activity Detection (VAD)**: Detects when speech is present in audio

## Implementation Details

### Speech Subsystem Class

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

To integrate the speech subsystem with the radbot agent framework, add an input processing method:

```python
# radbot/agent.py (extension)

class radbotAgent:
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

For web application integration, add FastAPI endpoints:

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

## Client-Side Integration

To enable voice interaction in web clients, implement a JavaScript interface:

```javascript
// radbot-client.js

class VoiceInterface {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Set up audio context for visualization
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
    }
    
    // Initialize and bind UI elements
    initialize(startButtonId, stopButtonId, statusId, resultId, visualizerId) {
        this.startButton = document.getElementById(startButtonId);
        this.stopButton = document.getElementById(stopButtonId);
        this.statusElement = document.getElementById(statusId);
        this.resultElement = document.getElementById(resultId);
        this.visualizer = document.getElementById(visualizerId);
        
        this.startButton.addEventListener('click', () => this.startRecording());
        this.stopButton.addEventListener('click', () => this.stopRecording());
        
        this.statusElement.textContent = 'Ready';
        this.stopButton.disabled = true;
    }
    
    // Start recording audio
    async startRecording() {
        try {
            this.audioChunks = [];
            this.isRecording = true;
            
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Set up audio visualization
            const source = this.audioContext.createMediaStreamSource(stream);
            source.connect(this.analyser);
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(stream);
            
            // Handle data availability
            this.mediaRecorder.addEventListener('dataavailable', event => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            });
            
            // Start recording
            this.mediaRecorder.start(100);
            
            // Update UI
            this.statusElement.textContent = 'Recording...';
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
            
            // Start visualization
            this.visualizeAudio();
        } catch (error) {
            console.error('Recording error:', error);
            this.statusElement.textContent = `Error: ${error.message}`;
        }
    }
    
    // Stop recording and process audio
    async stopRecording() {
        if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
            return;
        }
        
        this.mediaRecorder.stop();
        this.isRecording = false;
        
        // Update UI
        this.statusElement.textContent = 'Processing...';
        this.startButton.disabled = true;
        this.stopButton.disabled = true;
        
        // Wait for data processing
        await new Promise(resolve => {
            this.mediaRecorder.addEventListener('stop', async () => {
                try {
                    // Create audio blob
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    
                    // Create form data
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.wav');
                    
                    // Send to server
                    const response = await fetch(`${this.apiUrl}/api/voice/process`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    
                    // Display result
                    this.resultElement.textContent = result.text;
                    
                    // Play audio response if available
                    if (result.audio) {
                        const audio = new Audio(`data:audio/wav;base64,${result.audio}`);
                        audio.play();
                    }
                    
                    // Update UI
                    this.statusElement.textContent = 'Ready';
                    this.startButton.disabled = false;
                } catch (error) {
                    console.error('Processing error:', error);
                    this.statusElement.textContent = `Error: ${error.message}`;
                    this.startButton.disabled = false;
                }
                
                resolve();
            });
        });
    }
    
    // Visualize audio input
    visualizeAudio() {
        if (!this.isRecording) {
            return;
        }
        
        const canvasCtx = this.visualizer.getContext('2d');
        const width = this.visualizer.width;
        const height = this.visualizer.height;
        
        this.analyser.fftSize = 256;
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        canvasCtx.clearRect(0, 0, width, height);
        
        const draw = () => {
            if (!this.isRecording) {
                return;
            }
            
            requestAnimationFrame(draw);
            
            this.analyser.getByteFrequencyData(dataArray);
            
            canvasCtx.fillStyle = 'rgb(240, 240, 240)';
            canvasCtx.fillRect(0, 0, width, height);
            
            const barWidth = (width / bufferLength) * 2.5;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] / 2;
                
                canvasCtx.fillStyle = `rgb(0, ${barHeight + 100}, 120)`;
                canvasCtx.fillRect(x, height - barHeight, barWidth, barHeight);
                
                x += barWidth + 1;
            }
        };
        
        draw();
    }
}
```

## Model Optimization

For optimal performance on different hardware, implement model selection:

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

## Package Structure

```
radbot/
├── speech/
│   ├── __init__.py
│   ├── speech_system.py       # Main speech system implementation
│   ├── model_optimizer.py     # Model selection and optimization
│   └── exceptions.py          # Custom exceptions
├── api/
│   ├── __init__.py
│   └── speech_endpoints.py    # FastAPI endpoints
```

## Integration Points

The speech subsystem integrates with:

1. **Agent Framework**: Through the extended `radbotAgent` methods
2. **API Layer**: With FastAPI endpoints for web applications
3. **Web Client**: Through the JavaScript `VoiceInterface` class

## Testing Strategy

To test the speech subsystem:

1. **Unit Tests**: Test individual components (transcription, synthesis, VAD)
2. **Integration Tests**: Test end-to-end voice processing flow
3. **Performance Tests**: Measure latency and accuracy with different models

Example test code:

```python
# tests/speech/test_speech_system.py

import pytest
import os
import tempfile
import numpy as np
from radbot.speech.speech_system import SpeechSystem, SpeechProcessingError

@pytest.fixture
async def speech_system():
    """Create a speech system for testing."""
    system = SpeechSystem(whisper_model="tiny")  # Use tiny model for faster tests
    yield system

@pytest.mark.asyncio
async def test_speech_to_text(speech_system, test_audio_file):
    """Test speech-to-text functionality."""
    # Transcribe test audio
    result = await speech_system.transcribe(test_audio_file)
    
    # Check result
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_text_to_speech(speech_system):
    """Test text-to-speech functionality."""
    # Generate speech
    output_path = await speech_system.synthesize("Hello, this is a test.")
    
    # Check result
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # Clean up
    os.unlink(output_path)

def test_voice_activity_detection(speech_system):
    """Test voice activity detection."""
    # Create sample audio with and without speech
    silence = np.zeros(16000)  # 1 second of silence
    speech = np.random.normal(0, 0.1, 16000)  # 1 second of noise (simulating speech)
    
    # Test detection
    assert not speech_system.detect_speech(silence)
    assert speech_system.detect_speech(speech)
```

## Performance Considerations

To optimize performance in different environments:

1. **Model Selection**: Use `select_whisper_model()` to choose an appropriate model size
2. **Quantization**: Apply quantization for CPU environments
3. **Mixed Precision**: Use half-precision for GPU acceleration
4. **Batch Processing**: For non-interactive applications, process audio in batches
5. **Caching**: Cache common TTS responses for frequently used phrases

## Next Steps

Future enhancements for the speech subsystem:

1. Implement more voice options for TTS
2. Add wake word detection for always-on applications
3. Improve noise resistance in VAD
4. Implement streaming transcription for real-time responses
5. Add support for multiple languages