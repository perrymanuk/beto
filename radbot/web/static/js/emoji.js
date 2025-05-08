/**
 * Emoji functionality module for RadBot UI
 */

// Emoji autocomplete state
let emojiSuggestions = [];
let activeSuggestionIndex = -1;
let activeShortcodeStart = -1;
let activeShortcodeEnd = -1;
let emojiSuggestionsElement;

// Emoji data for autocomplete
const commonEmojis = [
    // Hand gestures and popular emojis
    {shortcode: ':hangloose:', emoji: '🤙', description: 'Hang Loose / Shaka'},
    {shortcode: ':call_me_hand:', emoji: '🤙', description: 'Call Me Hand'},
    {shortcode: ':ok_hand:', emoji: '👌', description: 'OK Hand'},
    {shortcode: ':wave:', emoji: '👋', description: 'Waving Hand'},
    {shortcode: ':raised_hands:', emoji: '🙌', description: 'Raised Hands'},
    {shortcode: ':clap:', emoji: '👏', description: 'Clapping Hands'},
    {shortcode: ':handshake:', emoji: '🤝', description: 'Handshake'},
    {shortcode: ':pray:', emoji: '🙏', description: 'Praying Hands'},
    {shortcode: ':metal:', emoji: '🤘', description: 'Metal / Rock On'},
    {shortcode: ':punch:', emoji: '👊', description: 'Fist Bump'},
    
    // Expressions
    {shortcode: ':smile:', emoji: '😊', description: 'Smile'},
    {shortcode: ':grin:', emoji: '😁', description: 'Grin'},
    {shortcode: ':joy:', emoji: '😂', description: 'Joy'},
    {shortcode: ':laughing:', emoji: '😆', description: 'Laughing'},
    {shortcode: ':rofl:', emoji: '🤣', description: 'ROFL'},
    {shortcode: ':smiley:', emoji: '😃', description: 'Smiley'},
    {shortcode: ':wink:', emoji: '😉', description: 'Wink'},
    {shortcode: ':blush:', emoji: '😊', description: 'Blush'},
    {shortcode: ':thinking:', emoji: '🤔', description: 'Thinking'},
    {shortcode: ':sob:', emoji: '😭', description: 'Crying'},
    {shortcode: ':angry:', emoji: '😠', description: 'Angry'},
    {shortcode: ':sunglasses:', emoji: '😎', description: 'Cool / Sunglasses'},
    {shortcode: ':sweat_smile:', emoji: '😅', description: 'Awkward Smile'},
    {shortcode: ':nerd_face:', emoji: '🤓', description: 'Nerd Face'},
    {shortcode: ':innocent:', emoji: '😇', description: 'Innocent'},
    
    // Objects and miscellaneous
    {shortcode: ':heart:', emoji: '❤️', description: 'Heart'},
    {shortcode: ':+1:', emoji: '👍', description: 'Thumbs Up'},
    {shortcode: ':thumbsup:', emoji: '👍', description: 'Thumbs Up'},
    {shortcode: ':-1:', emoji: '👎', description: 'Thumbs Down'},
    {shortcode: ':thumbsdown:', emoji: '👎', description: 'Thumbs Down'},
    {shortcode: ':tada:', emoji: '🎉', description: 'Celebration'},
    {shortcode: ':rocket:', emoji: '🚀', description: 'Rocket'},
    {shortcode: ':fire:', emoji: '🔥', description: 'Fire'},
    {shortcode: ':boom:', emoji: '💥', description: 'Explosion'},
    {shortcode: ':star:', emoji: '⭐', description: 'Star'},
    {shortcode: ':check:', emoji: '✅', description: 'Check Mark'},
    {shortcode: ':x:', emoji: '❌', description: 'Cross Mark'},
    {shortcode: ':warning:', emoji: '⚠️', description: 'Warning'},
    {shortcode: ':question:', emoji: '❓', description: 'Question'},
    {shortcode: ':zap:', emoji: '⚡', description: 'Lightning'},
    {shortcode: ':bulb:', emoji: '💡', description: 'Light Bulb'},
    {shortcode: ':computer:', emoji: '💻', description: 'Computer'},
    {shortcode: ':gear:', emoji: '⚙️', description: 'Gear'},
    {shortcode: ':eyes:', emoji: '👀', description: 'Eyes'},
    {shortcode: ':brain:', emoji: '🧠', description: 'Brain'},
    {shortcode: ':robot:', emoji: '🤖', description: 'Robot'},
    
    // Development related
    {shortcode: ':bug:', emoji: '🐛', description: 'Bug'},
    {shortcode: ':hammer_and_wrench:', emoji: '🛠️', description: 'Tools'},
    {shortcode: ':lock:', emoji: '🔒', description: 'Lock'},
    {shortcode: ':unlock:', emoji: '🔓', description: 'Unlock'},
    {shortcode: ':key:', emoji: '🔑', description: 'Key'},
    {shortcode: ':mag:', emoji: '🔍', description: 'Magnifying Glass'},
    {shortcode: ':clock:', emoji: '🕒', description: 'Clock'},
    {shortcode: ':hourglass:', emoji: '⌛', description: 'Hourglass'},
    {shortcode: ':pushpin:', emoji: '📌', description: 'Pushpin'},
    {shortcode: ':memo:', emoji: '📝', description: 'Memo'},
    {shortcode: ':book:', emoji: '📚', description: 'Books'},
    {shortcode: ':chart:', emoji: '📊', description: 'Chart'}
];

