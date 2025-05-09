/**
 * RadBot Web Interface Client - Agent Configuration Module
 * 
 * This module handles agent configuration, model selection, and UUID generation.
 */

// Format event type for display
export function formatEventType(type) {
    // Handle null or undefined types
    if (!type) return 'UNKNOWN';
    
    // Handle common variations
    const typeStr = type.toString().toLowerCase().trim();
    
    switch (typeStr) {
        case 'tool_call':
        case 'toolcall':
        case 'tool call':
        case 'tool-call':
            return 'TOOL CALL';
            
        case 'agent_transfer':
        case 'agenttransfer':
        case 'agent transfer':
        case 'agent-transfer':
            return 'AGENT TRANSFER';
            
        case 'planner':
        case 'planning':
        case 'plan':
            return 'PLANNER';
            
        case 'other':
        case 'system':
        case 'misc':
        case 'unknown':
            return 'SYSTEM';
            
        default:
            // Convert to uppercase for consistency
            return typeStr.toUpperCase();
    }
}

// Show event details
export function showEventDetails(event) {
    console.log('Showing event details:', event);
    
    // First, ensure the events tile is visible - this is using the tiling system
    let eventsPanel = document.querySelector('[data-content="events"]');
    if (!eventsPanel) {
        console.warn('Events panel not found in DOM, attempting to open it');
        // Try to trigger events panel command
        document.dispatchEvent(new CustomEvent('command:events'));
        
        // Wait a moment and try again
        setTimeout(() => {
            eventsPanel = document.querySelector('[data-content="events"]');
            if (eventsPanel) {
                console.log('Events panel now found, attempting to show details again');
                // Try again after panel is opened
                showEventDetails(event);
            } else {
                console.error('Could not find events panel after attempting to open it');
            }
        }, 300);
        return;
    }
    
    // Now check for the details container
    const detailsContainer = document.getElementById('event-details-content');
    if (!detailsContainer) {
        console.warn('Event details container not found in DOM - attempting to create it');
        
        // Look for detail panel where we can put the content
        const detailPanel = document.querySelector('.detail-panel');
        if (detailPanel) {
            console.log('Found detail-panel, creating event details content');
            
            // Create event details content container
            const detailsContent = document.createElement('div');
            detailsContent.className = 'event-details-content';
            detailsContent.id = 'event-details-content';
            
            // Find existing tile-content if it exists or create one
            let tileContent = detailPanel.querySelector('.tile-content');
            if (!tileContent) {
                tileContent = document.createElement('div');
                tileContent.className = 'tile-content event-details';
                detailPanel.appendChild(tileContent);
            }
            
            // Add details content to the tile content
            tileContent.innerHTML = ''; // Clear existing content
            tileContent.appendChild(detailsContent);
            console.log('Created event-details-content container');
            
            // Now try to use the newly created container
            setTimeout(() => showEventDetails(event), 100);
            return;
        }
        
        console.error('Could not find detail panel to add event details content');
        return;
    }
    
    console.log('Found event-details-content, rendering details');
    
    // Clear existing content
    detailsContainer.innerHTML = '';
    
    // Main details
    const headerSection = document.createElement('div');
    headerSection.className = 'detail-section';
    
    const title = document.createElement('h4');
    // Use the most descriptive field available for the title
    const titleText = event.summary || event.title || (event.tool_name ? `Tool Call: ${event.tool_name}` : `Event: ${event.type}`);
    title.innerHTML = `<span>${titleText}</span>`;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'detail-timestamp';
    timestamp.textContent = new Date(event.timestamp || event.start_time).toLocaleString();
    
    headerSection.appendChild(title);
    headerSection.appendChild(timestamp);
    
    // Event ID - hidden by default but can be shown for debugging
    const idSection = document.createElement('div');
    idSection.className = 'detail-section detail-small';
    
    const idValue = document.createElement('div');
    idValue.className = 'detail-id';
    const eventId = event.event_id || 'N/A';
    idValue.textContent = `Event ID: ${eventId}`;
    idSection.appendChild(idValue);
    
    // Type section with styled badge
    const typeSection = document.createElement('div');
    typeSection.className = 'detail-section';
    
    const typeTitle = document.createElement('h4');
    typeTitle.textContent = 'Event Type: ';
    const typeValue = document.createElement('span');
    typeValue.className = `event-type-badge ${event.type}`;
    typeValue.textContent = formatEventType(event.type);
    typeTitle.appendChild(typeValue);
    
    typeSection.appendChild(typeTitle);
    
    // Add main sections to container
    detailsContainer.appendChild(headerSection);
    detailsContainer.appendChild(typeSection);
    
    // Process specific fields based on event type
    if (event.type === 'tool_call' || event.category === 'tool_call' || 
        event.function_call || event.function_response || 
        event.tool_calls || event.tool_results) {
        
        // Tool call sections
        if (event.tool_name) {
            const toolSection = document.createElement('div');
            toolSection.className = 'detail-section';
            
            const toolTitle = document.createElement('h4');
            toolTitle.textContent = 'Tool:';
            toolSection.appendChild(toolTitle);
            
            const toolName = document.createElement('div');
            toolName.className = 'detail-value';
            toolName.textContent = event.tool_name;
            toolSection.appendChild(toolName);
            
            detailsContainer.appendChild(toolSection);
        }
        
        // Function call details
        if (event.function_call) {
            // Function call specific rendering
            const functionCallSection = document.createElement('div');
            functionCallSection.className = 'detail-section';
            
            const functionTitle = document.createElement('h4');
            functionTitle.textContent = 'Function Call:';
            functionCallSection.appendChild(functionTitle);
            
            if (event.function_call.name) {
                const funcName = document.createElement('div');
                funcName.className = 'detail-value';
                funcName.textContent = event.function_call.name;
                functionCallSection.appendChild(funcName);
            }
            
            if (event.function_call.args) {
                const argsValue = document.createElement('pre');
                argsValue.className = 'detail-json';
                argsValue.innerHTML = formatJsonSyntax(event.function_call.args);
                functionCallSection.appendChild(argsValue);
            }
            
            detailsContainer.appendChild(functionCallSection);
        }
        
        // Function response details
        if (event.function_response) {
            const functionResponseSection = document.createElement('div');
            functionResponseSection.className = 'detail-section';
            
            const responseTitle = document.createElement('h4');
            responseTitle.textContent = 'Function Response:';
            functionResponseSection.appendChild(responseTitle);
            
            if (event.function_response.name) {
                const funcName = document.createElement('div');
                funcName.className = 'detail-value';
                funcName.textContent = event.function_response.name;
                functionResponseSection.appendChild(funcName);
            }
            
            if (event.function_response.response) {
                const responseValue = document.createElement('pre');
                responseValue.className = 'detail-json';
                responseValue.innerHTML = formatJsonSyntax(event.function_response.response);
                functionResponseSection.appendChild(responseValue);
            }
            
            detailsContainer.appendChild(functionResponseSection);
        }
        
        // Input section (regular tool call)
        if (event.input) {
            const inputSection = document.createElement('div');
            inputSection.className = 'detail-section';
            
            const inputTitle = document.createElement('h4');
            inputTitle.textContent = 'Input:';
            inputSection.appendChild(inputTitle);
            
            const inputValue = document.createElement('pre');
            inputValue.className = 'detail-json';
            inputValue.innerHTML = formatJsonSyntax(event.input);
            inputSection.appendChild(inputValue);
            
            detailsContainer.appendChild(inputSection);
        }
        
        // Output section (regular tool call)
        if (event.output) {
            const outputSection = document.createElement('div');
            outputSection.className = 'detail-section';
            
            const outputTitle = document.createElement('h4');
            outputTitle.textContent = 'Output:';
            outputSection.appendChild(outputTitle);
            
            const outputValue = document.createElement('pre');
            outputValue.className = 'detail-json';
            outputValue.innerHTML = formatJsonSyntax(event.output);
            outputSection.appendChild(outputValue);
            
            detailsContainer.appendChild(outputSection);
        }
    } else if (event.type === 'agent_transfer') {
        // Agent transfer details
        const transferSection = document.createElement('div');
        transferSection.className = 'detail-section';
        
        const transferTitle = document.createElement('h4');
        transferTitle.textContent = 'Transfer Details:';
        transferSection.appendChild(transferTitle);
        
        const transferDetails = document.createElement('div');
        transferDetails.className = 'transfer-details';
        
        if (event.from_agent) {
            const fromAgent = document.createElement('div');
            fromAgent.className = 'detail-item';
            fromAgent.innerHTML = `<strong>From:</strong> ${event.from_agent}`;
            transferDetails.appendChild(fromAgent);
        }
        
        if (event.to_agent) {
            const toAgent = document.createElement('div');
            toAgent.className = 'detail-item';
            toAgent.innerHTML = `<strong>To:</strong> ${event.to_agent}`;
            transferDetails.appendChild(toAgent);
        }
        
        transferSection.appendChild(transferDetails);
        detailsContainer.appendChild(transferSection);
    } else if (event.type === 'planner') {
        // Planner details
        if (event.plan) {
            const planSection = document.createElement('div');
            planSection.className = 'detail-section';
            
            const planTitle = document.createElement('h4');
            planTitle.textContent = 'Plan:';
            planSection.appendChild(planTitle);
            
            const planDetails = document.createElement('div');
            planDetails.className = 'plan-details';
            
            // Handle plan query if available
            if (event.plan.query) {
                const query = document.createElement('div');
                query.className = 'detail-item';
                query.innerHTML = `<strong>Query:</strong> ${event.plan.query}`;
                planDetails.appendChild(query);
            }
            
            // Handle plan steps if available
            if (event.plan.steps && Array.isArray(event.plan.steps)) {
                const stepsContainer = document.createElement('div');
                stepsContainer.className = 'detail-item';
                
                const stepsTitle = document.createElement('strong');
                stepsTitle.textContent = 'Steps:';
                stepsContainer.appendChild(stepsTitle);
                
                const stepsList = document.createElement('ol');
                stepsList.className = 'steps-list';
                
                event.plan.steps.forEach(step => {
                    const stepItem = document.createElement('li');
                    stepItem.textContent = step;
                    stepsList.appendChild(stepItem);
                });
                
                stepsContainer.appendChild(stepsList);
                planDetails.appendChild(stepsContainer);
            }
            
            planSection.appendChild(planDetails);
            detailsContainer.appendChild(planSection);
        }
    } else if (event.type === 'model_response') {
        // Model response content
        if (event.text) {
            const textSection = document.createElement('div');
            textSection.className = 'detail-section';
            
            const textTitle = document.createElement('h4');
            textTitle.textContent = 'Response:';
            textSection.appendChild(textTitle);
            
            const textContent = document.createElement('pre');
            textContent.className = 'response-content';
            textContent.textContent = event.text;
            textSection.appendChild(textContent);
            
            detailsContainer.appendChild(textSection);
        }
    }
    
    // Add technical details section for all event types
    if (event.details && Object.keys(event.details).length > 0) {
        const detailsSection = document.createElement('div');
        detailsSection.className = 'detail-section technical-details';
        
        const detailsTitle = document.createElement('h4');
        detailsTitle.textContent = 'Technical Details:';
        detailsSection.appendChild(detailsTitle);
        
        const detailsContent = document.createElement('div');
        detailsContent.className = 'details-content';
        
        // Format technical details as a single JSON object instead of individual fields
        const technicalJsonContainer = document.createElement('div');
        technicalJsonContainer.className = 'json-container';
        technicalJsonContainer.style.maxHeight = '200px';
        technicalJsonContainer.style.overflowY = 'auto';
        
        const technicalJson = document.createElement('pre');
        technicalJson.className = 'detail-json';
        technicalJson.innerHTML = formatJsonSyntax(event.details);
        
        technicalJsonContainer.appendChild(technicalJson);
        detailsContent.appendChild(technicalJsonContainer);
        
        detailsSection.appendChild(detailsContent);
        detailsContainer.appendChild(detailsSection);
    }
    
    // Add event ID at the bottom for reference
    detailsContainer.appendChild(idSection);
    
    // Add category if it exists and different from type
    if (event.category && event.category !== event.type) {
        const categorySection = document.createElement('div');
        categorySection.className = 'detail-section detail-small';
        
        const categoryValue = document.createElement('div');
        categoryValue.className = 'detail-category';
        categoryValue.textContent = `Category: ${event.category}`;
        categorySection.appendChild(categoryValue);
        
        detailsContainer.appendChild(categorySection);
    }
    
    // Add a Raw JSON section to show the full event payload
    const rawSection = document.createElement('div');
    rawSection.className = 'detail-section raw-json-section';
    
    const rawHeader = document.createElement('div');
    rawHeader.className = 'raw-json-header';
    rawHeader.innerHTML = '<h4>Raw Event Data</h4><button class="toggle-raw-json">Show</button>';
    rawSection.appendChild(rawHeader);
    
    const rawContent = document.createElement('div');
    rawContent.className = 'raw-json-content hidden';
    rawContent.style.maxHeight = '300px';
    rawContent.style.overflow = 'hidden';
    
    // Create a scrollable container for the JSON
    const rawJsonContainer = document.createElement('div');
    rawJsonContainer.className = 'raw-json-container';
    rawJsonContainer.style.maxHeight = '300px';
    rawJsonContainer.style.overflowY = 'auto';
    
    // Create a pretty-printed JSON display
    const rawJson = document.createElement('pre');
    rawJson.className = 'raw-json';
    rawJson.style.maxHeight = 'none';
    rawJson.style.overflow = 'visible';
    
    // Remove circular references before stringifying
    const cleanedEvent = JSON.parse(JSON.stringify(event, (key, value) => {
        // Skip parent/circular references that can't be stringified
        if (key === 'parent' || key === '_parent') return undefined;
        return value;
    }));
    
    // Format the JSON with proper indentation and structure
    const formattedJson = JSON.stringify(cleanedEvent, null, 2);
    
    // For better readability, we'll syntax highlight the JSON
    rawJson.innerHTML = formatJsonSyntax(formattedJson);
    
    rawJsonContainer.appendChild(rawJson);
    rawContent.appendChild(rawJsonContainer);
    rawSection.appendChild(rawContent);
    
    // Add toggle behavior
    const toggleButton = rawHeader.querySelector('.toggle-raw-json');
    toggleButton.addEventListener('click', function() {
        rawContent.classList.toggle('hidden');
        this.textContent = rawContent.classList.contains('hidden') ? 'Show' : 'Hide';
    });
    
    detailsContainer.appendChild(rawSection);
}

