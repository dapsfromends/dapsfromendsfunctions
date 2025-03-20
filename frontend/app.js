// Replace with your Azure Function App URL
const API_BASE_URL = 'https://dapsfromendsfunction2.azurewebsites.net/api';

// DOM Elements
const taskForm = document.getElementById('task-form');
const tasksContainer = document.getElementById('tasks-container');
const statusFilter = document.getElementById('status-filter');
const titleInput = document.getElementById('title');
const descriptionInput = document.getElementById('description');

// Analytics Elements
const totalTasksElement = document.getElementById('total-tasks');
const completedTasksElement = document.getElementById('completed-tasks');
const pendingTasksElement = document.getElementById('pending-tasks');
const completionPercentageElement = document.getElementById('completion-percentage');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    loadAnalytics();
});

taskForm.addEventListener('submit', createTask);
statusFilter.addEventListener('change', loadTasks);

// Functions
async function loadTasks() {
    const status = statusFilter.value;
    let url = `${API_BASE_URL}/tasks`;
    
    if (status !== 'all') {
        url += `?status=${status}`;
    }
    
    try {
        const response = await fetch(url);
        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        tasksContainer.innerHTML = '<p>Failed to load tasks. Please try again later.</p>';
    }
}

function renderTasks(tasks) {
    tasksContainer.innerHTML = '';
    
    if (tasks.length === 0) {
        tasksContainer.innerHTML = '<p>No tasks found.</p>';
        return;
    }
    
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item';
        
        const statusClass = task.status === 'completed' ? 'completed' : 'pending';
        
        taskElement.innerHTML = `
            <h3>${task.title}</h3>
            <p>${task.description || 'No description'}</p>
            <span class="status ${statusClass}">${task.status}</span>
            <div class="actions">
                ${task.status !== 'completed' ? 
                    `<button class="complete-btn" data-id="${task.id}">Mark Complete</button>` : ''}
                <button class="delete-btn" data-id="${task.id}">Delete</button>
            </div>
        `;
        
        tasksContainer.appendChild(taskElement);
    });
    
    // Add event listeners to buttons
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', completeTask);
    });
    
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', deleteTask);
    });
}

async function createTask(e) {
    e.preventDefault();
    
    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();
    
    if (!title) {
        alert('Please enter a task title');
        return;
    }
    
    const taskData = { title, description };
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            titleInput.value = '';
            descriptionInput.value = '';
            loadTasks();
            loadAnalytics();
        } else {
            alert('Failed to create task. Please try again.');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        alert('Failed to create task. Please try again later.');
    }
}

async function completeTask(e) {
    const taskId = e.target.getAttribute('data-id');
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
            method: 'PATCH'
        });
        
        if (response.ok) {
            loadTasks();
            loadAnalytics();
        } else {
            alert('Failed to complete task. Please try again.');
        }
    } catch (error) {
        console.error('Error completing task:', error);
        alert('Failed to complete task. Please try again later.');
    }
}

async function deleteTask(e) {
    const taskId = e.target.getAttribute('data-id');
    
    if (confirm('Are you sure you want to delete this task?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadTasks();
                loadAnalytics();
            } else {
                alert('Failed to delete task. Please try again.');
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            alert('Failed to delete task. Please try again later.');
        }
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/completion`);
        if (response.ok) {
            const analytics = await response.json();
            
            totalTasksElement.textContent = analytics.total_tasks;
            completedTasksElement.textContent = analytics.completed_tasks;
            pendingTasksElement.textContent = analytics.pending_tasks;
            completionPercentageElement.textContent = `${analytics.completion_percentage}%`;
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}