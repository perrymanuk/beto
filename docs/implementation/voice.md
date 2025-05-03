# Bidirectional Voice Chat Implementation

This document outlines the implementation of voice capabilities for the Radbot project, using Google ADK for streaming interaction and Google Cloud Text-to-Speech for high-quality streaming TTS.

## Overview

The voice implementation allows users to interact with the agent using voice input and receive spoken responses. The implementation follows a modular, non-intrusive approach that works well with the ADK web interface.

The implementation consists of two main components:

1. **Google Cloud TTS Adapter** - A component that converts text to speech using Google Cloud Text-to-Speech streaming API
2. **ADK Web Extension** - A JavaScript extension that adds voice capabilities to the ADK web interface

This approach ensures compatibility with ADK 0.3.0 and takes advantage of Google's native streaming capabilities for a more integrated experience with ADK.

## Implementation Details

### Google Cloud TTS Adapter

The TTS adapter is implemented as a Python class that integrates with the Google Cloud Text-to-Speech API to convert text to speech using bidirectional streaming.

```python
async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
    """
    Stream text to speech using Google Cloud TTS.
    
    Args:
        text: Text to convert to speech
        
    Yields:
        bytes: Audio chunks as they are received
    """
    if not text.strip():
        return
    
    try:
        # Set up streaming configuration
        voice_params = get_voice_selection_params()
        audio_config = get_audio_config()
        
        # Create streaming config request
        streaming_config = texttospeech.StreamingSynthesizeRequest(
            streaming_config=texttospeech.StreamingSynthesisConfig(
                voice=voice_params,
                audio_config=audio_config
            )
        )
        
        # Create text iterator for streaming
        text_chunks = split_text_into_chunks(text)
        
        # Create request generator
        def request_generator():
            # First yield the config request
            yield streaming_config
            
            # Then yield each text chunk
            for chunk in text_chunks:
                if chunk.strip():
                    yield texttospeech.StreamingSynthesizeRequest(
                        input=texttospeech.StreamingSynthesisInput(text=chunk)
                    )
        
        # Stream responses
        streaming_responses = self.client.streaming_synthesize(request_generator())
        
        # Process streaming responses
        for response in streaming_responses:
            # Yield audio content
            if response.audio_content:
                yield response.audio_content
    except Exception as e:
        logger.error(f"Error in Google Cloud TTS streaming: {e}")
        raise
```

The adapter uses Google Cloud's bidirectional streaming capability for low-latency audio synthesis, which integrates seamlessly with ADK's streaming features.

### ADK Web Extension

The ADK Web Extension is implemented as a JavaScript file that can be loaded into the ADK web interface. It adds a button to enable/disable voice capabilities and intercepts agent responses to convert them to speech.

Key components of the extension:

1. **UI Elements**: A button for toggling voice and a status indicator
2. **Message Interception**: A MutationObserver that detects new messages from the agent
3. **Text-to-Speech**: A function that sends text to the TTS service and plays the resulting audio
4. **Audio Playback**: Functions for decoding and playing audio using the Web Audio API

The extension is designed to be non-intrusive and works with the existing ADK web interface without modifications.

## Configuration

The following environment variables control the voice behavior:

```
# Google Cloud credentials (required for TTS)
# You need to set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Optional Google Cloud TTS configuration
GOOGLE_TTS_LANGUAGE_CODE=en-US
GOOGLE_TTS_VOICE_NAME=en-US-Journey-F
GOOGLE_TTS_AUDIO_ENCODING=LINEAR16
GOOGLE_TTS_SPEAKING_RATE=1.0
GOOGLE_TTS_PITCH=0.0
GOOGLE_TTS_VOLUME_GAIN_DB=0.0
```

## Usage

### Using Google Cloud TTS with ADK

To use Google Cloud TTS with ADK:

1. Set up Google Cloud Text-to-Speech API on your Google Cloud project
2. Download your service account key file and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Configure optional TTS settings in your environment variables
4. Run the ADK web interface with the voice adapter enabled: `make run-web`
5. The TTS functionality will be automatically integrated with the ADK streaming interface

### Using the ADK Web Extension

To use the ADK Web Extension:

1. Start the ADK web interface: `make run-web`
2. Open the ADK web interface in your browser (typically http://localhost:8000)
3. Click the microphone button that appears in the interface to enable voice input
4. Speak to the agent and hear the responses synthesized using Google Cloud TTS in real-time

## Error Handling and Fallbacks

The implementation includes several fallback mechanisms:

1. If Google Cloud TTS API is unavailable, the adapter falls back to sending text responses
2. If audio playback fails, the extension falls back to text display
3. The extension can be easily disabled if issues occur
4. Text is split into chunks to ensure better streaming performance and reliability

## Performance Considerations

- **Latency**: Google Cloud TTS streaming provides low-latency audio synthesis
- **Audio Format**: Audio is returned in the configured format (default: LINEAR16)
- **Text Chunking**: Text is split into smaller chunks for better streaming performance
- **Voice Selection**: Journey voice models offer high-quality, natural-sounding speech

## Limitations

1. Requires Google Cloud Platform account with Text-to-Speech API enabled
2. Requires authentication credentials (service account key)
3. Subject to Google Cloud TTS quotas and pricing
4. Requires browser permission for audio playback
5. Voice input currently relies on the ADK web interface's built-in functionality

## Future Improvements

1. Add custom voice activation detection
2. Support voice preferences and settings
3. Implement a browser extension for better integration
4. Add client-side audio caching
5. Implement offline fallback TTS options
6. Add more voice customization options
