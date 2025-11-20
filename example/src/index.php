<?php
/**
 * Enhanced Task Management App - Main Interface (Notion Style)
 */

// Load database connection
require_once __DIR__ . '/../database.php';

$conn = get_connection();
?>

<div class="notion-app">
    <div class="notion-page">
        <!-- Page Header -->
        <div class="notion-page-header">
            <div class="notion-page-title">
                <h1>My Tasks</h1>
            </div>
            
            <!-- Search Bar -->
            <div class="notion-search-container">
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="Search tasks..." 
                    class="notion-search-input"
                >
                <span class="notion-search-icon">🔍</span>
            </div>
        </div>

        <!-- Quick Add Block -->
        <div class="notion-block notion-block-new">
            <form id="addTaskForm" class="notion-inline-form">
                <div class="notion-checkbox-wrapper">
                    <input type="checkbox" class="notion-checkbox" disabled>
                </div>
                <input 
                    type="text" 
                    id="taskTitle" 
                    placeholder="Type to add a new task..." 
                    required
                    class="notion-inline-input"
                >
                <div class="notion-inline-options" style="display: none;">
                    <div class="notion-inline-form-row">
                        <input 
                            type="text" 
                            id="taskDescription" 
                            placeholder="Add a description..."
                            class="notion-inline-input notion-input-secondary"
                        >
                    </div>
                    <div class="notion-inline-form-row">
                        <select id="taskCategory" class="notion-select">
                            <option value="">No Category</option>
                        </select>
                        <select id="taskProject" class="notion-select">
                            <option value="">No Project</option>
                        </select>
                        <select id="taskPriority" class="notion-select">
                            <option value="low">Low Priority</option>
                            <option value="medium" selected>Medium Priority</option>
                            <option value="high">High Priority</option>
                        </select>
                        <input 
                            type="date" 
                            id="taskDueDate" 
                            class="notion-input-date"
                        >
                    </div>
                    <div class="notion-inline-form-row">
                        <div class="notion-tag-selector" id="taskTagSelector">
                            <span class="notion-tag-label">Tags:</span>
                            <div class="notion-tag-list" id="taskTagList"></div>
                            <button type="button" class="notion-button-small" id="addTagBtn">+ Add Tag</button>
                        </div>
                    </div>
                    <div class="notion-inline-form-row">
                        <button type="submit" class="notion-button notion-button-primary">
                            Add
                        </button>
                        <button type="button" class="notion-button notion-button-secondary" id="cancelAdd">
                            Cancel
                        </button>
                    </div>
                </div>
            </form>
        </div>

        <!-- Filters and Sort -->
        <div class="notion-block notion-filters">
            <div class="notion-filters-left">
                <button class="notion-filter-btn active" data-filter="all">
                    <span>All</span>
                    <span class="notion-filter-count" id="allCount">0</span>
                </button>
                <button class="notion-filter-btn" data-filter="active">
                    <span>Active</span>
                    <span class="notion-filter-count" id="activeCount">0</span>
                </button>
                <button class="notion-filter-btn" data-filter="completed">
                    <span>Completed</span>
                    <span class="notion-filter-count" id="completedCount">0</span>
                </button>
                
                <select id="categoryFilter" class="notion-filter-select">
                    <option value="">All Categories</option>
                </select>
                
                <select id="projectFilter" class="notion-filter-select">
                    <option value="">All Projects</option>
                </select>
            </div>
            
            <div class="notion-filters-right">
                <select id="sortSelect" class="notion-filter-select">
                    <option value="priority">Sort by Priority</option>
                    <option value="date">Sort by Date</option>
                    <option value="title">Sort by Title</option>
                </select>
            </div>
        </div>

        <!-- Task List -->
        <div class="notion-todo-list" id="taskList">
            <div class="notion-loading">Loading tasks...</div>
        </div>

        <!-- Empty State -->
        <div class="notion-empty-state" id="emptyState" style="display: none;">
            <div class="notion-empty-icon">📝</div>
            <div class="notion-empty-text">
                <h3>No tasks yet</h3>
                <p>Click above to add your first task</p>
            </div>
        </div>
    </div>
</div>

