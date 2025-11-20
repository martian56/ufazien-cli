document.addEventListener('DOMContentLoaded', function() {
    const taskList = document.getElementById('taskList');
    const addTaskForm = document.getElementById('addTaskForm');
    const editTaskForm = document.getElementById('editTaskForm');
    const editSidebar = document.getElementById('editSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const closeSidebar = document.getElementById('closeSidebar');
    const cancelEdit = document.getElementById('cancelEdit');
    const cancelAdd = document.getElementById('cancelAdd');
    const filterButtons = document.querySelectorAll('.notion-filter-btn');
    const emptyState = document.getElementById('emptyState');
    const taskTitleInput = document.getElementById('taskTitle');
    const inlineOptions = document.querySelector('.notion-inline-options');
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const projectFilter = document.getElementById('projectFilter');
    const sortSelect = document.getElementById('sortSelect');
    const tagModal = document.getElementById('tagModal');
    const tagModalOverlay = document.getElementById('tagModalOverlay');
    const tagForm = document.getElementById('tagForm');
    
    // State
    let currentFilter = 'all';
    let currentCategory = '';
    let currentProject = '';
    let currentSort = 'priority';
    let searchQuery = '';
    let tasks = [];
    let categories = [];
    let projects = [];
    let tags = [];
    let selectedTags = [];
    let currentTaskId = null;

    // Initialize app
    init();

    async function init() {
        await Promise.all([
            loadCategories(),
            loadProjects(),
            loadTags(),
            loadTasks()
        ]);
    }

    async function loadCategories() {
        try {
            const response = await fetch('api.php?entity=category&action=list');
            const data = await response.json();
            if (data.success) {
                categories = data.categories;
                populateCategorySelects();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async function loadProjects() {
        try {
            const response = await fetch('api.php?entity=project&action=list&archived=0');
            const data = await response.json();
            if (data.success) {
                projects = data.projects;
                populateProjectSelects();
            }
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }

    async function loadTags() {
        try {
            const response = await fetch('api.php?entity=tag&action=list');
            const data = await response.json();
            if (data.success) {
                tags = data.tags;
                renderTagSelectors();
            }
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    function populateCategorySelects() {
        const selects = ['taskCategory', 'editTaskCategory', 'categoryFilter'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const currentValue = select.value;
                select.innerHTML = selectId === 'categoryFilter' 
                    ? '<option value="">All Categories</option>'
                    : '<option value="">No Category</option>';
                categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.icon ? `${cat.icon} ${cat.name}` : cat.name;
                    select.appendChild(option);
                });
                if (currentValue) select.value = currentValue;
            }
        });
    }

    function populateProjectSelects() {
        const selects = ['taskProject', 'editTaskProject', 'projectFilter'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const currentValue = select.value;
                select.innerHTML = selectId === 'projectFilter'
                    ? '<option value="">All Projects</option>'
                    : '<option value="">No Project</option>';
                projects.forEach(proj => {
                    const option = document.createElement('option');
                    option.value = proj.id;
                    option.textContent = proj.name;
                    select.appendChild(option);
                });
                if (currentValue) select.value = currentValue;
            }
        });
    }

    function renderTagSelectors() {
        const selectors = ['taskTagList', 'editTagList'];
        selectors.forEach(selectorId => {
            const container = document.getElementById(selectorId);
            if (container) {
                container.innerHTML = '';
                tags.forEach(tag => {
                    const tagEl = createTagElement(tag, selectorId === 'editTagList');
                    container.appendChild(tagEl);
                });
            }
        });
    }

    function createTagElement(tag, isEdit = false) {
        const tagEl = document.createElement('span');
        tagEl.className = 'notion-tag';
        tagEl.dataset.tagId = tag.id;
        tagEl.style.backgroundColor = tag.color || '#9b9a97';
        tagEl.style.color = 'white';
        tagEl.textContent = tag.name;
        
        if (isEdit) {
            tagEl.addEventListener('click', function() {
                this.classList.toggle('selected');
                updateSelectedTags();
            });
        } else {
            tagEl.addEventListener('click', function() {
                this.classList.toggle('selected');
                const tagId = parseInt(this.dataset.tagId);
                if (this.classList.contains('selected')) {
                    if (!selectedTags.includes(tagId)) {
                        selectedTags.push(tagId);
                    }
                } else {
                    selectedTags = selectedTags.filter(id => id !== tagId);
                }
            });
        }
        
        return tagEl;
    }

    function updateSelectedTags() {
        const selected = Array.from(document.querySelectorAll('#editTagList .notion-tag.selected'));
        selectedTags = selected.map(el => parseInt(el.dataset.tagId));
    }

    // Search
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = this.value.trim();
            loadTasks();
        }, 300);
    });

    // Filters
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            loadTasks();
        });
    });

    categoryFilter.addEventListener('change', function() {
        currentCategory = this.value;
        loadTasks();
    });

    projectFilter.addEventListener('change', function() {
        currentProject = this.value;
        loadTasks();
    });

    sortSelect.addEventListener('change', function() {
        currentSort = this.value;
        loadTasks();
    });

    // Expand inline form
    taskTitleInput.addEventListener('focus', function() {
        inlineOptions.style.display = 'flex';
    });

    cancelAdd.addEventListener('click', function() {
        addTaskForm.reset();
        inlineOptions.style.display = 'none';
        selectedTags = [];
        renderTagSelectors();
        taskTitleInput.blur();
    });

    // Add task
    addTaskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const title = taskTitleInput.value.trim();
        const description = document.getElementById('taskDescription').value.trim();
        const priority = document.getElementById('taskPriority').value;
        const dueDate = document.getElementById('taskDueDate').value;
        const categoryId = document.getElementById('taskCategory').value || null;
        const projectId = document.getElementById('taskProject').value || null;

        if (!title) return;

        try {
            const response = await fetch('api.php?entity=task&action=create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    description,
                    priority,
                    due_date: dueDate || null,
                    category_id: categoryId ? parseInt(categoryId) : null,
                    project_id: projectId ? parseInt(projectId) : null,
                    tag_ids: selectedTags
                })
            });

            const data = await response.json();
            
            if (data.success) {
                addTaskForm.reset();
                inlineOptions.style.display = 'none';
                selectedTags = [];
                renderTagSelectors();
                loadTasks();
                showNotification('Task created successfully', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Failed to create task'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to create task. Please try again.', 'error');
        }
    });

    // Load tasks
    async function loadTasks() {
        try {
            taskList.innerHTML = '<div class="notion-loading">Loading tasks...</div>';
            
            let url = `api.php?entity=task&action=list&filter=${currentFilter}&sort=${currentSort}`;
            if (currentCategory) url += `&category=${currentCategory}`;
            if (currentProject) url += `&project=${currentProject}`;
            if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                tasks = data.tasks;
                renderTasks();
                updateStats();
            } else {
                taskList.innerHTML = '<div class="notion-loading">Error loading tasks</div>';
            }
        } catch (error) {
            console.error('Error:', error);
            taskList.innerHTML = '<div class="notion-loading">Failed to load tasks</div>';
        }
    }

    function renderTasks() {
        if (tasks.length === 0) {
            taskList.style.display = 'none';
            emptyState.style.display = 'block';
        } else {
            taskList.style.display = 'block';
            emptyState.style.display = 'none';
            taskList.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
            attachTaskEventListeners();
        }
    }

    function createTaskHTML(task) {
        const dueDate = task.due_date ? new Date(task.due_date) : null;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const isOverdue = dueDate && dueDate < today && !task.completed;
        const dueDateStr = dueDate ? dueDate.toLocaleDateString('en-US', { 
            month: 'short', day: 'numeric',
            year: dueDate.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
        }) : null;

        let tagsHTML = '';
        if (task.tags && task.tags.length > 0) {
            tagsHTML = task.tags.map(tag => 
                `<span class="notion-tag" style="background-color: ${tag.color || '#9b9a97'}; color: white; font-size: 0.7rem; padding: 0.125rem 0.375rem;">${escapeHtml(tag.name)}</span>`
            ).join('');
        }

        return `
            <div class="notion-todo-item ${task.completed ? 'completed' : ''}" data-id="${task.id}">
                <div class="notion-checkbox-wrapper">
                    <input type="checkbox" class="notion-checkbox" ${task.completed ? 'checked' : ''} data-id="${task.id}">
                </div>
                <div class="notion-todo-content">
                    <div class="notion-todo-title">${escapeHtml(task.title)}</div>
                    ${task.description ? `<div class="notion-todo-description">${escapeHtml(task.description)}</div>` : ''}
                    <div class="notion-todo-meta">
                        ${task.category_name ? `<span class="notion-todo-category">${task.category_icon || ''} ${escapeHtml(task.category_name)}</span>` : ''}
                        ${task.project_name ? `<span class="notion-todo-project">${escapeHtml(task.project_name)}</span>` : ''}
                        <span class="notion-todo-priority ${task.priority}">${task.priority}</span>
                        ${tagsHTML ? `<div style="display: flex; gap: 0.25rem; flex-wrap: wrap;">${tagsHTML}</div>` : ''}
                        ${dueDateStr ? `<span class="notion-todo-due-date ${isOverdue ? 'overdue' : ''}">${dueDateStr}${isOverdue ? ' (Overdue)' : ''}</span>` : ''}
                    </div>
                </div>
                <div class="notion-todo-actions">
                    <button class="notion-todo-action edit" data-id="${task.id}" title="Edit">✏️</button>
                    <button class="notion-todo-action delete" data-id="${task.id}" title="Delete">🗑️</button>
                </div>
            </div>
        `;
    }

    function attachTaskEventListeners() {
        document.querySelectorAll('.notion-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', async function() {
                const id = parseInt(this.dataset.id);
                const completed = this.checked;
                
                try {
                    const response = await fetch('api.php?entity=task&action=update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id, completed })
                    });

                    const data = await response.json();
                    if (data.success) {
                        loadTasks();
                    } else {
                        this.checked = !completed;
                        showNotification('Error updating task', 'error');
                    }
                } catch (error) {
                    this.checked = !completed;
                    showNotification('Failed to update task', 'error');
                }
            });
        });

        document.querySelectorAll('.notion-todo-action.edit').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const id = parseInt(this.dataset.id);
                openEditSidebar(id);
            });
        });

        document.querySelectorAll('.notion-todo-action.delete').forEach(btn => {
            btn.addEventListener('click', async function(e) {
                e.stopPropagation();
                const id = parseInt(this.dataset.id);
                if (confirm('Are you sure you want to delete this task?')) {
                    try {
                        const response = await fetch(`api.php?entity=task&action=delete&id=${id}`, {
                            method: 'DELETE'
                        });
                        const data = await response.json();
                        if (data.success) {
                            loadTasks();
                            showNotification('Task deleted', 'success');
                        }
                    } catch (error) {
                        showNotification('Failed to delete task', 'error');
                    }
                }
            });
        });

        document.querySelectorAll('.notion-todo-item').forEach(item => {
            item.addEventListener('click', function(e) {
                if (!e.target.closest('.notion-todo-actions') && !e.target.closest('.notion-checkbox')) {
                    const id = parseInt(this.dataset.id);
                    openEditSidebar(id);
                }
            });
        });
    }

    async function openEditSidebar(id) {
        currentTaskId = id;
        try {
            const response = await fetch(`api.php?entity=task&action=get&id=${id}`);
            const data = await response.json();
            
            if (data.success) {
                const task = data.task;
                document.getElementById('editTaskId').value = task.id;
                document.getElementById('editTaskTitle').value = task.title;
                document.getElementById('editTaskDescription').value = task.description || '';
                document.getElementById('editTaskPriority').value = task.priority;
                document.getElementById('editTaskDueDate').value = task.due_date || '';
                document.getElementById('editTaskCategory').value = task.category_id || '';
                document.getElementById('editTaskProject').value = task.project_id || '';
                
                loadSubtasks(task.id);
                loadComments(task.id);
                
                selectedTags = task.tags ? task.tags.map(t => t.id) : [];
                renderTagSelectors();
                document.querySelectorAll('#editTagList .notion-tag').forEach(tagEl => {
                    if (selectedTags.includes(parseInt(tagEl.dataset.tagId))) {
                        tagEl.classList.add('selected');
                    }
                });
                
                editSidebar.classList.add('active');
                sidebarOverlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to load task', 'error');
        }
    }

    function closeEditSidebar() {
        editSidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
        editTaskForm.reset();
        currentTaskId = null;
        selectedTags = [];
    }

    closeSidebar.addEventListener('click', closeEditSidebar);
    cancelEdit.addEventListener('click', closeEditSidebar);
    sidebarOverlay.addEventListener('click', closeEditSidebar);

    // Edit form
    editTaskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const id = parseInt(document.getElementById('editTaskId').value);
        const title = document.getElementById('editTaskTitle').value.trim();
        const description = document.getElementById('editTaskDescription').value.trim();
        const priority = document.getElementById('editTaskPriority').value;
        const dueDate = document.getElementById('editTaskDueDate').value;
        const categoryId = document.getElementById('editTaskCategory').value || null;
        const projectId = document.getElementById('editTaskProject').value || null;

        if (!title) {
            showNotification('Please enter a title', 'error');
            return;
        }

        try {
            const response = await fetch('api.php?entity=task&action=update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id,
                    title,
                    description,
                    priority,
                    due_date: dueDate || null,
                    category_id: categoryId ? parseInt(categoryId) : null,
                    project_id: projectId ? parseInt(projectId) : null,
                    tag_ids: selectedTags
                })
            });

            const data = await response.json();
            
            if (data.success) {
                closeEditSidebar();
                loadTasks();
                showNotification('Task updated successfully', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Failed to update task'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to update task', 'error');
        }
    });

    // Archive
    document.getElementById('archiveTaskBtn').addEventListener('click', async function() {
        if (!currentTaskId) return;
        if (confirm('Are you sure you want to archive this task?')) {
            try {
                const response = await fetch('api.php?entity=task&action=update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: currentTaskId, archived: true })
                });
                const data = await response.json();
                if (data.success) {
                    closeEditSidebar();
                    loadTasks();
                    showNotification('Task archived', 'success');
                }
            } catch (error) {
                showNotification('Failed to archive task', 'error');
            }
        }
    });

    // Subtasks
    async function loadSubtasks(taskId) {
        try {
            const response = await fetch(`api.php?entity=task&action=get&id=${taskId}`);
            const data = await response.json();
            if (data.success && data.task.subtasks) {
                renderSubtasks(data.task.subtasks);
            }
        } catch (error) {
            console.error('Error loading subtasks:', error);
        }
    }

    function renderSubtasks(subtasks) {
        const container = document.getElementById('subtasksList');
        if (!container) return;
        
        if (subtasks.length === 0) {
            container.innerHTML = '<div style="color: var(--notion-gray-6); font-size: 0.875rem;">No subtasks</div>';
            return;
        }
        
        container.innerHTML = subtasks.map(subtask => `
            <div class="notion-subtask-item ${subtask.completed ? 'completed' : ''}" data-id="${subtask.id}">
                <input type="checkbox" class="notion-checkbox" ${subtask.completed ? 'checked' : ''} data-id="${subtask.id}">
                <span class="notion-subtask-title">${escapeHtml(subtask.title)}</span>
                <div class="notion-subtask-actions">
                    <button class="notion-subtask-action delete-subtask" data-id="${subtask.id}">🗑️</button>
                </div>
            </div>
        `).join('');
        
        attachSubtaskListeners();
    }

    function attachSubtaskListeners() {
        document.querySelectorAll('#subtasksList .notion-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', async function() {
                const id = parseInt(this.dataset.id);
                const completed = this.checked;
                try {
                    const response = await fetch('api.php?entity=subtask&action=update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id, completed })
                    });
                    const data = await response.json();
                    if (data.success) loadSubtasks(currentTaskId);
                } catch (error) {
                    this.checked = !completed;
                }
            });
        });

        document.querySelectorAll('.delete-subtask').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = parseInt(this.dataset.id);
                if (confirm('Delete this subtask?')) {
                    try {
                        const response = await fetch(`api.php?entity=subtask&action=delete&id=${id}`, {
                            method: 'DELETE'
                        });
                        const data = await response.json();
                        if (data.success) loadSubtasks(currentTaskId);
                    } catch (error) {
                        showNotification('Failed to delete subtask', 'error');
                    }
                }
            });
        });
    }

    document.getElementById('addSubtaskBtn').addEventListener('click', function() {
        const title = prompt('Enter subtask title:');
        if (title && currentTaskId) {
            fetch('api.php?entity=subtask&action=create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: currentTaskId, title: title.trim() })
            }).then(r => r.json()).then(data => {
                if (data.success) loadSubtasks(currentTaskId);
            });
        }
    });

    // Comments
    async function loadComments(taskId) {
        try {
            const response = await fetch(`api.php?entity=task&action=get&id=${taskId}`);
            const data = await response.json();
            if (data.success && data.task.comments) {
                renderComments(data.task.comments);
            }
        } catch (error) {
            console.error('Error loading comments:', error);
        }
    }

    function renderComments(comments) {
        const container = document.getElementById('commentsList');
        if (!container) return;
        
        if (comments.length === 0) {
            container.innerHTML = '<div style="color: var(--notion-gray-6); font-size: 0.875rem;">No comments</div>';
            return;
        }
        
        container.innerHTML = comments.map(comment => `
            <div class="notion-comment-item" data-id="${comment.id}">
                <div class="notion-comment-meta">${new Date(comment.created_at).toLocaleString()}</div>
                <div>${escapeHtml(comment.content)}</div>
                <div class="notion-comment-actions">
                    <button class="notion-subtask-action delete-comment" data-id="${comment.id}">Delete</button>
                </div>
            </div>
        `).join('');
        
        document.querySelectorAll('.delete-comment').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = parseInt(this.dataset.id);
                if (confirm('Delete this comment?')) {
                    try {
                        const response = await fetch(`api.php?entity=comment&action=delete&id=${id}`, {
                            method: 'DELETE'
                        });
                        const data = await response.json();
                        if (data.success) loadComments(currentTaskId);
                    } catch (error) {
                        showNotification('Failed to delete comment', 'error');
                    }
                }
            });
        });
    }

    document.getElementById('addCommentBtn').addEventListener('click', async function() {
        const content = document.getElementById('newComment').value.trim();
        if (content && currentTaskId) {
            try {
                const response = await fetch('api.php?entity=comment&action=create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: currentTaskId, content })
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('newComment').value = '';
                    loadComments(currentTaskId);
                }
            } catch (error) {
                showNotification('Failed to add comment', 'error');
            }
        }
    });

    // Tag creation
    document.getElementById('addTagBtn').addEventListener('click', function() {
        tagModal.classList.add('active');
        tagModalOverlay.classList.add('active');
    });

    document.getElementById('editAddTagBtn').addEventListener('click', function() {
        tagModal.classList.add('active');
        tagModalOverlay.classList.add('active');
    });

    document.getElementById('closeTagModal').addEventListener('click', closeTagModal);
    document.getElementById('cancelTagBtn').addEventListener('click', closeTagModal);
    tagModalOverlay.addEventListener('click', closeTagModal);

    function closeTagModal() {
        tagModal.classList.remove('active');
        tagModalOverlay.classList.remove('active');
        tagForm.reset();
    }

    tagForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const name = document.getElementById('tagName').value.trim();
        const color = document.getElementById('tagColor').value;
        
        if (!name) return;
        
        try {
            const response = await fetch('api.php?entity=tag&action=create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, color })
            });
            const data = await response.json();
            if (data.success) {
                closeTagModal();
                await loadTags();
                showNotification('Tag created', 'success');
            }
        } catch (error) {
            showNotification('Failed to create tag', 'error');
        }
    });

    // Stats
    function updateStats() {
        const total = tasks.length;
        const active = tasks.filter(t => !t.completed).length;
        const completed = tasks.filter(t => t.completed).length;
        
        document.getElementById('allCount').textContent = total;
        document.getElementById('activeCount').textContent = active;
        document.getElementById('completedCount').textContent = completed;
    }

    // Notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; bottom: 20px; right: 20px; padding: 0.75rem 1rem;
            background: ${type === 'error' ? 'var(--notion-red)' : type === 'success' ? 'var(--notion-green)' : 'var(--notion-gray-9)'};
            color: white; border-radius: 3px; font-size: 0.875rem; z-index: 10000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