// Initialize emoji functionality
export function initEmoji() {
    console.log('Initializing emoji module');
    
    // Emoji suggestions
    emojiSuggestionsElement = document.getElementById('emoji-suggestions');
    
    // Add event listeners for emoji suggestions
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', handleEmojiAutocomplete);
        chatInput.addEventListener('keydown', handleEmojiKeyNavigation);
    }
    
    return true;
}

// Convert emoji shortcodes to emoji characters
export function convertEmoji(text) {
    if (!text) return text;
    
    if (typeof joypixels !== 'undefined') {
        try {
            // Use joypixels library if available - this library handles more emoji codes
            return joypixels.shortnameToUnicode(text);
        } catch (error) {
            console.warn("Error using joypixels to convert emoji:", error);
            // Fall back to manual conversion
        }
    }
    
    // Fallback with basic emoji mappings
    const emojiMap = {};
    commonEmojis.forEach(item => {
        emojiMap[item.shortcode] = item.emoji;
    });
    
    // Replace shortcodes with emojis
    return text.replace(/:[a-z0-9_+-]+:/g, match => {
        return emojiMap[match] || match;
    });
}

// Handle emoji autocomplete
export function handleEmojiAutocomplete(event) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find if we're inside a potential emoji shortcode
    const colonBefore = text.lastIndexOf(':', cursorPosition);
    
    // If there's no colon before cursor, or there's a completed shortcode, hide suggestions
    if (colonBefore === -1 || text.slice(colonBefore, cursorPosition).includes(' ')) {
        hideEmojiSuggestions();
        return;
    }
    
    // Check if there's a completed emoji shortcode (ending with ':')
    const colonAfter = text.indexOf(':', colonBefore + 1);
    if (colonAfter !== -1 && colonAfter < cursorPosition) {
        hideEmojiSuggestions();
        return;
    }
    
    // Extract the current incomplete shortcode (without the leading ':')
    const shortcodeFragment = text.slice(colonBefore + 1, cursorPosition);
    
    // Store the position for replacement later
    activeShortcodeStart = colonBefore;
    activeShortcodeEnd = cursorPosition;
    
    // Filter emoji suggestions based on the shortcode fragment
    updateEmojiSuggestions(shortcodeFragment);
}

// Update emoji suggestions based on input
function updateEmojiSuggestions(fragment) {
    // Filter emoji list based on the fragment
    emojiSuggestions = commonEmojis
        .filter(emoji => emoji.shortcode.slice(1, -1).toLowerCase().includes(fragment.toLowerCase()))
        .sort((a, b) => {
            // Sort exact matches first, then by starts with, then alphabetically
            const aShortcode = a.shortcode.slice(1, -1).toLowerCase();
            const bShortcode = b.shortcode.slice(1, -1).toLowerCase();
            
            // Exact match gets highest priority
            if (aShortcode === fragment.toLowerCase()) return -1;
            if (bShortcode === fragment.toLowerCase()) return 1;
            
            // Starts with gets next priority
            const aStartsWith = aShortcode.startsWith(fragment.toLowerCase());
            const bStartsWith = bShortcode.startsWith(fragment.toLowerCase());
            
            if (aStartsWith && !bStartsWith) return -1;
            if (!aStartsWith && bStartsWith) return 1;
            
            // Finally sort alphabetically
            return aShortcode.localeCompare(bShortcode);
        })
        .slice(0, 8); // Limit to 8 suggestions for performance
    
    if (emojiSuggestions.length > 0) {
        showEmojiSuggestions();
    } else {
        hideEmojiSuggestions();
    }
}