// Format JSON with syntax highlighting
export function formatJsonSyntax(json) {
    if (!json) return '';
    
    // Handle the case where json is already an object
    if (typeof json !== 'string') {
        json = JSON.stringify(json, null, 2);
    }
    
    // Replace potentially harmful characters
    json = json.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Format different parts of JSON with specific colors
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function(match) {
        let cls = 'json-number'; // default is number
        
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key'; // keys
            } else {
                cls = 'json-string'; // strings
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean'; // booleans
        } else if (/null/.test(match)) {
            cls = 'json-null'; // null
        }
        
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

// Get initial agent and model information
export function fetchAgentInfo() {
    console.log("Fetching agent and model information");
    
    try {
        // Make a request to get the agent info from the server
        fetch('/api/agent-info')
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    console.warn("Agent info API returned error:", response.status);
                    return null;
                }
            })
            .then(data => {
                if (data) {
                    console.log("Agent info loaded from API:", data);
                    
                    // Store the agent models in window.state for later reference
                    window.state.agentModels = data.agent_models || {};
                    
                    // Add debug output of available models
                    if (data.agent_models) {
                        console.log("Available agent models:");
                        for (const [agent, model] of Object.entries(data.agent_models)) {
                            console.log(`  ${agent}: ${model}`);
                        }
                    }
                    
                    // Update agent name if available
                    if (data.agent_name) {
                        window.statusUtils.updateAgentStatus(data.agent_name);
                    }
                    
                    // Get the appropriate model for the current agent
                    const currentAgent = window.state.currentAgentName.toLowerCase();
                    let modelToUse = data.model; // Default to main model
                    
                    // Try all possible ways to find the right model
                    if (data.agent_models) {
                        // Look for an exact match first
                        if (data.agent_models[currentAgent]) {
                            modelToUse = data.agent_models[currentAgent];
                            console.log(`Found exact model match for ${currentAgent}: ${modelToUse}`);
                        } 
                        // Then try special case for scout
                        else if (currentAgent === 'scout' && data.agent_models.scout_agent) {
                            modelToUse = data.agent_models.scout_agent;
                            console.log(`Using scout_agent model for ${currentAgent}: ${modelToUse}`);
                        }
                        // Try with _agent suffix
                        else if (data.agent_models[currentAgent + '_agent']) {
                            modelToUse = data.agent_models[currentAgent + '_agent'];
                            console.log(`Using ${currentAgent}_agent model: ${modelToUse}`);
                        }
                        // Try without _agent suffix
                        else if (currentAgent.endsWith('_agent') && data.agent_models[currentAgent.replace('_agent', '')]) {
                            modelToUse = data.agent_models[currentAgent.replace('_agent', '')];
                            console.log(`Using ${currentAgent.replace('_agent', '')} model: ${modelToUse}`);
                        }
                        // For any partial match (case insensitive)
                        else {
                            for (const [agentKey, modelValue] of Object.entries(data.agent_models)) {
                                if (currentAgent.includes(agentKey.toLowerCase()) || 
                                    agentKey.toLowerCase().includes(currentAgent)) {
                                    modelToUse = modelValue;
                                    console.log(`Using partial match ${agentKey} model for ${currentAgent}: ${modelToUse}`);
                                    break;
                                }
                            }
                        }
                    }
                    
                    console.log(`Selected model for ${currentAgent}: ${modelToUse}`);
                    
                    // Update model name
                    if (modelToUse) {
                        window.statusUtils.updateModelStatus(modelToUse);
                    } else {
                        // Fallback to updateModelForCurrentAgent
                        updateModelForCurrentAgent();
                    }
                    
                    // Force a visual refresh of the status bar
                    if (typeof updateStatusBar === 'function') {
                        updateStatusBar();
                    } else if (window.statusUtils && window.statusUtils.updateStatusBar) {
                        window.statusUtils.updateStatusBar();
                    }
                } else {
                    // Fallback to updateModelForCurrentAgent
                    updateModelForCurrentAgent();
                }
            })
            .catch(error => {
                console.warn("Failed to fetch agent info:", error);
                
                // If API fails, still update the displayed model based on current agent
                updateModelForCurrentAgent();
            });
    } catch (error) {
        console.warn("Error in fetchAgentInfo:", error);
        
        // If API fails, still update the displayed model based on current agent
        updateModelForCurrentAgent();
    }
}