<!-- Edit Task Sidebar -->
<div class="notion-sidebar" id="editSidebar">
    <div class="notion-sidebar-content">
        <div class="notion-sidebar-header">
            <h2>Edit Task</h2>
            <button class="notion-sidebar-close" id="closeSidebar">×</button>
        </div>
        <form id="editTaskForm" class="notion-form">
            <input type="hidden" id="editTaskId">
            <div class="notion-form-group">
                <label class="notion-form-label">Title</label>
                <input 
                    type="text" 
                    id="editTaskTitle" 
                    required
                    class="notion-input"
                >
            </div>
            <div class="notion-form-group">
                <label class="notion-form-label">Description</label>
                <textarea 
                    id="editTaskDescription" 
                    rows="4"
                    class="notion-textarea"
                    placeholder="Add a description..."
                ></textarea>
            </div>
            <div class="notion-form-row">
                <div class="notion-form-group">
                    <label class="notion-form-label">Category</label>
                    <select id="editTaskCategory" class="notion-select">
                        <option value="">No Category</option>
                    </select>
                </div>
                <div class="notion-form-group">
                    <label class="notion-form-label">Project</label>
                    <select id="editTaskProject" class="notion-select">
                        <option value="">No Project</option>
                    </select>
                </div>
            </div>
            <div class="notion-form-row">
                <div class="notion-form-group">
                    <label class="notion-form-label">Priority</label>
                    <select id="editTaskPriority" class="notion-select">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
                <div class="notion-form-group">
                    <label class="notion-form-label">Due Date</label>
                    <input 
                        type="date" 
                        id="editTaskDueDate" 
                        class="notion-input"
                    >
                </div>
            </div>
            <div class="notion-form-group">
                <label class="notion-form-label">Tags</label>
                <div class="notion-tag-selector" id="editTagSelector">
                    <div class="notion-tag-list" id="editTagList"></div>
                    <button type="button" class="notion-button-small" id="editAddTagBtn">+ Add Tag</button>
                </div>
            </div>
            
            <!-- Subtasks Section -->
            <div class="notion-form-group">
                <div class="notion-section-header">
                    <label class="notion-form-label">Subtasks</label>
                    <button type="button" class="notion-button-small" id="addSubtaskBtn">+ Add Subtask</button>
                </div>
                <div class="notion-subtasks-list" id="subtasksList"></div>
            </div>
            
            <!-- Comments Section -->
            <div class="notion-form-group">
                <div class="notion-section-header">
                    <label class="notion-form-label">Comments</label>
                </div>
                <div class="notion-comments-list" id="commentsList"></div>
                <div class="notion-comment-form">
                    <textarea 
                        id="newComment" 
                        rows="2"
                        class="notion-textarea"
                        placeholder="Add a comment..."
                    ></textarea>
                    <button type="button" class="notion-button notion-button-primary" id="addCommentBtn">
                        Add Comment
                    </button>
                </div>
            </div>
            
            <div class="notion-form-actions">
                <button type="button" class="notion-button notion-button-danger" id="archiveTaskBtn">
                    Archive
                </button>
                <button type="button" class="notion-button notion-button-secondary" id="cancelEdit">
                    Cancel
                </button>
                <button type="submit" class="notion-button notion-button-primary">
                    Save
                </button>
            </div>
        </form>
    </div>
</div>
<div class="notion-sidebar-overlay" id="sidebarOverlay"></div>

<!-- Tag Creation Modal -->
<div class="notion-modal" id="tagModal">
    <div class="notion-modal-content">
        <div class="notion-modal-header">
            <h3>Create Tag</h3>
            <button class="notion-modal-close" id="closeTagModal">×</button>
        </div>
        <form id="tagForm">
            <div class="notion-form-group">
                <label class="notion-form-label">Tag Name</label>
                <input type="text" id="tagName" class="notion-input" required>
            </div>
            <div class="notion-form-group">
                <label class="notion-form-label">Color</label>
                <input type="color" id="tagColor" class="notion-input-color" value="#9b9a97">
            </div>
            <div class="notion-form-actions">
                <button type="button" class="notion-button notion-button-secondary" id="cancelTagBtn">
                    Cancel
                </button>
                <button type="submit" class="notion-button notion-button-primary">
                    Create
                </button>
            </div>
        </form>
    </div>
</div>
<div class="notion-modal-overlay" id="tagModalOverlay"></div>
