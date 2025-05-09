/**
 * Commands functionality module for RadBot UI
 */

// Slash commands functionality
const commands = [
    { name: '/sessions', description: 'Toggle sessions panel' },
    { name: '/tasks', description: 'Toggle tasks panel' },
    { name: '/events', description: 'Toggle events panel' },
    { name: '/clear', description: 'Clear conversation history' },
    { name: '/help', description: 'Show available commands' },
    { name: '/details', description: 'Show details for an item by ID', requiresArg: true },
    { name: '/claude', description: 'Use Claude template from config', requiresArg: true }
];

let activeCommandIndex = -1;
let commandSuggestions = [];

// Initialize commands functionality
export function initCommands() {
    console.log('Initializing commands module');
    
    // Create command suggestions element if it doesn't exist
    let commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) {
        commandSuggestionsElement = document.createElement('div');
        commandSuggestionsElement.id = 'command-suggestions';
        commandSuggestionsElement.className = 'command-suggestions';
        document.querySelector('.chat-input-wrapper').appendChild(commandSuggestionsElement);
    }
    
    // Add event listeners for command suggestions
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', handleCommandAutocomplete);
        chatInput.addEventListener('keydown', handleCommandKeyNavigation);
    }
    
    return true;
}

// Execute slash command
export function executeCommand(commandText) {
    const parts = commandText.slice(1).split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1).join(' ');
    
    console.log(`Executing command: ${cmd} with args: ${args}`);
    
    switch (cmd) {
        case 'sessions':
            document.dispatchEvent(new CustomEvent('command:sessions'));
            window.chatModule.addMessage('system', 'Sessions panel toggled');
            break;
            
        case 'tasks':
            document.dispatchEvent(new CustomEvent('command:tasks'));
            window.chatModule.addMessage('system', 'Tasks panel toggled');
            break;
            
        case 'events':
            document.dispatchEvent(new CustomEvent('command:events'));
            window.chatModule.addMessage('system', 'Events panel toggled');
            break;
            
        case 'clear':
            window.chatModule.getChatElements().resetButton.click();
            break;
            
        case 'help':
            showHelp();
            break;
            
        case 'details':
            if (!args) {
                window.chatModule.addMessage('system', 'Error: Please provide an item ID. Usage: /details [item-id]');
            } else {
                showItemDetails(args);
            }
            break;
            
        case 'claude':
            if (!args) {
                window.chatModule.addMessage('system', 'Error: Please provide text or a template name. Usage: /claude [text] or /claude:[template-name]');
            } else {
                // Check if the first argument is a template name or direct text
                const parts = args.trim().split(/\s+/);
                const firstPart = parts[0];
                
                // Check if the first part looks like a template name (no spaces, punctuation, etc)
                const isTemplateName = /^[a-zA-Z0-9_-]+$/.test(firstPart) && !firstPart.includes('=');
                
                if (isTemplateName) {
                    // Fetch templates to check if it matches
                    fetch('/api/claude-templates')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! Status: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data && data.templates && data.templates[firstPart]) {
                                // It's a template, handle it as a template
                                handleClaudeTemplate(args);
                            } else {
                                // Not a valid template, treat the whole thing as direct text to Claude
                                sendDirectToClaudePrompt(args);
                            }
                        })
                        .catch(error => {
                            // If we can't check templates, assume it's direct text
                            console.error('Error checking templates:', error);
                            sendDirectToClaudePrompt(args);
                        });
                } else {
                    // Not a template name format, send directly to Claude
                    sendDirectToClaudePrompt(args);
                }
            }
            break;
            
        default:
            // Check if this is a claude template command with colon syntax (/claude:template-name)
            if (cmd.startsWith('claude:')) {
                const templateName = cmd.substring(7); // Remove 'claude:'
                handleClaudeTemplate(templateName + (args ? ' ' + args : ''));
            } else {
                window.chatModule.addMessage('system', `Unknown command: ${cmd}. Type /help for available commands.`);
            }
    }
    
    // Ensure chat input retains focus after command execution
    setTimeout(() => {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.focus();
        }
    }, 0);
}

// Show help message
function showHelp() {
    let helpMessage = '**Available Commands:**\n\n';
    
    commands.forEach(cmd => {
        helpMessage += `- \`${cmd.name}\` - ${cmd.description}\n`;
    });
    
    helpMessage += '\n**UI Controls:**\n';
    helpMessage += '- Enter - Send message\n';
    helpMessage += '- Shift+Enter - New line\n';
    helpMessage += '- Up Arrow - Navigate to previous messages in history\n';
    helpMessage += '- Down Arrow - Navigate to more recent messages in history\n';
    
    window.chatModule.addMessage('system', helpMessage);
}

