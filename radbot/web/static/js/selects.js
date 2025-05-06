/**
 * Simple Select Component for RadBot UI
 */

// State
let selectedProject = 'all';
let selectedStatus = 'all';
let projects = [];

// DOM elements
let projectSelectBtn;
let projectSelectText;
let projectSelectDropdown;
let projectSelectContainer;

let statusSelectBtn;
let statusSelectText;
let statusSelectDropdown;
let statusSelectContainer;

// Document click handler
let documentClickHandler;

// Initialize select components
export function initSelects() {
    console.log('Initializing select components');
    
    // Track retry attempts to avoid infinite loops
    let retryCount = 0;
    const MAX_RETRIES = 5;
    
    // Attempt to initialize with a delay if elements don't exist yet
    const tryInit = () => {
        // If tasks panel isn't open yet, don't flood console with errors
        const tasksPanel = document.querySelector('[data-content="tasks"]');
        if (!tasksPanel) {
            console.log('Tasks panel not found in DOM, waiting for panel to be created');
            return false;
        }
        
        // Get DOM elements
        projectSelectBtn = document.getElementById('project-select-btn');
        projectSelectText = document.getElementById('project-select-text');
        projectSelectDropdown = document.getElementById('project-select-dropdown');
        projectSelectContainer = document.getElementById('project-select-container');
        
        statusSelectBtn = document.getElementById('status-select-btn');
        statusSelectText = document.getElementById('status-select-text');
        statusSelectDropdown = document.getElementById('status-select-dropdown');
        statusSelectContainer = document.getElementById('status-select-container');
        
        // Check if all required elements exist
        const elementsExist = !!projectSelectBtn && !!projectSelectDropdown && 
                              !!statusSelectBtn && !!statusSelectDropdown;
        
        // Only log element status on first attempt or when debugging
        if (retryCount === 0) {
            console.log('Found elements:', {
                projectSelectBtn: !!projectSelectBtn,
                projectSelectText: !!projectSelectText,
                projectSelectDropdown: !!projectSelectDropdown,
                projectSelectContainer: !!projectSelectContainer,
                statusSelectBtn: !!statusSelectBtn,
                statusSelectText: !!statusSelectText,
                statusSelectDropdown: !!statusSelectDropdown,
                statusSelectContainer: !!statusSelectContainer
            });
        }
        
        retryCount++;
        
        if (!elementsExist) {
            if (retryCount <= MAX_RETRIES) {
                console.log(`Selects initialization attempt ${retryCount}/${MAX_RETRIES}: Some elements not found, will retry`);
                setTimeout(tryInit, 500); // Increased delay
                return false;
            } else {
                console.warn('Max retries reached for selects initialization. Will initialize when tasks panel is opened.');
                // Set up a one-time event listener for the tasks panel being added to DOM
                const observer = new MutationObserver((mutations) => {
                    if (document.querySelector('[data-content="tasks"]')) {
                        console.log('Tasks panel detected in DOM, retrying initialization');
                        observer.disconnect();
                        retryCount = 0; // Reset counter
                        setTimeout(tryInit, 500);
                    }
                });
                observer.observe(document.body, { childList: true, subtree: true });
                return false;
            }
        }
        
        // Clear previous event listeners if re-initializing
        if (documentClickHandler) {
            document.removeEventListener('click', documentClickHandler);
        }
        
        // Ensure dropdowns are initially properly hidden
        if (projectSelectDropdown) {
            projectSelectDropdown.style.display = 'none';
            projectSelectDropdown.style.visibility = 'hidden';
            projectSelectDropdown.style.opacity = '0';
        }
        
        if (statusSelectDropdown) {
            statusSelectDropdown.style.display = 'none';
            statusSelectDropdown.style.visibility = 'hidden';
            statusSelectDropdown.style.opacity = '0';
        }
        
        // Set up project select button with direct handler
        if (projectSelectBtn) {
            // Remove old event listeners by cloning
            const newProjectBtn = projectSelectBtn.cloneNode(true);
            projectSelectBtn.parentNode.replaceChild(newProjectBtn, projectSelectBtn);
            projectSelectBtn = newProjectBtn;
            
            console.log('Adding click handler to project button');
            projectSelectBtn.addEventListener('click', function(e) {
                console.log('Project button clicked');
                e.preventDefault();
                e.stopPropagation();
                toggleProjectDropdown();
            });
        }
        
        // Set up status select button with direct handler
        if (statusSelectBtn) {
            // Remove old event listeners by cloning
            const newStatusBtn = statusSelectBtn.cloneNode(true);
            statusSelectBtn.parentNode.replaceChild(newStatusBtn, statusSelectBtn);
            statusSelectBtn = newStatusBtn;
            
            console.log('Adding click handler to status button');
            statusSelectBtn.addEventListener('click', function(e) {
                console.log('Status button clicked');
                e.preventDefault();
                e.stopPropagation();
                toggleStatusDropdown();
            });
        }
        
        // Set up radio button change listeners for status
        const statusOptions = document.querySelectorAll('#status-select-dropdown .select-option input[type="radio"]');
        console.log(`Found ${statusOptions.length} status options`);
        statusOptions.forEach(option => {
            option.addEventListener('change', function() {
                console.log('Status option changed:', this.value);
                if (this.checked) {
                    selectedStatus = this.value;
                    updateStatusUI();
                    closeAllDropdowns();
                    
                    // Call the render function to update the tasks list
                    if (typeof window.renderTasks === 'function') {
                        window.renderTasks();
                    }
                }
            });
        });
        
        // Close dropdowns when clicking outside
        documentClickHandler = function(e) {
            // If the click is outside both select containers, close all dropdowns
            if (!projectSelectContainer?.contains(e.target) && 
                !statusSelectContainer?.contains(e.target)) {
                closeAllDropdowns();
            }
        };
        
        document.addEventListener('click', documentClickHandler);
        
        return true;
    };
    
    // Try to initialize and return the result
    return tryInit();
}

