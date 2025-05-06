/**
 * Filter controls module for RadBot UI
 */

// Filter state
let selectedProjects = ['all'];
let selectedStatuses = ['all'];
let projects = [];

// Export references to be used by other modules
export function getFilterState() {
    return {
        selectedProjects,
        selectedStatuses,
        projects
    };
}

// Update projects list
export function setProjects(projectsList) {
    projects = projectsList;
}

// Initialize filter controls
export function initFilters() {
    console.log('Setting up filter controls');
    
    // Reset any previous event handlers
    if (window.closeDropdownsHandler) {
        document.removeEventListener('click', window.closeDropdownsHandler);
    }
    
    // New global click handler for document
    window.closeDropdownsHandler = function(e) {
        const projectFilterBtn = document.getElementById('project-filter-btn');
        const projectFilterContent = document.getElementById('project-filter-content');
        const statusFilterBtn = document.getElementById('status-filter-btn');
        const statusFilterContent = document.getElementById('status-filter-content');
        
        // Check if click is outside all dropdown elements
        const isOutsideProjectDropdown = projectFilterContent && 
                                       !projectFilterContent.contains(e.target) && 
                                       projectFilterBtn && 
                                       !projectFilterBtn.contains(e.target);
        
        const isOutsideStatusDropdown = statusFilterContent && 
                                      !statusFilterContent.contains(e.target) && 
                                      statusFilterBtn && 
                                      !statusFilterBtn.contains(e.target);
        
        // If clicking outside dropdowns, close them
        if (isOutsideProjectDropdown && isOutsideStatusDropdown) {
            if (projectFilterContent && projectFilterContent.classList.contains('show')) {
                projectFilterContent.classList.remove('show');
            }
            
            if (statusFilterContent && statusFilterContent.classList.contains('show')) {
                statusFilterContent.classList.remove('show');
            }
        }
    };
    
    // Add the document listener
    document.addEventListener('click', window.closeDropdownsHandler);
    
    // Event type filter
    const eventTypeFilter = document.getElementById('event-type-filter');
    if (eventTypeFilter) {
        eventTypeFilter.addEventListener('change', () => {
            console.log(`Event type filter changed to: ${eventTypeFilter.value}`);
            window.renderEvents();
        });
    }
    
    setupProjectFilter();
    setupStatusFilter();
}

