<?php
header('Content-Type: application/json');
require_once __DIR__ . '/database.php';

$conn = get_connection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';
$entity = $_GET['entity'] ?? 'task'; // task, category, project, tag, subtask, comment

function getTaskWithRelations($conn, $id) {
    $stmt = $conn->prepare("
        SELECT t.*, 
               c.name as category_name, c.color as category_color, c.icon as category_icon,
               p.name as project_name, p.color as project_color
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.id = ? AND t.archived = 0
    ");
    $stmt->execute([$id]);
    $task = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($task) {
        // Get tags
        $stmt = $conn->prepare("
            SELECT t.id, t.name, t.color
            FROM tags t
            INNER JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
        ");
        $stmt->execute([$id]);
        $task['tags'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get subtasks
        $stmt = $conn->prepare("SELECT * FROM subtasks WHERE task_id = ? ORDER BY position, created_at");
        $stmt->execute([$id]);
        $task['subtasks'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Get comments
        $stmt = $conn->prepare("SELECT * FROM comments WHERE task_id = ? ORDER BY created_at DESC");
        $stmt->execute([$id]);
        $task['comments'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    return $task;
}

try {
    switch ($method) {
        case 'GET':
            if ($entity === 'task') {
                if ($action === 'list') {
                    $filter = $_GET['filter'] ?? 'all';
                    $category = $_GET['category'] ?? null;
                    $project = $_GET['project'] ?? null;
                    $tag = $_GET['tag'] ?? null;
                    $search = $_GET['search'] ?? '';
                    $sort = $_GET['sort'] ?? 'priority'; // priority, date, title
                    
                    $query = "SELECT t.*, 
                                     c.name as category_name, c.color as category_color, c.icon as category_icon,
                                     p.name as project_name, p.color as project_color
                              FROM tasks t
                              LEFT JOIN categories c ON t.category_id = c.id
                              LEFT JOIN projects p ON t.project_id = p.id
                              WHERE t.archived = 0";
                    
                    $params = [];
                    
                    if ($filter === 'active') {
                        $query .= " AND t.completed = 0";
                    } elseif ($filter === 'completed') {
                        $query .= " AND t.completed = 1";
                    }
                    
                    if ($category) {
                        $query .= " AND t.category_id = ?";
                        $params[] = (int)$category;
                    }
                    
                    if ($project) {
                        $query .= " AND t.project_id = ?";
                        $params[] = (int)$project;
                    }
                    
                    if ($tag) {
                        $query .= " AND t.id IN (
                            SELECT task_id FROM task_tags WHERE tag_id = ?
                        )";
                        $params[] = (int)$tag;
                    }
                    
                    if ($search) {
                        $query .= " AND (t.title LIKE ? OR t.description LIKE ?)";
                        $searchTerm = "%$search%";
                        $params[] = $searchTerm;
                        $params[] = $searchTerm;
                    }
                    
                    // Sorting
                    switch ($sort) {
                        case 'date':
                            $query .= " ORDER BY t.created_at DESC";
                            break;
                        case 'title':
                            $query .= " ORDER BY t.title ASC";
                            break;
                        case 'priority':
                        default:
                            $query .= " ORDER BY 
                                CASE t.priority 
                                    WHEN 'high' THEN 1 
                                    WHEN 'medium' THEN 2 
                                    WHEN 'low' THEN 3 
                                END,
                                t.created_at DESC";
                    }
                    
                    $stmt = $conn->prepare($query);
                    $stmt->execute($params);
                    $tasks = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    
                    // Get tags for each task
                    foreach ($tasks as &$task) {
                        $task['completed'] = (bool)$task['completed'];
                        $task['id'] = (int)$task['id'];
                        $task['category_id'] = $task['category_id'] ? (int)$task['category_id'] : null;
                        $task['project_id'] = $task['project_id'] ? (int)$task['project_id'] : null;
                        
                        $stmt = $conn->prepare("
                            SELECT t.id, t.name, t.color
                            FROM tags t
                            INNER JOIN task_tags tt ON t.id = tt.tag_id
                            WHERE tt.task_id = ?
                        ");
                        $stmt->execute([$task['id']]);
                        $task['tags'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    }
                    
                    echo json_encode(['success' => true, 'tasks' => $tasks]);
                } elseif ($action === 'get' && isset($_GET['id'])) {
                    $id = (int)$_GET['id'];
                    $task = getTaskWithRelations($conn, $id);
                    
                    if ($task) {
                        $task['completed'] = (bool)$task['completed'];
                        $task['id'] = (int)$task['id'];
                        echo json_encode(['success' => true, 'task' => $task]);
                    } else {
                        http_response_code(404);
                        echo json_encode(['success' => false, 'error' => 'Task not found']);
                    }
                }
            } elseif ($entity === 'category') {
                if ($action === 'list') {
                    $stmt = $conn->query("SELECT * FROM categories ORDER BY name");
                    $categories = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    echo json_encode(['success' => true, 'categories' => $categories]);
                }
            } elseif ($entity === 'project') {
                if ($action === 'list') {
                    $archived = $_GET['archived'] ?? '0';
                    $query = "SELECT * FROM projects WHERE archived = ? ORDER BY name";
                    $stmt = $conn->prepare($query);
                    $stmt->execute([$archived]);
                    $projects = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    echo json_encode(['success' => true, 'projects' => $projects]);
                }
            } elseif ($entity === 'tag') {
                if ($action === 'list') {
                    $stmt = $conn->query("SELECT * FROM tags ORDER BY name");
                    $tags = $stmt->fetchAll(PDO::FETCH_ASSOC);
                    echo json_encode(['success' => true, 'tags' => $tags]);
                }
            }
            break;
            
        case 'POST':
            if ($entity === 'task') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    
                    $title = trim($data['title'] ?? '');
                    $description = trim($data['description'] ?? '');
                    $priority = $data['priority'] ?? 'medium';
                    $due_date = $data['due_date'] ?? null;
                    $category_id = $data['category_id'] ?? null;
                    $project_id = $data['project_id'] ?? null;
                    $tag_ids = $data['tag_ids'] ?? [];
                    
                    if (empty($title)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Title is required']);
                        exit;
                    }
                    
                    if (!in_array($priority, ['low', 'medium', 'high'])) {
                        $priority = 'medium';
                    }
                    
                    if ($due_date && $due_date !== '') {
                        $due_date = date('Y-m-d', strtotime($due_date));
                    } else {
                        $due_date = null;
                    }
                    
                    $category_id = $category_id ? (int)$category_id : null;
                    $project_id = $project_id ? (int)$project_id : null;
                    
                    $conn->beginTransaction();
                    
                    try {
                        $stmt = $conn->prepare("
                            INSERT INTO tasks (title, description, priority, due_date, category_id, project_id) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        ");
                        $stmt->execute([$title, $description, $priority, $due_date, $category_id, $project_id]);
                        $id = $conn->lastInsertId();
                        
                        // Add tags
                        if (!empty($tag_ids)) {
                            $stmt = $conn->prepare("INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)");
                            foreach ($tag_ids as $tag_id) {
                                $stmt->execute([$id, (int)$tag_id]);
                            }
                        }
                        
                        $conn->commit();
                        $task = getTaskWithRelations($conn, $id);
                        $task['completed'] = (bool)$task['completed'];
                        $task['id'] = (int)$task['id'];
                        echo json_encode(['success' => true, 'task' => $task]);
                    } catch (Exception $e) {
                        $conn->rollBack();
                        throw $e;
                    }
                } elseif ($action === 'update') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $id = (int)($data['id'] ?? 0);
                    
                    if (!$id) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'ID is required']);
                        exit;
                    }
                    
                    $updates = [];
                    $params = [];
                    
                    if (isset($data['title'])) {
                        $updates[] = "title = ?";
                        $params[] = trim($data['title']);
                    }
                    if (isset($data['description'])) {
                        $updates[] = "description = ?";
                        $params[] = trim($data['description']);
                    }
                    if (isset($data['priority'])) {
                        $priority = $data['priority'];
                        if (in_array($priority, ['low', 'medium', 'high'])) {
                            $updates[] = "priority = ?";
                            $params[] = $priority;
                        }
                    }
                    if (isset($data['due_date'])) {
                        $due_date = $data['due_date'];
                        if ($due_date && $due_date !== '') {
                            $updates[] = "due_date = ?";
                            $params[] = date('Y-m-d', strtotime($due_date));
                        } else {
                            $updates[] = "due_date = NULL";
                        }
                    }
                    if (isset($data['category_id'])) {
                        $updates[] = "category_id = ?";
                        $params[] = $data['category_id'] ? (int)$data['category_id'] : null;
                    }
                    if (isset($data['project_id'])) {
                        $updates[] = "project_id = ?";
                        $params[] = $data['project_id'] ? (int)$data['project_id'] : null;
                    }
                    if (isset($data['completed'])) {
                        $updates[] = "completed = ?";
                        $params[] = $data['completed'] ? 1 : 0;
                    }
                    if (isset($data['archived'])) {
                        $updates[] = "archived = ?";
                        $params[] = $data['archived'] ? 1 : 0;
                    }
                    
                    if (empty($updates)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'No fields to update']);
                        exit;
                    }
                    
                    $params[] = $id;
                    $sql = "UPDATE tasks SET " . implode(', ', $updates) . " WHERE id = ?";
                    $stmt = $conn->prepare($sql);
                    $stmt->execute($params);
                    
                    // Update tags if provided
                    if (isset($data['tag_ids'])) {
                        $conn->beginTransaction();
                        try {
                            $stmt = $conn->prepare("DELETE FROM task_tags WHERE task_id = ?");
                            $stmt->execute([$id]);
                            
                            if (!empty($data['tag_ids'])) {
                                $stmt = $conn->prepare("INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)");
                                foreach ($data['tag_ids'] as $tag_id) {
                                    $stmt->execute([$id, (int)$tag_id]);
                                }
                            }
                            $conn->commit();
                        } catch (Exception $e) {
                            $conn->rollBack();
                            throw $e;
                        }
                    }
                    
                    $task = getTaskWithRelations($conn, $id);
                    if ($task) {
                        $task['completed'] = (bool)$task['completed'];
                        $task['id'] = (int)$task['id'];
                        echo json_encode(['success' => true, 'task' => $task]);
                    } else {
                        http_response_code(404);
                        echo json_encode(['success' => false, 'error' => 'Task not found']);
                    }
                }
            } elseif ($entity === 'category') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $name = trim($data['name'] ?? '');
                    $color = $data['color'] ?? '#667eea';
                    $icon = $data['icon'] ?? '';
                    
                    if (empty($name)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Name is required']);
                        exit;
                    }
                    
                    $stmt = $conn->prepare("INSERT INTO categories (name, color, icon) VALUES (?, ?, ?)");
                    $stmt->execute([$name, $color, $icon]);
                    $id = $conn->lastInsertId();
                    
                    $stmt = $conn->prepare("SELECT * FROM categories WHERE id = ?");
                    $stmt->execute([$id]);
                    $category = $stmt->fetch(PDO::FETCH_ASSOC);
                    
                    echo json_encode(['success' => true, 'category' => $category]);
                }
            } elseif ($entity === 'project') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $name = trim($data['name'] ?? '');
                    $description = trim($data['description'] ?? '');
                    $color = $data['color'] ?? '#667eea';
                    
                    if (empty($name)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Name is required']);
                        exit;
                    }
                    
                    $stmt = $conn->prepare("INSERT INTO projects (name, description, color) VALUES (?, ?, ?)");
                    $stmt->execute([$name, $description, $color]);
                    $id = $conn->lastInsertId();
                    
                    $stmt = $conn->prepare("SELECT * FROM projects WHERE id = ?");
                    $stmt->execute([$id]);
                    $project = $stmt->fetch(PDO::FETCH_ASSOC);
                    
                    echo json_encode(['success' => true, 'project' => $project]);
                }
            } elseif ($entity === 'tag') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $name = trim($data['name'] ?? '');
                    $color = $data['color'] ?? '#9b9a97';
                    
                    if (empty($name)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Name is required']);
                        exit;
                    }
                    
                    $stmt = $conn->prepare("INSERT INTO tags (name, color) VALUES (?, ?)");
                    $stmt->execute([$name, $color]);
                    $id = $conn->lastInsertId();
                    
                    $stmt = $conn->prepare("SELECT * FROM tags WHERE id = ?");
                    $stmt->execute([$id]);
                    $tag = $stmt->fetch(PDO::FETCH_ASSOC);
                    
                    echo json_encode(['success' => true, 'tag' => $tag]);
                }
            } elseif ($entity === 'subtask') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $task_id = (int)($data['task_id'] ?? 0);
                    $title = trim($data['title'] ?? '');
                    
                    if (!$task_id || empty($title)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Task ID and title are required']);
                        exit;
                    }
                    
                    $stmt = $conn->prepare("INSERT INTO subtasks (task_id, title) VALUES (?, ?)");
                    $stmt->execute([$task_id, $title]);
                    $id = $conn->lastInsertId();
                    
                    $stmt = $conn->prepare("SELECT * FROM subtasks WHERE id = ?");
                    $stmt->execute([$id]);
                    $subtask = $stmt->fetch(PDO::FETCH_ASSOC);
                    $subtask['completed'] = (bool)$subtask['completed'];
                    
                    echo json_encode(['success' => true, 'subtask' => $subtask]);
                } elseif ($action === 'update') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $id = (int)($data['id'] ?? 0);
                    
                    if (!$id) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'ID is required']);
                        exit;
                    }
                    
                    $updates = [];
                    $params = [];
                    
                    if (isset($data['title'])) {
                        $updates[] = "title = ?";
                        $params[] = trim($data['title']);
                    }
                    if (isset($data['completed'])) {
                        $updates[] = "completed = ?";
                        $params[] = $data['completed'] ? 1 : 0;
                    }
                    
                    if (empty($updates)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'No fields to update']);
                        exit;
                    }
                    
                    $params[] = $id;
                    $sql = "UPDATE subtasks SET " . implode(', ', $updates) . " WHERE id = ?";
                    $stmt = $conn->prepare($sql);
                    $stmt->execute($params);
                    
                    $stmt = $conn->prepare("SELECT * FROM subtasks WHERE id = ?");
                    $stmt->execute([$id]);
                    $subtask = $stmt->fetch(PDO::FETCH_ASSOC);
                    $subtask['completed'] = (bool)$subtask['completed'];
                    
                    echo json_encode(['success' => true, 'subtask' => $subtask]);
                }
            } elseif ($entity === 'comment') {
                if ($action === 'create') {
                    $data = json_decode(file_get_contents('php://input'), true);
                    $task_id = (int)($data['task_id'] ?? 0);
                    $content = trim($data['content'] ?? '');
                    
                    if (!$task_id || empty($content)) {
                        http_response_code(400);
                        echo json_encode(['success' => false, 'error' => 'Task ID and content are required']);
                        exit;
                    }
                    
                    $stmt = $conn->prepare("INSERT INTO comments (task_id, content) VALUES (?, ?)");
                    $stmt->execute([$task_id, $content]);
                    $id = $conn->lastInsertId();
                    
                    $stmt = $conn->prepare("SELECT * FROM comments WHERE id = ?");
                    $stmt->execute([$id]);
                    $comment = $stmt->fetch(PDO::FETCH_ASSOC);
                    
                    echo json_encode(['success' => true, 'comment' => $comment]);
                }
            }
            break;
            
        case 'DELETE':
            if ($entity === 'task' && $action === 'delete' && isset($_GET['id'])) {
                $id = (int)$_GET['id'];
                $stmt = $conn->prepare("DELETE FROM tasks WHERE id = ?");
                $stmt->execute([$id]);
                
                if ($stmt->rowCount() > 0) {
                    echo json_encode(['success' => true, 'message' => 'Task deleted']);
                } else {
                    http_response_code(404);
                    echo json_encode(['success' => false, 'error' => 'Task not found']);
                }
            } elseif ($entity === 'subtask' && $action === 'delete' && isset($_GET['id'])) {
                $id = (int)$_GET['id'];
                $stmt = $conn->prepare("DELETE FROM subtasks WHERE id = ?");
                $stmt->execute([$id]);
                
                if ($stmt->rowCount() > 0) {
                    echo json_encode(['success' => true, 'message' => 'Subtask deleted']);
                } else {
                    http_response_code(404);
                    echo json_encode(['success' => false, 'error' => 'Subtask not found']);
                }
            } elseif ($entity === 'comment' && $action === 'delete' && isset($_GET['id'])) {
                $id = (int)$_GET['id'];
                $stmt = $conn->prepare("DELETE FROM comments WHERE id = ?");
                $stmt->execute([$id]);
                
                if ($stmt->rowCount() > 0) {
                    echo json_encode(['success' => true, 'message' => 'Comment deleted']);
                } else {
                    http_response_code(404);
                    echo json_encode(['success' => false, 'error' => 'Comment not found']);
                }
            }
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
    }
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Database error: ' . $e->getMessage()]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>
