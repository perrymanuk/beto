/**
 * RadBot Web Interface Client - Data Services Module
 * 
 * This module handles fetching and rendering data from API endpoints
 */

import * as selectsUtils from './selects.js';
import { state, tasks, projects, events } from './app_core.js';

// Fetch tasks from API
export async function fetchTasks() {
    console.log("Fetching tasks data...");
    try {
        // Try to fetch from the real API first
        try {
            const apiUrl = 'http://localhost:8001/api/tasks'; // Use the actual task API endpoint
            console.log(`Attempting to fetch real tasks data from ${apiUrl}`);
            
            const response = await fetch(apiUrl);
            
            if (response.ok) {
                const tasksData = await response.json();
                console.log("Successfully fetched real task data:", tasksData);
                
                // The API returns tasks as a direct array
                window.tasks = tasksData || [];
                
                // We need to fetch projects separately
                try {
                    const projectsResponse = await fetch('http://localhost:8001/api/projects');
                    if (projectsResponse.ok) {
                        window.projects = await projectsResponse.json();
                        console.log("Successfully fetched real projects data:", window.projects);
                    } else {
                        console.warn("Failed to fetch projects, using default project");
                        window.projects = [{project_id: "unknown", name: "Default"}];
                    }
                } catch (projectError) {
                    console.warn("Error fetching projects:", projectError);
                    window.projects = [{project_id: "unknown", name: "Default"}];
                }
                
                // Update selects module with projects
                selectsUtils.setProjects(window.projects);
                
                renderTasks();
                return;
            } else {
                console.warn(`Real API returned error status: ${response.status}. Will use mock data instead.`);
            }
        } catch (apiError) {
            console.warn("Failed to connect to real API:", apiError);
        }
        
        // If we get here, the real API failed - use mock data
        console.log("Using mock task data");
        
        // Mock data for testing
        window.tasks = [
            { task_id: "task1", title: "Implement login screen", status: "inprogress", priority: "high", project_id: "proj1" },
            { task_id: "task2", title: "Fix navigation bug", status: "backlog", priority: "medium", project_id: "proj1" },
            { task_id: "task3", title: "Update documentation", status: "done", priority: "low", project_id: "proj2" },
            { task_id: "task4", title: "Refactor database layer", status: "backlog", priority: "high", project_id: "proj2" },
            { task_id: "task5", title: "Add unit tests", status: "inprogress", priority: "medium", project_id: "proj1" }
        ];
        
        window.projects = [
            { project_id: "proj1", name: "Frontend App" },
            { project_id: "proj2", name: "Backend API" }
        ];
        
        // Update selects module with projects
        selectsUtils.setProjects(window.projects);
        
        renderTasks();
    } catch (error) {
        console.error('Unexpected error in fetchTasks:', error);
        
        // Fall back to simple mock data if everything else fails
        window.tasks = [{ task_id: "error1", title: "Error fetching tasks", status: "backlog", priority: "high", project_id: "error" }];
        window.projects = [{ project_id: "error", name: "Error" }];
        
        selectsUtils.setProjects(window.projects);
        renderTasks();
    }
}

// Render tasks in UI
export function renderTasks() {
    const tasksContainer = document.getElementById('tasks-container');
    if (!tasksContainer) return;
    
    // Clear existing tasks
    tasksContainer.innerHTML = '';
    
    // Get the selection state
    const { selectedProject, selectedStatus } = selectsUtils.getSelectionState();
    
    // Filter tasks
    const filteredTasks = window.tasks.filter(task => {
        // Handle project filtering with both project_id and project_name
        let projectMatch = selectedProject === 'all';
        if (!projectMatch) {
            if (task.project_name) {
                // Try to match by project name if it exists on the task
                const project = window.projects.find(p => p.name === task.project_name);
                if (project) {
                    projectMatch = project.project_id === selectedProject;
                }
            }
            // If we still don't have a match, try the project_id directly
            if (!projectMatch) {
                projectMatch = task.project_id === selectedProject;
            }
        }
        
        const statusMatch = selectedStatus === 'all' || selectedStatus === task.status;
        return projectMatch && statusMatch;
    });
    
    // Sort tasks - priority first, then by status
    filteredTasks.sort((a, b) => {
        // First sort by priority
        const priorityOrder = { high: 1, medium: 2, low: 3 };
        const priorityA = priorityOrder[a.priority] || 4;
        const priorityB = priorityOrder[b.priority] || 4;
        
        if (priorityA !== priorityB) {
            return priorityA - priorityB;
        }
        
        // Then sort by status
        const statusOrder = { inprogress: 1, backlog: 2, done: 3 };
        const statusA = statusOrder[a.status] || 4;
        const statusB = statusOrder[b.status] || 4;
        
        return statusA - statusB;
    });
    
    // Render each task
    filteredTasks.forEach(task => {
        const taskItem = document.createElement('div');
        taskItem.className = `task-item ${task.status}`;
        taskItem.dataset.id = task.task_id;
        
        const taskStatus = document.createElement('div');
        taskStatus.className = `task-status-indicator ${task.status}`;
        
        const taskTitle = document.createElement('div');
        taskTitle.className = 'task-title';
        // Use description as title for API data, or title for mock data
        taskTitle.textContent = task.description || task.title || "Untitled Task";
        
        const taskProject = document.createElement('div');
        taskProject.className = 'task-project';
        
        // First try to use project_name if it exists directly on the task
        if (task.project_name) {
            taskProject.textContent = task.project_name;
        } else {
            // Fall back to looking up by project_id
            const project = window.projects.find(p => p.project_id === task.project_id);
            taskProject.textContent = project ? project.name : (task.project_id || "Unknown Project");
        }
        
        taskItem.appendChild(taskStatus);
        taskItem.appendChild(taskTitle);
        taskItem.appendChild(taskProject);
        
        // Add click handler to show task details
        taskItem.addEventListener('click', () => {
            window.commandUtils.executeCommand(`/details ${task.task_id}`);
        });
        
        tasksContainer.appendChild(taskItem);
    });
    
    // Show a message if no tasks found
    if (filteredTasks.length === 0) {
        const noTasksMsg = document.createElement('div');
        noTasksMsg.className = 'no-items-message';
        noTasksMsg.textContent = 'No tasks match the current filters';
        tasksContainer.appendChild(noTasksMsg);
    }
}