// Show details for a specific item
function showItemDetails(itemId) {
    // First, check tasks
    const task = window.tasks ? window.tasks.find(t => t.task_id === itemId) : null;
    
    if (task) {
        let details = `**Task Details: ${task.task_id}**\n\n`;
        details += `- **Title:** ${task.title}\n`;
        details += `- **Status:** ${task.status}\n`;
        details += `- **Project:** ${task.project_name || task.project_id}\n`;
        details += `- **Priority:** ${task.priority}\n`;
        details += `- **Created:** ${new Date(task.created_at).toLocaleString()}\n`;
        
        if (task.description) {
            details += `\n**Description:**\n${task.description}\n`;
        }
        
        window.chatModule.addMessage('system', details);
        return;
    }
    
    // Then check events
    const event = window.events ? window.events.find(e => e.event_id === itemId) : null;
    
    if (event) {
        let details = `**Event Details: ${event.event_id}**\n\n`;
        details += `- **Title:** ${event.title}\n`;
        details += `- **Type:** ${event.type}\n`;
        details += `- **Start:** ${new Date(event.start_time).toLocaleString()}\n`;
        
        if (event.end_time) {
            details += `- **End:** ${new Date(event.end_time).toLocaleString()}\n`;
        }
        
        if (event.location) {
            details += `- **Location:** ${event.location}\n`;
        }
        
        if (event.description) {
            details += `\n**Description:**\n${event.description}\n`;
        }
        
        window.chatModule.addMessage('system', details);
        return;
    }
    
    // If not found
    window.chatModule.addMessage('system', `No item found with ID: ${itemId}`);
}

// Handle command autocomplete
export function handleCommandAutocomplete(event) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find if we're typing a command (line starts with /)
    const lastLineStart = text.lastIndexOf('\n', cursorPosition - 1) + 1;
    const currentLine = text.substring(lastLineStart, cursorPosition);
    
    // If current line starts with slash, show command suggestions
    if (currentLine.startsWith('/')) {
        const commandText = currentLine.split(' ')[0]; // Get just the command part
        
        // Filter matching commands
        commandSuggestions = commands.filter(cmd => 
            cmd.name.startsWith(commandText.toLowerCase())
        );
        
        if (commandSuggestions.length > 0) {
            showCommandSuggestions();
            input.classList.add('has-command');
        } else {
            hideCommandSuggestions();
        }
    } else {
        hideCommandSuggestions();
        input.classList.remove('has-command');
    }
}

// Show command suggestions
function showCommandSuggestions() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) return;
    
    commandSuggestionsElement.innerHTML = '';
    
    // Create suggestion elements
    commandSuggestions.forEach((cmd, index) => {
        const item = document.createElement('div');
        item.className = 'command-item';
        item.dataset.index = index;
        
        const name = document.createElement('span');
        name.className = 'command-name';
        name.textContent = cmd.name;
        
        const description = document.createElement('span');
        description.className = 'command-description';
        description.textContent = cmd.description;
        
        item.appendChild(name);
        item.appendChild(description);
        
        // Add click handler
        item.addEventListener('click', () => {
            insertCommand(index);
        });
        
        commandSuggestionsElement.appendChild(item);
    });
    
    // Reset active suggestion
    activeCommandIndex = -1;
    
    // Show suggestions
    commandSuggestionsElement.classList.add('visible');
}

// Hide command suggestions
function hideCommandSuggestions() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) return;
    
    commandSuggestionsElement.classList.remove('visible');
    commandSuggestions = [];
    activeCommandIndex = -1;
}

// Handle keyboard navigation for command suggestions
// Send text directly to Claude without template processing
function sendDirectToClaudePrompt(text) {
    // For direct Claude prompts, we'll add a special prefix
    const promptPrefix = "Claude: ";
    const promptText = promptPrefix + text.trim();
    
    // Send the message
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = promptText;
        window.chatModule.sendMessage();
    } else {
        window.chatModule.addMessage('system', 'Error: Could not send message to Claude.');
    }
}