// Update model display based on the current agent name
export function updateModelForCurrentAgent() {
    const agentName = window.state.currentAgentName.toLowerCase();
    let modelName;
    
    // Log the current agent for debugging
    console.log(`Updating model for agent: ${agentName}`);
    
    // Try to find the model in agentModels first (from API)
    if (window.state.agentModels) {
        // Check all possible variations of the agent name
        const possibleNames = [
            agentName,
            agentName + '_agent',
            agentName.replace('_agent', '')
        ];
        
        // Try each possible name
        for (const name of possibleNames) {
            if (window.state.agentModels[name]) {
                modelName = window.state.agentModels[name];
                console.log(`Found model in agentModels for "${name}": ${modelName}`);
                break;
            }
        }
    }
    
    // If we still don't have a model, use hardcoded values matching config.yaml
    if (!modelName) {
        console.log(`No model found in agentModels, using hardcoded values`);
        
        // Check the agent name with more flexibility - EXACTLY match config.yaml values
        if (agentName.includes('scout')) {
            modelName = "gemini-2.5-pro-preview-05-06";  // Match config.yaml scout_agent
        } else if (agentName.includes('code') || agentName === "code_execution_agent") {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml code_execution_agent
        } else if (agentName.includes('search')) {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml search_agent
        } else if (agentName.includes('todo')) {
            modelName = "gemini-2.5-flash-preview-04-17";  // Match config.yaml todo_agent
        } else {
            // Default for beto/main agent - match config.yaml main_model
            modelName = "gemini-2.5-flash-preview-04-17";
        }
    }
    
    window.statusUtils.updateModelStatus(modelName);
    console.log(`Updated model based on agent ${agentName}: ${modelName}`);
    
    // Force a visual refresh of the status bar
    if (typeof updateStatusBar === 'function') {
        updateStatusBar();
    } else if (window.statusUtils && window.statusUtils.updateStatusBar) {
        window.statusUtils.updateStatusBar();
    }
}

// Generate a UUID for session ID
export function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}