// Setup project filter
function setupProjectFilter() {
    let projectFilterBtn = document.getElementById('project-filter-btn');
    const projectFilterContent = document.getElementById('project-filter-content');
    
    if (projectFilterBtn && projectFilterContent) {
        // Remove any existing listeners to prevent duplicates
        const newProjectFilterBtn = projectFilterBtn.cloneNode(true);
        projectFilterBtn.parentNode.replaceChild(newProjectFilterBtn, projectFilterBtn);
        projectFilterBtn = newProjectFilterBtn;
        
        // Remove any existing close buttons first
        const existingCloseBtn = projectFilterContent.querySelector('.dropdown-close-btn');
        if (existingCloseBtn) {
            projectFilterContent.removeChild(existingCloseBtn);
        }
        
        // Add a direct close button to the dropdown 
        const closeBtn = document.createElement('button');
        closeBtn.className = 'dropdown-close-btn';
        closeBtn.innerHTML = '×';
        closeBtn.title = "Close dropdown";
        
        // Use addEventListener to ensure proper event handling
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            projectFilterContent.classList.remove('show');
        });
        
        projectFilterContent.appendChild(closeBtn);
        
        // Toggle dropdown with new approach
        projectFilterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle this dropdown
            projectFilterContent.classList.toggle('show');
            
            // Hide status dropdown if it's open
            const statusFilterContent = document.getElementById('status-filter-content');
            if (statusFilterContent && statusFilterContent.classList.contains('show')) {
                statusFilterContent.classList.remove('show');
            }
            
            // Force a repaint to ensure visibility
            setTimeout(() => {
                if (projectFilterContent.classList.contains('show')) {
                    projectFilterContent.style.display = 'block';
                    // Bring to front
                    projectFilterContent.style.zIndex = "500";
                    // Scroll to top when opened
                    projectFilterContent.scrollTop = 0;
                }
            }, 0);
        });
        
        // Handle "All Projects" checkbox
        const allProjectsCheckbox = document.getElementById('project-all');
        if (allProjectsCheckbox) {
            // Replace the checkbox with a fresh clone to remove any existing event listeners
            const newAllProjectsCheckbox = allProjectsCheckbox.cloneNode(true);
            allProjectsCheckbox.parentNode.replaceChild(newAllProjectsCheckbox, allProjectsCheckbox);
            
            // Stop propagation for all-projects checkbox with a simpler approach
            newAllProjectsCheckbox.onclick = function(e) {
                e.stopPropagation();
                return true; // Allow the default checkbox behavior
            };
            
            // Stop propagation for label clicks with a simpler approach
            const allProjectsLabel = document.querySelector('label[for="project-all"]');
            if (allProjectsLabel) {
                allProjectsLabel.onclick = function(e) {
                    e.stopPropagation();
                    return true; // Allow the default label behavior
                };
            }
            
            newAllProjectsCheckbox.addEventListener('change', (e) => {
                const projectCheckboxes = projectFilterContent.querySelectorAll('input[type="checkbox"]:not(#project-all)');
                
                if (e.target.checked) {
                    // Uncheck all other projects
                    projectCheckboxes.forEach(cb => {
                        cb.checked = false;
                    });
                    
                    selectedProjects = ['all'];
                    projectFilterBtn.textContent = 'All Projects';
                } else {
                    // Ensure at least one project is selected
                    const anyChecked = Array.from(projectCheckboxes).some(cb => cb.checked);
                    if (!anyChecked) {
                        e.target.checked = true;  // Recheck "All Projects" if nothing else is selected
                    }
                }
                
                window.renderTasks();
            });
        }
        
        // Add project checkboxes dynamically from available projects
        if (projects && projects.length > 0) {
            projects.forEach(project => {
                const projectId = project.project_id;
                const projectName = project.name || projectId;
                
                // Check if this project checkbox already exists
                const existingCheckbox = document.getElementById(`project-${projectId}`);
                if (!existingCheckbox) {
                    const option = document.createElement('div');
                    option.className = 'filter-option';
                    
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = `project-${projectId}`;
                    checkbox.value = projectId;
                    
                    const label = document.createElement('label');
                    label.htmlFor = `project-${projectId}`;
                    label.textContent = projectName;
                    
                    // Stop propagation for checkbox clicks
                    checkbox.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                    
                    // Stop propagation for label clicks
                    label.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                    
                    checkbox.addEventListener('change', (e) => {
                        e.stopPropagation();
                        const allCheckbox = document.getElementById('project-all');
                        
                        if (checkbox.checked) {
                            // Uncheck "All Projects"
                            if (allCheckbox) allCheckbox.checked = false;
                            
                            // Add to selected projects
                            if (!selectedProjects.includes(projectId)) {
                                selectedProjects = selectedProjects.filter(id => id !== 'all');
                                selectedProjects.push(projectId);
                            }
                        } else {
                            // Remove from selected projects
                            selectedProjects = selectedProjects.filter(id => id !== projectId);
                            
                            // If no projects selected, check "All Projects"
                            if (selectedProjects.length === 0 && allCheckbox) {
                                allCheckbox.checked = true;
                                selectedProjects = ['all'];
                            }
                        }
                        
                        // Update button text
                        if (selectedProjects.includes('all')) {
                            projectFilterBtn.textContent = 'All Projects';
                        } else if (selectedProjects.length === 1) {
                            const selectedProject = projects.find(p => p.project_id === selectedProjects[0]);
                            projectFilterBtn.textContent = selectedProject ? (selectedProject.name || selectedProject.project_id) : selectedProjects[0];
                        } else {
                            projectFilterBtn.textContent = `${selectedProjects.length} Projects`;
                        }
                        
                        window.renderTasks();
                    });
                    
                    option.appendChild(checkbox);
                    option.appendChild(label);
                    projectFilterContent.appendChild(option);
                }
            });
        }
    }
}