// Handle Claude template commands
function handleClaudeTemplate(argString) {
    // First fetch the templates from the server
    fetch('/api/claude-templates')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Parse the command structure (template name and any args)
            const parts = argString.trim().split(/\s+/);
            const templateName = parts[0];
            
            if (!data || !data.templates || !data.templates[templateName]) {
                window.chatModule.addMessage('system', `Error: Template "${templateName}" not found in configuration.`);
                return;
            }
            
            let templateText = data.templates[templateName];
            
            // Check if there are arguments to process
            if (parts.length > 1) {
                // Extract arguments in key=value format
                const argPairs = {};
                const remainingText = [];
                
                for (let i = 1; i < parts.length; i++) {
                    const part = parts[i];
                    // Check if it's a key=value pair
                    if (part.includes('=')) {
                        const [key, value] = part.split('=');
                        // Remove quotes if they exist
                        argPairs[key] = value.replace(/^"(.*)"$/, '$1').replace(/^'(.*)'$/, '$1');
                    } else {
                        // If it's not a key=value pair, add it to remaining text
                        remainingText.push(part);
                    }
                }
                
                // Replace variables in the template
                for (const [key, value] of Object.entries(argPairs)) {
                    const varRegex = new RegExp('\\$' + key, 'g');
                    templateText = templateText.replace(varRegex, value);
                }
                
                // Append any remaining text that wasn't in key=value format
                if (remainingText.length > 0) {
                    templateText += ' ' + remainingText.join(' ');
                }
            }
            
            // Send the templated message
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.value = templateText;
                window.chatModule.sendMessage();
            } else {
                window.chatModule.addMessage('system', 'Error: Could not send templated message.');
            }
        })
        .catch(error => {
            console.error('Error fetching Claude templates:', error);
            window.chatModule.addMessage('system', `Error: Could not fetch Claude templates. ${error.message}`);
        });
}

export function handleCommandKeyNavigation(event) {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) return;
    
    // Only process if command suggestions are visible
    if (!commandSuggestionsElement.classList.contains('visible') || commandSuggestions.length === 0) {
        return;
    }
    
    switch (event.key) {
        case 'ArrowDown':
            // Move selection down
            event.preventDefault();
            activeCommandIndex = (activeCommandIndex + 1) % commandSuggestions.length;
            updateActiveCommand();
            break;
            
        case 'ArrowUp':
            // Move selection up
            event.preventDefault();
            activeCommandIndex = (activeCommandIndex - 1 + commandSuggestions.length) % commandSuggestions.length;
            updateActiveCommand();
            break;
            
        case 'Tab':
        case 'Enter':
            // Insert selected command
            if (activeCommandIndex >= 0) {
                event.preventDefault();
                insertCommand(activeCommandIndex);
            } else if (commandSuggestions.length === 1) {
                event.preventDefault();
                insertCommand(0);
            }
            break;
            
        case 'Escape':
            // Close suggestions
            event.preventDefault();
            hideCommandSuggestions();
            break;
    }
}

// Update active command highlighting
function updateActiveCommand() {
    const commandSuggestionsElement = document.getElementById('command-suggestions');
    if (!commandSuggestionsElement) return;
    
    // Remove active class from all items
    const items = commandSuggestionsElement.querySelectorAll('.command-item');
    items.forEach(item => item.classList.remove('selected'));
    
    // Add active class to selected item
    if (activeCommandIndex >= 0 && activeCommandIndex < items.length) {
        items[activeCommandIndex].classList.add('selected');
        
        // Ensure the active item is visible in the scroll area
        const activeItem = items[activeCommandIndex];
        const container = commandSuggestionsElement;
        
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

// Insert command suggestion
function insertCommand(index) {
    if (index < 0 || index >= commandSuggestions.length) return;
    
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const text = input.value;
    const cursorPosition = input.selectionStart;
    
    // Find the start of the current command
    const lastLineStart = text.lastIndexOf('\n', cursorPosition - 1) + 1;
    const currentLineEnd = text.indexOf('\n', cursorPosition);
    const endPos = currentLineEnd === -1 ? text.length : currentLineEnd;
    
    // Get the command and any existing arguments
    const currentLine = text.substring(lastLineStart, endPos);
    const commandParts = currentLine.split(' ');
    
    // Check if there are arguments or not
    const hasArgs = commandParts.length > 1;
    const selectedCommand = commandSuggestions[index];
    
    let newText;
    if (hasArgs) {
        // Replace just the command part, keep arguments
        newText = text.substring(0, lastLineStart) +
               selectedCommand.name + ' ' +
               commandParts.slice(1).join(' ') +
               text.substring(endPos);
    } else {
        // Replace the entire command
        newText = text.substring(0, lastLineStart) +
               selectedCommand.name + 
               (selectedCommand.requiresArg ? ' ' : '') +
               text.substring(endPos);
    }
    
    // Update input value
    input.value = newText;
    
    // Set cursor position after the inserted command
    const newPosition = lastLineStart + selectedCommand.name.length + (selectedCommand.requiresArg ? 1 : 0);
    input.setSelectionRange(newPosition, newPosition);
    
    // Focus the input
    input.focus();
    
    // Hide suggestions
    hideCommandSuggestions();
    
    // Resize textarea to fit new content
    window.chatModule.resizeTextarea();
}