// Show emoji suggestions
function showEmojiSuggestions() {
    // Check if element exists
    if (!emojiSuggestionsElement) {
        emojiSuggestionsElement = document.getElementById('emoji-suggestions');
        if (!emojiSuggestionsElement) return;
    }
    
    // Clear existing suggestions
    emojiSuggestionsElement.innerHTML = '';
    
    // Create suggestion elements
    emojiSuggestions.forEach((emoji, index) => {
        const item = document.createElement('div');
        item.className = 'emoji-suggestion-item';
        item.dataset.index = index;
        
        const emojiSpan = document.createElement('span');
        emojiSpan.className = 'emoji-suggestion-emoji';
        emojiSpan.textContent = emoji.emoji;
        
        const shortcodeSpan = document.createElement('span');
        shortcodeSpan.className = 'emoji-suggestion-shortcode';
        shortcodeSpan.textContent = emoji.shortcode;
        
        const descriptionSpan = document.createElement('span');
        descriptionSpan.className = 'emoji-suggestion-description';
        descriptionSpan.textContent = emoji.description;
        
        item.appendChild(emojiSpan);
        item.appendChild(shortcodeSpan);
        item.appendChild(descriptionSpan);
        
        // Add click handler
        item.addEventListener('click', () => {
            insertEmojiSuggestion(index);
        });
        
        emojiSuggestionsElement.appendChild(item);
    });
    
    // Reset active suggestion
    activeSuggestionIndex = -1;
    
    // Show suggestions
    emojiSuggestionsElement.classList.remove('hidden');
}

// Hide emoji suggestions
function hideEmojiSuggestions() {
    if (!emojiSuggestionsElement) {
        emojiSuggestionsElement = document.getElementById('emoji-suggestions');
        if (!emojiSuggestionsElement) return;
    }
    
    emojiSuggestionsElement.classList.add('hidden');
    emojiSuggestions = [];
    activeSuggestionIndex = -1;
    activeShortcodeStart = -1;
    activeShortcodeEnd = -1;
}

// Handle keyboard navigation for emoji suggestions
export function handleEmojiKeyNavigation(event) {
    // Only process if suggestions are visible and element exists
    if (!emojiSuggestionsElement) {
        emojiSuggestionsElement = document.getElementById('emoji-suggestions');
        if (!emojiSuggestionsElement) return;
    }
    
    if (emojiSuggestions.length === 0 || emojiSuggestionsElement.classList.contains('hidden')) {
        return;
    }
    
    switch (event.key) {
        case 'ArrowDown':
            // Move selection down
            event.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex + 1) % emojiSuggestions.length;
            updateActiveSuggestion();
            break;
            
        case 'ArrowUp':
            // Move selection up
            event.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex - 1 + emojiSuggestions.length) % emojiSuggestions.length;
            updateActiveSuggestion();
            break;
            
        case 'Tab':
        case 'Enter':
            // Insert selected emoji
            if (activeSuggestionIndex >= 0) {
                event.preventDefault();
                insertEmojiSuggestion(activeSuggestionIndex);
            }
            break;
            
        case 'Escape':
            // Close suggestions
            event.preventDefault();
            hideEmojiSuggestions();
            break;
    }
}

// Update active suggestion highlighting
function updateActiveSuggestion() {
    // Check if element exists
    if (!emojiSuggestionsElement) {
        emojiSuggestionsElement = document.getElementById('emoji-suggestions');
        if (!emojiSuggestionsElement) return;
    }
    
    // Remove active class from all items
    const items = emojiSuggestionsElement.querySelectorAll('.emoji-suggestion-item');
    items.forEach(item => item.classList.remove('active'));
    
    // Add active class to selected item
    if (activeSuggestionIndex >= 0 && activeSuggestionIndex < items.length) {
        items[activeSuggestionIndex].classList.add('active');
        
        // Ensure the active item is visible in the scroll area
        const activeItem = items[activeSuggestionIndex];
        const container = emojiSuggestionsElement;
        
        const itemTop = activeItem.offsetTop;
        const itemBottom = itemTop + activeItem.offsetHeight;
        const containerTop = container.scrollTop;
        const containerBottom = containerTop + container.offsetHeight;
        
        if (itemTop < containerTop) {
            container.scrollTop = itemTop;
        } else if (itemBottom > containerBottom) {
            container.scrollTop = itemBottom - container.offsetHeight;
        }
    }
}

// Insert emoji suggestion
function insertEmojiSuggestion(index) {
    if (index >= 0 && index < emojiSuggestions.length && 
        activeShortcodeStart >= 0 && activeShortcodeEnd >= 0) {
        
        const emoji = emojiSuggestions[index];
        const input = document.getElementById('chat-input');
        if (!input) return;
        
        const text = input.value;
        
        // Replace the text from : to cursor with the shortcode
        const newText = text.slice(0, activeShortcodeStart) + 
                      emoji.shortcode + 
                      text.slice(activeShortcodeEnd);
        
        // Update input value
        input.value = newText;
        
        // Set cursor position after the inserted emoji
        const newPosition = activeShortcodeStart + emoji.shortcode.length;
        input.setSelectionRange(newPosition, newPosition);
        
        // Focus the input
        input.focus();
        
        // Hide suggestions
        hideEmojiSuggestions();
        
        // Resize textarea to fit new content
        window.chatModule.resizeTextarea();
    }
}

// Get current emoji suggestions (used by other modules)
export function getSuggestions() {
    return emojiSuggestions;
}