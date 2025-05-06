// Matrix digital rain animation - Enhanced version
class MatrixRainEffect {
  constructor(options = {}) {
    this.options = {
      fontSize: options.fontSize || 18,         // Font size in pixels
      speed: options.speed || 1.2,              // Animation speed multiplier
      density: options.density || 30,           // Number of columns (higher = more columns)
      opacity: options.opacity || 0.8,          // Opacity of the entire effect
      charOpacityMin: options.charOpacityMin || 0.1,  // Minimum character opacity
      charOpacityMax: options.charOpacityMax || 1,    // Maximum character opacity
      useKatakana: options.useKatakana !== undefined ? options.useKatakana : true,
      useLatin: options.useLatin !== undefined ? options.useLatin : true,
      useSymbols: options.useSymbols !== undefined ? options.useSymbols : true,
      useDigits: options.useDigits !== undefined ? options.useDigits : true,
      ...options
    };
    
    this.matrixBg = null;
    this.canvas = null;
    this.ctx = null;
    this.drops = [];
    this.columnWidth = 0;
    this.chars = this.generateCharacterSet();
    this.animationId = null;
    this.active = false;
    this.frameCount = 0;
  }
  
  generateCharacterSet() {
    let chars = [];
    
    // Katakana characters
    if (this.options.useKatakana) {
      chars = chars.concat('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'.split(''));
    }
    
    // Latin characters
    if (this.options.useLatin) {
      chars = chars.concat('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.split(''));
    }
    
    // Symbols
    if (this.options.useSymbols) {
      chars = chars.concat('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'.split(''));
    }
    
    // Digits
    if (this.options.useDigits) {
      chars = chars.concat('0123456789'.split(''));
    }
    
    // Fallback if no character sets were selected
    if (chars.length === 0) {
      chars = 'MATRIX'.split('');
    }
    
    return chars;
  }
  
  initialize() {
    console.log('Initializing enhanced matrix effect');
    
    // Clean up any existing elements
    if (this.matrixBg) {
      this.matrixBg.remove();
    }
    
    // Create container
    this.matrixBg = document.createElement('div');
    this.matrixBg.className = 'matrix-background';
    this.matrixBg.style.opacity = this.options.opacity;
    document.body.appendChild(this.matrixBg);
    
    // Create canvas
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.matrixBg.appendChild(this.canvas);
    
    // Make canvas full screen and handle resolution
    this.resizeCanvas();
    
    // Setup column data
    this.setupColumns();
    
    // Set the background to black with some opacity
    this.matrixBg.style.backgroundColor = 'rgba(0, 0, 0, 0.15)';
    
    // Make it active
    this.active = true;
    this.animate();
    
    // Handle window resize
    window.addEventListener('resize', this.handleResize.bind(this));
    
    // Add CSS styles to container
    Object.assign(this.matrixBg.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      zIndex: '-1',
      overflow: 'hidden'
    });
    
    // Add styles to canvas
    Object.assign(this.canvas.style, {
      display: 'block',
      width: '100%',
      height: '100%'
    });
    
    console.log('Enhanced matrix effect initialized');
  }
  
  resizeCanvas() {
    // Handle high DPI displays for sharp rendering
    const dpr = window.devicePixelRatio || 1;
    const rect = this.matrixBg.getBoundingClientRect();
    
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    
    // Scale the context to ensure correct drawing operations
    this.ctx.scale(dpr, dpr);
    
    // Set font once after resize
    this.ctx.font = `bold ${this.options.fontSize}px "Source Code Pro", monospace`;
  }
  
  setupColumns() {
    const width = this.canvas.width / (window.devicePixelRatio || 1);
    const height = this.canvas.height / (window.devicePixelRatio || 1);
    
    // Determine column width based on font size
    this.columnWidth = Math.ceil(width / this.options.density);
    const columns = Math.ceil(width / this.columnWidth);
    
    // Initialize drops
    this.drops = [];
    for (let i = 0; i < columns; i++) {
      this.drops[i] = {
        y: Math.random() * -100, // Start above screen with randomness
        speed: Math.random() * 1.5 + 0.5, // Random speed for each column
        length: Math.floor(Math.random() * 15) + 5, // Random length of trail
        chars: [], // Characters in this column
        lastUpdate: 0, // Frame counter for character change
      };
      
      // Initialize characters for this column
      for (let j = 0; j < this.drops[i].length; j++) {
        this.drops[i].chars[j] = {
          value: this.chars[Math.floor(Math.random() * this.chars.length)],
          opacity: this.mapRange(j, 0, this.drops[i].length - 1, this.options.charOpacityMax, this.options.charOpacityMin)
        };
      }
    }
  }
  
  // Map a value from one range to another
  mapRange(value, in_min, in_max, out_min, out_max) {
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
  }
  