// Set available projects data
export function setProjects(projectsList) {
    console.log('Setting projects in selects module:', projectsList);
    projects = projectsList;
    populateProjectOptions();
}

// Get current selection state
export function getSelectionState() {
    return {
        selectedProject,
        selectedStatus
    };
}

// Populate project options
function populateProjectOptions() {
    console.log('Populating project options');
    
    // Ensure the dropdown exists before trying to populate it
    projectSelectDropdown = document.getElementById('project-select-dropdown');
    if (!projectSelectDropdown) {
        console.log('Project select dropdown not found, will try again later');
        // Try again a bit later if tiling system is still setting up
        setTimeout(() => {
            projectSelectDropdown = document.getElementById('project-select-dropdown');
            if (projectSelectDropdown) populateProjectOptions();
        }, 500);
        return;
    }
    
    if (!projects || !projects.length) {
        console.log('No projects available to populate dropdown');
        return;
    }
    
    console.log(`Found ${projects.length} projects to populate dropdown`);
    
    // Clear existing project options except the "All Projects" option
    const allProjectsOption = projectSelectDropdown.querySelector('[data-value="all"]');
    projectSelectDropdown.innerHTML = '';
    if (allProjectsOption) {
        projectSelectDropdown.appendChild(allProjectsOption);
    }
    
    // Add project options
    console.log('Adding project options:', projects);
    projects.forEach(project => {
        const projectId = project.project_id;
        const projectName = project.name || projectId;
        
        const option = document.createElement('div');
        option.className = 'select-option';
        option.dataset.value = projectId;
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.id = `project-option-${projectId}`;
        radio.name = 'project';
        radio.value = projectId;
        
        const label = document.createElement('label');
        label.htmlFor = `project-option-${projectId}`;
        label.textContent = projectName;
        
        // Add change listener
        radio.addEventListener('change', function() {
            if (this.checked) {
                selectedProject = this.value;
                updateProjectUI();
                closeAllDropdowns();
                
                // Call the render function to update the tasks list
                if (typeof window.renderTasks === 'function') {
                    window.renderTasks();
                }
            }
        });
        
        option.appendChild(radio);
        option.appendChild(label);
        projectSelectDropdown.appendChild(option);
    });
}

