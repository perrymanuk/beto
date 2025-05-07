# ElevenLabs to Google Cloud TTS Migration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document describes the migration from ElevenLabs Text-to-Speech to Google Cloud Text-to-Speech in the radbot project.

## Overview

We've replaced the ElevenLabs implementation with Google Cloud Text-to-Speech for the following reasons:

1. Better integration with ADK's streaming capabilities
2. More consistent streaming experience
3. Reduced latency with bidirectional streaming
4. More voice customization options
5. Better compatibility with Google's ecosystem

## Changes Made

1. **Dependencies**:
   - Added `google-cloud-texttospeech>=2.26.0` to `pyproject.toml`
   - Removed dedicated ElevenLabs dependency comment in `pyproject.toml`

2. **Implementation**:
   - Created a new `GoogleCloudTTSAdapter` class in `google_cloud_tts_adapter.py`
   - Updated `__init__.py` to export the new adapter class
   - Updated `adk_voice_handler.py` to use the new adapter
   - Updated `voice_server.py` to use the new adapter
   - Updated documentation in `voice.md`

3. **Configuration**:
   - Updated `.env.example` with Google Cloud TTS configuration options
   - Updated environment variable checks to look for `GOOGLE_APPLICATION_CREDENTIALS`
   - Added new environment variables for voice customization

4. **Authentication**:
   - Now requires Google Cloud service account credentials
   - Uses standard Google Cloud authentication flow

## How to Use

1. Set up Google Cloud Text-to-Speech API:
   - Create a Google Cloud project
   - Enable the Text-to-Speech API
   - Create a service account with Text-to-Speech API access
   - Download the service account key file

2. Configure the Environment:
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account key file
   - Optionally configure voice settings through environment variables

3. Run the Application:
   - Run the ADK web interface: `make run-web`
   - The TTS functionality will be automatically integrated with ADK streaming

## Streaming Implementation

The key improvement in the new implementation is the use of bidirectional streaming:

```python
async def stream_speech(self, text: str) -> AsyncGenerator[bytes, None]:
    # ...
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
    # ...
```

This implementation allows for low-latency, real-time audio streaming that integrates well with ADK's streaming capabilities.

## Voice Customization

The Google Cloud TTS implementation offers various customization options:

- Language code (e.g., `en-US`, `fr-FR`)
- Voice name (e.g., `en-US-Journey-F`)
- Audio encoding (e.g., `LINEAR16`, `MP3`, `OGG_OPUS`)
- Speaking rate (0.25 to 4.0)
- Pitch (-20.0 to 20.0)
- Volume gain (-96.0 to 16.0)

These can be configured through environment variables.

## Known Limitations

1. Requires Google Cloud Platform account with Text-to-Speech API enabled
2. Subject to Google Cloud TTS quotas and pricing
3. Journey voices may have higher latency than some ElevenLabs models

## Future Improvements

1. Add client-side caching for common responses
2. Implement offline fallback TTS options
3. Add more voice customization options in the UI
4. Support for advanced SSML features