  animate() {
    if (!this.active) return;
    
    this.frameCount++;
    
    // Clear the canvas
    this.ctx.clearRect(0, 0, this.canvas.width / (window.devicePixelRatio || 1), this.canvas.height / (window.devicePixelRatio || 1));
    
    const height = this.canvas.height / (window.devicePixelRatio || 1);
    const speed = this.options.speed;
    
    // Draw each column
    for (let i = 0; i < this.drops.length; i++) {
      const drop = this.drops[i];
      const x = i * this.columnWidth;
      
      // Move the drop down
      drop.y += drop.speed * speed;
      
      // Update characters occasionally
      if (this.frameCount % 5 === 0 && Math.random() > 0.7) {
        // Change the first (leading) character
        drop.chars[0].value = this.chars[Math.floor(Math.random() * this.chars.length)];
      }
      
      // Draw the characters in this column
      for (let j = 0; j < drop.chars.length; j++) {
        const char = drop.chars[j];
        const y = drop.y - (j * this.options.fontSize);
        
        if (y > -this.options.fontSize && y < height) {
          // Set the appropriate green color with opacity
          this.ctx.fillStyle = `rgba(0, 255, 0, ${char.opacity})`;
          
          // Draw the character
          this.ctx.fillText(char.value, x, y);
        }
      }
      
      // When the leading character is off screen, reset the column
      if (drop.y - ((drop.chars.length - 1) * this.options.fontSize) > height) {
        drop.y = Math.random() * -100; // Reset to random position above screen
        drop.speed = Math.random() * 1.5 + 0.5; // New random speed
        drop.length = Math.floor(Math.random() * 15) + 5; // New random length
        
        // Reset characters with new opacity gradient
        drop.chars = [];
        for (let j = 0; j < drop.length; j++) {
          drop.chars[j] = {
            value: this.chars[Math.floor(Math.random() * this.chars.length)],
            opacity: this.mapRange(j, 0, drop.length - 1, this.options.charOpacityMax, this.options.charOpacityMin)
          };
        }
      }
    }
    
    this.animationId = requestAnimationFrame(this.animate.bind(this));
  }
  
  handleResize() {
    cancelAnimationFrame(this.animationId);
    this.resizeCanvas();
    this.setupColumns();
    if (this.active) {
      this.animate();
    }
  }
  
  setOpacity(opacity) {
    this.options.opacity = opacity;
    if (this.matrixBg) {
      this.matrixBg.style.opacity = opacity;
    }
  }
  
  setSpeed(speed) {
    this.options.speed = speed;
  }
  
  setDensity(density) {
    this.options.density = density;
    this.setupColumns();
  }
  
  stop() {
    this.active = false;
    cancelAnimationFrame(this.animationId);
  }
  
  start() {
    if (!this.active) {
      this.active = true;
      this.animate();
    }
  }
  
  toggle() {
    console.log(`Toggling matrix effect. Current state: ${this.active ? 'active' : 'inactive'}`);
    
    if (this.active) {
      this.stop();
      
      // Hide the matrix background container
      if (this.matrixBg) {
        this.matrixBg.style.visibility = 'hidden';
      }
    } else {
      // Make sure it's visible
      if (this.matrixBg) {
        this.matrixBg.style.visibility = 'visible';
      }
      
      this.start();
    }
    
    console.log(`Matrix effect is now: ${this.active ? 'active' : 'inactive'}`);
    return this.active;
  }
}

// Initialize matrix rain effect when document is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Create a better matrix effect using canvas for performance and visuals
  window.matrixEffect = new MatrixRainEffect({
    opacity: 0.9,             // Very visible
    speed: 1.2,               // Slightly faster than normal
    density: 40,              // Many columns
    fontSize: 20,             // Larger characters
    charOpacityMin: 0.2,      // Minimum character opacity (trail end)
    charOpacityMax: 1.0,      // Maximum character opacity (trail start)
    useKatakana: true,        // Include Katakana characters
    useLatin: true,           // Include Latin characters
    useSymbols: true,         // Include symbols
    useDigits: true           // Include digits
  });
  
  // Initialize the effect (creates elements)
  window.matrixEffect.initialize();
  
  // Stop it initially - user needs to enable explicitly
  window.matrixEffect.stop();
  
  // Add commands for controlling the matrix effect
  document.addEventListener('command:matrix', (e) => {
    const params = e.detail || {};
    
    if (params.toggle !== undefined) {
      const isActive = window.matrixEffect.toggle();
      console.log(`Matrix effect ${isActive ? 'enabled' : 'disabled'}`);
    }
    
    if (params.opacity !== undefined) {
      window.matrixEffect.setOpacity(parseFloat(params.opacity));
      console.log(`Matrix effect opacity set to ${params.opacity}`);
    }
    
    if (params.speed !== undefined) {
      window.matrixEffect.setSpeed(parseFloat(params.speed));
      console.log(`Matrix effect speed set to ${params.speed}`);
    }
    
    if (params.density !== undefined) {
      window.matrixEffect.setDensity(parseFloat(params.density));
      console.log(`Matrix effect density set to ${params.density}`);
    }
  });
});