// Setup status filter
function setupStatusFilter() {
    let statusFilterBtn = document.getElementById('status-filter-btn');
    const statusFilterContent = document.getElementById('status-filter-content');
    
    if (statusFilterBtn && statusFilterContent) {
        // Remove any existing listeners to prevent duplicates
        const newStatusFilterBtn = statusFilterBtn.cloneNode(true);
        statusFilterBtn.parentNode.replaceChild(newStatusFilterBtn, statusFilterBtn);
        statusFilterBtn = newStatusFilterBtn;
        
        // Remove any existing close buttons first
        const existingCloseStatusBtn = statusFilterContent.querySelector('.dropdown-close-btn');
        if (existingCloseStatusBtn) {
            statusFilterContent.removeChild(existingCloseStatusBtn);
        }
        
        // Add a direct close button to the dropdown
        const closeStatusBtn = document.createElement('button');
        closeStatusBtn.className = 'dropdown-close-btn';
        closeStatusBtn.innerHTML = '×';
        closeStatusBtn.title = "Close dropdown";
        
        // Use addEventListener to ensure proper event handling
        closeStatusBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            statusFilterContent.classList.remove('show');
        });
        
        statusFilterContent.appendChild(closeStatusBtn);
        
        // Toggle dropdown with new approach
        statusFilterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle this dropdown
            statusFilterContent.classList.toggle('show');
            
            // Hide project dropdown if it's open
            const projectFilterContent = document.getElementById('project-filter-content');
            if (projectFilterContent && projectFilterContent.classList.contains('show')) {
                projectFilterContent.classList.remove('show');
            }
            
            // Force a repaint to ensure visibility
            setTimeout(() => {
                if (statusFilterContent.classList.contains('show')) {
                    statusFilterContent.style.display = 'block';
                    // Bring to front
                    statusFilterContent.style.zIndex = "500";
                    // Scroll to top when opened
                    statusFilterContent.scrollTop = 0;
                }
            }, 0);
        });
        
        // Handle "All Statuses" checkbox
        const allStatusesCheckbox = document.getElementById('status-all');
        if (allStatusesCheckbox) {
            // Replace the checkbox with a fresh clone to remove any existing event listeners
            const newAllStatusesCheckbox = allStatusesCheckbox.cloneNode(true);
            allStatusesCheckbox.parentNode.replaceChild(newAllStatusesCheckbox, allStatusesCheckbox);
            
            // Stop propagation for all-statuses checkbox with a simpler approach
            newAllStatusesCheckbox.onclick = function(e) {
                e.stopPropagation();
                return true; // Allow the default checkbox behavior
            };
            
            // Stop propagation for label clicks with a simpler approach
            const allStatusesLabel = document.querySelector('label[for="status-all"]');
            if (allStatusesLabel) {
                allStatusesLabel.onclick = function(e) {
                    e.stopPropagation();
                    return true; // Allow the default label behavior
                };
            }
            
            newAllStatusesCheckbox.addEventListener('change', (e) => {
                const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
                
                if (e.target.checked) {
                    // Uncheck all other statuses
                    statusCheckboxes.forEach(cb => {
                        cb.checked = false;
                    });
                    
                    selectedStatuses = ['all'];
                    statusFilterBtn.textContent = 'All Statuses';
                } else {
                    // Ensure at least one status is selected
                    const anyChecked = Array.from(statusCheckboxes).some(cb => cb.checked);
                    if (!anyChecked) {
                        e.target.checked = true;  // Recheck "All Statuses" if nothing else is selected
                    }
                }
                
                window.renderTasks();
            });
        }
        
        // Status checkboxes event handlers
        const statusCheckboxes = statusFilterContent.querySelectorAll('input[type="checkbox"]:not(#status-all)');
        statusCheckboxes.forEach(checkbox => {
            // Stop propagation for checkbox clicks
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            // Stop propagation for label clicks
            const label = document.querySelector(`label[for="${checkbox.id}"]`);
            if (label) {
                label.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
            }
            
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                const allCheckbox = document.getElementById('status-all');
                
                if (checkbox.checked) {
                    // Uncheck "All Statuses"
                    if (allCheckbox) allCheckbox.checked = false;
                    
                    // Add to selected statuses
                    if (!selectedStatuses.includes(checkbox.value)) {
                        selectedStatuses = selectedStatuses.filter(status => status !== 'all');
                        selectedStatuses.push(checkbox.value);
                    }
                } else {
                    // Remove from selected statuses
                    selectedStatuses = selectedStatuses.filter(status => status !== checkbox.value);
                    
                    // If no statuses selected, check "All Statuses"
                    if (selectedStatuses.length === 0 && allCheckbox) {
                        allCheckbox.checked = true;
                        selectedStatuses = ['all'];
                    }
                }
                
                // Update button text
                if (selectedStatuses.includes('all')) {
                    statusFilterBtn.textContent = 'All Statuses';
                } else if (selectedStatuses.length === 1) {
                    // Capitalize status name
                    const statusName = selectedStatuses[0].charAt(0).toUpperCase() + selectedStatuses[0].slice(1);
                    statusFilterBtn.textContent = statusName;
                } else {
                    statusFilterBtn.textContent = `${selectedStatuses.length} Statuses`;
                }
                
                window.renderTasks();
            });
        });
    }
}