// Toggle project dropdown
function toggleProjectDropdown() {
    console.log("Toggling project dropdown");
    const isOpen = projectSelectContainer.classList.contains('open');
    
    // Close all dropdowns first
    closeAllDropdowns();
    
    // If it wasn't open before, open it now
    if (!isOpen) {
        console.log("Opening project dropdown");
        
        // Force the dropdown to be visible before adding the open class
        if (projectSelectDropdown) {
            projectSelectDropdown.style.display = 'block';
            projectSelectDropdown.style.visibility = 'visible';
            projectSelectDropdown.style.opacity = '1';
        }
        
        // Add open class
        projectSelectContainer.classList.add('open');
        
        // Log the current state for debugging
        console.log("Dropdown state after opening:", {
            display: projectSelectDropdown ? projectSelectDropdown.style.display : 'unknown',
            visibility: projectSelectDropdown ? projectSelectDropdown.style.visibility : 'unknown',
            opacity: projectSelectDropdown ? projectSelectDropdown.style.opacity : 'unknown',
            containerHasOpenClass: projectSelectContainer.classList.contains('open')
        });
    }
}

// Toggle status dropdown
function toggleStatusDropdown() {
    console.log("Toggling status dropdown");
    const isOpen = statusSelectContainer.classList.contains('open');
    
    // Close all dropdowns first
    closeAllDropdowns();
    
    // If it wasn't open before, open it now
    if (!isOpen) {
        console.log("Opening status dropdown");
        
        // Force the dropdown to be visible before adding the open class
        if (statusSelectDropdown) {
            statusSelectDropdown.style.display = 'block';
            statusSelectDropdown.style.visibility = 'visible';
            statusSelectDropdown.style.opacity = '1';
        }
        
        // Add open class
        statusSelectContainer.classList.add('open');
        
        // Log the current state for debugging
        console.log("Status dropdown state after opening:", {
            display: statusSelectDropdown ? statusSelectDropdown.style.display : 'unknown',
            visibility: statusSelectDropdown ? statusSelectDropdown.style.visibility : 'unknown',
            opacity: statusSelectDropdown ? statusSelectDropdown.style.opacity : 'unknown',
            containerHasOpenClass: statusSelectContainer.classList.contains('open')
        });
    }
}

// Close all dropdowns
function closeAllDropdowns() {
    console.log("Closing all dropdowns");
    
    if (projectSelectContainer) {
        projectSelectContainer.classList.remove('open');
    }
    
    if (statusSelectContainer) {
        statusSelectContainer.classList.remove('open');
    }
    
    // Explicitly hide dropdowns
    if (projectSelectDropdown) {
        setTimeout(() => {
            projectSelectDropdown.style.visibility = 'hidden';
            projectSelectDropdown.style.opacity = '0';
        }, 50);
    }
    
    if (statusSelectDropdown) {
        setTimeout(() => {
            statusSelectDropdown.style.visibility = 'hidden';
            statusSelectDropdown.style.opacity = '0';
        }, 50);
    }
}

// Update project UI
function updateProjectUI() {
    if (!projectSelectText) return;
    
    if (selectedProject === 'all') {
        projectSelectText.textContent = 'All Projects';
    } else {
        const selectedProjectObj = projects.find(p => p.project_id === selectedProject);
        projectSelectText.textContent = selectedProjectObj ? (selectedProjectObj.name || selectedProjectObj.project_id) : selectedProject;
    }
    
    // Update the checked state of the radio buttons
    const projectRadios = document.querySelectorAll('#project-select-dropdown .select-option input[type="radio"]');
    projectRadios.forEach(radio => {
        radio.checked = radio.value === selectedProject;
    });
}

// Update status UI
function updateStatusUI() {
    if (!statusSelectText) return;
    
    if (selectedStatus === 'all') {
        statusSelectText.textContent = 'All Statuses';
    } else {
        // Capitalize status name
        const statusName = selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1);
        statusSelectText.textContent = statusName;
    }
    
    // Update the checked state of the radio buttons
    const statusRadios = document.querySelectorAll('#status-select-dropdown .select-option input[type="radio"]');
    statusRadios.forEach(radio => {
        radio.checked = radio.value === selectedStatus;
    });
}