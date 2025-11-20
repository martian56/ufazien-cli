<?php
/**
 * Database Configuration and Setup
 * 
 * This file handles database connection and initial table creation.
 * Edit this file to add more tables as needed.
 */

// Load configuration
require_once __DIR__ . '/config.php';

// Global database connection variable
$conn = null;

/**
 * Get database connection
 * @return PDO|null Database connection or null on failure
 */
function get_connection() {
    global $conn;
    
    if ($conn !== null) {
        return $conn;
    }
    
    try {
        $conn = getDBConnection();
        return $conn;
    } catch (Exception $e) {
        error_log("Database connection error: " . $e->getMessage());
        return null;
    }
}

/**
 * Initialize database tables
 * This function creates the initial tables for your application.
 * Add more table creation statements as needed.
 */
function init_database() {
    $pdo = get_connection();
    if (!$pdo) {
        throw new Exception("Cannot connect to database");
    }
    
    try {
        // Create categories table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                color VARCHAR(7) DEFAULT '#667eea',
                icon VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create projects table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                color VARCHAR(7) DEFAULT '#667eea',
                archived TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create tags table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                color VARCHAR(7) DEFAULT '#9b9a97',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create tasks table (updated with new fields)
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                completed TINYINT(1) DEFAULT 0,
                priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
                due_date DATE,
                category_id INT,
                project_id INT,
                archived TINYINT(1) DEFAULT 0,
                position INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
                INDEX idx_category (category_id),
                INDEX idx_project (project_id),
                INDEX idx_archived (archived)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create task_tags junction table (many-to-many)
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS task_tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                tag_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                UNIQUE KEY unique_task_tag (task_id, tag_id),
                INDEX idx_task (task_id),
                INDEX idx_tag (tag_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create subtasks table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS subtasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                completed TINYINT(1) DEFAULT 0,
                position INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                INDEX idx_task (task_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Create comments table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                INDEX idx_task (task_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");

        // Insert default categories
        $pdo->exec("
            INSERT IGNORE INTO categories (name, color, icon) VALUES
            ('Personal', '#667eea', '👤'),
            ('Work', '#f7c948', '💼'),
            ('Shopping', '#0f7b6c', '🛒'),
            ('Health', '#e16259', '💊'),
            ('Learning', '#2383e2', '📚')
        ");

        // Insert default project
        $pdo->exec("
            INSERT IGNORE INTO projects (name, description, color) VALUES
            ('Inbox', 'Default project for new tasks', '#667eea')
        ");
        
        return true;
    } catch (PDOException $e) {
        error_log("Database initialization error: " . $e->getMessage());
        throw $e;
    }
}

// Auto-initialize database on first load
init_database();

// Make connection available globally
$conn = get_connection();
?>
