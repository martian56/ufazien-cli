<?php
/**
 * Ufazien Configuration
 * Loads environment variables from .env file
 */

// Load environment variables from .env file
function loadEnv($path) {
    if (!file_exists($path)) {
        // .env file not found, use defaults or environment variables
        return;
    }
    
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        
        if (strpos($line, '=') === false) {
            continue;
        }
        
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        
        if (!array_key_exists($name, $_ENV)) {
            putenv("$name=$value");
            $_ENV[$name] = $value;
        }
    }
}

// Load .env file - try multiple possible locations
$envPaths = [
    __DIR__ . '/.env',           // Same directory as config.php (root)
    dirname(__DIR__) . '/.env',  // Parent directory (if config.php is in subdirectory)
    getcwd() . '/.env',          // Current working directory
];

$envLoaded = false;
foreach ($envPaths as $envPath) {
    if (file_exists($envPath)) {
        loadEnv($envPath);
        $envLoaded = true;
        break;
    }
}

// Database configuration
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: '');
define('DB_NAME', getenv('DB_NAME') ?: 'ufazienclitest_db');
define('DB_PORT', getenv('DB_PORT') ?: '3306');

// Create database connection
function getDBConnection() {
    try {
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $conn = new PDO($dsn, DB_USER, DB_PASSWORD);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $conn->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        
        return $conn;
    } catch (PDOException $e) {
        die("Database connection error: " . $e->getMessage());
    }
}

// Alias for compatibility
function get_db_connection() {
    return getDBConnection();
}
