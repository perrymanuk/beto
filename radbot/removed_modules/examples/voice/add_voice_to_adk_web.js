/**
 * ADK Web Voice Extension
 * 
 * This script adds voice capabilities to the ADK web interface by intercepting
 * agent responses and converting them to speech using ElevenLabs.
 * 
 * To use:
 * 1. Start the ADK web interface (adk web)
 * 2. Open the browser console (F12)
 * 3. Paste and run this script
 * 
 * Note: You need to have ELEVEN_LABS_API_KEY set in your environment variables
 * for this to work correctly.
 */

// Configuration
const TTS_ENDPOINT = '/api/voice/text-to-speech';  // This will be a custom endpoint we'll add

class ADKVoiceExtension {
  constructor() {
    this.audioContext = null;
    this.audioQueue = [];
    this.isPlaying = false;
    this.nextPlayTime = 0;
    this.isEnabled = false;
    this.PLAYBACK_SAMPLE_RATE = 44100;  // Standard audio sample rate

    // UI elements
    this.voiceButton = null;
    this.statusElement = null;

    // Initialize
    this.init();
  }

  /**
   * Initialize the voice extension
   */
  init() {
    console.log('Initializing ADK Voice Extension...');
    
    // Wait for the DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupUI());
    } else {
      this.setupUI();
    }
  }

  /**
   * Set up the UI elements
   */
  setupUI() {
    // Create a button for toggling voice
    this.voiceButton = document.createElement('button');
    this.voiceButton.textContent = '🔊 Enable Voice';
    this.voiceButton.style.position = 'fixed';
    this.voiceButton.style.bottom = '20px';
    this.voiceButton.style.right = '20px';
    this.voiceButton.style.zIndex = '9999';
    this.voiceButton.style.padding = '10px 15px';
    this.voiceButton.style.backgroundColor = '#4a90e2';
    this.voiceButton.style.color = 'white';
    this.voiceButton.style.border = 'none';
    this.voiceButton.style.borderRadius = '5px';
    this.voiceButton.style.cursor = 'pointer';
    this.voiceButton.addEventListener('click', () => this.toggleVoice());
    document.body.appendChild(this.voiceButton);
    
    // Create a status element
    this.statusElement = document.createElement('div');
    this.statusElement.style.position = 'fixed';
    this.statusElement.style.bottom = '60px';
    this.statusElement.style.right = '20px';
    this.statusElement.style.zIndex = '9999';
    this.statusElement.style.padding = '5px 10px';
    this.statusElement.style.backgroundColor = '#f0f0f0';
    this.statusElement.style.color = '#333';
    this.statusElement.style.border = 'none';
    this.statusElement.style.borderRadius = '5px';
    this.statusElement.style.fontSize = '12px';
    this.statusElement.style.display = 'none';
    document.body.appendChild(this.statusElement);
    
    // Set up API endpoint for TTS
    this.setupTTSEndpoint();
    
    console.log('ADK Voice Extension UI initialized');
  }

  /**
   * Set up the TTS endpoint
   */
  setupTTSEndpoint() {
    // Define the TTS endpoint
    this.ttsEndpoint = 'http://localhost:8001/api/voice/text-to-speech';
    
    console.log('TTS endpoint set up:', this.ttsEndpoint);
  }

  /**
   * Toggle voice capabilities
   */
  toggleVoice() {
    this.isEnabled = !this.isEnabled;
    
    if (this.isEnabled) {
      this.voiceButton.textContent = '🔇 Disable Voice';
      this.voiceButton.style.backgroundColor = '#e24a4a';
      this.statusElement.textContent = 'Voice enabled';
      this.statusElement.style.display = 'block';
      
      // Initialize audio context
      this.initializeAudio();
      
      // Set up message interception
      this.interceptMessages();
      
    } else {
      this.voiceButton.textContent = '🔊 Enable Voice';
      this.voiceButton.style.backgroundColor = '#4a90e2';
      this.statusElement.style.display = 'none';
      
      // Clean up
      this.cleanUp();
    }
    
    console.log(`Voice ${this.isEnabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Initialize audio context
   */
  initializeAudio() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.nextPlayTime = this.audioContext.currentTime;
      console.log(`Audio context initialized. Sample rate: ${this.audioContext.sampleRate}Hz`);
    } catch (error) {
      console.error('Error initializing audio:', error);
    }
  }

  /**
   * Set up message interception
   */
  interceptMessages() {
    // This is where we would normally intercept WebSocket messages
    // For this example, we'll use a simple MutationObserver
    
    // Find the chat container
    const chatContainer = document.querySelector('.conversation-container');
    if (!chatContainer) {
      console.error('Chat container not found');
      return;
    }
    
    // Set up a MutationObserver to watch for new messages
    this.observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Check if the added node is a bot message
          for (const node of mutation.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE && 
                node.classList.contains('message') && 
                !node.classList.contains('user-message')) {
              // Get the text content
              const text = node.textContent.trim();
              if (text) {
                // Convert to speech
                this.textToSpeech(text);
              }
            }
          }
        }
      }
    });
    
    // Start observing
    this.observer.observe(chatContainer, { childList: true, subtree: true });
    
    console.log('Message interception set up');
  }

  /**
   * Clean up resources
   */
  cleanUp() {
    // Stop observing
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    
    // Clear audio queue
    this.audioQueue = [];
    
    // Close audio context
    if (this.audioContext) {
      this.audioContext.close().catch(console.error);
      this.audioContext = null;
    }
    
    console.log('Resources cleaned up');
  }

  /**
   * Convert text to speech
   * 
   * @param {string} text - Text to convert to speech
   */
  async textToSpeech(text) {
    if (!this.isEnabled || !text) {
      return;
    }
    
    console.log('Converting to speech:', text);
    this.statusElement.textContent = 'Converting to speech...';
    
    try {
      // Call the TTS endpoint
      const response = await fetch(this.ttsEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });
      
      if (!response.ok) {
        throw new Error(`TTS request failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success || !data.audio) {
        throw new Error('Invalid TTS response');
      }
      
      // Decode audio data
      const audioData = atob(data.audio);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }
      
      // Play audio
      this.playAudio(audioArray.buffer);
      
    } catch (error) {
      console.error('Error converting text to speech:', error);
      this.statusElement.textContent = 'TTS error';
      
      // Fall back to Web Speech API
      this.fallbackTTS(text);
    }
  }
  /**
   * Play audio data
   * 
   * @param {ArrayBuffer} audioBuffer - Audio data to play
   */
  async playAudio(audioBuffer) {
    if (!this.audioContext) {
      this.initializeAudio();
    }
    
    if (this.audioContext.state !== 'running') {
      try {
        await this.audioContext.resume();
      } catch (error) {
        console.error('Error resuming audio context:', error);
        this.fallbackTTS('Audio playback failed');
        return;
      }
    }
    
    try {
      // Add to queue
      this.audioQueue.push(audioBuffer);
      
      // Try to play
      this.schedulePlayback();
      
    } catch (error) {
      console.error('Error playing audio:', error);
      this.statusElement.textContent = 'Audio error';
    }
  }
  
  /**
   * Schedule audio playback
   */
  schedulePlayback() {
    if (!this.audioContext || this.audioContext.state !== 'running') {
      if (this.audioContext) {
        this.audioContext.resume().catch(console.error);
      }
      return;
    }
    
    if (this.isPlaying || this.audioQueue.length === 0) {
      return;
    }
    
    this.isPlaying = true;
    this.statusElement.textContent = 'Speaking...';
    
    // Get next chunk
    const audioBufferChunk = this.audioQueue.shift();
    
    // Decode audio
    this.audioContext.decodeAudioData(audioBufferChunk).then(audioBuffer => {
      // Create source node
      const sourceNode = this.audioContext.createBufferSource();
      sourceNode.buffer = audioBuffer;
      sourceNode.connect(this.audioContext.destination);
      
      // Calculate start time
      const currentTime = this.audioContext.currentTime;
      const startTime = Math.max(currentTime, this.nextPlayTime);
      
      // Schedule playback
      sourceNode.start(startTime);
      
      // Calculate when this chunk will finish
      const duration = audioBuffer.duration;
      this.nextPlayTime = startTime + duration;
      
      // When finished, play next chunk
      sourceNode.onended = () => {
        this.isPlaying = false;
        
        if (this.audioQueue.length === 0) {
          this.statusElement.textContent = 'Voice enabled';
        }
        
        this.schedulePlayback();
      };
    }).catch(error => {
      console.error('Error decoding audio:', error);
      this.isPlaying = false;
      this.statusElement.textContent = 'Decode error';
      
      // Try next chunk
      this.schedulePlayback();
    });
  }
  
  /**
   * Fall back to Web Speech API
   * 
   * @param {string} text - Text to speak
   */
  fallbackTTS(text) {
    // Use Web Speech API as fallback
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 1.0;
    speech.pitch = 1.0;
    speech.volume = 1.0;
    
    speech.onstart = () => {
      this.statusElement.textContent = 'Speaking (fallback)...';
    };
    
    speech.onend = () => {
      this.statusElement.textContent = 'Voice enabled';
    };
    
    speech.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      this.statusElement.textContent = 'Speech error';
    };
    
    window.speechSynthesis.speak(speech);
  }
}

// Initialize the voice extension
const voiceExtension = new ADKVoiceExtension();
console.log('ADK Voice Extension loaded');