// Fetch events from API
export async function fetchEvents() {
    console.log("Fetching events data...");
    try {
        // Determine the API base URL - use current origin
        const baseUrl = `${window.location.protocol}//${window.location.host}`;
        
        // Get the current session ID - reuse the one from socket connection if available
        const sessionId = state.sessionId || localStorage.getItem('radbot_session_id') || generateUUID();
        
        // Based on custom_web_ui.md - we need to use the session API endpoint
        const apiUrl = `${baseUrl}/api/events/${sessionId}`;
        console.log(`Attempting to fetch events data from ${apiUrl}`);
        
        try {
            // Make the API request
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Parse the response
                const data = await response.json();
                console.log("Successfully fetched events data:", data);
                
                if (data && Array.isArray(data)) {
                    // Direct array of events
                    window.events = data;
                } else if (data && data.events && Array.isArray(data.events)) {
                    // Object with events array property
                    window.events = data.events;
                } else {
                    console.warn("Unexpected events data format:", data);
                    window.events = [];
                }
                
                // Render the events in the UI
                window.renderEvents();
                return;
            } else {
                // Handle error response
                console.warn(`API returned error status: ${response.status}`);
                
                // Try to get more details from error response
                try {
                    const errorData = await response.json();
                    console.warn("Error details:", errorData);
                } catch (parseError) {
                    console.warn("Could not parse error response");
                }
                
                // Use fallback data if API fails
                if (response.status === 404) {
                    console.log("No events found for this session or endpoint not found");
                    
                    // Create a demo event to show the system is working
                    window.events = [{
                        type: "model_response",
                        timestamp: new Date().toISOString(),
                        category: "model_response",
                        summary: "Welcome Message",
                        text: "Welcome to RadBot! I'm ready to assist you. Try asking me a question or giving me a task to work on.",
                        is_final: true,
                        details: {
                            "model": "gemini-pro",
                            "session_id": sessionId
                        }
                    }];
                } else {
                    // Create an error event
                    window.events = [{
                        type: "other",
                        timestamp: new Date().toISOString(),
                        category: "error",
                        summary: `API Error: ${response.status} ${response.statusText}`,
                        details: {
                            error_message: `The events API returned status code ${response.status}`,
                            service: "Events API",
                            endpoint: apiUrl,
                            status_code: response.status,
                            status_text: response.statusText
                        }
                    }];
                }
                
                window.renderEvents();
            }
        } catch (apiError) {
            // Handle API connection errors (CORS, connection refused, etc.)
            console.error("API error fetching events:", apiError);
            
            // Create a connection error event
            window.events = [{
                type: "other",
                timestamp: new Date().toISOString(),
                category: "error",
                summary: "API Connection Error",
                details: {
                    error_message: `Failed to connect to Events API: ${apiError.message}`,
                    service: "Events API",
                    endpoint: apiUrl,
                    error_type: apiError.name,
                    error_stack: apiError.stack
                }
            }];
            
            window.renderEvents();
        }
    } catch (error) {
        // Handle any unexpected errors
        console.error('Unexpected error in fetchEvents:', error);
        
        window.events = [{
            type: "other",
            timestamp: new Date().toISOString(),
            category: "error",
            summary: "Unexpected Error",
            details: {
                error_message: `An unexpected error occurred: ${error.message}`,
                error_type: error.name,
                error_stack: error.stack
            }
        }];
        
        window.renderEvents();
    }
}

// Helper function to generate UUID (moved from main file)
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}